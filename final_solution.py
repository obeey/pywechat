#!/usr/bin/env python3
"""
最终解决方案：直接使用browser-use获取知乎邀请问题并发送给微信
"""

import os
import subprocess
import time
from datetime import datetime

def run_browser_cmd(cmd_args):
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
            timeout=30,
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

def get_zhihu_invitations():
    """获取知乎邀请问题"""
    print("=" * 60)
    print("获取知乎邀请问题")
    print("=" * 60)

    # 1. 关闭现有会话
    print("\n1. 关闭现有会话...")
    run_browser_cmd(["close"])
    time.sleep(2)

    # 2. 打开知乎邀请页面
    print("\n2. 打开知乎邀请页面...")
    print("   页面: https://www.zhihu.com/question/waiting")
    print("   请在弹出的浏览器窗口中登录知乎账号（如果需要）")

    result = run_browser_cmd(["--headed", "open", "https://www.zhihu.com/question/waiting"])

    if not result['success']:
        print(f"打开页面失败: {result['stderr']}")
        return None

    print("页面已打开，等待30秒让您登录...")

    # 3. 等待用户登录
    wait_time = 30
    print(f"等待 {wait_time} 秒，请在此期间登录知乎账号...")
    time.sleep(wait_time)

    # 4. 获取页面状态
    print("\n3. 获取页面状态...")
    state_result = run_browser_cmd(["--headed", "state"])

    if not state_result['success'] or not state_result['stdout']:
        print(f"获取页面状态失败: {state_result['stderr']}")
        return None

    state_text = state_result['stdout']

    # 保存状态
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    state_file = f"zhihu_state_{timestamp}.txt"
    with open(state_file, "w", encoding="utf-8", errors="replace") as f:
        f.write(state_text)

    print(f"页面状态已保存: {state_file}")
    print(f"状态长度: {len(state_text)} 字符")

    # 5. 截图
    print("\n4. 截图保存...")
    screenshot_file = f"zhihu_screenshot_{timestamp}.png"
    run_browser_cmd(["--headed", "screenshot", screenshot_file])
    print(f"截图已保存: {screenshot_file}")

    # 6. 关闭会话
    print("\n5. 关闭浏览器会话...")
    run_browser_cmd(["close"])

    return state_text

def analyze_content(content):
    """分析页面内容"""
    print("\n" + "=" * 60)
    print("分析页面内容")
    print("=" * 60)

    if not content:
        return "未获取到页面内容。"

    # 简单提取问题
    lines = content.split('\n')
    questions = []

    for line in lines:
        line = line.strip()
        if len(line) < 10:
            continue

        # 查找包含问号的行
        if '?' in line or '？' in line:
            # 简单清理
            import re
            text = re.sub(r'\[\d+\]', '', line)
            text = re.sub(r'<[^>]+>', '', text)
            text = ' '.join(text.split())

            if len(text) >= 8:
                questions.append(text[:100])

    # 去重
    unique_questions = []
    seen = set()
    for q in questions:
        if q not in seen:
            seen.add(q)
            unique_questions.append(q)

    print(f"提取到 {len(unique_questions)} 个问题")

    # 生成报告
    report = []
    report.append("知乎邀请问题分析报告")
    report.append("=" * 50)
    report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")

    if unique_questions:
        # 限制为10个问题
        questions_to_show = unique_questions[:10]
        report.append(f"发现邀请问题: {len(questions_to_show)} 个")
        report.append("")

        report.append("最新邀请问题:")
        for i, q in enumerate(questions_to_show):
            report.append(f"{i+1}. {q}")

        # 简单统计
        lengths = [len(q) for q in questions_to_show]
        avg_len = sum(lengths) / len(lengths)

        report.append("")
        report.append("问题特点:")
        report.append(f"- 平均长度: {avg_len:.0f} 字符")
        report.append(f"- 最短: {min(lengths)} 字符")
        report.append(f"- 最长: {max(lengths)} 字符")

        # 类型分析
        tech_count = sum(1 for q in questions_to_show if any(kw in q.lower() for kw in ['程序', '代码', 'python', 'java', 'c++', '算法']))
        study_count = sum(1 for q in questions_to_show if any(kw in q.lower() for kw in ['学习', '教育', '学校', '考试', '课程', '大学']))
        work_count = sum(1 for q in questions_to_show if any(kw in q.lower() for kw in ['工作', '职场', '面试', '职业', '薪资', '公司']))

        report.append("")
        report.append("问题类型:")
        if tech_count > 0:
            report.append(f"- 技术相关: {tech_count} 个")
        if study_count > 0:
            report.append(f"- 学习相关: {study_count} 个")
        if work_count > 0:
            report.append(f"- 工作相关: {work_count} 个")

        report.append("")
        report.append("分析发现:")
        if len(questions_to_show) >= 8:
            report.append("- 邀请量较多，您在相关领域有一定影响力")
        elif len(questions_to_show) >= 4:
            report.append("- 邀请量适中，保持活跃")
        else:
            report.append("- 邀请量较少，可考虑增加活跃度")

        if tech_count > len(questions_to_show) * 0.4:
            report.append("- 问题主要集中在技术领域")
        if study_count > len(questions_to_show) * 0.4:
            report.append("- 问题主要集中在学习领域")
        if work_count > len(questions_to_show) * 0.4:
            report.append("- 问题主要集中在职场领域")

        if avg_len > 50:
            report.append("- 问题描述较为详细，需要深入思考")
        elif avg_len < 25:
            report.append("- 问题较为简短，适合快速回答")

    else:
        report.append("未找到邀请问题")
        report.append("")
        report.append("可能原因:")
        report.append("1. 尚未登录知乎账号")
        report.append("2. 没有待回答的邀请问题")
        report.append("3. 页面内容解析失败")

    report.append("")
    report.append("建议:")
    report.append("1. 优先回答您擅长的领域问题")
    report.append("2. 简短问题可快速回复建立互动")
    report.append("3. 复杂问题可提供分点详细解答")
    report.append("4. 定期清理已回答的问题")

    return '\n'.join(report)

def send_to_wechat(friend_name, message):
    """发送消息到微信"""
    try:
        from pyweixin import Messages, GlobalConfig

        # 配置参数
        GlobalConfig.close_weixin = False
        GlobalConfig.is_maximize = False
        GlobalConfig.send_delay = 0.5

        print(f"\n发送消息给微信好友: {friend_name}")

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

    except ImportError:
        print("错误: 无法导入pyweixin模块")
        print("请确保已安装pyweixin依赖")
        return False
    except Exception as e:
        print(f"微信发送失败: {e}")
        return False

def main():
    print("知乎邀请问题分析工具")
    print("=" * 60)

    # 1. 获取知乎页面内容
    content = get_zhihu_invitations()

    # 2. 分析内容
    report = analyze_content(content)

    # 3. 显示报告
    print("\n" + "=" * 60)
    print("分析报告:")
    print("=" * 60)
    print(report)

    # 4. 保存报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"zhihu_final_report_{timestamp}.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n报告已保存: {report_file}")

    # 5. 询问是否发送到微信
    print("\n" + "=" * 60)
    print("是否发送报告给微信好友'长风'?")
    print("请确保:")
    print("1. 微信已登录并运行")
    print("2. 好友'长风'在通讯录中")
    print("3. 微信窗口没有最小化")

    response = input("\n输入 'y' 确认发送，其他键跳过: ")

    if response.lower() == 'y':
        print("\n正在发送给微信好友'长风'...")
        if send_to_wechat("长风", report):
            print("\n发送成功!")
        else:
            print("\n发送失败，报告已保存到文件")
    else:
        print("\n跳过微信发送，报告已保存到文件")

    print("\n" + "=" * 60)
    print("分析完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()