#!/usr/bin/env python3
"""funnel — 选题漏斗管理（对应 SKILL.md §1.2，含防窄化提醒）。

用法:
    python3 scripts/funnel.py add --title "N1 崩坏概率地图" --status killed --reason "现象是常识"
    python3 scripts/funnel.py list                    # 全部
    python3 scripts/funnel.py list --status alive     # 只看存活
    python3 scripts/funnel.py narrow-watch            # 防窄化预警

状态: alive（在研）/ killed（查新/实验淘汰）/ dropped（主动放弃）/ idea（未查新）
存储 funnel.tsv。窄化预警 = 同一 4 字片段出现在 ≥3 个 killed 题目里时提醒。
"""
import argparse
import csv
import datetime
import os
import re
from collections import Counter

FILE = "funnel.tsv"
FIELDS = ["title", "status", "reason", "next", "time"]
STATUSES = ("alive", "killed", "dropped", "idea")


def load(path=FILE):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def save(rows, path=FILE):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def cmd_add(args):
    if args.status not in STATUSES:
        raise SystemExit(f"status 必须是 {STATUSES}")
    rows = load()
    rows.append({
        "title": args.title,
        "status": args.status,
        "reason": args.reason or "-",
        "next": args.next or "-",
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    save(rows)
    print(f"已记录: [{args.status}] {args.title}（累计 {len(rows)} 条）")


def cmd_list(args):
    rows = load()
    if args.status:
        rows = [r for r in rows if r["status"] == args.status]
    if not rows:
        print("暂无记录")
        return
    n_killed = sum(1 for r in load() if r["status"] == "killed")
    print(f"{'status':<9}{'title':<36}{'reason':<28}{'time'}")
    for r in rows:
        print(f"{r['status']:<9}{r['title'][:34]:<36}{r['reason'][:26]:<28}{r['time']}")
    print(f"\nkilled 累计 {n_killed} 条" + (" · 用 narrow-watch 查防窄化" if n_killed >= 3 else ""))


def cmd_narrow_watch(args):
    """同一 4 字片段出现在 ≥3 个 killed 题目 → 疑似原地窄化，提醒换方向。"""
    killed = [r["title"] for r in load() if r["status"] == "killed"]
    if len(killed) < 3:
        print(f"killed 仅 {len(killed)} 条，暂无窄化风险")
        return
    grams, prefixes = Counter(), Counter()
    for t in killed:
        chars = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", t)
        for i in range(len(chars) - 3):
            grams[chars[i:i + 4]] += 1
        for plen in (2, 3):
            if len(chars) >= plen:
                prefixes[chars[:plen]] += 1
    hits = [(g, c) for g, c in grams.most_common(5) if c >= 3]
    phits = [(p, c) for p, c in prefixes.most_common(5) if c >= 3]
    if hits or phits:
        print("⚠️ 防窄化预警（§1.2）——")
        for p, c in phits:
            print(f"  同一方向前缀「{p}」× {c} 条 killed：疑似原地窄化，换方向 > 钻窄缝")
        for g, c in hits:
            print(f"  片段「{g}」× {c}：深挖请挖新维度，不是收窄题目")
    else:
        print("未发现窄化模式 ✓")


def main():
    ap = argparse.ArgumentParser(description="选题漏斗 + 防窄化")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="记录一条")
    a.add_argument("--title", required=True)
    a.add_argument("--status", required=True, choices=STATUSES)
    a.add_argument("--reason", default="")
    a.add_argument("--next", default="")
    a.set_defaults(func=cmd_add)

    l = sub.add_parser("list", help="列出")
    l.add_argument("--status", choices=STATUSES)
    l.set_defaults(func=cmd_list)

    n = sub.add_parser("narrow-watch", help="防窄化预警")
    n.set_defaults(func=cmd_narrow_watch)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
