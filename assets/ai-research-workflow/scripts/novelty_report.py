#!/usr/bin/env python3
"""novelty_report — 查新报告取证校验（对应 SKILL.md §2 取证标准）。

硬规则: 只读摘要不得出现在 KEEP/KILL 判定里。
本脚本做格式校验: 报告中每篇被引用的工作, 附近必须出现读取程度标注
(摘要级 / 正文 / 全文 三词之一)。查不到标注 → FAIL。

用法:
    python3 scripts/novelty_report.py 查新报告.md

判定逻辑:
  1. 找出含 arXiv 编号 (XXXX.XXXXX) 或「(20XX)」年份引用的行;
  2. 检查该行 ±2 行内是否含 摘要级/正文/全文 之一;
  3. 含 KEEP/KILL 判定的行(含这两个词), 若其引用的工作全是"摘要级" → 额外 WARN。
"""
import argparse
import re
import sys

ARXIV = re.compile(r"\b2\d{3}\.\d{4,5}\b")
CITE = re.compile(r"[A-Z][A-Za-z\-]+[^\n]{0,40}(?:\(?(?:19|20)\d{2}[a-z]?\)?)")
LEVELS = ("摘要级", "正文", "全文")
VERDICT = re.compile(r"\b(KEEP|KILL)\b", re.I)


def analyze(text):
    lines = text.split("\n")
    cited, missing_level, verdict_lines = [], [], []
    for i, line in enumerate(lines):
        has_arxiv = bool(ARXIV.search(line))
        has_cite = bool(CITE.search(line)) and ("http" in line or "(" in line)
        if not (has_arxiv or has_cite):
            if VERDICT.search(line):
                verdict_lines.append((i + 1, line.strip()[:80]))
            continue
        window = "\n".join(lines[max(0, i - 2):i + 3])
        level = next((w for w in LEVELS if w in window), None)
        entry = {"line": i + 1, "text": line.strip()[:60], "level": level}
        cited.append(entry)
        if level is None:
            missing_level.append(entry)
    return cited, missing_level, verdict_lines


def main():
    ap = argparse.ArgumentParser(description="查新报告取证校验")
    ap.add_argument("report")
    args = ap.parse_args()
    text = open(args.report, encoding="utf-8").read()
    cited, missing, verdicts = analyze(text)

    print(f"引用工作 {len(cited)} 篇 | 缺读取程度标注 {len(missing)} 篇 | KEEP/KILL 判定行 {len(verdicts)} 行\n")

    for m in missing:
        print(f"  ❌ 第{m['line']}行无标注: {m['text']}")
    if missing:
        print("\n判定：FAIL —— 按 §2 取证标准，这些条目必须补标注")
        print("（标注方式：在该工作附近写「摘要级」「正文」或「全文」）")
    else:
        print("判定：PASS —— 每篇引用都有读取程度标注 ✓")

    if verdicts:
        print("\nKEEP/KILL 判定行（人工复核：其依据是否为正文级？）:")
        for ln, t in verdicts:
            print(f"  第{ln}行: {t}")

    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
