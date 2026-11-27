#!/usr/bin/env python3
"""gen_row7.py — DSH Research Agent 架构图。

布局（严格按需求）：
    标题 + 副标题
    流程卡片：一行四个，两行共八个，行间用箭头连接，卡片互不遮挡
        每卡：顶部色条 + 标题 + 3~4 行小细节 + 灰色脚注
    查新分支面板（挂在"三轮查新"下方）
    8 个工具
    融合层 / 跨平台
    色卡 + 平台条
"""
import argparse
import os

BG = "#FDFBF7"
INK = "#1E293B"
SUB = "#374151"
MUTED = "#9CA3AF"
HAIR = "#C7CEDC"
RED = "#DC2626"
ACCENT = "#F87171"
RED_DARK = "#7F1D1D"
MONO = "ui-monospace, SFMono-Regular, Menlo, monospace"
SANS = "-apple-system, 'Segoe UI', 'PingFang SC', 'Noto Sans CJK SC', 'Microsoft YaHei', sans-serif"

STAGES = {
    "brief":  ("#94A3B8", "#334155", "#F8FAFC", "#CBD5E1"),
    "novel":  ("#60A5FA", "#1D4ED8", "#FFFFFF", "#93C5FD"),
    "make":   ("#34D399", "#047857", "#FFFFFF", "#6EE7B7"),
    "law":    ("#22D3EE", "#0E7490", "#FFFFFF", "#67E8F9"),
    "idea":   ("#FBBF24", "#B45309", "#FFFFFF", "#FCD34D"),
    "verify": ("#A78BFA", "#6D28D9", "#FFFFFF", "#C4B5FD"),
    "audit":  ("#94A3B8", "#334155", "#FFFFFF", "#CBD5E1"),
}

W = 1560
MARGIN = 60
PAD = 28
TITLE_Y = 56
SUB_Y = 90
ROW_Y = 130
CARD_H = 280
CARD_GAP = 24
ROW_GAP = 44
PANEL_Y_GAP = 50
PANEL_H = 110
TOOLS_Y_GAP = 36
TOOL_H = 66
TOOL_GAP = 14
FUSION_Y_GAP = 36
FUSION_H = 110
PAL_Y_GAP = 28
PAL_H = 46
BAR_H = 58


class SVG:
    def __init__(self, w):
        self.w, self.h, self.o = w, 0, []

    def add(self, s):
        self.o.append(s)

    def rect(self, x, y, w, h, fill="#FFFFFF", stroke=None, sw=1.5, r=10, dash=None):
        a = [f'x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{r:g}" fill="{fill}"']
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
            a.append(f'ttext-anchor="{anchor}"'.replace("ttext", "text"))
        if mono:
            a.append(f'font-family="{MONO}"')
        self.add(f'<text {" ".join(a)}>{t}</text>')

    def shadow(self, x, y, w, h, r=12):
        self.add(f'<g filter="url(#soft)"><rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{r:g}" fill="#FFFFFF"/></g>')

    def arrow(self, x1, y1, x2, y2, color=ACCENT, sw=3):
        self.add(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{color}" stroke-width="{sw:g}" stroke-linecap="round" marker-end="url(#arr)"/>')

    def path(self, d, color=ACCENT, sw=2):
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw:g}" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arr)"/>')

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


def stage_card(svg, x, y, w, h, key, title, lines, foot=None, deco=None):
    stroke, title_c, tint, bar = STAGES[key]
    svg.shadow(x, y, w, h)
    svg.rect(x, y, w, h, fill=tint, stroke=stroke, sw=1.8, r=12)
    svg.rect(x + 14, y + 13, w - 28, 5, fill=bar, r=2.5)
    ty = y + 46
    svg.text(x + 18, ty, title, size=21, fill=title_c, weight="700")
    ly = ty + 32
    for ln in lines:
        svg.text(x + 18, ly, ln, size=14.5, fill=SUB)
        ly += 26
    if deco:
        svg.rect(x + 12, y + 140, w - 24, h - 152, fill="#F8FAFC", r=8)
        deco(svg, x, y, w, h)
    if foot:
        svg.text(x + 18, y + h - 14, foot, size=11.5, fill=MUTED)


def tool_card(svg, x, y, w, h, name, use):
    svg.shadow(x, y, w, h, r=8)
    svg.rect(x, y, w, h, fill="#FFFFFF", stroke="#E2E8F0", sw=1.2, r=8)
    svg.text(x + 12, y + 24, name, size=12, fill=INK, weight="600", mono=True)
    svg.text(x + 12, y + 45, use, size=10.5, fill=MUTED)





def deco_template(svg, x, y, w, h):
    # 右下角：文档 + 放大镜
    dx, dy = x + w - 90, y + h - 80
    svg.add(f'<rect x="{dx}" y="{dy}" width="44" height="54" rx="5" fill="#EFF6FF" stroke="#60A5FA" stroke-width="1.5"/>')
    for i in range(4):
        svg.add(f'<line x1="{dx+7}" y1="{dy+12+i*11}" x2="{dx+37}" y2="{dy+12+i*11}" stroke="#93C5FD" stroke-width="2"/>')
    svg.add(f'<circle cx="{dx+52}" cy="{dy+48}" r="12" fill="none" stroke="#1D4ED8" stroke-width="2"/>')
    svg.add(f'<line x1="{dx+60}" y1="{dy+56}" x2="{dx+70}" y2="{dy+66}" stroke="#1D4ED8" stroke-width="2.5"/>')

def deco_brief(svg, x, y, w, h):
    # 清单：四行勾选，对应"方向/算力/时间/目标"
    items = [("方向", True), ("算力", True), ("时间", True), ("目标", False)]
    bx = x + 20
    for i, (t, ok) in enumerate(items):
        cy = y + 152 + i * 26
        svg.add(f'<rect x="{bx}" y="{cy}" width="20" height="20" rx="4" fill="{"#ECFDF5" if ok else "#FEF2F2"}" stroke="{"#34D399" if ok else "#F87171"}" stroke-width="1.5"/>')
        svg.add(f'<text x="{bx+4}" y="{cy+14}" font-size="12" fill="{"#059669" if ok else "#DC2626"}" font-weight="700">{"✓" if ok else "?"}</text>')
        svg.add(f'<text x="{bx+28}" y="{cy+14}" font-size="12" fill="{SUB}">{t}</text>')

def deco_template(svg, x, y, w, h):
    # 左：一叠文档；右：放大镜，对应"找论文取模板"
    dx, dy = x + 24, y + 148
    svg.add(f'<rect x="{dx}" y="{dy}" width="52" height="64" rx="5" fill="#EFF6FF" stroke="#60A5FA" stroke-width="1.5" transform="rotate(-4 {dx+26} {dy+32})"/>')
    svg.add(f'<rect x="{dx+6}" y="{dy+6}" width="52" height="64" rx="5" fill="#DBEAFE" stroke="#60A5FA" stroke-width="1.5"/>')
    for i in range(4):
        svg.add(f'<line x1="{dx+13}" y1="{dy+18+i*12}" x2="{dx+51}" y2="{dy+18+i*12}" stroke="#93C5FD" stroke-width="2.5"/>')
    mx, my = dx + 78, dy + 52
    svg.add(f'<circle cx="{mx}" cy="{my}" r="16" fill="none" stroke="#1D4ED8" stroke-width="2.5"/>')
    svg.add(f'<line x1="{mx+11}" y1="{my+11}" x2="{mx+24}" y2="{my+24}" stroke="#1D4ED8" stroke-width="3"/>')
    svg.add(f'<text x="{dx+52}" y="{dy+86}" text-anchor="middle" font-size="10" fill="{MUTED}">arXiv</text>')

def deco_make(svg, x, y, w, h):
    # 实验网格：3x4 彩色圆点，对应"海量秒级实验"
    colors = ["#6EE7B7", "#67E8F9", "#93C5FD", "#FCD34D", "#FBCFE8", "#A7F3D0", "#FDA4AF", "#C4B5FD", "#FDE68A", "#5EEAD4", "#BAE6FD", "#FED7AA"]
    ox, oy = x + 28, y + 148
    for i, c in enumerate(colors):
        r, col = divmod(i, 4)
        svg.add(f'<circle cx="{ox + col * 26}" cy="{oy + r * 26}" r="9" fill="{c}"/>')
    svg.add(f'<text x="{ox + 3*26 + 12}" y="{oy + 26}" font-size="11" fill="{MUTED}">n≈500</text>')
    svg.add(f'<text x="{ox + 3*26 + 12}" y="{oy + 40}" font-size="11" fill="{MUTED}">runs</text>')

def deco_law(svg, x, y, w, h):
    # 占下半卡的大折线图：实线规律 + 虚线不稳定
    px, py = x + 20, y + 148
    pw, ph = w - 40, 108
    pts1 = [(0, ph-24), (pw*0.2, ph-48), (pw*0.4, ph-38), (pw*0.6, ph-64), (pw*0.8, ph-58), (pw, ph-80)]
    pts2 = [(0, ph-14), (pw*0.25, ph-18), (pw*0.5, ph-11), (pw*0.75, ph-20), (pw, ph-15)]
    svg.add('<polyline points="' + " ".join(f"{px+a:.0f},{py+b:.0f}" for a, b in pts2) + '" fill="none" stroke="#F87171" stroke-width="2" stroke-dasharray="5 4"/>')
    svg.add(f'<polyline points="' + " ".join(f"{px+a:.0f},{py+b:.0f}" for a, b in pts1) + f'" fill="none" stroke="#22D3EE" stroke-width="2.5" stroke-linecap="round"/>')
    svg.add(f'<circle cx="{px+pw}" cy="{py+ph-66}" r="4" fill="#22D3EE"/>')
    svg.add(f'<text x="{px+pw-4}" y="{py+ph-72}" text-anchor="end" font-size="14" fill="#0E7490" font-style="italic" font-family="Georgia, serif">τ(β,λ)</text>')

def deco_idea(svg, x, y, w, h):
    # 三来源：胶囊在下，序号并入文字，说明最底
    items = [("现象 ①", "#FEF3C7", "#B45309", "#F59E0B"), ("文献 ②", "#FFFFFF", "#64748B", "#CBD5E1"), ("凭空 ③", "#FFFFFF", MUTED, "#E2E8F0")]
    pw = (w - 40 - 20) / 3
    for i, (t, f, tc, sc) in enumerate(items):
        cx = x + 20 + i * (pw + 10)
        cy = y + 148
        svg.add(f'<rect x="{cx}" y="{cy}" width="{pw}" height="36" rx="18" fill="{f}" stroke="{sc}" stroke-width="1.5"/>')
        svg.add(f'<text x="{cx + pw/2}" y="{cy+23}" text-anchor="middle" font-size="13" font-weight="700" fill="{tc}">{t}</text>')
    svg.add(f'<text x="{x+20}" y="{y+212}" font-size="11" fill="{MUTED}">优先用规律 · 凭空想 = 高概率白做</text>')


def deco_novel(svg, x, y, w, h):
    # 三个大圆圈 R1R2R3 + 右侧"只读摘要✗"徽章
    rx = x + 26
    for i, lab in enumerate(["R1", "R2", "R3"]):
        svg.add(f'<circle cx="{rx + i * 46}" cy="{y+136}" r="19" fill="#EFF6FF" stroke="#60A5FA" stroke-width="2"/>')
        svg.add(f'<text x="{rx + i * 46}" y="{y+142}" text-anchor="middle" font-size="12" font-weight="700" fill="#1D4ED8">{lab}</text>')
    svg.add(f'<rect x="{rx + 3*46 + 8}" y="{y+118}" width="98" height="34" rx="17" fill="#FEF2F2" stroke="#F87171" stroke-width="1.5"/>')
    svg.add(f'<text x="{rx + 3*46 + 57}" y="{y+140}" text-anchor="middle" font-size="11" font-weight="700" fill="#B91C1C">只读摘要 ✗</text>')
    svg.add(f'<text x="{x+20}" y="{y+176}" font-size="10" fill="{MUTED}">R1 同问题 · R2 同方法 · R3 相邻领域</text>')

def deco_verify(svg, x, y, w, h):
    # 大柱状图 keep/discard/crash
    bx, by = x + 30, y + 192
    bars = [("keep", 52, "#34D399"), ("discard", 30, "#CBD5E1"), ("crash", 14, "#F87171")]
    for i, (t, bh, c) in enumerate(bars):
        cx = bx + i * 52
        svg.add(f'<rect x="{cx}" y="{by-bh}" width="30" height="{bh}" rx="3" fill="{c}"/>')
        svg.add(f'<text x="{cx+15}" y="{by+14}" text-anchor="middle" font-size="10" fill="#6B7280">{t}</text>')
    svg.add(f'<line x1="{bx-8}" y1="{by}" x2="{bx+3*52}" y2="{by}" stroke="#CBD5E1" stroke-width="1.5"/>')

def deco_audit(svg, x, y, w, h):
    # 五个大勾选 + 红色 FAIL 印章
    ax = x + 20
    for i in range(5):
        svg.add(f'<rect x="{ax + i*34}" y="{y+118}" width="26" height="26" rx="5" fill="#ECFDF5" stroke="#34D399" stroke-width="2"/>')
        svg.add(f'<text x="{ax + i*34 + 4}" y="{y+137}" font-size="16" fill="#059669" font-weight="700">✓</text>')
    svg.add(f'<circle cx="{ax + 5*34 + 16}" cy="{y+131}" r="18" fill="#FEF2F2" stroke="#DC2626" stroke-width="2"/>')
    svg.add(f'<text x="{ax + 5*34 + 16}" y="{y+136}" text-anchor="middle" font-size="10" font-weight="700" fill="#DC2626">FAIL</text>')
    svg.add(f'<text x="{x+20}" y="{y+170}" font-size="10" fill="{MUTED}">诚·证·数·引·驳 全 PASS · 任一 FAIL 阻断</text>')


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

    svg.text(W / 2, TITLE_Y, title, size=30, fill=INK, weight="800", anchor="middle")
    svg.text(W / 2, SUB_Y, subtitle, size=13.5, fill="#64748B", anchor="middle")

    # ── 流程卡片：一行四个，两行 ────────────────────────────
    card_w = (inner - 3 * CARD_GAP) / 4
    y = ROW_Y
    row1 = [
        ("brief",  "立项确认",    ["先问清 4 件事："], "project_brief.py · 第 0 步", deco_brief),
        ("novel",  "找实验模板",   ["arXiv 找已发表论文", "看别人怎么做实验"], "不限顶会 · 先模板后扫", deco_template),
        ("make",   "造现象",      ["小系统 0.1–4M 参数", "预注册 · 异常四关"], "先看已发表论文怎么做", deco_make),
        ("law",    "找规律",      ["全条件成立才保留", "剔除不稳定"], None, deco_law),
    ]
    row2 = [
        ("idea",   "反推 idea",   ["三种来源，按优先级："], None, deco_idea),
        ("novel",  "三轮查新",    ["读正文 · 三路核查", "摘要不得下判定"], None, deco_novel),
        ("verify", "上卡验证",    ["固定预算 · 基线先行 · 评测只读"], None, deco_verify),
        ("audit",  "五层审计",    ["先 story 后 paper · 五层链"], None, deco_audit),
    ]

    # 第一行
    x = MARGIN
    xs1 = []
    for key, t, lines, foot, *d in row1:
        xs1.append(x)
        stage_card(svg, x, y, card_w, CARD_H, key, t, lines, foot, d[0] if d else None)
        x += card_w + CARD_GAP
    mid1 = y + CARD_H / 2
    svg.arrow(MARGIN - 14, mid1, MARGIN - 3, mid1)
    for i in range(3):
        svg.arrow(xs1[i] + card_w + 3, mid1, xs1[i + 1] - 3, mid1)

    # 第二行
    y2 = y + CARD_H + ROW_GAP
    xs2 = []
    x = MARGIN
    for key, t, lines, foot, *d in row2:
        xs2.append(x)
        stage_card(svg, x, y2, card_w, CARD_H, key, t, lines, foot, d[0] if d else None)
        x += card_w + CARD_GAP
    mid2 = y2 + CARD_H / 2
    for i in range(3):
        svg.arrow(xs2[i] + card_w + 3, mid2, xs2[i + 1] - 3, mid2)
    # 第一行最后一张 → 第二行第一张
    svg.path(f"M {xs1[3] + card_w / 2:g} {y + CARD_H + 2:g} L {xs1[3] + card_w / 2:g} {y2 - 2:g}")

    # ── 查新分支面板 ─────────────────────────────────────
    py = y2 + CARD_H + PANEL_Y_GAP
    nx = xs2[1]  # 三轮查新
    svg.text(nx - 2, py - 8, "(b)", size=12, fill=MUTED, weight="600")
    panel_w = card_w * 2 + CARD_GAP
    svg.shadow(nx, py, panel_w, PANEL_H, r=10)
    svg.rect(nx, py, panel_w, PANEL_H, fill="#FFFFFF", stroke=HAIR, sw=1.4, r=10)
    svg.text(nx + 16, py + 24, "查新后的两个出口", size=13, fill=INK, weight="600")
    ew = (panel_w - 32 - 12) / 2
    svg.rect(nx + 16, py + 38, ew, 58, fill="#FFFBEB", stroke="#D97706", sw=1.2, r=7)
    svg.text(nx + 26, py + 60, "撞车 → 深挖新维度", size=12, fill="#92400E", weight="600")
    svg.text(nx + 26, py + 80, "换观测维度，不是把题目改窄", size=10, fill="#78716C")
    svg.rect(nx + 28 + ew, py + 38, ew, 58, fill="#FEF2F2", stroke=RED, sw=1.2, r=7)
    svg.text(nx + 38 + ew, py + 60, "实质重复 → 淘汰", size=12, fill="#991B1B", weight="600")
    svg.text(nx + 38 + ew, py + 80, "记入漏斗，作反重复记忆", size=10, fill="#78716C")
    svg.path(f"M {nx + card_w / 2:g} {y2 + CARD_H + 2:g} L {nx + card_w / 2:g} {py - 2:g}")

    # ── 工具区 ───────────────────────────────────────────
    ty = py + PANEL_H + TOOLS_Y_GAP
    svg.text(MARGIN - 2, ty - 8, "(c)", size=12, fill=MUTED, weight="600")
    svg.text(MARGIN, ty + 18, "配套工具", size=14, fill=INK, weight="700")
    svg.text(MARGIN + 72, ty + 18, "8 个 · 纯 Python 标准库 · 任何能跑 bash 的 agent 可用", size=11, fill=MUTED)
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

    # ── 融合层 / 跨平台 ──────────────────────────────────
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
        svg.rect(cx, cy, fcw, 48, fill="#F8FAFC", stroke=c, sw=1.3, r=8)
        svg.text(cx + 12, cy + 20, t, size=12, fill=INK, weight="600")
        svg.text(cx + 12, cy + 38, l1, size=10, fill=SUB)

    # ── 色卡 + 平台条 ───────────────────────────────────
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
    svg.text(W / 2, bar_y + BAR_H / 2 + 7, bar_text, size=15, fill="#FFFFFF", weight="700", anchor="middle")

    svg.h = bar_y + BAR_H + 34
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
