#!/usr/bin/env python3
"""
简单分析脚本，避免编码问题
"""

import re
import sys
from datetime import datetime

def simple_analyze(content):
    """简单分析内容"""
    print(f"内容长度: {len(content)} 字符")

    # 提取问题
    questions = []
    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        if len(line) < 10:
            continue

        # 查找包含问号的行
        if '?' in line or '？' in line:
            # 简单清理
            text = re.sub(r'\[\d+\]', '', line)
            text = re.sub(r'<[^>]+>', '', text)
            text = ' '.join(text.split())

            if len(text) >= 8:
                questions.append(text[:100])

    # 去重
    unique = []
    seen = set()
    for q in questions:
        if q not in seen:
            seen.add(q)
            unique.append(q)

    print(f"找到 {len(unique)} 个问题")

    # 生成简单报告
    report = []
    report.append("知乎页面分析报告")
    report.append("=" * 50)
    report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    report.append(f"发现潜在问题: {len(unique)} 个")
    report.append("")

    if unique:
        report.append("问题示例:")
        for i, q in enumerate(unique[:10]):
            report.append(f"{i+1}. {q}")

        # 简单分析
        lengths = [len(q) for q in unique]
        avg_len = sum(lengths) / len(lengths)

        report.append("")
        report.append(f"平均问题长度: {avg_len:.0f} 字符")

        # 检查问题类型
        tech_count = 0
        study_count = 0
        work_count = 0

        for q in unique:
            q_lower = q.lower()
            if any(kw in q_lower for kw in ['程序', '代码', 'python', 'java', 'c++', '算法', '开发']):
                tech_count += 1
            elif any(kw in q_lower for kw in ['学习', '教育', '学校', '考试', '课程', '大学']):
                study_count += 1
            elif any(kw in q_lower for kw in ['工作', '职场', '面试', '职业', '薪资', '公司']):
                work_count += 1

        report.append("")
        report.append("问题类型:")
        if tech_count > 0:
            report.append(f"- 技术相关: {tech_count} 个")
        if study_count > 0:
            report.append(f"- 学习相关: {study_count} 个")
        if work_count > 0:
            report.append(f"- 工作相关: {work_count} 个")

        report.append("")
        report.append("分析:")
        if tech_count > len(unique) * 0.3:
            report.append("- 内容主要集中在技术领域")
        if study_count > len(unique) * 0.3:
            report.append("- 内容主要集中在学习领域")
        if work_count > len(unique) * 0.3:
            report.append("- 内容主要集中在职场领域")

        if avg_len > 50:
            report.append("- 问题描述较为详细")
        elif avg_len < 25:
            report.append("- 问题较为简短")

        if len(unique) >= 10:
            report.append("- 问题数量较多，内容丰富")
        elif len(unique) <= 3:
            report.append("- 问题数量较少")

    else:
        report.append("未找到明显的问题内容")
        report.append("可能原因:")
        report.append("1. 页面内容不完整")
        report.append("2. 编码问题导致文本提取失败")
        report.append("3. 当前页面没有明显的问题")

    report.append("")
    report.append("建议:")
    report.append("1. 关注您擅长领域的问题")
    report.append("2. 简短问题可快速回答")
    report.append("3. 复杂问题可详细解答")

    return '\n'.join(report)

def main():
    # 从标准输入读取
    print("正在读取页面内容...")
    content = sys.stdin.read()

    if not content:
        print("没有输入内容")
        return

    report = simple_analyze(content)

    # 输出报告
    print("\n" + "=" * 60)
    print("分析报告:")
    print("=" * 60)
    print(report)

    # 保存报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"zhihu_report_{timestamp}.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n报告已保存: {report_file}")
    print("\n分析完成!")

if __name__ == "__main__":
    main()