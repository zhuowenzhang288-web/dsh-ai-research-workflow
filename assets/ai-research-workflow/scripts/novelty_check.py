#!/usr/bin/env python3
"""novelty_check — 查新辅助：给定关键词，查 arXiv 官方 API，输出候选论文元数据，供三轮查新对照。

用法:
    python3 novelty_check.py "GRPO collapse probability across seeds"
    python3 novelty_check.py "维数灾难" --max 15 --field cs.LG

说明:
    只依赖 Python 标准库，任何能跑 bash 的 agent 都能用。
    摘要仅用于初筛；KEEP/KILL 判定必须读正文（见 SKILL.md §2 取证标准）。
"""
import argparse
import re
import sys
import time
import urllib.parse
import urllib.request

API = "http://export.arxiv.org/api/query"


def parse_atom(xml: str):
    """解析 arXiv API 返回的 Atom XML，抽取 entry 列表。"""
    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.S)
    out = []
    for e in entries:
        def grab(tag):
            m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", e, re.S)
            return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""

        id_match = re.search(r"<id>(.*?)</id>", e, re.S)
        arxiv_id = ""
        if id_match:
            m = re.search(r"abs/([^v<>]+)", id_match.group(1))
            arxiv_id = m.group(1).strip() if m else ""
        published = grab("published")
        year = published[:4] if published else ""
        title = grab("title")
        summary = grab("summary")
        out.append({
            "id": arxiv_id,
            "year": year,
            "title": title,
            "summary": summary,
        })
    return out


def search(query: str, max_results: int, field: str, retries: int = 3):
    q = urllib.parse.quote(f"all:{query}")
    url = f"{API}?search_query={q}&start=0&max_results={max_results}&sortBy=relevance"
    if field:
        url += f"&search_query=cat:{field}+AND+all:{urllib.parse.quote(query)}"
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt == retries - 1:
                print(f"[novelty_check] 查询失败: {e}", file=sys.stderr)
                return ""
            time.sleep(2 * (attempt + 1))
    return ""


def main():
    ap = argparse.ArgumentParser(description="查新：查 arXiv 并列出候选论文")
    ap.add_argument("query", help="关键词或一句话研究问题")
    ap.add_argument("--max", dest="max_results", type=int, default=10, help="最多返回篇数（默认 10）")
    ap.add_argument("--field", default="", help="arXiv 分类（如 cs.LG、cs.AI、cs.CL），可选")
    args = ap.parse_args()

    print(f"查新查询: {args.query}")
    print(f"返回上限: {args.max_results}" + (f" | 领域: {args.field}" if args.field else ""))
    print("-" * 70)

    xml = search(args.query, args.max_results, args.field)
    if not xml:
        sys.exit(1)
    entries = parse_atom(xml)
    if not entries:
        print("无命中。换关键词或放宽范围。")
        return

    print(f"命中 {len(entries)} 篇（注：摘要级，仅初筛；KEEP/KILL 需读正文）:\n")
    for i, e in enumerate(entries, 1):
        summary = e["summary"][:180] + ("…" if len(e["summary"]) > 180 else "")
        print(f"[{i}] arXiv:{e['id']}  ({e['year']})")
        print(f"    {e['title']}")
        print(f"    {summary}")
        print()

    print("=" * 70)
    print("下一步（按 SKILL.md §2 三轮查新）:")
    print("  1. 相同问题  2. 相同方法  3. 相邻领域")
    print("  对最接近的 2-3 篇，读正文方法+实验+图表后再判 KEEP/KILL；")
    print("  只读摘要不得下判定。")


if __name__ == "__main__":
    main()