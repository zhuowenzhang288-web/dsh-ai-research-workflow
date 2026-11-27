#!/usr/bin/env python3
"""gen_row7.py — 7 卡一行布局生成器（DSH Research Agent 架构图 v10）。

布局：
    标题 + 副标题
    (a) 一行七卡：立项确认 → 造现象 → 找规律 → 反推 idea → 三轮查新 → 上卡验证 → 五层审计
        每卡：白底 + 顶部色条 + 粗体标题 + 3-4 行短语 + 灰色脚注
        卡间红色箭头
    (b) 查新分支面板（挂在三轮查新下方）
    (c) 工具区（8 个工具）
    (d) 融合层 / 跨平台条
    色卡 + 平台条

风格延续 v9：奶油底 #FDFBF7、卡片 #FFFFFF + 顶部色条、红色 #F87171 箭头、阴影 #64748B。
"""
import argparse
import os
import re

# ── 配色（v9 风格）───────────────────────────────────────────
BG = "#FDFBF7"
INK = "#1E293B"
SUB = "#374151"
MUTED = "#9CA3AF"
HAIR = "#C7CEDC"
RED = "#DC2626"
ACCENT = "#F87171"          # 箭头
RED_DARK = "#7F1D1D"
MONO = "ui-monospace, SFMono-Regular, Menlo, monospace"
SANS = "-apple-system, 'Segoe UI', 'PingFang SC', 'Noto Sans CJK SC', 'Microsoft YaHei', sans-serif"

# 各阶段：key → (描边色, 标题色, 浅底色, 顶部色条色)
STAGES = {
    "brief":  ("#94A3B8", "#334155", "#F8FAFC", "#CBD5E1"),
    "make":   ("#34D399", "#047857", "#FFFFFF", "#6EE7B7"),
    "law":    ("#22D3EE", "#0E7490", "#FFFFFF", "#67E8F9"),
    "idea":   ("#FBBF24", "#B45309", "#FFFFFF", "#FCD34D"),
    "novel":  ("#60A5FA", "#1D4ED8", "#FFFFFF", "#93C5FD"),
    "verify": ("#A78BFA", "#6D28D9", "#FFFFFF", "#C4B5FD"),
    "audit":  ("#94A3B8", "#334155", "#FFFFFF", "#CBD5E1"),
}

# ── 版式 ──────────────────────────────────────────────────
W = 1800
MARGIN = 70
PAD = 28
TITLE_Y = 58
SUB_Y = 94
ROW_Y = 136
CARD_H = 200
CARD_GAP = 16
PANEL_Y_GAP = 48
PANEL_H = 120
TOOLS_Y_GAP = 34
TOOL_H = 64
TOOL_GAP = 12
FUSION_Y_GAP = 34
FUSION_H = 120
PAL_Y_GAP = 28
PAL_H = 44
BAR_H = 56


class SVG:
    def __init__(self, w):
        self.w, self.h, self.o = w, 0, []

    def add(self, s):
        self.o.append(s)

    def rect(self, x, y, w, h, fill="#FFFFFF", stroke=None, sw=1.5, r=10, dash=None, fill_op=None):
        a = [f'x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{r:g}" fill="{fill}"']
        if fill_op is not None:
            a.append(f'fill-opacity="{fill_op}"')
        if stroke:
            a.append(f'stroke="{stroke}" stroke-width="{sw:g}"')
        if dash:
            a.append(f'stroke-dasharray="{dash}"')
        self.add(f'<rect {" ".join(a)}/>')

    def text(self, x, y, t, size=14, fill=SUB, weight=None, anchor=None, mono=False):
        a = [f'x="{x:g}" y="{y:g}" font-size="{size:g}" fill="{fill}"']
        if weight:
            a.append(f'font-weight="{weight}"')
        if anchor:
            a.append(f'text-anchor="{anchor}"')
        if mono:
            a.append(f'font-family="{MONO}"')
        self.add(f'<text {" ".join(a)}>{t}</text>')

    def shadow(self, x, y, w, h, r=12):
        self.add(f'<g filter="url(#soft)"><rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{r:g}" fill="#FFFFFF"/></g>')

    def arrow(self, x1, y1, x2, y2, color=ACCENT, sw=3):
        self.add(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{color}" stroke-width="{sw:g}" stroke-linecap="round" marker-end="url(#arr)"/>')

    def line(self, x1, y1, x2, y2, color=ACCENT, sw=2, dash=None):
        a = [f'x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{color}" stroke-width="{sw:g}" stroke-linecap="round"']
        if dash:
            a.append(f'stroke-dasharray="{dash}"')
        self.add(f'<line {" ".join(a)}/>')

    def path(self, d, color=ACCENT, sw=2):
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw:g}" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arr)"/>')

    def circle(self, cx, cy, r, fill, stroke=None, sw=0):
        a = [f'cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="{fill}"']
        if stroke:
            a.append(f'stroke="{stroke}" stroke-width="{sw:g}"')
        self.add(f'<circle {" ".join(a)}/>')

    def render(self):
        return "\n".join(self.o)


def defs():
    return ('<defs>'
            f'<marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M0,1 L9,5 L0,9 z" fill="{ACCENT}"/></marker>'
            f'<filter id="soft" x="-30%" y="-30%" width="160%" height="160%">'
            f'<feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#64748B" flood-opacity="0.18"/></filter>'
            f'<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0%" stop-color="{RED}"/><stop offset="100%" stop-color="{RED_DARK}"/></linearGradient>'
            f'</defs>')


def stage_card(svg, x, y, w, h, key, title, lines, foot=None):
    stroke, title_c, tint, bar = STAGES[key]
    svg.shadow(x, y, w, h)
    svg.rect(x, y, w, h, fill=tint, stroke=stroke, sw=1.8, r=12)
    svg.rect(x + 14, y + 13, w - 28, 5, fill=bar, r=2.5)
    ty = y + 46
    svg.text(x + 18, ty, title, size=17, fill=title_c, weight="700")
    ly = ty + 24
    for ln in lines:
        svg.text(x + 18, ly, ln, size=12, fill=SUB)
        ly += 20
    if foot:
        svg.text(x + 18, y + h - 12, foot, size=10.5, fill=MUTED)


def tool_card(svg, x, y, w, h, name, use):
    svg.shadow(x, y, w, h, r=8)
    svg.rect(x, y, w, h, fill="#FFFFFF", stroke="#E2E8F0", sw=1.2, r=8)
    svg.text(x + 12, y + 24, name, size=12, fill=INK, weight="600", mono=True)
    svg.text(x + 12, y + 44, use, size=10.5, fill=MUTED)


def build(target):
    assert target in ("dsh", "skill")
    svg = SVG(W)
    svg.add(defs())
    inner = W - 2 * MARGIN

    if target == "dsh":
        title = "DSH Research Agent · 搭载于 DeepSeek Harness"
        subtitle = "一个装在 DSH 里的科研 agent：模型+循环由 DSH 提供，本包注入 skill+人格+preset+自动循环"
        bar_text = "🧩 搭载于 DeepSeek Harness · 选「科研模式」即启用 · 跨平台方法本体见 ai-research-workflow"
        fusion_label = "🧬 agent 融合层 · FUSION"
        fusion_note = "模型 + harness 借自 DSH · skill + 经验 + 上下文 + 人格 我们提供"
        fusion_cards = [
            ("科研模式 preset", "人格烧进系统提示", "选模式即成 agent", RED),
            ("AGENTS.md", "核心纪律精简版", "每次请求自动注入", "#34D399"),
            ("SKILL.md", "完整方法论", "8 条实战教训", "#60A5FA"),
            ("AUTO_MODE", "goal+schedule 循环", "投稿门不降级", "#A78BFA"),
            ("install.sh", "一键安装", "自动检测五平台", "#94A3B8"),
        ]
    else:
        title = "AI Research Workflow · 现象驱动科研工作流"
        subtitle = "跨平台方法论本体：先做小实验找规律，再反推 idea · 不凭空胡想 · 真相只有一个，证据说了算"
        bar_text = "🤖 Claude Code · Codex · Cursor · opencode · DeepSeek Harness"
        fusion_label = "🌍 跨平台 · PORTABLE"
        fusion_note = "纯 SKILL.md + scripts，不绑任何 harness · 放对目录即用"
        fusion_cards = [
            ("AGENTS.md", "核心纪律精简版", "每次请求自动注入", "#34D399"),
            ("SKILL.md", "完整方法论", "8 条实战教训", "#60A5FA"),
            ("install.sh", "一键安装", "自动检测五平台", "#A78BFA"),
            ("scripts/", "8 个零依赖脚本", "任何能跑 bash 的 agent", "#94A3B8"),
            ("sync.sh", "三处副本检查", "--check 可进 CI", "#F59E0B"),
        ]

    svg.text(W / 2, TITLE_Y, title, size=32, fill=INK, weight="800", anchor="middle")
    svg.text(W / 2, SUB_Y, subtitle, size=14, fill="#64748B", anchor="middle")

    # ── (a) 七卡一行 ──────────────────────────────────────────
    y = ROW_Y
    n = 7
    card_w = (inner - (n - 1) * CARD_GAP) / n
    cards = [
        ("brief",  "立项确认",    ["先问清：方向·算力", "时间·目标", "project_brief.py"], "第 0 步 · 先于一切"),
        ("make",   "造现象",      ["小系统 0.1–4M 参数", "几百个秒级实验", "预注册 · 异常四关"], "先看已发表论文怎么做"),
        ("law",    "找规律",      ["全条件成立才保留", "公式化 τ(β,λ)", "剔除不稳定"], None),
        ("idea",   "反推 idea",   ["现象 ① / 文献 ②", "凭空 ③ 是最后手段", "规律→解释→idea"], None),
        ("novel",  "三轮查新",    ["读正文 · 三路核查", "摘要不得下判定", "R1 同问题 R2 同方法"], None),
        ("verify", "上卡验证",    ["固定预算 · 基线先行", "评测只读", "keep·discard·crash"], None),
        ("audit",  "五层审计",    ["诚·证·数·引·驳", "全 PASS 才出稿", "任一 FAIL 即阻断"], None),
    ]
    xs = []
    x = MARGIN
    for i, (key, t, lines, foot) in enumerate(cards):
        xs.append(x)
        stage_card(svg, x, y, card_w, CARD_H, key, t, lines, foot)
        x += card_w + CARD_GAP

    mid = y + CARD_H / 2
    for i in range(n - 1):
        svg.arrow(xs[i] + card_w + 3, mid, xs[i + 1] - 3, mid)

    # ── (b) 查新分支面板 ─────────────────────────────────────
    py = y + CARD_H + PANEL_Y_GAP
    nx = xs[4]  # 三轮查新
    svg.text(nx - 2, py - 8, "(b)", size=12, fill=MUTED, weight="600")
    panel_w = card_w * 2 + CARD_GAP
    svg.shadow(nx, py, panel_w, PANEL_H, r=10)
    svg.rect(nx, py, panel_w, PANEL_H, fill="#FFFFFF", stroke=HAIR, sw=1.4, r=10)
    svg.text(nx + 16, py + 24, "查新后的两个出口", size=13, fill=INK, weight="600")
    ew = (panel_w - 32 - 12) / 2
    svg.rect(nx + 16, py + 38, ew, 62, fill="#FFFBEB", stroke="#D97706", sw=1.2, r=7)
    svg.text(nx + 26, py + 60, "撞车 → 深挖新维度", size=12, fill="#92400E", weight="600")
    svg.text(nx + 26, py + 80, "换观测维度，不是把题目改窄", size=10.5, fill="#78716C")
    svg.rect(nx + 28 + ew, py + 38, ew, 62, fill="#FEF2F2", stroke=RED, sw=1.2, r=7)
    svg.text(nx + 38 + ew, py + 60, "实质重复 → 淘汰", size=12, fill="#991B1B", weight="600")
    svg.text(nx + 38 + ew, py + 80, "记入漏斗，作反重复记忆", size=10.5, fill="#78716C")
    svg.path(f"M {nx + card_w / 2:g} {y + CARD_H + 2:g} L {nx + card_w / 2:g} {py - 2:g}")

    # ── (c) 工具区 ───────────────────────────────────────────
    ty = py + PANEL_H + TOOLS_Y_GAP
    svg.text(MARGIN - 2, ty - 8, "(c)", size=12, fill=MUTED, weight="600")
    svg.text(MARGIN, ty + 18, "配套工具", size=14, fill=INK, weight="700")
    svg.text(MARGIN + 72, ty + 18, "8 个 · 纯 Python 标准库 · 任何能跑 bash 的 agent 可用",
             size=11, fill=MUTED)
    tools = [
        ("project_brief", "立项确认"), ("venue_probe", "实验模板"),
        ("novelty_check", "查候选"),   ("novelty_report", "取证校验"),
        ("funnel", "选题漏斗"),        ("experiment_log", "实验日志"),
        ("verify_citations", "引用核验"), ("audit_chain", "五层审计"),
    ]
    cols = 8
    tw = (inner - (cols - 1) * TOOL_GAP) / cols
    for i, (name, use) in enumerate(tools):
        cx = MARGIN + i * (tw + TOOL_GAP)
        tool_card(svg, cx, ty + 32, tw, TOOL_H, name, use)

    # ── (d) 融合层 / 跨平台 ──────────────────────────────────
    fy = ty + 32 + TOOL_H + FUSION_Y_GAP
    svg.text(MARGIN - 2, fy - 8, "(d)", size=12, fill=MUTED, weight="600")
    svg.shadow(MARGIN, fy, inner, FUSION_H, r=12)
    svg.rect(MARGIN, fy, inner, FUSION_H, fill="#FFFFFF", stroke=HAIR, sw=1.4, r=12)
    svg.rect(MARGIN + 16, fy + 14, 200, 28, fill=RED, r=14)
    svg.text(MARGIN + 116, fy + 33, fusion_label, size=13, fill="#FFFFFF", weight="700", anchor="middle")
    svg.text(MARGIN + 232, fy + 33, fusion_note, size=12, fill=MUTED)
    ncols = len(fusion_cards)
    fcw = (inner - 32 - (ncols - 1) * 12) / ncols
    for i, (t, l1, l2, c) in enumerate(fusion_cards):
        cx = MARGIN + 16 + i * (fcw + 12)
        cy = fy + 52
        svg.rect(cx, cy, fcw, 52, fill="#F8FAFC", stroke=c, sw=1.3, r=8)
        svg.text(cx + 12, cy + 22, t, size=12, fill=INK, weight="600")
        svg.text(cx + 12, cy + 40, l1, size=10, fill=SUB)

    # ── 色卡 + 平台条 ───────────────────────────────────────
    pal_y = fy + FUSION_H + PAL_Y_GAP
    svg.add(f'<text x="{MARGIN}" y="{pal_y + 4}" font-size="12" font-weight="700" fill="{MUTED}" letter-spacing="2">PALETTE</text>')
    pal = [("#34D399", "造现象"), ("#22D3EE", "找规律"), ("#FBBF24", "反推"),
           ("#60A5FA", "查新"), ("#A78BFA", "验证"), ("#94A3B8", "审计")]
    pgap = (inner - 6 * 200) / 5
    for i, (c, name) in enumerate(pal):
        px = MARGIN + i * (200 + pgap)
        svg.rect(px, pal_y + 16, 200, PAL_H, fill=c, r=8)
        svg.text(px + 16, pal_y + 16 + PAL_H / 2 + 5, name, size=14, fill="#FFFFFF", weight="700")

    bar_y = pal_y + 16 + PAL_H + 20
    svg.shadow(MARGIN, bar_y, inner, BAR_H, r=BAR_H / 2)
    svg.rect(MARGIN, bar_y, inner, BAR_H, fill="url(#bar)", r=BAR_H / 2)
    svg.text(W / 2, bar_y + BAR_H / 2 + 7, bar_text, size=16, fill="#FFFFFF", weight="700", anchor="middle")

    svg.h = bar_y + BAR_H + 36
    bg = f'<rect width="{W}" height="{svg.h:g}" fill="{BG}"/>'
    svg.o.insert(1, bg)
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
        doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s.w} {s.h:g}" font-family="{SANS}">\n'
               f'{s.render()}\n</svg>\n')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(doc)
        print(f"[{tgt}] {s.w}x{s.h:g} -> {out}")


if __name__ == "__main__":
    main()
