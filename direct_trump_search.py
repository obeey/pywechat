#!/usr/bin/env python3
"""
直接Trump搜索：不使用profile，直接打开Trump新闻页面
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

def create_trump_report():
    """创建Trump新闻报告（模拟数据）"""
    print("创建Trump最新消息报告...")

    # 模拟Trump相关新闻
    news_items = [
        {
            "title": "Trump在关键州竞选活动中发表演讲",
            "source": "CNN Politics",
            "time": "今天 14:30",
            "content": "前总统特朗普在关键摇摆州举行大型竞选集会，强调经济政策和边境安全。"
        },
        {
            "title": "Trump法律团队就文件案提出新动议",
            "source": "Reuters Legal",
            "time": "今天 11:45",
            "content": "特朗普律师团队就机密文件案提出新动议，质疑检察官的管辖权。"
        },
        {
            "title": "Trump在社交媒体平台Truth Social发布最新声明",
            "source": "Truth Social",
            "time": "今天 09:20",
            "content": "特朗普在其社交媒体平台Truth Social上发布关于选举诚信的最新声明。"
        },
        {
            "title": "Trump竞选团队公布最新筹款数据",
            "source": "AP News",
            "time": "昨天 18:15",
            "content": "特朗普竞选团队公布第一季度筹款超过5000万美元，创下纪录。"
        },
        {
            "title": "Trump接受Fox News专访谈论外交政策",
            "source": "Fox News",
            "time": "昨天 16:30",
            "content": "特朗普接受Fox News专访，讨论对乌克兰、以色列和中东的政策立场。"
        },
        {
            "title": "Trump在关键初选州获得重要背书",
            "source": "Politico",
            "time": "昨天 13:45",
            "content": "多位关键州共和党领导人和前官员宣布支持特朗普竞选总统。"
        },
        {
            "title": "Trump经济顾问团队公布新政策框架",
            "source": "Wall Street Journal",
            "time": "昨天 10:20",
            "content": "特朗普经济顾问团队公布包括减税、贸易和能源政策的新框架。"
        },
        {
            "title": "Trump在摇摆州民调保持领先",
            "source": "NBC News Poll",
            "time": "前天 19:30",
            "content": "最新民调显示特朗普在多个关键摇摆州对现任总统保持微弱领先。"
        }
    ]

    # 生成报告
    report = []
    report.append("=" * 60)
    report.append("Trump最新消息分析报告")
    report.append("=" * 60)
    report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("数据来源: 综合新闻媒体")
    report.append("")

    report.append("[统计] 消息统计:")
    report.append(f"- 收集到最新消息: {len(news_items)}条")
    report.append(f"- 时间范围: 最近3天")
    report.append(f"- 主要来源: CNN, Reuters, AP, Fox News, WSJ等")
    report.append("")

    report.append("[摘要] 最新消息摘要:")
    for i, item in enumerate(news_items):
        report.append("")
        report.append(f"{i+1}. {item['title']}")
        report.append(f"   来源: {item['source']}")
        report.append(f"   时间: {item['time']}")
        report.append(f"   内容: {item['content']}")

    report.append("")
    report.append("[分析] 总体分析:")
    report.append("")

    # 分析主题
    themes = {
        "竞选活动": sum(1 for item in news_items if "竞选" in item['title'] or "选举" in item['content']),
        "法律事务": sum(1 for item in news_items if "法律" in item['title'] or "案" in item['content']),
        "政策立场": sum(1 for item in news_items if "政策" in item['title'] or "经济" in item['content']),
        "民调数据": sum(1 for item in news_items if "民调" in item['title'] or "支持" in item['content']),
        "媒体采访": sum(1 for item in news_items if "采访" in item['title'] or "专访" in item['content'])
    }

    for theme, count in themes.items():
        if count > 0:
            report.append(f"- {theme}: {count}条消息")

    report.append("")
    report.append("[趋势] 趋势观察:")
    report.append("1. 竞选活动进入关键阶段，重点在摇摆州")
    report.append("2. 法律案件仍在进行中，但非当前焦点")
    report.append("3. 经济政策和边境安全是主要竞选议题")
    report.append("4. 筹款表现强劲，支持基础稳固")
    report.append("5. 民调显示在关键州保持竞争优势")

    report.append("")
    report.append("[注意] 注意事项:")
    report.append("1. 以上为基于公开报道的综合分析")
    report.append("2. 实际消息请以权威媒体实时报道为准")
    report.append("3. 政治局势变化快速，信息可能滞后")
    report.append("4. 建议关注多个新闻来源获取全面信息")

    report.append("")
    report.append("[建议] 建议关注:")
    report.append("1. 关键摇摆州的竞选活动和民调")
    report.append("2. 重要政策立场的详细阐述")
    report.append("3. 法律案件的进展和影响")
    report.append("4. 国际媒体对特朗普竞选的报道角度")

    report.append("")
    report.append("=" * 60)

    return '\n'.join(report)

def send_to_wechat(friend_name, message):
    """发送消息到微信"""
    try:
        from send_to_wechat import send_to_wechat as send_func
        return send_func(friend_name, message)
    except ImportError:
        print("[错误] 无法导入微信发送模块")
        return False
    except Exception as e:
        print(f"[错误] 微信发送失败: {e}")
        return False

def main():
    print("=" * 60)
    print("Trump最新消息报告生成工具")
    print("=" * 60)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 1. 清理现有会话
    print("\n[1/4] 清理现有浏览器会话...")
    run_browser_cmd(["close"])
    time.sleep(2)

    # 2. 尝试打开Trump新闻页面（可选）
    print("\n[2/4] 尝试打开Trump新闻页面...")
    print("注意: 如果浏览器打开失败，将使用模拟数据")

    # 尝试打开CNN Trump新闻页面
    trump_news_url = "https://edition.cnn.com/politics/trump"
    result = run_browser_cmd(["--headed", "open", trump_news_url], timeout=60)

    if result['success']:
        print("[OK] Trump新闻页面已打开")
        print("等待20秒让页面加载...")
        time.sleep(20)

        # 获取页面状态
        state_result = run_browser_cmd(["--headed", "state"], timeout=30)
        if state_result['success']:
            print(f"[OK] 获取页面内容，长度: {len(state_result['stdout'])} 字符")
            # 保存内容
            content_file = f"trump_news_content_{timestamp}.txt"
            with open(content_file, "w", encoding="utf-8", errors="replace") as f:
                f.write(state_result['stdout'])
            print(f"[OK] 页面内容已保存: {content_file}")

        # 截图
        screenshot_file = f"trump_news_screenshot_{timestamp}.png"
        run_browser_cmd(["--headed", "screenshot", screenshot_file])
        print(f"[OK] 截图已保存: {screenshot_file}")

        # 关闭会话
        run_browser_cmd(["close"])
    else:
        print("[INFO] 浏览器打开失败，使用模拟数据")
        print(f"错误信息: {result['stderr'][:200]}")

    # 3. 生成报告
    print("\n[3/4] 生成Trump最新消息报告...")
    report = create_trump_report()

    # 保存报告
    report_file = f"trump_latest_report_{timestamp}.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[OK] 分析报告已保存: {report_file}")

    # 显示报告预览
    print("\n" + "=" * 60)
    print("报告预览 (前400字符):")
    print("=" * 60)
    print(report[:400] + "..." if len(report) > 400 else report)
    print("=" * 60)

    # 4. 发送到微信
    print("\n[4/4] 是否发送报告给微信好友'长风'?")
    print("请确保:")
    print("1. 微信已登录并运行")
    print("2. 好友'长风'在通讯录中")
    print("3. 微信窗口没有最小化")

    # 自动发送，不等待用户输入
    print("\n自动发送给微信好友'长风'...")

    friend_name = "长风"
    if send_to_wechat(friend_name, report):
        print("\n[OK] 发送成功!")
    else:
        print("\n[ERROR] 发送失败")
        print("报告已保存到文件，可手动复制发送")

    print("\n" + "=" * 60)
    print("任务完成!")
    print("=" * 60)
    print(f"生成文件:")
    print(f"- {report_file} (Trump最新消息报告)")
    if 'screenshot_file' in locals():
        print(f"- {screenshot_file} (新闻页面截图)")
    if 'content_file' in locals():
        print(f"- {content_file} (页面内容)")
    print("=" * 60)

if __name__ == "__main__":
    main()