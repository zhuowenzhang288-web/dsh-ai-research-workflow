#!/usr/bin/env python3
"""gen_architecture.py — 参数化生成架构图 SVG。

为什么要有这个脚本：架构图原来是手写坐标的 SVG，150+ 个元素互相用绝对位置对齐，
每加一个区域都要手调下面所有坐标，极易出错。这里把布局变成变量：
    - 改卡片高度/间距/新增区域，只改顶部的 LAYOUT 常量
    - 箭头端点从卡片矩形推导，不手写
    - 两个仓各生成一张：--target skill（跨平台方法）/ --target dsh（DSH agent）

用法:
    python3 docs/gen_architecture.py --target dsh  --out docs/architecture.svg
    python3 docs/gen_architecture.py --target skill --out docs/architecture.svg
    python3 docs/gen_architecture.py --all     # 按仓库相对路径生成两张
"""
import argparse
import os

# ----------------------------------------------------------------------------- palette
INK, SUB, MUTED, LINE = "#1E293B", "#374151", "#9CA3AF", "#C7CEDC"
BG = "#FDFBF7"
RED = "#DC2626"
RED_DARK = "#7F1D1D"
#        (描边, 标题色, 浅底)
GREEN, TEAL, AMBER, BLUE, PURPLE, SLATE = "#34D399", "#22D3EE", "#FBBF24", "#60A5FA", "#A78BFA", "#94A3B8"
GREEN_T, TEAL_T, AMBER_T, BLUE_T, PURPLE_T, SLATE_T = "#047857", "#0E7490", "#B45309", "#1D4ED8", "#6D28D9", "#334155"
GREEN_L, TEAL_L, AMBER_L, BLUE_L = "#6EE7B7", "#67E8F9", "#FCD34D", "#93C5FD"
MONO = "ui-monospace, SFMono-Regular, Menlo, monospace"
SANS = "-apple-system, 'Segoe UI', 'PingFang SC', 'Noto Sans CJK SC', 'Microsoft YaHei', sans-serif"

# ----------------------------------------------------------------------------- layout
M = 60                  # 左右外边距
W = 1800                # 画布宽
TITLE_Y, SUBTITLE_Y = 72, 110
BRIEF_H = 140           # 立项确认条高
GAP = 20                # 区块间距
CARD_H_LOOP = 220       # (a) 第一行卡高
CARD_H_BOT = 200        # (a) 第二行卡高
ROW_GAP = 40
BRANCH_H = 44
PAD = 30                # 区块内边距
TOOLS_COLS, TOOLS_ROWS = 2, 4   # 工具区网格（7 个工具 + 1 格说明）
FUSION_H = 220
PAL_H = 44
BAR_H = 64

# ----------------------------------------------------------------------------- helpers
def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class SVG:
    def __init__(self, w, h):
        self.w, self.h, self.o = w, h, []

    def add(self, s):
        self.o.append(s)

    def rect(self, x, y, w, h, fill="#FFFFFF", stroke=None, sw=0, r=12, op=None, fill_op=None, dash=None, shadow=False, extra=""):
        a = [f'x="{x:g}"', f'y="{y:g}"', f'width="{w:g}"', f'height="{h:g}"', f'rx="{r:g}"', f'fill="{fill}"']
        if fill_op is not None:
            a.append(f'fill-opacity="{fill_op}"')
        if op is not None:
            a.append(f'opacity="{op}"')
        if stroke:
            a.append(f'stroke="{stroke}" stroke-width="{sw:g}"')
        if dash:
            a.append(f'stroke-dasharray="{dash}"')
        if extra:
            a.append(extra)
        s = f'<rect {" ".join(a)}/>'
        if shadow:
            s = f'<g filter="url(#soft)">{s}</g>'
        self.add(s)

    def text(self, x, y, t, size=15, fill=SUB, weight=None, anchor=None, mono=False, italic=False, op=None):
        a = [f'x="{x:g}"', f'y="{y:g}"', f'font-size="{size:g}"', f'fill="{fill}"']
        if weight:
            a.append(f'font-weight="{weight}"')
        if anchor:
            a.append(f'text-anchor="{anchor}"')
        if mono:
            a.append(f'font-family="{MONO}"')
        if italic:
            a.append('font-style="italic" font-family="Georgia, serif"')
        if op is not None:
            a.append(f'opacity="{op}"')
        self.add(f'<text {" ".join(a)}>{esc(t)}</text>')

    def line(self, x1, y1, x2, y2, color="#F87171", sw=4, arrow=False):
        a = [f'x1="{x1:g}"', f'y1="{y1:g}"', f'x2="{x2:g}"', f'y2="{y2:g}"', f'stroke="{color}"',
             f'stroke-width="{sw:g}"', 'stroke-linecap="round"']
        if arrow:
            a.append('marker-end="url(#arr)"')
        self.add(f'<line {" ".join(a)}/>')

    def path(self, d, color="#F87171", sw=3, arrow=False):
        a = [f'd="{d}"', 'fill="none"', f'stroke="{color}"', f'stroke-width="{sw:g}"',
             'stroke-linecap="round"', 'stroke-linejoin="round"']
        if arrow:
            a.append('marker-end="url(#arr)"')
        self.add(f'<path {" ".join(a)}/>')

    def circle(self, cx, cy, r, fill, stroke=None, sw=0):
        a = [f'cx="{cx:g}"', f'cy="{cy:g}"', f'r="{r:g}"', f'fill="{fill}"']
        if stroke:
            a.append(f'stroke="{stroke}" stroke-width="{sw:g}"')
        self.add(f'<circle {" ".join(a)}/>')

    def pill(self, x, y, w, h, label, fill, fg, size=15, stroke=None, dash=None, weight=700, shadow=False):
        self.rect(x, y, w, h, fill=fill, stroke=stroke, sw=2 if stroke else 0, r=h / 2, dash=dash, shadow=shadow)
        self.text(x + w / 2, y + h / 2 + size * 0.36, label, size=size, fill=fg, weight=weight, anchor="middle")

    def render(self):
        return ("\n".join(self.o))


def header(svg):
    svg.add(f'<defs>'
            f'<marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,1 L9,5 L0,9 z" fill="#F87171"/></marker>'
            f'<filter id="soft" x="-30%" y="-30%" width="160%" height="160%">'
            f'<feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#64748B" flood-opacity="0.2"/></filter>'
            f'<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0%" stop-color="{RED}"/><stop offset="100%" stop-color="{RED_DARK}"/></linearGradient>'
            f'</defs>')


def zone_label(svg, x, y, letter):
    svg.circle(x, y, 16, "#64748B")
    svg.text(x, y + 5, letter, size=15, fill="#FFFFFF", weight=700, anchor="middle")


def zone(svg, x, y, w, h, letter):
    svg.rect(x, y, w, h, fill="#FFFFFF", fill_op=0.6, stroke=LINE, sw=2, r=24, dash="8 6")
    zone_label(svg, x, y, letter)


# ----------------------------------------------------------------------------- live counts
import re as _re
def _count_lessons():
    """数 SKILL.md 里「实战教训」那一节的编号条目。

    只数该小节——整篇用同一个正则会把各节的编号列表都数进去（曾数出 28）。
    默认读本仓库的 SKILL.md（docs/../SKILL.md），可用环境变量 SKILL_MD 指定别的；
    找不到文件或小节就返回 None，图上不写数字（不猜）。
    """
    p = os.environ.get("SKILL_MD") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SKILL.md")
    p = os.path.normpath(p)
    if not os.path.exists(p):
        return None
    txt = open(p, encoding="utf-8").read()
    m = _re.search(r"^## \d+\. 实战教训.*?\n(.*?)(?=^## )", txt, _re.S | _re.M)
    return len(_re.findall(r"^\d+\. \*\*", m.group(1), _re.M)) if m else None
N_LESSONS = _count_lessons()

# ----------------------------------------------------------------------------- cards
def loop_card(svg, x, y, w, h, color, color_t, color_l, title, lines, foot=None):
    """(a) 区的流程卡：顶部色条 + 标题 + 若干行 + 可选灰色脚注。返回内容区基准坐标。"""
    svg.rect(x, y, w, h, stroke=color, sw=2.5, r=18, shadow=True)
    svg.rect(x + PAD - 22, y + 14, 52, 8, fill=color_l, r=4)
    ty = y + 50
    svg.text(x + PAD - 22, ty, title, size=22, weight=700, fill=color_t)
    ly = ty + 32
    for ln in lines:
        svg.text(x + PAD - 22, ly, ln, size=15, fill=SUB)
        ly += 28
    if foot:
        svg.text(x + PAD - 22, y + h - 16, foot, size=14, fill=MUTED)
    return ly


# ----------------------------------------------------------------------------- (0) brief
def brief_bar(svg, y, w):
    svg.rect(M, y, w, BRIEF_H, fill=INK, r=24)
    svg.circle(M, y, 16, "#FDE68A")
    svg.text(M, y + 6, "0", size=15, weight=700, fill=INK, anchor="middle")
    x0 = M + 32
    svg.text(x0, y + 46, "📋 第 0 步 · 立项确认", size=26, weight=800, fill="#FDE68A")
    svg.text(x0, y + 84, "动手之前先和用户对齐，落盘成 PROJECT_BRIEF.md（单一事实源）。必填项没填，不进入选题。", size=17, fill="#E2E8F0")
    svg.text(x0, y + 116, "方向 · 目标会议/截稿 · 算力 · 预算 · 距截稿几周 · 每周投入 · 团队 · 什么算成功 · 硬约束 · 不做的事", size=17, fill="#CBD5E1")
    # 右侧脚本卡
    bw = 540
    bx = M + w - bw - 24
    svg.rect(bx, y + 20, bw, 44, fill="#374151", r=22)
    svg.text(bx + bw / 2, y + 49, "project_brief.py init → check", size=17, weight=700, fill="#F8FAFC", anchor="middle", mono=True)
    svg.text(bx + bw / 2, y + 96, "check：算力够不到子领域起步规模、时间不够 → 先停下与用户确认", size=15, fill="#FCA5A5", anchor="middle")
    svg.text(bx + bw / 2, y + 122, "不替用户填；用户不确定的标「待定」并写何时能定", size=15, fill="#94A3B8", anchor="middle")
    return BRIEF_H


# ----------------------------------------------------------------------------- (a) loop
def section_loop(svg, y, w, force_h=None):
    """(a) 研究循环。返回区块高度。"""
    x = M
    h = force_h or (PAD + CARD_H_LOOP + ROW_GAP + CARD_H_BOT + 34 + BRANCH_H + 44)
    zone(svg, x, y, w, h, "a")

    # 左侧竖条：画在 (a) 区内、卡片左边，不超出区块也不压外边距
    tab_w = 30
    tab_x = x + 16
    svg.rect(tab_x, y + 30, tab_w, h - 60, fill=RED, stroke="#FFFFFF", sw=3, r=tab_w / 2)
    cx, cy = tab_x + tab_w / 2, y + 30 + (h - 60) / 2
    svg.add(f'<text x="{cx:g}" y="{cy + 5:g}" text-anchor="middle" font-size="15" font-weight="700" fill="#FFFFFF" '
            f'letter-spacing="3" transform="rotate(-90 {cx:g} {cy:g})">RESEARCH LOOP 🔬</text>')

    # 卡片区从竖条右侧开始
    ix = tab_x + tab_w + 16
    iw = x + w - PAD - ix
    gap = 30
    cw = (iw - 2 * gap) / 3
    c1x, c2x, c3x = ix, ix + cw + gap, ix + 2 * (cw + gap)
    y1 = y + PAD
    y2 = y1 + CARD_H_LOOP + ROW_GAP

    loop_card(svg, c1x, y1, cw, CARD_H_LOOP, GREEN, GREEN_T, GREEN_L, "🧫 造现象", [
        "小系统 0.1–4M 参数 · 几百个秒级实验",
        "预注册写死阈值 → 再看数据",
        "异常四关：效应量/锐利/可复现/非已知",
        "管道先验证，再解释数据",
    ], foot="第 0 步先看顶会怎么做实验 · 3 轮无异常换旋钮族")

    loop_card(svg, c2x, y1, cw, CARD_H_LOOP, TEAL, TEAL_T, TEAL_L, "🔍 找规律", [
        "每批追问：有无普遍成立的简单规律",
        "剔除不稳定结论，全条件成立才保留",
        "公式化，可复用可预测",
    ], foot="跨规模推广标「待大规模实测」")
    # 迷你折线图：占 3 行正文之后、脚注之前的那一带（高约 44）
    px, py = c2x + PAD - 22, y1 + 150   # 图顶：在最后一行正文(y1+138)之下、脚注(y1+204)之上
    pts1 = [(px, py + 28), (px + 52, py + 8), (px + 102, py + 16), (px + 152, py + 2), (px + 200, py - 6)]
    pts2 = [(px, py + 34), (px + 52, py + 28), (px + 102, py + 34), (px + 152, py + 22), (px + 200, py + 26)]
    svg.add('<polyline points="%s" fill="none" stroke="#F87171" stroke-width="2.5" stroke-dasharray="5 4" stroke-linecap="round"/>' % " ".join(f"{a:.0f},{b:.0f}" for a, b in pts2))
    svg.add('<polyline points="%s" fill="none" stroke="%s" stroke-width="3" stroke-linecap="round"/>' % (" ".join(f"{a:.0f},{b:.0f}" for a, b in pts1), TEAL))
    svg.circle(pts1[-1][0], pts1[-1][1], 4, TEAL)
    svg.text(px + 214, py + 6, "τ(β,λ)", size=18, fill=TEAL_T, italic=True)

    svg.rect(c3x, y1, cw, CARD_H_LOOP, stroke=AMBER, sw=2.5, r=18, shadow=True)
    svg.rect(c3x + PAD - 22, y1 + 14, 52, 8, fill=AMBER_L, r=4)
    svg.text(c3x + PAD - 22, y1 + 50, "💡 规律反推 idea", size=22, weight=700, fill=AMBER_T)
    svg.text(c3x + PAD - 22, y1 + 82, "idea 是挖出来的，不是憋出来的", size=15, fill=SUB)
    pw = (cw - 2 * PAD + 44 - 24) / 3
    svg.pill(c3x + PAD - 22, y1 + 102, pw, 34, "现象 ①", "#FEF3C7", AMBER_T)
    svg.pill(c3x + PAD - 22 + pw + 12, y1 + 102, pw, 34, "文献 ②", "#FFFFFF", "#64748B", stroke="#CBD5E1", weight=700)
    svg.pill(c3x + PAD - 22 + 2 * (pw + 12), y1 + 102, pw, 34, "凭空 ③", "#FFFFFF", MUTED, stroke="#E2E8F0", dash="4 3", weight=400)
    svg.text(c3x + PAD - 22, y1 + 170, "优先用规律；凭空想 = 高概率白做", size=15, fill=SUB)
    svg.text(c3x + PAD - 22, y1 + CARD_H_LOOP - 16, "规律 → 解释 → idea", size=14, fill=MUTED)

    # 第二行
    c4x, c5x, c6x = c3x, c2x, c1x
    loop_card(svg, c4x, y2, cw, CARD_H_BOT, BLUE, BLUE_T, BLUE_L, "📚 三轮查新", [])
    rx = c4x + PAD - 2
    for i, lab in enumerate(["R1", "R2", "R3"]):
        svg.circle(rx + i * 50, y2 + 84, 17, "#EFF6FF", stroke=BLUE, sw=2)
        svg.text(rx + i * 50, y2 + 90, lab, size=13, weight=700, fill=BLUE_T, anchor="middle")
    svg.pill(rx + 140, y2 + 68, 130, 32, "只读摘要 ✗", "#FEF2F2", "#B91C1C", size=14, stroke="#F87171")
    svg.text(c4x + PAD - 22, y2 + 126, "读正文：方法 + 实验 + 图表", size=15, fill=SUB)
    svg.text(c4x + PAD - 22, y2 + 154, "覆盖非论文渠道 HF/GitHub/博客", size=15, fill=SUB)
    svg.text(c4x + PAD - 22, y2 + CARD_H_BOT - 12, "R1 同问题 · R2 同方法 · R3 相邻领域", size=14, fill=MUTED)

    svg.rect(c5x, y2, cw, CARD_H_BOT, stroke=PURPLE, sw=2.5, r=18, shadow=True)
    svg.rect(c5x + PAD - 22, y2 + 14, 52, 8, fill="#C4B5FD", r=4)
    svg.text(c5x + PAD - 22, y2 + 50, "🚀 上卡验证", size=22, weight=700, fill=PURPLE_T)
    svg.text(c5x + PAD - 22, y2 + 82, "固定预算 · 基线先行 · 评测只读", size=15, fill=SUB)
    svg.text(c5x + PAD - 22, y2 + 112, "🚩 基线先行 · ⏱ 固定预算", size=14, fill=PURPLE_T)
    base = y2 + CARD_H_BOT - 34        # 柱状图的地面
    bx0 = c5x + PAD - 10
    svg.rect(bx0, base - 40, 20, 40, fill=GREEN, r=3)
    svg.rect(bx0 + 32, base - 24, 20, 24, fill="#CBD5E1", r=3)
    svg.rect(bx0 + 64, base - 14, 20, 14, fill="#F87171", r=3)
    svg.line(bx0 - 10, base, bx0 + 100, base, color="#CBD5E1", sw=2)
    svg.text(bx0 + 112, base - 22, "keep", size=14, fill="#6B7280")
    svg.text(bx0 + 112, base - 4, "discard", size=14, fill="#6B7280")
    svg.text(c5x + PAD - 22, y2 + CARD_H_BOT - 12, "简洁性准则：删代码不降性能=胜利", size=14, fill=MUTED)

    svg.rect(c6x, y2, cw, CARD_H_BOT, stroke=SLATE, sw=2.5, r=18, shadow=True)
    svg.rect(c6x + PAD - 22, y2 + 14, 52, 8, fill="#CBD5E1", r=4)
    svg.text(c6x + PAD - 22, y2 + 50, "🛡️ 写作审计", size=22, weight=700, fill=SLATE_T)
    svg.text(c6x + PAD - 22, y2 + 82, "先 story 后 paper · 写作契约", size=15, fill=SUB)
    for i in range(5):
        svg.rect(c6x + PAD - 22 + i * 32, y2 + 102, 22, 22, fill="#ECFDF5", stroke=GREEN, sw=2, r=5)
        svg.text(c6x + PAD - 18 + i * 32, y2 + 119, "✓", size=15, fill="#059669")
    svg.circle(c6x + PAD - 22 + 5 * 32 + 14, y2 + 113, 17, "#FEF2F2", stroke=RED, sw=2)
    svg.text(c6x + PAD - 22 + 5 * 32 + 14, y2 + 118, "FAIL", size=11, weight=700, fill=RED, anchor="middle")
    svg.text(c6x + PAD - 22, y2 + 158, "五层：诚·证·数·引·驳，全 PASS 才出稿", size=15, fill=SUB)
    svg.text(c6x + PAD - 22, y2 + CARD_H_BOT - 12, "任一 FAIL 即阻断", size=14, fill=MUTED)

    # ---- 箭头（全部从卡片几何推导）----
    my1 = y1 + CARD_H_LOOP / 2
    svg.line(c1x + cw, my1, c2x - 4, my1, arrow=True)
    svg.line(c2x + cw, my1, c3x - 4, my1, arrow=True)
    svg.line(c3x + cw / 2, y1 + CARD_H_LOOP, c3x + cw / 2, y2 - 6, arrow=True)
    my2 = y2 + CARD_H_BOT / 2
    svg.line(c4x - 4, my2, c5x + cw + 4, my2, arrow=True)
    svg.line(c5x - 4, my2, c6x + cw + 4, my2, arrow=True)

    # ---- 查新分支 ----
    by = y2 + CARD_H_BOT + 34
    src_x, mid_y = c4x + cw / 2, y2 + CARD_H_BOT + 14
    lo, hi = ix + 10, ix + iw - 10                  # 允许的范围
    bw2 = min(cw, ((hi - lo) - 3 * 16) / 2)          # 两个胶囊 + 间隙放得下
    # 整体居中到查新卡中心，再夹进允许范围
    total = 2 * bw2 + 16
    left_cx = min(max(src_x - total / 2 + bw2 / 2, lo + bw2 / 2), hi - bw2 / 2 - (bw2 + 16))
    right_cx = left_cx + bw2 + 16
    svg.line(src_x, y2 + CARD_H_BOT, src_x, mid_y, sw=3)
    svg.line(left_cx, mid_y, right_cx, mid_y, sw=3)
    svg.line(left_cx, mid_y, left_cx, by - 6, sw=3, arrow=True)
    svg.line(right_cx, mid_y, right_cx, by - 6, sw=3, arrow=True)
    svg.circle(src_x, mid_y, 4, "#F87171")
    svg.pill(left_cx - bw2 / 2, by, bw2, BRANCH_H, "⛏️ 撞车 → 深挖新维度", "#FFFBEB", "#92400E", size=17, stroke=AMBER, shadow=True)
    svg.pill(right_cx - bw2 / 2, by, bw2, BRANCH_H, "🚫 实质重复 → 淘汰", "#FEF2F2", "#991B1B", size=17, stroke="#F87171", shadow=True)
    svg.text(x + w / 2, by + BRANCH_H + 30, "深挖 = 换维度翻可证伪新预言 ≠ 收窄题目 · 警惕原地越钻越窄", size=15, fill=AMBER_T, anchor="middle")

    return h


# ----------------------------------------------------------------------------- (b) tools
TOOLS = [
    (BLUE, BLUE_T, "project_brief", "立项确认 init / check", "算力·时间 vs 子领域硬约束"),
    (BLUE, BLUE_T, "venue_probe", "顶会论文怎么做实验", "造现象前先拿实验模板"),
    (TEAL, TEAL_T, "novelty_check", "查 arXiv 出候选清单", "三轮查新的第一步"),
    ("#38BDF8", "#0C4A6E", "novelty_report", "取证校验：读取程度标注", "缺标即 FAIL"),
    (GREEN, GREEN_T, "funnel", "选题漏斗 add / list", "narrow-watch 防窄化预警"),
    (PURPLE, PURPLE_T, "experiment_log", "keep·discard·crash 汇总", "每跑一次记一笔"),
    ("#4ADE80", "#14532D", "verify_citations", "引用核验 → 幻觉率 HR", "投稿前必过"),
    ("#F87171", "#881337", "audit_chain", "五层审计 + 结果编造检查", "verify-results 数值锚点"),
]


def section_tools(svg, y, w, force_h=None):
    x = M + w + GAP
    tw = W - M - x
    rows = TOOLS_ROWS
    inner_h = force_h or ((PAD + 34 + 16) + rows * 150 + (rows - 1) * 20 + PAD - 10)
    zone(svg, x, y, tw, inner_h, "b")
    svg.pill(x + PAD, y + PAD - 10, 280, 34, "🧰 配套工具 · ZERO-DEP", "#8FAADC", "#FFFFFF", size=17, shadow=True)
    svg.text(x + tw - PAD, y + PAD + 13, f"{len(TOOLS)} 个 · 纯 Python 标准库", size=14, fill=MUTED, anchor="end")
    cw = (tw - 2 * PAD - 20) / 2
    top = y + PAD + 44
    for i, (c, ct, name, d1, d2) in enumerate(TOOLS):
        r, col = divmod(i, TOOLS_COLS)
        cx = x + PAD + col * (cw + 20)
        cy = top + r * 170
        svg.rect(cx, cy, cw, 150, stroke=c, sw=2.5, r=14, shadow=True)
        svg.text(cx + 16, cy + 34, name, size=17, weight=700, fill=ct, mono=True)
        svg.text(cx + 16, cy + 64, d1, size=14, fill=SUB)
        svg.text(cx + 16, cy + 90, d2, size=13, fill=MUTED)
    return inner_h


# ----------------------------------------------------------------------------- (c)
def section_fusion(svg, y, w):
    h = FUSION_H
    zone(svg, M, y, w, h, "c")
    svg.pill(M + PAD - 10, y + 20, 280, 34, "🧬 agent 融合层 · FUSION", RED, "#FFFFFF", size=17, shadow=True)
    svg.text(M + PAD + 290, y + 43, "模型 + harness 借自 DSH · skill + 经验 + 上下文 + 人格 我们提供", size=15, fill="#94A3B8")
    cards = [
        (RED, "#B91C1C", "🎭 科研模式 preset", ["人格「科研侦探」烧进系统提示", "选模式即成科研 agent"], "不靠自觉加载 skill"),
        (GREEN, GREEN_T, "📌 AGENTS.md", ["核心纪律精简版", "每次请求自动注入"], "必读兜底，不漏触发"),
        (BLUE, BLUE_T, "📖 SKILL.md", ["完整方法论", (f"{N_LESSONS} 条实战教训" if N_LESSONS else "含实战教训")], "按需加载补全细节"),
        (PURPLE, PURPLE_T, "🔄 AUTO_MODE", ["goal + schedule 拼出循环", "门前降级为记 PENDING"], "投稿门永不降级"),
        (SLATE, SLATE_T, "⚡ install.sh", ["一键安装", "自动检测五个平台"], "--dry-run 可预览"),
    ]
    gap = 20
    cw = (w - 2 * PAD - 4 * gap) / 5
    cy = y + 70
    for i, (c, ct, title, lines, foot) in enumerate(cards):
        cx = M + PAD + i * (cw + gap)
        svg.rect(cx, cy, cw, 130, stroke=c, sw=2.5, r=16, shadow=True)
        svg.text(cx + 18, cy + 34, title, size=19, weight=700, fill=ct)
        for j, ln in enumerate(lines):
            svg.text(cx + 18, cy + 64 + j * 26, ln, size=14, fill=SUB)
        svg.text(cx + 18, cy + 114, foot, size=13, fill=MUTED)
    return h


def section_portable(svg, y, w):
    """skill 仓用：跨平台条取代 DSH 融合层。"""
    h = 120
    zone(svg, M, y, w, h, "c")
    svg.pill(M + PAD - 10, y + 20, 280, 34, "🌍 跨平台 · PORTABLE", "#0EA5E9", "#FFFFFF", size=17, shadow=True)
    svg.text(M + PAD + 290, y + 43, "纯 SKILL.md + scripts，不绑任何 harness · 放对目录即用", size=15, fill="#94A3B8")
    svg.text(M + PAD, y + 86, "本仓＝方法论本体（skill）。DSH 深度集成版（preset/人格/自动循环）见 dsh-research-agent。", size=16, fill=SUB)
    return h


# ----------------------------------------------------------------------------- footer
def footer(svg, y, w, bar_text):
    svg.text(M, y + 20, "PALETTE", size=16, weight=700, fill="#94A3B8")
    pal = [(GREEN, "造现象", "#D1FAE5"), (TEAL, "找规律", "#CFFAFE"), (AMBER, "反推", "#FEF3C7"),
           (BLUE, "查新", "#DBEAFE"), (PURPLE, "验证", "#EDE9FE"), (SLATE, "审计", "#F1F5F9")]
    gap = (w - 6 * 260) / 5
    py = y + 36
    for i, (c, name, light) in enumerate(pal):
        px = M + i * (260 + gap)
        svg.rect(px, py, 260, PAL_H, fill=c, r=10)
        svg.text(px + 18, py + 29, name, size=16, weight=700, fill="#FFFFFF")
        svg.text(px + 120, py + 29, c, size=16, fill=light, mono=True)
    by = py + PAL_H + 20
    svg.rect(M, by, w, BAR_H, fill="url(#bar)", r=32, shadow=True)
    svg.text(M + w / 2, by + BAR_H / 2 + 8, bar_text, size=22, weight=700, fill="#FFFFFF", anchor="middle")
    return (by + BAR_H + 40) - y          # 高度 = 底部 - 顶部


# ----------------------------------------------------------------------------- build
def build(target):
    assert target in ("dsh", "skill")
    svg = SVG(W, 0)
    header(svg)
    w = W - 2 * M

    if target == "dsh":
        title = "🕵️ DSH Research Agent · 搭载于 DeepSeek Harness"
        subtitle = "一个装在 DSH 里的科研 agent：模型+循环由 DSH 提供，本包注入 skill+人格+preset+自动循环"
        bar = "🧩 搭载于 DeepSeek Harness · 选「科研模式」即启用 · 跨平台方法本体见 ai-research-workflow"
    else:
        title = "🔬 AI Research Workflow · 现象驱动科研工作流"
        subtitle = "跨平台的方法论本体：先做小实验找规律，再反推 idea · 不凭空胡想 · 真相只有一个，证据说了算"
        bar = "🤖 Claude Code · Codex · Cursor · opencode · DeepSeek Harness"

    return _layout(svg, target, title, subtitle, bar, w)


def _layout(svg, target, title, subtitle, bar, w):
    """自上而下堆叠区块。每个 section 返回自己的高度，这里只负责推进 y。"""
    body_start = len(svg.o)
    svg.text(W / 2, TITLE_Y, title, size=42, weight=800, fill=INK, anchor="middle")
    svg.text(W / 2, SUBTITLE_Y, subtitle, size=20, fill="#64748B", anchor="middle")

    y = 140
    y += brief_bar(svg, y, w) + GAP

    # (a) 与 (b) 并排等高：先在临时画布上量各自高度，取较大值，再按统一高度画
    w_loop = w - 560 - GAP
    h_loop = section_loop(SVG(W, 0), 0, w_loop)
    h_tools = section_tools(SVG(W, 0), 0, w_loop)
    h_ab = max(h_loop, h_tools)
    section_loop(svg, y, w_loop, force_h=h_ab)
    section_tools(svg, y, w_loop, force_h=h_ab)
    y += h_ab + GAP

    y += (section_fusion if target == "dsh" else section_portable)(svg, y, w) + GAP
    y += footer(svg, y, w, bar)

    svg.h = y
    svg.o.insert(body_start, f'<rect width="{W}" height="{y:g}" fill="{BG}"/>')
    return svg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["dsh", "skill"])
    ap.add_argument("--out")
    ap.add_argument("--all", action="store_true", help="按默认仓库路径生成两张")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    ws = os.path.abspath(os.path.join(here, "..", ".."))
    jobs = []
    if a.all:
        jobs = [("skill", os.path.join(ws, "ai-research-workflow-repo", "docs", "architecture.svg")),
                ("dsh", os.path.join(ws, "dsh-ai-research-workflow", "docs", "architecture.svg"))]
    else:
        jobs = [(a.target, a.out or os.path.join(here, "architecture.svg"))]
    for tgt, out in jobs:
        s = build(tgt)
        doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s.w} {s.h:g}" font-family="{SANS}">\n'
               + s.render() + "\n</svg>\n")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(doc)
        print(f"[{tgt}] {s.w}x{s.h:g} -> {out}")


if __name__ == "__main__":
    main()
