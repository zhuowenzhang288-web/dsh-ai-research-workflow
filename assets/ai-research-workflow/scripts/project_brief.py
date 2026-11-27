#!/usr/bin/env python3
"""project_brief — 立项确认：在造现象/查新之前，先问清方向、资源、时间、目标。

对应 SKILL.md §0.5。很多研究做不下去不是方法不对，而是一开始就没对齐：
题目需要 8 张卡但只有 1 张、截稿在 8 周后但实验要跑 3 个月、想做 A 类但选了
"7B 起步"的赛道。先把约束写下来，后面的每一步才有判断依据。

用法:
    python3 scripts/project_brief.py init      # 交互填写，写入 PROJECT_BRIEF.md
    python3 scripts/project_brief.py check     # 检查现有简报的完整性与硬约束冲突
    python3 scripts/project_brief.py show      # 打印简报

产物 PROJECT_BRIEF.md 是单一事实源：选题、实验设计、CCF-A 判断都应引用它。
只依赖 Python 标准库。
"""
import argparse
import os
import re
import sys

FILE = "PROJECT_BRIEF.md"

# (键, 提示, 示例, 是否必填)
FIELDS = [
    ("direction", "研究方向/问题域（一句话）", "例：agentic RL 的训练稳定性", True),
    ("venue", "目标会议/期刊及截稿", "例：ICML 2027，约 2027-01 下旬截稿", True),
    ("deadline_weeks", "距截稿还有几周", "例：9", True),
    ("compute", "可用算力", "例：Mac M2 8GB（MPS）；备选 8×RTX 4090 轻量训练", True),
    ("budget", "预算上限（GPU·h / API 费用）", "例：≤50 GPU·h；API <$50", True),
    ("hours_per_week", "每周能投入的小时数", "例：15", False),
    ("team", "人数与分工", "例：1 人，独立完成", False),
    ("hard_constraints", "硬约束（不可协商）", "例：不用 7B 以上模型；不做需要人工标注的评测", False),
    ("success_criteria", "什么算成功", "例：投出 1 篇主会；或有 1 个可证伪的新预言被验证", True),
    ("non_goals", "明确不做什么", "例：不做工程系统；不追 SOTA", False),
]

# 子领域的"起步规模"经验值：用于提示算力是否够到及格线（SKILL.md §9）
SCALE_HINTS = [
    (r"rl\s*(后训练|post-?training|微调|fine-?tun)|grpo|ppo|dpo|对齐|alignment", "RL 后训练/对齐",
     "通常 7B 起步", "单卡很难补齐结构性劣势；考虑换到「小规模本身是标准」的方向"),
    (r"电路|circuit|可解释性|interp|机制分析|mechanistic", "机制可解释性",
     "通常 7B–70B", "小模型上的电路发现往往不被认为有代表性"),
    (r"预训练|pre-?train|scaling|缩放定律", "预训练/缩放定律",
     "需要多档模型规模", "单卡只能做很小的规模区间，结论难外推"),
]


def parse(text):
    out = {}
    for m in re.finditer(r"^- \*\*(.+?)\*\*[：:]\s*(.*)$", text, re.M):
        out[m.group(1).strip()] = m.group(2).strip()
    return out


LABEL = {k: dict(
    direction="方向", venue="目标会议", deadline_weeks="距截稿（周）", compute="算力",
    budget="预算上限", hours_per_week="每周投入（小时）", team="团队",
    hard_constraints="硬约束", success_criteria="成功标准", non_goals="不做的事",
)[k] for k, *_ in FIELDS}


def cmd_init():
    print("立项确认（直接回车跳过可选项；已有值会显示在方括号里）\n")
    existing = parse(open(FILE, encoding="utf-8").read()) if os.path.exists(FILE) else {}
    values = {}
    for key, prompt, example, required in FIELDS:
        while True:
            cur = f" [{existing.get(LABEL[key], '')}]" if existing.get(LABEL[key]) else ""
            v = input(f"{prompt}{cur}\n  {example}\n> ").strip() or existing.get(LABEL[key], "")
            if v or not required:
                values[key] = v
                break
            print("  这一项是必填的——后面的选题和实验设计都要靠它。\n")
    lines = ["# PROJECT_BRIEF — 立项确认", "",
             "> 单一事实源。选题、实验设计、CCF-A 判断都应引用这里；约束变了就改这个文件。", ""]
    for key, *_ in FIELDS:
        lines.append(f"- **{LABEL[key]}**：{values.get(key) or '（未填）'}")
    lines += ["", "## 检查", "", "改完约束后运行 `python3 scripts/project_brief.py check`。"]
    open(FILE, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"\n已写入 {FILE}")
    check(verbose=False)


def cmd_check():
    if not os.path.exists(FILE):
        print(f"没有 {FILE}。先运行 init。")
        return 1
    return check(verbose=True)


def check(verbose=True):
    d = parse(open(FILE, encoding="utf-8").read())
    problems, warns = [], []

    for key, _, _, required in FIELDS:
        if required and not d.get(LABEL[key]):
            problems.append(f"缺必填项：{LABEL[key]}")

    # 时间：少于 6 周基本只能做纯分析/API 类
    m = re.search(r"\d+", d.get(LABEL["deadline_weeks"], ""))
    if m:
        w = int(m.group(0))
        if w < 6:
            warns.append(f"距截稿仅 {w} 周：新训练实验大概率来不及，优先考虑分析型/API 小实验型选题")
        elif w < 10:
            warns.append(f"距截稿 {w} 周：只够一个「窄题 + 小实验」选题，不建议并行多个")

    # 算力 vs 子领域
    direction = d.get(LABEL["direction"], "").lower()
    compute = d.get(LABEL["compute"], "").lower()
    small = bool(re.search(r"mps|macbook|m1|m2|m3|m4|8\s*gb|16\s*gb|单卡|1\s*张|laptop|笔记本", compute))
    for rx, name, scale, advice in SCALE_HINTS:
        if re.search(rx, direction) and small:
            warns.append(f"「{name}」{scale}，而你的算力是单卡/本地——结构性劣势，建议换子领域：{advice}")

    # 成功标准 vs 不做的事 冲突
    s, n = d.get(LABEL["success_criteria"], ""), d.get(LABEL["non_goals"], "")
    if "主会" in s and "不追" in n and "SOTA" in n.upper():
        pass  # 合理：主会不一定要 SOTA
    if s and not re.search(r"\d", s):
        warns.append("成功标准里没有可检验的数字/条件（如「1 篇」「1 个预言被验证」），到时难以判断做没做成")

    if verbose:
        print(f"\n{FILE} 检查：")
        for p in problems:
            print(f"  ❌ {p}")
        for w in warns:
            print(f"  ⚠️  {w}")
        if not problems and not warns:
            print("  ✅ 必填项齐全，未发现明显冲突")
        elif not problems:
            print("  （无缺项；以上为提醒，不是否决）")
    return 1 if problems else 0


def cmd_show():
    if not os.path.exists(FILE):
        print(f"没有 {FILE}")
        return 1
    print(open(FILE, encoding="utf-8").read())
    return 0


def main():
    ap = argparse.ArgumentParser(description="立项确认：方向/资源/时间/目标")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="交互填写").set_defaults(func=lambda a: cmd_init())
    sub.add_parser("check", help="检查完整性").set_defaults(func=lambda a: sys.exit(cmd_check()))
    sub.add_parser("show", help="打印简报").set_defaults(func=lambda a: sys.exit(cmd_show()))
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
