#!/usr/bin/env python3
"""
发送Trump报告给微信好友"长风"
"""

import os
import sys
from datetime import datetime

# 添加系统Python路径
sys.path.insert(0, r'C:\Users\Nico\AppData\Local\Programs\Python\Python312\Lib\site-packages')

def send_to_wechat(friend_name, message):
    """发送消息到微信"""
    try:
        # 添加当前目录到路径
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        from pyweixin import Messages, GlobalConfig

        # 配置参数
        GlobalConfig.close_weixin = False
        GlobalConfig.is_maximize = False
        GlobalConfig.send_delay = 0.5

        print(f"发送消息给微信好友: {friend_name}")

        # 分条发送长消息
        messages = []
        max_length = 400

        for i in range(0, len(message), max_length):
            chunk = message[i:i + max_length]
            messages.append(chunk)

        # 发送消息
        Messages.send_messages_to_friend(
            friend=friend_name,
            messages=messages
        )

        print("微信消息发送成功")
        return True

    except ImportError as e:
        print(f"错误: 无法导入pyweixin模块: {e}")
        print("请确保:")
        print("1. pyweixin目录在当前目录下")
        print("2. 所有依赖已安装")
        return False
    except Exception as e:
        print(f"微信发送失败: {e}")
        return False

def find_latest_trump_report():
    """查找最新的Trump报告"""
    import glob

    report_files = glob.glob("trump_latest_report_*.txt")
    if not report_files:
        print("未找到Trump报告文件")
        print("请先运行 direct_trump_search.py 生成报告")
        return None

    # 按修改时间排序，获取最新的
    latest_file = max(report_files, key=os.path.getmtime)
    return latest_file

def main():
    print("=" * 60)
    print("Trump报告微信发送工具")
    print("=" * 60)

    # 1. 查找最新报告
    report_file = find_latest_trump_report()
    if not report_file:
        return

    print(f"找到报告文件: {report_file}")

    # 2. 读取报告内容
    try:
        with open(report_file, "r", encoding="utf-8") as f:
            report_content = f.read()
    except Exception as e:
        print(f"读取报告文件失败: {e}")
        return

    print(f"报告长度: {len(report_content)} 字符")

    # 3. 显示报告预览
    print("\n报告预览 (前300字符):")
    print("-" * 40)
    print(report_content[:300] + "..." if len(report_content) > 300 else report_content)
    print("-" * 40)

    # 4. 发送到微信
    friend_name = "长风"
    print(f"\n正在发送给微信好友: {friend_name}...")
    print("请确保:")
    print("1. 微信已登录并运行")
    print("2. 好友'长风'在通讯录中")
    print("3. 微信窗口没有最小化")

    if send_to_wechat(friend_name, report_content):
        print("\n[OK] 发送成功!")
    else:
        print("\n[ERROR] 发送失败")
        print("报告已保存到文件，可手动复制发送")

    print("\n" + "=" * 60)
    print("完成")
    print("=" * 60)

if __name__ == "__main__":
    main()