#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""运动世界校园跑（7.4.01）自动刷

用法:
  python3 go.py login  --user <手机号> --password <密码>
  python3 go.py run    [--mode 1] [--distance 2000] [--time 720]
  python3 go.py status
  python3 go.py logout
"""

import argparse
import json
import os
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
SESSION = os.path.join(BASE, ".session.json")

from sport_client import SportClient792


def save_session(client):
    fd = os.open(SESSION, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"uid": client.uid, "token": client.token, "unid": client.unid},
                  f, ensure_ascii=False, indent=2)
    print(f"会话已保存: {SESSION}")


def load_session(required=True):
    if not os.path.exists(SESSION):
        if required:
            raise SystemExit("未找到会话，请先执行: python3 go.py login --user <手机号> --password <密码>")
        return None
    with open(SESSION, "r", encoding="utf-8") as f:
        return json.load(f)


def build_client(args=None):
    s = load_session()
    return SportClient792(
        uid=s["uid"], token=s["token"], unid=s.get("unid"),
        anchor_lat=getattr(args, "lat", 39.996099),
        anchor_lng=getattr(args, "lng", 116.364501),
    )


def cmd_login(args):
    client = SportClient792(anchor_lat=args.lat, anchor_lng=args.lng)
    res = client.login(args.user, args.password, progress_callback=print)
    if not res.success:
        print(f"登录失败: code={res.error_code} 原因={res.message}")
        return 1
    print(f"登录成功: uid={client.uid} unid={client.unid}")
    save_session(client)
    print("提示: 本客户端保持登录期间，手机端会提示'已在其他设备登录'。")
    print("      要让手机登录，请先执行: python3 go.py logout")
    return 0


def cmd_logout(args):
    s = load_session(required=False)
    if s:
        client = SportClient792(uid=s["uid"], token=s["token"], unid=s.get("unid"))
        print("正在注销服务端会话 ...")
        res = client.logout()
        if isinstance(res, dict) and res.get("error") == 10000:
            print("服务端会话已注销（token 已失效）")
        else:
            print(f"服务端注销返回: {res}")
    if os.path.exists(SESSION):
        os.remove(SESSION)
        print(f"本地会话已删除: {SESSION}")
    else:
        print("本地没有会话文件")
    return 0


def cmd_run(args):
    client = build_client(args)
    print(f"开始跑步: 距离={args.distance}m 时长={args.time}s 模式={args.mode}")
    res = client.execute_run(
        target_distance_m=args.distance,
        target_time_sec=args.time,
        sport_type=args.mode,
        progress_callback=lambda m: print(f"  {m}"),
    )
    if not res.success:
        print(f"提交失败: code={res.error_code} 原因={res.message}")
        if res.error_code in (401, 10003):
            print("会话已失效，请重新登录: python3 go.py login --user ... --password ...")
        return 1
    print(f"提交成功: rrid={res.rrid} 里程={res.total_distance}m 耗时={res.total_time}s "
          f"状态={'达标' if res.is_valid else '未达标'}")
    return 0


def _fmt_time(ms):
    try:
        return datetime.fromtimestamp(int(ms) / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ms)


def cmd_status(args):
    client = build_client(args)
    s = load_session()

    print("=" * 58)
    print("账号状态")
    print("=" * 58)
    print(f"uid={s['uid']}  unid={s.get('unid')}")

    sem = client.get_semester_progress(run_mode=1)
    summary = client.policy.get_semester_summary()

    if sem is None:
        print("\n会话已失效，请重新登录: python3 go.py login --user ... --password ...")
        return 1
    
    done_km = None
    if isinstance(summary, dict) and summary.get("error") == 10000 and summary.get("data"):
        d = summary["data"]
    if sem.raw.get("semesterValid"):
        done_km = float(sem.raw["semesterValid"]) / 1000.0
    if not done_km and sem.target_distance:
        done_km = sem.target_distance

    print(f"\n[学期] {sem.raw.get('sname') or sem.semester_name or '-'}")
    if done_km is None:
        done_km = sem.total_completed_distance
    if done_km:
        print(f"有效公里: {done_km:.2f} km")

    recs = client.get_history_records(page_num=1, page_size=5)
    data = recs.get("data") if isinstance(recs, dict) else None
    if isinstance(data, dict):
        data = data.get("list") or data.get("records") or []
    data = data or []

    print(f"\n[最近跑步] 共 {len(data)} 条")
    for i, r in enumerate(data[:5], 1):
        ok = "完成" if r.get("complete") else "未完成"
        print(f"  {i}. {_fmt_time(r.get('stopTime'))}  {r.get('totalDis')}m  {ok}  "
              f"步频={r.get('avgStepFreq')}  rrid={r.get('rrid')}")

    if data:
        last = data[0]
        detail = client.get_run_record_detail(int(last["rrid"]))
        print("\n[上次跑步状态]")
        print(f"  rrid      : {last.get('rrid')}")
        print(f"  开始/结束 : {_fmt_time(last.get('startTime'))} → {_fmt_time(last.get('stopTime'))}")
        print(f"  距离/有效 : {last.get('totalDis')}m / {last.get('validDis')}m")
        print(f"  时长/有效 : {last.get('totalTime')}s / {last.get('validTime')}s")
        print(f"  完成状态  : {'完成' if last.get('complete') else '未完成'}")
        if detail:
            print(f"  平均速度  : {detail.avg_speed} m/s")
            print(f"  步频      : {detail.avg_step_freq} 步/分钟")
            print(f"  卡路里    : {detail.calorie}")
    return 0


def main():
    p = argparse.ArgumentParser(description="运动世界校园跑 7.4.01 自动跑")
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("login", help="登录（手机号+密码，自动过极验）")
    q.add_argument("--user", "-u", required=True)
    q.add_argument("--password", "-p", required=True)
    q.add_argument("--lat", type=float, default=39.996099)
    q.add_argument("--lng", type=float, default=116.364501)
    q.set_defaults(func=cmd_login)

    q = sub.add_parser("run", help="生成轨迹并提交一次跑步")
    q.add_argument("--mode", "-m", type=int, default=1, choices=[1, 6])
    q.add_argument("--distance", "-d", type=int, default=2000)
    q.add_argument("--time", "-t", type=int, default=720)
    q.add_argument("--lat", type=float, default=39.996099)
    q.add_argument("--lng", type=float, default=116.364501)
    q.set_defaults(func=cmd_run)

    q = sub.add_parser("status", help="查看有效公里数与上次跑步状态")
    q.add_argument("--lat", type=float, default=39.996099)
    q.add_argument("--lng", type=float, default=116.364501)
    q.set_defaults(func=cmd_status)

    q = sub.add_parser("logout", help="注销服务端会话并删除本地会话")
    q.set_defaults(func=cmd_logout)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
