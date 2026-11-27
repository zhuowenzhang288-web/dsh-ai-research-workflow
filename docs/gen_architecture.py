#!/usr/bin/env python3
"""gen_architecture.py — 生成论文 teaser 风格的架构图（白底 / 横向流程 / 少字）。

设计参照高星项目的 Architecture 图与论文 teaser：
    - 白底、细边框、低饱和配色，不放大色块和深色横条
    - 流程从左到右一条主线；"第 0 步"是起点小节点，不是横幅
    - 框内只放 2–3 个词的短语；解释性文字放 README
    - 分支/细节收进下方 (a)(b) 两个小面板
    - 不用 emoji（论文图惯例），只留极少量作视觉锚点

用法:
    python3 docs/gen_architecture.py --target dsh   --out dsh-ai-research-workflow/docs/architecture.svg
    python3 docs/gen_architecture.py --target skill --out ai-research-workflow-repo/docs/architecture.svg
    python3 docs/gen_architecture.py --all
"""
import argparse
import os
import re

# ─────────────────────────────────────────────────────── 配色：低饱和、纸面感
INK = "#0F172A"        # 标题
BODY = "#334155"       # 正文
MUTED = "#94A3B8"      # 次要
HAIR = "#E2E8F0"       # 细边框
PANEL = "#F8FAFC"      # 面板底
ACCENT = "#DC2626"     # 唯一强调色（连线/强调），克制使用

# 每个阶段一个低饱和主色（用于细边框 + 顶部细线 + 文字）
STAGES = {
    "brief":  ("#64748B", "#F1F5F9"),
    "make":   ("#059669", "#ECFDF5"),
    "law":    ("#0891B2", "#ECFEFF"),
    "idea":   ("#B45309", "#FFFBEB"),
    "novel":  ("#1D4ED8", "#EFF6FF"),
    "verify": ("#6D28D9", "#F5F3FF"),
    "audit":  ("#334155", "#F8FAFC"),
}

SANS = ("-apple-system, 'Segoe UI', 'PingFang SC', 'Noto Sans CJK SC', "
        "'Microsoft YaHei', sans-serif")
MONO = "ui-monospace, SFMono-Regular, Menlo, monospace"

# ─────────────────────────────────────────────────────── 版式常量
W = 1600                # 画布宽
MARGIN = 70             # 左右留白
TITLE_Y = 58
SUB_Y = 92
ROW_Y = 150             # 主流程顶部
BOX_H = 132             # 主流程框高
GAP = 22                # 主流程框间距
PANEL_Y_GAP = 56        # 主流程到细节面板
PANEL_H = 132
TOOLS_Y_GAP = 40
CHIP_H = 46


class SVG:
    def __init__(self, w):
        self.w, self.h, self.o = w, 0, []

    def add(self, s):
        self.o.append(s)

    def rect(self, x, y, w, h, fill="none", stroke=None, sw=1.5, r=10, dash=None):
        a = [f'x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{r:g}" fill="{fill}"']
        if stroke:
            a.append(f'stroke="{stroke}" stroke-width="{sw:g}"')
        if dash:
            a.append(f'stroke-dasharray="{dash}"')
        self.add(f'<rect {" ".join(a)}/>')

    def text(self, x, y, t, size=14, fill=BODY, weight=None, anchor=None, mono=False, spacing=None):
        a = [f'x="{x:g}" y="{y:g}" font-size="{size:g}" fill="{fill}"']
        if weight:
            a.append(f'font-weight="{weight}"')
        if anchor:
            a.append(f'text-anchor="{anchor}"')
        if mono:
            a.append(f'font-family="{MONO}"')
        if spacing:
            a.append(f'letter-spacing="{spacing:g}"')
        self.add(f'<text {" ".join(a)}>{t}</text>')

    def arrow(self, x1, y1, x2, y2, color="#94A3B8", sw=1.6, dash=None):
        a = [f'x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{color}"',
             f'stroke-width="{sw:g}" stroke-linecap="round" marker-end="url(#head)"']
        if dash:
            a.append(f'stroke-dasharray="{dash}"')
        self.add(f'<line {" ".join(a)}/>')

    def path(self, d, color="#94A3B8", sw=1.6, dash=None):
        a = [f'd="{d}" fill="none" stroke="{color}" stroke-width="{sw:g}"',
             'stroke-linecap="round" stroke-linejoin="round" marker-end="url(#head)"']
        if dash:
            a.append(f'stroke-dasharray="{dash}"')
        self.add(f'<path {" ".join(a)}/>')

    def render(self):
        return "\n".join(self.o)


def defs():
    return ('<defs>'
            '<marker id="head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
            '<path d="M0,0 L10,5 L0,10 z" fill="#94A3B8"/></marker>'
            '<marker id="headRed" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{ACCENT}"/></marker>'
            '</defs>')


def stage_box(svg, x, y, w, h, key, title, line1, line2=None, note=None):
    """一个阶段框：淡色底 + 顶部细色线 + 粗体标题 + 一到两行短语。"""
    color, tint = STAGES[key]
    svg.rect(x, y, w, h, fill=tint, stroke=color, sw=1.6, r=10)
    svg.rect(x + 14, y + 14, w - 28, 3, fill=color, r=1.5)     # 顶部细线
    ty = y + 44
    svg.text(x + 18, ty, title, size=17, fill=INK, weight="600")
    svg.text(x + 18, ty + 26, line1, size=12.5, fill=BODY)
    if line2:
        svg.text(x + 18, ty + 46, line2, size=12.5, fill=BODY)
    if note:
        svg.text(x + 18, y + h - 14, note, size=11, fill=MUTED)


def panel_label(svg, x, y, letter):
    svg.text(x, y, f"({letter})", size=13, fill=MUTED, weight="600")


def build(target):
    assert target in ("dsh", "skill")
    svg = SVG(W)
    svg.add(defs())
    inner = W - 2 * MARGIN

    if target == "dsh":
        title = "DSH Research Agent"
        sub = "现象驱动的科研工作流 · 装上即用，纪律常驻"
    else:
        title = "AI Research Workflow"
        sub = "现象驱动的科研工作流 · 先做实验找规律，再反推 idea"

    svg.text(W / 2, TITLE_Y, title, size=30, fill=INK, weight="700", anchor="middle")
    svg.text(W / 2, SUB_Y, sub, size=14, fill=MUTED, anchor="middle")

    # ── (a) 主流程：起点小节点 + 六个阶段 ───────────────────────
    y = ROW_Y
    panel_label(svg, MARGIN - 4, y - 10, "a")
    start_w = 132
    n = 6
    box_w = (inner - start_w - (n) * GAP) / n

    # 起点：第 0 步（小节点，不是横幅）
    color, tint = STAGES["brief"]
    svg.rect(MARGIN, y + 28, start_w, BOX_H - 56, fill=tint, stroke=color, sw=1.6, r=8, dash="4 3")
    svg.text(MARGIN + start_w / 2, y + 52, "第 0 步", size=12, fill=color, weight="600", anchor="middle")
    svg.text(MARGIN + start_w / 2, y + 72, "立项确认", size=14, fill=INK, weight="600", anchor="middle")
    svg.text(MARGIN + start_w / 2, y + 92, "方向·算力·时间", size=10.5, fill=MUTED, anchor="middle")

    stages = [
        ("make",  "造现象",     "小系统 0.1–4M 参数", "预注册 · 异常四关", "先看已发表论文怎么做"),
        ("law",   "找规律",     "全条件成立才保留",   "公式化 τ(β,λ)",     None),
        ("idea",  "反推 idea",  "现象 ① / 文献 ②",    "凭空 ③ 是最后手段", None),
        ("novel", "三轮查新",   "读正文 · 三路核查",   "摘要不得下判定",     None),
        ("verify","上卡验证",   "固定预算 · 基线先行", "评测只读",           None),
        ("audit", "五层审计",   "诚·证·数·引·驳",     "全 PASS 才出稿",     None),
    ]
    xs = []
    x = MARGIN + start_w + GAP
    for i, (key, t, l1, l2, note) in enumerate(stages):
        xs.append(x)
        stage_box(svg, x, y, box_w, BOX_H, key, t, l1, l2, note)
        x += box_w + GAP

    # 箭头：起点 → 各阶段
    mid = y + BOX_H / 2
    svg.arrow(MARGIN + start_w + 2, mid, xs[0] - 4, mid)
    for i in range(n - 1):
        svg.arrow(xs[i] + box_w + 2, mid, xs[i + 1] - 4, mid)

    # ── (a) 查新分支（挂在“三轮查新”下方）──────────────────────
    py = y + BOX_H + PANEL_Y_GAP
    nx = xs[3]
    svg.path(f"M {nx + box_w / 2:g} {y + BOX_H + 2:g} L {nx + box_w / 2:g} {py - 18:g}", color=ACCENT)
    panel_w = box_w * 2 + GAP
    panel_label(svg, nx - 4, py - 6, "b")
    svg.rect(nx, py, panel_w, PANEL_H, fill="#FFFFFF", stroke=HAIR, sw=1.4, r=10)
    svg.text(nx + 18, py + 26, "查新后的两个出口", size=13, fill=INK, weight="600")
    # 两个出口
    ex = [nx + 18, nx + panel_w / 2 + 6]
    ew = panel_w / 2 - 30
    svg.rect(ex[0], py + 40, ew, 62, fill="#FFFBEB", stroke="#D97706", sw=1.3, r=7)
    svg.text(ex[0] + 12, py + 62, "撞车 → 深挖新维度", size=12.5, fill="#92400E", weight="600")
    svg.text(ex[0] + 12, py + 82, "换观测维度，不是把题目改窄", size=11, fill="#78716C")
    svg.rect(ex[1], py + 40, ew, 62, fill="#FEF2F2", stroke="#DC2626", sw=1.3, r=7)
    svg.text(ex[1] + 12, py + 62, "实质重复 → 淘汰", size=12.5, fill="#991B1B", weight="600")
    svg.text(ex[1] + 12, py + 82, "记入漏斗，作反重复记忆", size=11, fill="#78716C")

    # ── (b) 工具条 ─────────────────────────────────────────
    ty2 = py + PANEL_H + TOOLS_Y_GAP
    panel_label(svg, MARGIN - 4, ty2 - 6, "c")
    svg.text(MARGIN, ty2 + 16, "配套工具", size=13, fill=INK, weight="600")
    svg.text(MARGIN + 68, ty2 + 16, "8 个 · 纯 Python 标准库 · 任何能跑 bash 的 agent 可用",
             size=11.5, fill=MUTED)

    tools = [
        ("project_brief", "立项确认"), ("venue_probe", "实验模板"),
        ("novelty_check", "查候选"),   ("novelty_report", "取证校验"),
        ("funnel", "选题漏斗"),        ("experiment_log", "实验日志"),
        ("verify_citations", "引用核验"), ("audit_chain", "五层审计"),
    ]
    cols, cgx = 8, 12
    chip_w = (inner - (cols - 1) * cgx) / cols
    for i, (name, use) in enumerate(tools):
        r, c = divmod(i, cols)
        cx = MARGIN + c * (chip_w + cgx)
        cy = ty2 + 30 + r * (CHIP_H + 12)
        svg.rect(cx, cy, chip_w, CHIP_H, fill=PANEL, stroke=HAIR, sw=1.2, r=7)
        svg.text(cx + 10, cy + 19, name, size=9.5, fill=INK, weight="600", mono=True)
        svg.text(cx + 10, cy + 34, use, size=9.5, fill=MUTED)

    # ── (c) 定位说明 ───────────────────────────────────────
    cy2 = ty2 + 30 + (CHIP_H + 12) + 30
    panel_label(svg, MARGIN - 4, cy2 - 6, "d")
    if target == "dsh":
        svg.text(MARGIN, cy2 + 16, "角色分工", size=13, fill=INK, weight="600")
        svg.text(MARGIN + 68, cy2 + 16,
                 "模型与 agent 循环由 DeepSeek Harness 提供 ｜ 本包提供方法、8 个工具、人格与科研模式 preset",
                 size=11.5, fill=MUTED)
    else:
        svg.text(MARGIN, cy2 + 16, "跨平台", size=13, fill=INK, weight="600")
        svg.text(MARGIN + 56, cy2 + 16,
                 "方法论本体不绑 harness：Claude Code · Codex · Cursor · opencode · DeepSeek Harness",
                 size=11.5, fill=MUTED)

    svg.h = cy2 + 44
    bg = f'<rect width="{W}" height="{svg.h:g}" fill="#FFFFFF"/>'
    svg.o.insert(1, bg)      # 紧跟 defs：o[0]=defs, o[1]=背景, o[2]=标题（插 2 会盖住标题）
    return svg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["dsh", "skill"])
    ap.add_argument("--out")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    ws = os.path.abspath(os.path.join(here, "..", ".."))
    jobs = [("skill", os.path.join(ws, "ai-research-workflow-repo", "docs", "architecture.svg")),
            ("dsh", os.path.join(ws, "dsh-ai-research-workflow", "docs", "architecture.svg"))] if a.all \
        else [(a.target, a.out or os.path.join(here, "architecture.svg"))]
    for tgt, out in jobs:
        s = build(tgt)
        doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s.w} {s.h:g}" '
               f'font-family="{SANS}">\n{s.render()}\n</svg>\n')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(doc)
        print(f"[{tgt}] {s.w}x{s.h:g} -> {out}")


if __name__ == "__main__":
    main()
