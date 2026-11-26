#!/usr/bin/env python3
"""venue_probe — 从 CCF-A 顶会已录用论文里找「实验怎么做」，给造现象提供模板。

对应 SKILL.md §4.2.1 造现象的前置：与其盲扫，先看目标会议近年论文
①用了什么实验系统/规模 ②扫了哪些旋钮 ③画了哪类图、报了哪些指标。

用法:
    python3 scripts/venue_probe.py "GRPO collapse" --venue NeurIPS
    python3 scripts/venue_probe.py "phase transition" --max 12 --years 2

说明:
    - 只依赖 Python 标准库。
    - arXiv API 没有「会议」过滤，本脚本用 arXiv 的 comments/journal-ref 字段
      匹配会议名，匹配不到的会被丢弃——所以结果偏少但更准。
    - 输出是「实验模板候选」，每篇仍须读正文实验节，摘要只用于初筛。
"""
import argparse
import re
import sys
import time
import urllib.parse
import urllib.request

API = "http://export.arxiv.org/api/query"
VENUE_PATTERNS = {
    "neurips": r"neurips|nips|neural information processing",
    "icml": r"\bicml\b|international conference on machine learning",
    "iclr": r"\biclr\b|international conference on learning representations",
    "cvpr": r"\bcvpr\b",
    "iccv": r"\biccv\b",
    "eccv": r"\beccv\b",
    "acl": r"\bacl\b|association for computational linguistics",
    "emnlp": r"\bemnlp\b",
    "kdd": r"\bkdd\b",
    "sigir": r"\bsigir\b",
    "osdi": r"\bosdi\b",
    "sosp": r"\bsosp\b",
    "ccs": r"\bccs\b",
    "usenix": r"usenix",
}

# 实验相关的线索词：用于从摘要里粗提「做了什么实验」，仅为提示，须读正文核实
HINTS = {
    "规模": r"\b\d+(?:\.\d+)?\s*[BMK]\b|\b\d+(?:\.\d+)?\s*(?:million|billion)\b|parameters?|params",
    "数据/环境": r"benchmark|dataset|environment|MiniWoB|ALFWorld|WebShop|GAIA|Minecraft|SWE-?bench",
    "对照": r"ablation|baseline|compared? (?:to|with)|control",
    "度量": r"accuracy|success rate|pass@|F1|AUC|p-value|confidence interval|seeds?",
    "图型": r"phase (?:diagram|transition)|scaling law|heatmap|sweep| Pareto",
}


def fetch(url, retries=3):
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            if i == retries - 1:
                print(f"[venue_probe] 请求失败: {e}", file=sys.stderr)
                return ""
            time.sleep(2 * (i + 1))
    return ""


def parse(xml):
    out = []
    for e in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        def g(tag):
            m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", e, re.S)
            return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        aid = re.search(r"abs/([^v<>]+)", g("id"))
        out.append({
            "id": aid.group(1).strip() if aid else "",
            "title": g("title"),
            "summary": g("summary"),
            "comment": g("arxiv:comment"),
            "journal": g("arxiv:journal_ref"),
            "year": g("published")[:4],
        })
    return out


def main():
    ap = argparse.ArgumentParser(description="从顶会录用论文里找实验模板")
    ap.add_argument("query", help="研究方向关键词")
    ap.add_argument("--venue", default="", help="会议名（neurips/icml/iclr/cvpr/acl/emnlp/kdd...），不填则不限会议")
    ap.add_argument("--max", type=int, default=8, help="最多列出篇数（默认 8）")
    ap.add_argument("--years", type=int, default=3, help="只看最近 N 年（默认 3）")
    args = ap.parse_args()

    pat = VENUE_PATTERNS.get(args.venue.lower(), None)
    if args.venue and not pat:
        pat = re.escape(args.venue.lower())

    terms = [t for t in re.split(r"\s+", args.query.strip()) if t]
    query = " AND ".join(f"all:{t}" for t in terms)
    q = urllib.parse.quote(query)
    want = min(args.max * 8, 80)  # 会议过滤会丢很多，多抓一些
    xml = fetch(f"{API}?search_query={q}&start=0&max_results={want}&sortBy=relevance")
    papers = parse(xml)
    import datetime
    this_year = datetime.date.today().year
    kept, n_workshop = [], 0
    for p in papers:
        if args.years and p["year"] and p["year"].isdigit():
            if int(p["year"]) < this_year - args.years + 1:
                continue
        if pat:
            note = p["comment"] + " " + p["journal"]
            if not re.search(pat, note, re.I):
                continue
            if re.search(r"workshop|non-?archival|under review|submitted to", note, re.I):
                n_workshop += 1
                continue
        kept.append(p)
    kept = kept[: args.max]

    print(f"查询: {args.query}" + (f" | 会议: {args.venue}" if args.venue else " | 不限会议"))
    n_note = sum(1 for p in papers if p["comment"] or p["journal"])
    print(f"抓到 {len(papers)} 篇 → 会议/年份过滤后 {len(kept)} 篇"
          + (f"（另有 {n_workshop} 篇是 workshop，已排除）" if n_workshop else "") + "\n")
    if pat:
        print(f"⚠️ 覆盖率提示：抓到的 {len(papers)} 篇里只有 {n_note} 篇在 arXiv 标了备注/期刊信息。")
        print("   很多已录用论文不在 arXiv 标会议 → 本工具会漏掉它们，结果偏少不等于该会议没相关工作。")
        print("   补全办法：直接翻会议官网的 accepted papers 列表（如 neurips.cc/Virtual），或让子 agent 去查。\n")
    if not kept:
        print("无命中。可放宽：换关键词、去掉 --venue、或调大 --years。")
        return

    for i, p in enumerate(kept, 1):
        venue_note = " / ".join(x for x in (p["comment"][:60], p["journal"][:40]) if x) or "未标注会议"
        print(f"[{i}] arXiv:{p['id']} ({p['year']})  {p['title']}")
        print(f"    出处线索: {venue_note}")
        for name, rx in HINTS.items():
            hits = sorted(set(m.group(0).lower() for m in re.finditer(rx, p["summary"], re.I)))
            if hits:
                shown = ", ".join(hits[:5]) + ("…" if len(hits) > 5 else "")
                print(f"    · {name}: {shown}")
        print(f"    摘要(初筛): {p['summary'][:150]}…\n")

    print("=" * 70)
    print("下一步（§4.2.1 造现象前置）：")
    print("  1. 挑 2–3 篇最贴近的，读正文实验节：系统规模、旋钮、图表类型、指标、种子数")
    print("  2. 把它们的实验设计当成模板，改成你算力能跑的小规模版本")
    print("  3. 先复现其趋势（阳性对照），再在你关心的旋钮上找异常")
    print("  只读摘要不得直接照搬实验设计；会议归属以原文为准，comments 字段可能不准。")


if __name__ == "__main__":
    main()
