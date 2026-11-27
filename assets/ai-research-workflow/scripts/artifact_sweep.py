#!/usr/bin/env python3
"""artifact_sweep — 扫描项目里"该删没删"的产物，释放空间。

对应 SKILL.md「产物生命周期」：产出任何东西时先判断保留级别。
- ephemeral  用完即删（临时文件、一次性脚本输出）
- regenerable 只留源头（报告由数据+代码生成，删报告留数据/代码）
- durable      才进 repo（漏斗、结论、项目简报、已发表论文的源文件）

用法:
    python3 scripts/artifact_sweep.py [目录]        # 默认当前目录
    python3 scripts/artifact_sweep.py --big 10      # 只列 >10MB 的
    python3 scripts/artifact_sweep.py --apply       # 删除 ephemeral（需确认）

判定规则（保守，宁列勿删）：
  - 名字含 tmp/temp/backup/old/.bak/.swp/__pycache__  → ephemeral
  - .md 报告 且 同目录有生成它的 .py/.ipynb 或 data/   → regenerable（留源）
  - 体积 > 8MB 的 .csv/.npy/.pt/.ckpt/.log              → 提示，多半 regenerable
  - 其余不列。不确定的一律不删，只提示人工判断。
"""
import argparse
import os
import re
import sys

EPHEMERAL_NAME = re.compile(r"(tmp|temp|backup|old|\.bak|\.swp|__pycache__|\.pyc$)", re.I)
BIG_DATA = re.compile(r"\.(csv|npy|npz|pt|pth|ckpt|safetensors|log|out)$", re.I)
GENERATOR_NEARBY = re.compile(r"\.(py|ipynb)$")
MB = 1024 * 1024


def human(n):
    return f"{n / MB:.1f}MB" if n >= MB else f"{n / 1024:.0f}KB"


def classify(path, size):
    """返回 (级别, 理由)。级别: ephemeral / regenerable / None(不管)。"""
    name = os.path.basename(path)
    if EPHEMERAL_NAME.search(name):
        return "ephemeral", "临时/缓存命名"
    ext = os.path.splitext(name)[1].lower()
    dir_ = os.path.dirname(path)
    if ext == ".md" and size > 0:
        # 同目录有生成脚本或数据目录 → 报告可由它们重生
        try:
            sibs = os.listdir(dir_ or ".")
        except OSError:
            sibs = []
        if any(GENERATOR_NEARBY.search(s) for s in sibs) or "data" in sibs or "results" in sibs:
            return "regenerable", "报告，同目录有生成源/数据"
    if BIG_DATA.search(name) and size > 8 * MB:
        return "regenerable", "大体积数据/日志，多半可重生"
    return None, ""


def walk(root, min_mb):
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__")]
        for f in filenames:
            p = os.path.join(dirpath, f)
            try:
                size = os.path.getsize(p)
            except OSError:
                continue
            if size < min_mb * MB:
                continue
            level, why = classify(p, size)
            if level:
                found.append((level, size, p, why))
    return found


def main():
    ap = argparse.ArgumentParser(description="扫描并清理该删的产物")
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--big", type=float, default=0.5, help="只列 >=N MB 的文件（默认 0.5）")
    ap.add_argument("--apply", action="store_true", help="实际删除 ephemeral（regenerable 只提示）")
    args = ap.parse_args()

    items = walk(args.root, args.big)
    if not items:
        print(f"扫描 {args.root}：没有 >= {args.big}MB 的可疑产物 ✓")
        return 0

    ephem = [x for x in items if x[0] == "ephemeral"]
    regen = [x for x in items if x[0] == "regenerable"]
    print(f"扫描 {args.root}：ephemeral {len(ephem)} 个（共 {human(sum(s for _, s, _, _ in ephem))}），"
          f"regenerable {len(regen)} 个（共 {human(sum(s for _, s, _, _ in regen))}）\n")

    for level, size, p, why in ephem:
        print(f"  [ephemeral] {human(size):>8}  {p}  ({why})")
    for level, size, p, why in regen:
        print(f"  [regenerable] {human(size):>8}  {p}  ({why})")

    print("\n处置：")
    if ephem:
        print(f"  ephemeral：建议直接删（{len(ephem)} 个）")
    if regen:
        print(f"  regenerable：删报告/数据前，先确认生成源（代码+数据）还在，再删")
    print("  原则：不确定的一律留，宁留勿删。")

    if args.apply:
        if not ephem:
            print("\n没有可删的 ephemeral。")
            return 0
        print(f"\n--apply：删除 {len(ephem)} 个 ephemeral …")
        for _, _, p, _ in ephem:
            try:
                os.remove(p)
                print(f"  已删 {p}")
            except OSError as e:
                print(f"  删失败 {p}: {e}")
    else:
        print("\n（只列不删。确认后加 --apply 删除 ephemeral；regenerable 请人工确认源还在再删。）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
