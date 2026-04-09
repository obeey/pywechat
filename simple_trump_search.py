#!/usr/bin/env python3
"""
简化版Trump搜索：直接使用browser-use命令
"""

import subprocess
import os
import sys
import time
from datetime import datetime

def run_browser_cmd(cmd_args, timeout=30):
    """运行browser-use命令"""
    browser_path = r"C:\Users\Nico\.browser-use-env\Scripts\browser-use.exe"
    cmd = [browser_path] + cmd_args

    print(f"[执行] {' '.join(cmd)}")

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            env=env
        )

        # 解码输出
        def decode(data):
            if not data:
                return ""
            try:
                return data.decode('utf-8')
            except:
                try:
                    return data.decode('gbk', errors='ignore')
                except:
                    return str(data)

        stdout = decode(result.stdout)
        stderr = decode(result.stderr)

        return {
            'success': result.returncode == 0,
            'stdout': stdout,
            'stderr': stderr
        }

    except subprocess.TimeoutExpired:
        print("[超时] 命令执行超时")
        return {'success': False, 'stdout': '', 'stderr': '超时'}
    except Exception as e:
        print(f"[错误] 命令执行失败: {e}")
        return {'success': False, 'stdout': '', 'stderr': str(e)}

def analyze_content(content):
    """分析内容"""
    print(f"分析内容，长度: {len(content)} 字符")

    if not content or len(content) < 100:
        return "未获取到有效的页面内容"

    # 简单提取Trump相关内容
    trump_keywords = ['trump', 'Trump', 'TRUMP', '特朗普', '川普', '唐纳德', 'Donald']
    lines = content.split('\n')
    messages = []

    for line in lines:
        line = line.strip()
        if len(line) < 10:
            continue

        if any(keyword in line for keyword in trump_keywords):
            messages.append(line[:150])

    # 去重
    unique_messages = []
    seen = set()
    for msg in messages:
        if msg not in seen:
            seen.add(msg)
            unique_messages.append(msg)

    # 生成报告
    report = []
    report.append("=" * 60)
    report.append("Trump相关消息分析报告")
    report.append("=" * 60)
    report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    if unique_messages:
        report.append(f"发现Trump相关消息: {len(unique_messages)}条")
        report.append("")

        for i, msg in enumerate(unique_messages[:10]):
            report.append(f"{i+1}. {msg}")
            report.append("")

        report.append("分析说明:")
        report.append("1. 以上为页面中提取的Trump相关内容")
        report.append("2. 建议关注权威新闻媒体官方账号")
        report.append("3. 注意验证重要消息的原始来源")
    else:
        report.append("未找到明显的Trump相关消息")
        report.append("")
        report.append("可能原因:")
        report.append("1. 页面内容可能未完全加载")
        report.append("2. 搜索词可能需要调整")
        report.append("3. Facebook算法可能限制了搜索结果")

    report.append("")
    report.append("=" * 60)

    return '\n'.join(report)

def main():
    print("=" * 60)
    print("Trump消息搜索工具")
    print("=" * 60)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 1. 清理现有会话
    print("\n[1/4] 清理现有会话...")
    run_browser_cmd(["close"])
    time.sleep(2)

    # 2. 打开Facebook
    print("\n[2/4] 打开Facebook...")
    print("注意: 将使用Nico的Chrome profile打开Facebook")
    print("如果未登录，请在弹出的浏览器窗口中登录")

    result = run_browser_cmd(["--profile", "Default", "--headed", "open", "https://www.facebook.com"], timeout=60)

    if not result['success']:
        print(f"[ERROR] Facebook打开失败: {result['stderr'][:200]}")
        print("尝试直接打开Trump搜索页面...")

        # 尝试直接打开Trump搜索页面
        trump_search_url = "https://www.facebook.com/search/top?q=Trump"
        result = run_browser_cmd(["--profile", "Default", "--headed", "open", trump_search_url], timeout=60)

        if not result['success']:
            print(f"[ERROR] 搜索页面打开失败: {result['stderr'][:200]}")
            sys.exit(1)

    print("[OK] 页面已打开")
    print("等待30秒让页面加载和登录...")
    time.sleep(30)

    # 3. 获取页面状态
    print("\n[3/4] 获取页面状态...")
    state_result = run_browser_cmd(["--profile", "Default", "--headed", "state"], timeout=30)

    if not state_result['success'] or not state_result['stdout']:
        print(f"[ERROR] 获取页面状态失败: {state_result['stderr'][:200]}")
        state_text = "无法获取页面内容"
    else:
        state_text = state_result['stdout']
        print(f"[OK] 页面状态获取成功，长度: {len(state_text)} 字符")

        # 保存内容
        content_file = f"facebook_trump_content_{timestamp}.txt"
        with open(content_file, "w", encoding="utf-8", errors="replace") as f:
            f.write(state_text)
        print(f"[OK] 页面内容已保存: {content_file}")

    # 4. 截图
    print("\n[4/4] 截图保存...")
    screenshot_file = f"facebook_trump_screenshot_{timestamp}.png"
    run_browser_cmd(["--profile", "Default", "--headed", "screenshot", screenshot_file])
    print(f"[OK] 截图已保存: {screenshot_file}")

    # 分析内容
    print("\n分析页面内容...")
    report = analyze_content(state_text if 'state_text' in locals() else "")

    # 保存报告
    report_file = f"trump_report_{timestamp}.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[OK] 分析报告已保存: {report_file}")

    # 显示报告
    print("\n" + "=" * 60)
    print("分析报告:")
    print("=" * 60)
    print(report[:500] + "..." if len(report) > 500 else report)
    print("=" * 60)

    # 询问是否发送到微信
    print("\n是否发送报告给微信好友'长风'?")
    print("请确保:")
    print("1. 微信已登录并运行")
    print("2. 好友'长风'在通讯录中")
    print("3. 微信窗口没有最小化")

    confirm = input("\n输入 'y' 确认发送，其他键跳过: ")

    if confirm.lower() == 'y':
        print("\n正在发送给微信好友'长风'...")

        try:
            from send_to_wechat import send_to_wechat as send_func
            friend_name = "长风"
            if send_func(friend_name, report):
                print("\n[OK] 发送成功!")
            else:
                print("\n[ERROR] 发送失败")
                print("报告已保存到文件，可手动复制发送")
        except ImportError:
            print("\n[ERROR] 无法导入微信发送模块")
            print("报告已保存到文件，可手动复制发送")
    else:
        print("\n跳过微信发送")

    # 关闭会话
    print("\n关闭浏览器会话...")
    run_browser_cmd(["close"])

    print("\n" + "=" * 60)
    print("任务完成!")
    print("=" * 60)
    print(f"生成文件:")
    print(f"- {report_file} (分析报告)")
    print(f"- {screenshot_file} (截图)")
    if 'content_file' in locals():
        print(f"- {content_file} (页面内容)")
    print("=" * 60)

if __name__ == "__main__":
    main()