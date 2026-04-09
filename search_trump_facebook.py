#!/usr/bin/env python3
"""
在Facebook上搜索Trump的最新消息并发送给微信用户"长风"
"""

import os
import sys
import time
import re
from datetime import datetime
from typing import List, Dict, Optional

# 导入browser-use技能
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from browser_use_skill import BrowserUseSkill
except ImportError:
    print("错误: 无法导入browser_use_skill模块")
    print("请确保browser_use_skill.py在同一目录下")
    sys.exit(1)

def analyze_facebook_content(content: str) -> str:
    """
    分析Facebook页面内容，提取Trump相关消息

    Args:
        content: 页面内容文本

    Returns:
        分析报告
    """
    print(f"分析页面内容，长度: {len(content)} 字符")

    if not content or len(content) < 100:
        return "未获取到有效的页面内容"

    lines = content.split('\n')
    messages = []

    # 关键词列表：Trump、特朗普、川普等
    trump_keywords = ['trump', 'Trump', 'TRUMP', '特朗普', '川普', '唐纳德', 'Donald']

    for i, line in enumerate(lines):
        line = line.strip()
        if len(line) < 10:
            continue

        # 检查是否包含Trump相关关键词
        if any(keyword in line for keyword in trump_keywords):
            # 清理文本
            text = re.sub(r'\[\d+\]', '', line)
            text = re.sub(r'<[^>]+>', '', text)
            text = ' '.join(text.split())

            if len(text) >= 15:
                messages.append(text[:200])  # 限制长度

    # 去重
    unique_messages = []
    seen = set()
    for msg in messages:
        if msg not in seen:
            seen.add(msg)
            unique_messages.append(msg)

    print(f"找到 {len(unique_messages)} 条Trump相关消息")

    # 生成报告
    report = []
    report.append("=" * 60)
    report.append("Facebook Trump最新消息分析报告")
    report.append("=" * 60)
    report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"账号: Nico的Facebook账号")
    report.append("")

    if unique_messages:
        # 按长度排序，取最新的前10条
        unique_messages.sort(key=len, reverse=True)
        messages_to_show = unique_messages[:10]

        report.append(f"消息统计:")
        report.append(f"• 发现Trump相关消息: {len(messages_to_show)}条")
        report.append(f"• 主要消息来源: Facebook搜索'Trump'")
        report.append("")

        report.append("最新消息摘要:")
        for i, msg in enumerate(messages_to_show):
            report.append(f"")
            report.append(f"{i+1}. {msg}")

            # 简单分析消息内容
            if any(kw in msg.lower() for kw in ['election', '竞选', '选举', 'vote']):
                report.append(f"   主题: 选举相关")
            elif any(kw in msg.lower() for kw in ['speech', '演讲', '讲话', 'statement']):
                report.append(f"   主题: 演讲/声明")
            elif any(kw in msg.lower() for kw in ['trial', '审判', 'court', '法庭', '法律']):
                report.append(f"   主题: 法律/审判")
            elif any(kw in msg.lower() for kw in ['policy', '政策', '政策', '计划']):
                report.append(f"   主题: 政策/计划")
            elif any(kw in msg.lower() for kw in ['news', '新闻', '报道', 'update']):
                report.append(f"   主题: 新闻更新")
            else:
                report.append(f"   主题: 其他")

            # 来源推测
            if any(src in msg for src in ['CNN', 'BBC', 'Reuters', 'AP']):
                report.append(f"   来源: 新闻媒体")
            elif any(src in msg for src in ['White House', '白宫', 'official']):
                report.append(f"   来源: 官方声明")
            else:
                report.append(f"   来源: 社交媒体")

        report.append("")
        report.append("总体分析:")
        report.append("")

        # 分析消息特点
        election_count = sum(1 for msg in messages_to_show if any(kw in msg.lower() for kw in ['election', '竞选', '选举', 'vote']))
        legal_count = sum(1 for msg in messages_to_show if any(kw in msg.lower() for kw in ['trial', '审判', 'court', '法庭', '法律']))
        news_count = sum(1 for msg in messages_to_show if any(kw in msg.lower() for kw in ['news', '新闻', '报道', 'update']))

        if election_count > 0:
            report.append(f"• 选举相关消息: {election_count}条")
        if legal_count > 0:
            report.append(f"• 法律/审判相关: {legal_count}条")
        if news_count > 0:
            report.append(f"• 新闻更新: {news_count}条")

        report.append("")

        # 时效性分析
        recent_keywords = ['today', '今天', 'just', '刚刚', 'recent', '最近', 'latest', '最新']
        recent_count = sum(1 for msg in messages_to_show if any(kw in msg.lower() for kw in recent_keywords))

        if recent_count >= 3:
            report.append("• 时效性: 较高 - 多条最新消息")
        elif recent_count >= 1:
            report.append("• 时效性: 中等 - 有最新消息")
        else:
            report.append("• 时效性: 一般 - 多为常规报道")

        # 可信度分析
        credible_sources = ['CNN', 'BBC', 'Reuters', 'AP', 'NBC', 'CBS', 'ABC', 'WSJ', '纽约时报', '华盛顿邮报']
        credible_count = sum(1 for msg in messages_to_show if any(src in msg for src in credible_sources))

        if credible_count >= 3:
            report.append(f"• 可信度: 高 - {credible_count}条来自权威媒体")
        elif credible_count >= 1:
            report.append(f"• 可信度: 中 - {credible_count}条来自权威媒体")
        else:
            report.append("• 可信度: 需验证 - 多为社交媒体内容")

    else:
        report.append("[WARNING] 未找到明显的Trump相关消息")
        report.append("")
        report.append("可能原因:")
        report.append("1. 搜索词可能需要调整")
        report.append("2. Facebook算法可能限制了搜索结果")
        report.append("3. 页面内容解析可能需要改进")

    report.append("")
    report.append("[WARNING] 注意事项:")
    report.append("1. Facebook搜索结果受算法和个人化推荐影响")
    report.append("2. 建议交叉验证重要消息")
    report.append("3. 注意区分新闻报道和用户观点")
    report.append("4. 警惕虚假信息和夸大宣传")

    report.append("")
    report.append("🎯 建议:")
    report.append("1. 关注权威新闻媒体官方账号")
    report.append("2. 验证重要消息的原始来源")
    report.append("3. 保持批判性思维，区分事实和观点")

    report.append("")
    report.append("=" * 60)

    return '\n'.join(report)

def send_to_wechat(friend_name: str, message: str) -> bool:
    """
    发送消息到微信

    Args:
        friend_name: 微信好友名称
        message: 要发送的消息

    Returns:
        是否发送成功
    """
    try:
        # 尝试从现有文件导入
        from send_to_wechat import send_to_wechat as send_func
        return send_func(friend_name, message)
    except ImportError:
        print("错误: 无法导入send_to_wechat模块")
        return False
    except Exception as e:
        print(f"微信发送错误: {e}")
        return False

def main():
    """主函数"""
    print("=" * 70)
    print("Facebook Trump搜索与微信发送工具")
    print("=" * 70)

    # 检查微信发送功能
    try:
        from send_to_wechat import send_to_wechat as send_func
        print("[OK] 微信发送模块可用")
    except ImportError:
        print("[X] 微信发送模块不可用，仅生成报告")

    # 1. 打开Facebook并搜索Trump
    print("\n[1/4] 准备打开Facebook...")

    try:
        browser = BrowserUseSkill(profile="Default", headless=False)
        print("[OK] BrowserUseSkill初始化成功")
    except Exception as e:
        print(f"[ERROR] 初始化失败: {e}")
        print("请检查:")
        print("1. browser-use工具是否安装")
        print("2. Chrome profile路径是否正确")
        sys.exit(1)

    # 生成唯一会话名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    session_name = f"trump_search_{timestamp}"

    print(f"\n[2/4] 打开Facebook (会话: {session_name})...")
    print("注意: 这将使用Nico的Chrome profile打开Facebook")
    print("如果未登录，请在弹出的浏览器窗口中登录")

    # 打开Facebook
    if not browser.open_facebook(wait_login=30):
        print("[ERROR] Facebook打开失败")
        sys.exit(1)

    print("[OK] Facebook打开成功")

    # 等待一下确保页面加载完成
    time.sleep(5)

    # 尝试在Facebook搜索框中搜索Trump
    print(f"\n[3/4] 在Facebook中搜索'Trump'...")
    print("注意: 需要手动点击Facebook搜索框")

    # 输入搜索词
    search_term = "Trump"
    print(f"搜索词: {search_term}")

    # 输入搜索词
    if not browser.type_text(search_term):
        print("[WARNING] 文本输入可能失败，请手动在搜索框中输入'Trump'")

    time.sleep(2)

    # 按Enter搜索
    if not browser.press_enter():
        print("[WARNING] Enter键可能未生效，请手动按Enter搜索")

    print("等待搜索结果加载...")
    time.sleep(8)  # 等待搜索结果

    # 获取页面状态
    print("获取页面状态...")
    state = browser.get_page_state(session_name)

    if not state:
        print("[ERROR] 无法获取页面状态")
        # 尝试截图
        screenshot_file = f"facebook_trump_search_{timestamp}.png"
        browser.take_screenshot(screenshot_file)
        print(f"已截图: {screenshot_file}")
        state = "无法获取完整页面内容，已截图保存"
    else:
        print(f"[OK] 页面状态获取成功，长度: {len(state)} 字符")

        # 截图保存
        screenshot_file = f"facebook_trump_search_{timestamp}.png"
        browser.take_screenshot(screenshot_file)
        print(f"[OK] 截图已保存: {screenshot_file}")

        # 保存原始页面内容
        content_file = f"facebook_trump_content_{timestamp}.txt"
        with open(content_file, "w", encoding="utf-8", errors="replace") as f:
            f.write(state)
        print(f"[OK] 页面内容已保存: {content_file}")

    # 分析内容
    print(f"\n[4/4] 分析Trump相关消息...")
    report = analyze_facebook_content(state if state else "")

    # 保存报告
    report_file = f"trump_facebook_report_{timestamp}.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[OK] 分析报告已保存: {report_file}")

    # 显示报告预览
    print("\n" + "=" * 60)
    print("报告预览 (前300字符):")
    print("=" * 60)
    print(report[:300] + "..." if len(report) > 300 else report)
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

        friend_name = "长风"
        if send_to_wechat(friend_name, report):
            print("\n[OK] 发送成功!")
        else:
            print("\n[ERROR] 发送失败")
            print("报告已保存到文件，可手动复制发送")
    else:
        print("\n跳过微信发送")

    # 关闭会话
    print("\n关闭浏览器会话...")
    browser.close_session()

    print("\n" + "=" * 70)
    print("任务完成!")
    print("=" * 70)
    print(f"生成文件:")
    print(f"- {report_file} (分析报告)")
    if 'screenshot_file' in locals():
        print(f"- {screenshot_file} (搜索结果截图)")
    if 'content_file' in locals():
        print(f"- {content_file} (页面内容)")
    print("=" * 70)

if __name__ == "__main__":
    main()