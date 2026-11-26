#!/usr/bin/env python3
"""audit_chain — 五层审计链 checklist（对应 SKILL.md §7.3）。

用法:
    python3 audit_chain.py            # 交互式，逐层判断
    python3 audit_chain.py --report   # 只看各层检查项，不打交互

五层（出终稿/投稿前逐层过）:
    1 实验诚实性   2 结论-证据一致   3 论文如实性   4 引用审计   5 最强反驳
每层状态: PASS / WARN / FAIL / BLOCKED。
汇总: 任一 FAIL 即阻断；WARN 以上必须处理或经用户知情同意。
只依赖 Python 标准库。
"""
import argparse
import os
import sys

LAYERS = [
    ("实验诚实性", [
        "评测代码是否诚实？（无假标签、无自归一化分数、无幽灵结果）",
        "每个实验结果能否指回 run.log / results.tsv / commit？",
    ]),
    ("结论-证据一致", [
        "每个 claim 是否被结果支持？（样本量、方差、基线、评测）",
        "结论是否超出实验条件范围？",
    ]),
    ("论文如实性", [
        "论文报告的数字是否与实验日志一致？",
        "有无把猜想写成既成事实？",
    ]),
    ("引用审计", [
        "每个引用存在吗？（用 scripts/verify_citations.py 核验）",
        "引用的\"声称内容\"与原文一致吗？",
    ]),
    ("最强反驳", [
        "写一封最强拒绝信，每条攻击点能否顶住？",
        "顶不住的，是否已补强或降级主张？",
    ]),
]

VALID = ("PASS", "WARN", "FAIL", "BLOCKED")


def interactive():
    results = []
    print("五层审计链（每层输入 PASS/WARN/FAIL/BLOCKED 之一）\n")
    for i, (name, checks) in enumerate(LAYERS, 1):
        print(f"═══ 第 {i} 层：{name} ═══")
        for c in checks:
            print(f"  · {c}")
        while True:
            v = input(f"  → 判定 [{i} {name}] (pass/warn/fail/blocked，回车=pass): ").strip().upper()
            if v == "":
                v = "PASS"
            if v in VALID:
                break
            print(f"  请输入 {VALID} 之一")
        results.append((name, v))
        print()
    return results


def report_only():
    print("五层审计链检查项（出终稿/投稿前逐层过）\n")
    for i, (name, checks) in enumerate(LAYERS, 1):
        print(f"[{i}] {name}")
        for c in checks:
            print(f"    · {c}")
        print()


def summarize(results):
    print("=" * 60)
    print("审计汇总")
    print("=" * 60)
    ordered = {"BLOCKED": 4, "FAIL": 3, "WARN": 2, "PASS": 1}
    worst = "PASS"
    for name, v in results:
        marker = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "BLOCKED": "⛔"}[v]
        print(f"  {marker} {name}: {v}")
        if ordered.get(v, 0) > ordered.get(worst, 0):
            worst = v
    print("-" * 60)
    if worst == "FAIL" or worst == "BLOCKED":
        print("结论：⛔ 阻断 —— 任一 FAIL/BLOCKED 即不出终稿，先修对应层。")
    elif worst == "WARN":
        print("结论：⚠️ 有条件 —— WARN 层必须处理或经用户知情同意。")
    else:
        print("结论：✅ 通过 —— 全 PASS，可出终稿。")


def verify_results(report_f, log_files):
    """结果编造检查（§7.3.A「结果编造」的代码化）：
    报告里每个实验性数值，必须在日志/结果文件里能找到锚点。
    找不到 → WARN（人工判断，不误杀）。只依赖标准库。"""
    import re
    report = open(report_f, encoding="utf-8").read()
    log_text = ""
    for lf in log_files:
        if os.path.exists(lf):
            log_text += open(lf, encoding="utf-8", errors="replace").read() + "\n"
    if not log_text:
        print(f"⚠️ 未找到任何日志文件 {[log_files]}——无法做 back-pointer 检查")
        return 2

    # 提取实验性数值：小数、百分数、指标词后的整数；排除年份
    pat = re.compile(r"(?<!\d)(\d+\.\d+%?|\d+%|(?<=[=\s:，,])\d{2,}(?![\d年]))")
    year = re.compile(r"^(19|20)\d{2}$")
    lines = report.split("\n")
    unanchored = []
    for i, line in enumerate(lines, 1):
        for m in pat.finditer(line):
            val = m.group(1)
            if year.match(val.rstrip("%")):
                continue
            needle = val.rstrip("%")
            if re.search(r"(?<![\d.])" + re.escape(needle) + r"(?![\d.%])", log_text):
                continue
            unanchored.append((i, val, line.strip()[:60]))
    if not unanchored:
        print("✅ 报告中所有实验性数值都能在日志中找到锚点")
        return 0
    print(f"⚠️ {len(unanchored)} 处数值无 back-pointer（报告里有、日志里没有）:")
    for ln, val, ctx in unanchored:
        print(f"  第{ln}行 「{val}」 …{ctx}")
    print("\n处置：逐条确认——若来自口头试跑/外部文献，补标注来源；")
    print("若属于实验结果，先在 experiment_log.py 补记后再写入报告。")
    return 2


def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "verify-results":
        ap = argparse.ArgumentParser(description="结果编造 back-pointer 检查")
        ap.add_argument("report")
        ap.add_argument("--log", dest="logs", action="append", default=[],
                        help="日志/结果文件，可多次（默认 results.tsv run.log）")
        args = ap.parse_args(sys.argv[2:])
        logs = args.logs or ["results.tsv", "run.log", "EXPERIMENT_LOG.md", "实验日志.md"]
        sys.exit(verify_results(args.report, logs))

    ap = argparse.ArgumentParser(description="五层审计链")
    ap.add_argument("--report", action="store_true", help="只看检查项，不交互")
    args = ap.parse_args()
    if args.report:
        report_only()
        return
    results = interactive()
    summarize(results)


if __name__ == "__main__":
    main()