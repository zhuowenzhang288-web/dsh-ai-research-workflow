#!/usr/bin/env python3
"""verify_citations — 客观核验报告中的 arXiv / DOI 引用，输出 Hallucination Rate (HR)。

对齐 REASONS benchmark (arXiv:2405.02228) 的 Hallucination Rate 指标：
    HR = 无法核验（不存在 / 号错）的引用数 / 总引用数

用法:
    python3 verify_citations.py <报告.md> [--json out.json]

只做「客观核验」：引用号是否存在、对应标题是什么。不做「归因是否断章取义」——
那需要正文级精读，另行处理。核验源：arXiv 官方 API（export.arxiv.org）+ Crossref。

依赖：仅 Python 标准库，无第三方包。
"""
import sys
import re
import json
import time
import argparse
import urllib.request
import urllib.parse

# arXiv 号：YYMM.NNNNN（2 开头，2007-03 后），可选 vN 版本后缀
ARXIV_RE = re.compile(r'\b(2\d{3}\.\d{4,5})(?:v\d+)?\b')
DOI_RE = re.compile(r'\b(10\.\d{4,9}/[^\s<>"\')\]}]+)')


def arxiv_lookup(aid, timeout=25):
    """查 arXiv API，返回 {arxiv, exists, title}。exists: True/False/None(网络失败)。"""
    url = f"http://export.arxiv.org/api/query?id_list={aid}"
    for attempt in range(3):
        try:
            xml = urllib.request.urlopen(url, timeout=timeout).read().decode()
            if '<entry>' not in xml:
                return {"arxiv": aid, "exists": False, "title": None}
            m = re.search(r'<entry>.*?<title>(.*?)</title>', xml, re.S)
            if m:
                title = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                return {"arxiv": aid, "exists": True, "title": title}
            return {"arxiv": aid, "exists": False, "title": None}
        except Exception as e:
            if attempt == 2:
                return {"arxiv": aid, "exists": None, "title": None, "error": str(e)}
            time.sleep(3)
    return {"arxiv": aid, "exists": None, "title": None}


def doi_lookup(doi, timeout=15):
    """查 Crossref，返回 {doi, exists, title}。"""
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "verify-citations/1.0 (mailto:research@example.com)"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.load(r)
        title = d["message"]["title"][0] if d["message"].get("title") else None
        return {"doi": doi, "exists": True, "title": title}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"doi": doi, "exists": False, "title": None}
        return {"doi": doi, "exists": None, "title": None, "error": str(e)}
    except Exception as e:
        return {"doi": doi, "exists": None, "title": None, "error": str(e)}


def main():
    ap = argparse.ArgumentParser(description="客观核验引用，输出 Hallucination Rate")
    ap.add_argument("report", help="Markdown 报告路径")
    ap.add_argument("--json", dest="json_out", default=None, help="结果 JSON 输出路径")
    args = ap.parse_args()

    with open(args.report, encoding="utf-8") as f:
        text = f.read()

    arxiv_ids = sorted(set(ARXIV_RE.findall(text)))
    dois = sorted(set(DOI_RE.findall(text)))

    results = []
    for aid in arxiv_ids:
        results.append(arxiv_lookup(aid))
        time.sleep(1.2)
    for doi in dois:
        results.append(doi_lookup(doi))
        time.sleep(0.8)

    total = len(results)
    verified = sum(1 for r in results if r.get("exists") is True)
    fabricated = sum(1 for r in results if r.get("exists") is False)
    unknown = sum(1 for r in results if r.get("exists") is None)
    hr = fabricated / total if total else 0.0

    out = {
        "report": args.report,
        "total_citations": total,
        "verified": verified,
        "fabricated": fabricated,
        "unknown": unknown,
        "hallucination_rate": round(hr, 4),
        "results": results,
    }

    print(f"报告: {args.report}")
    print(f"总引用 {total} | 核验通过 {verified} | 编造/不存在 {fabricated} | 无法核验 {unknown}")
    print(f"Hallucination Rate (HR) = {hr * 100:.1f}%")
    for r in results:
        key = r.get("arxiv") or r.get("doi")
        if r.get("exists") is True:
            print(f"  ✅ {key}  {r.get('title', '')[:80]}")
        elif r.get("exists") is False:
            print(f"  ❌ {key}  不存在/号错")
        else:
            print(f"  ⚠️  {key}  无法核验 {r.get('error', '')[:40]}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"\nJSON 已存: {args.json_out}")


if __name__ == "__main__":
    main()
