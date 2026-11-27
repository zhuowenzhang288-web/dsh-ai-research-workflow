#!/usr/bin/env python3
"""SKILL.md 启动自检 — 每次会话开始时，把关键纪律程序化注入系统提示。

为什么需要这个：光靠 AGENTS.md / preset 里的"请你加载 skill"是提示词层劝说，
agent 理论上可忽略。这个 skill 在会话启动时主动读 SKILL.md 的核心段落，
写进系统提示，让纪律"每次都在场"，不依赖 agent 自觉。

用法（由 preset / 启动钩子调用，也可手动）：
    python3 scripts/skill_bootstrap.py        # 读 SKILL.md，输出核心纪律文本
"""
import os
import re

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SKILL.md")

def core():
    """抽取 SKILL.md 里最不能忘的几段：身份、0.2 总原则、门控、产物清理、教训。"""
    if not os.path.exists(SKILL):
        return f"[skill_bootstrap] 找不到 {SKILL}"
    t = open(SKILL, encoding="utf-8").read()
    out = ["【科研工作流·已加载核心纪律】"]
    # 身份段
    m = re.search(r"\*\*身份\*\*：(.+?)(?=\n\n|\n\*\*配套)", t, re.S)
    if m:
        out.append("身份：" + re.sub(r"\s+", " ", m.group(1)).strip())
    # 0.2 总原则 5 条
    m = re.search(r"## 0\.2 总原则.*?\n(.*?)(?=^## )", t, re.S | re.M)
    if m:
        out.append("\n总原则：")
        for line in m.group(1).strip().split("\n"):
            if line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                out.append("  " + re.sub(r"\s+", " ", line.strip()))
    # 门控表
    m = re.search(r"## 门控.*?\n(\|.*\|)\n", t, re.S)
    if m:
        out.append("\n门控（门前必须停）：")
        out.append(m.group(1))
    # 产物清理
    if "artifact_sweep" in t:
        out.append("\n产物清理：每个产物判 ephemeral/regenerable/durable，不确定宁留勿删。")
    return "\n".join(out)


if __name__ == "__main__":
    print(core())
