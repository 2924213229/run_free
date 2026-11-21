#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速使用脚本 - 简化版（首次完整 + 后续简化）

用法：
  # 第一次使用时（需要登录）
  python3 quick_use.py --login --user <userid> --password <pwd> --run
  
  # 后续使用时（已有 session.json，只需跑步和查看成绩）
  python3 quick_use.py --run --distance 2000 --time 720

退出登录：python3 go.py logout
"""

import argparse
import json
import os
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from sport_client import SportClient792


def load_session():
    """加载 session 文件，如果没有则退出"""
    session_file = os.path.join(BASE, ".session.json")
    
    if not os.path.exists(session_file):
        print("\n⚠️ 未找到 .session.json 文件")
        print("   请先登录：python3 go.py login --user <userid> --password <pwd>")
        return None
    
    with open(session_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data


def cmd_run(args):
    """跑步"""
    # Load session or use provided credentials
    if args.login and (args.user or args.password):
        username = args.user
        password = args.password
        
        client = SportClient792()
        res = client.login(username, password)
        
        if not res.success:
            print(f"登录失败：code={res.error_code} 原因={res.message}")
            return 1
        
        uid = client.uid
        token = client.token
        unid = client.unid
        
        # Save session for next run
        with open(os.path.join(BASE, ".session.json"), "w", encoding="utf-8") as f:
            json.dump({"uid": uid, "token": token, "unid": unid}, f)
    else:
        # Load from session file
        data = load_session()
        
        if not data:
            print("请先登录：python3 go.py login --user <userid> --password <pwd>")
            return 1
        
        uid = data["uid"]
        token = data["token"]
        unid = data.get("unid")
    
    # Create running client with credentials
    c = SportClient792(uid=uid, token=token, unid=unid)
    
    print(f"\n开始跑步：距离={args.distance}m 时长={args.time}s mode={args.mode}")
    
    try:
        res = c.execute_run(
            target_distance_m=args.distance,
            target_time_sec=args.time,
            sport_type=args.mode,
        )
        
        if res.success:
            print(f"\n提交成功：rrid={res.rrid} 里程={res.total_distance}m "
                  f"耗时={res.total_time}s 状态={'达标' if res.is_valid else '未达标'}")
            
            # Save details for next check
            with open(os.path.join(BASE, ".last_run.json"), "w", encoding="utf-8") as f:
                json.dump({"rrid": res.rrid, "distance": res.total_distance}, f)
        else:
            print(f"\n提交失败：code={res.error_code} 原因={res.message}")
            
    except Exception as e:
        import traceback
        print(f"执行异常：{e}")
        traceback.print_exc()
        return 1


def cmd_check(args):
    """查看成绩和有效公里数"""
    # Load session or use provided credentials
    if args.login and (args.user or args.password):
        username = args.user
        password = args.password
        
        client = SportClient792()
        res = client.login(username, password)
        
        if not res.success:
            print(f"登录失败：code={res.error_code} 原因={res.message}")
            return 1
        
        uid = client.uid
        token = client.token
        unid = client.unid
    else:
        # Load from session file
        data = load_session()
        
        if not data:
            print("请先登录：python3 go.py login --user <userid> --password <pwd>")
            return 1
        
        uid = data["uid"]
        token = data["token"]
        unid = data.get("unid")
    
    # Create clients for checking
    c_profile = SportClient792(uid=uid, token=token, unid=unid)
    c_history = SportClient792(uid=uid, token=token, unid=unid)
    
    print(f"\n{'='*60}")
    print("查看成绩和有效公里数")
    print(f"{'='*60}")
    
    # Get semester progress (effective distance)
    res = c_profile.get_semester_progress(run_mode=1)
    if res:
        print(f"\n[学期进度] 有效距离：{res.total_completed_distance:.2f}km")
        target = res.target_distance
        remaining = res.remaining_distance
        print(f"目标距离：{target:.2f}km | 剩余：{remaining:.2f}km")
    
    # Get recent run records
    records_res = c_history.get_run_records(page_num=1, page_size=5)
    if records_res and "data" in records_res:
        data = records_res["data"]
        print(f"\n[最近跑步记录] 共 {len(data)} 条:")
        
        # Sort by time descending
        sorted_data = sorted(data, key=lambda x: x.get("stopTime", 0), reverse=True)
        
        for i, rec in enumerate(sorted_data[:3]):
            stop_time = datetime.fromtimestamp(rec["stopTime"] / 1000)
            status_msg = "达标" if rec.get("complete") else f"未达标 ({rec.get('unCompleteReason', '未知')})"
            
            print(f"\n[{i+1}] {stop_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    里程：{rec['totalDis']}m | 状态：{status_msg}")
        
        # Show latest record details if available
        if sorted_data:
            latest = sorted_data[0]
            rrid = latest.get("rrid")
            if rrid:
                print(f"\n[详细记录]")
                detail_res = c_history.get_one_record(rrid=rrid)
                if detail_res:
                    print(f"    步频：{detail_res.avg_step_freq}步/分钟")
                    print(f"    平均速度：{detail_res.avg_speed:.2f}m/s")
    
    # Show last run details from file if available
    last_run_file = os.path.join(BASE, ".last_run.json")
    if os.path.exists(last_run_file):
        with open(last_run_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        print(f"\n[上次跑步详情]")
        print(f"  rrid={data.get('rrid')} | 距离：{data.get('distance')}m")
    
    # Show current session status
    with open(os.path.join(BASE, ".session.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"\n[当前会话] uid={data['uid']} unid={data.get('unid', 'N/A')}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(description="快速使用脚本 - 简化版（首次完整 + 后续简化）")
    
    # Add login flag (optional)
    parser.add_argument("--login", action="store_true", 
                       help="执行登录流程（需要 --user/--password）")
    
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    
    # Run command  
    p = subparsers.add_parser("run", help="生成轨迹并提交一次跑步")
    p.add_argument("--login", action="store_true", default=False, 
                   help="执行登录（需要 --user/--password）")
    p.add_argument("--user", "-u", type=str, default=None, 
                   help="用户 ID/手机号（可选，从 session.json 读取）")
    p.add_argument("--password", "-p", type=str, default=None, 
                   help="密码（可选）")
    p.add_argument("--mode", "-m", type=int, default=1, choices=[1, 6], 
                   help="跑步模式：1-计分跑，6-自由跑（默认计分跑）")
    p.add_argument("--distance", "-d", type=int, default=2000, 
                   help="目标距离米数（默认 2000m）")
    p.add_argument("--time", "-t", type=int, default=720, 
                   help="目标时长秒数（默认 720s）")
    p.set_defaults(func=cmd_run)
    
    # Check command  
    p = subparsers.add_parser("check", help="查看成绩和有效公里数")
    p.add_argument("--login", action="store_true", default=False, 
                   help="执行登录（需要 --user/--password）")
    p.set_defaults(func=cmd_check)
    
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
