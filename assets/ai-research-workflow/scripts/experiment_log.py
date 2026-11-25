#!/usr/bin/env python3
"""experiment_log — 小实验记录与汇总（对应 SKILL.md §4 实验纪律的 keep/discard 日志）。

用法:
    python3 experiment_log.py add --commit abc123 --metric val_bpb=0.99 --status keep --note "基线"
    python3 experiment_log.py add --commit def456 --status crash --note "改宽度 OOM"
    python3 experiment_log.py list
    python3 experiment_log.py list --status keep    # 只看保留的

记录存 results.tsv（tab 分隔），字段:
    commit  metric  status  note  time
只依赖 Python 标准库。
"""
import argparse
import csv
import datetime
import os

DEFAULT_FILE = "results.tsv"
FIELDS = ["commit", "metric", "status", "note", "time"]
VALID_STATUS = ("keep", "discard", "crash")


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def save(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def cmd_add(args):
    if args.status not in VALID_STATUS:
        raise SystemExit(f"status 必须是 {VALID_STATUS} 之一")
    row = {
        "commit": args.commit or "-",
        "metric": args.metric or "-",
        "status": args.status,
        "note": args.note or "-",
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    rows = load(DEFAULT_FILE)
    rows.append(row)
    save(DEFAULT_FILE, rows)
    print(f"已记录: commit={row['commit']} status={row['status']} metric={row['metric']}")
    print(f"累计 {len(rows)} 条 → {DEFAULT_FILE}")


def cmd_list(args):
    rows = load(DEFAULT_FILE)
    if args.status:
        rows = [r for r in rows if r.get("status") == args.status]
    if not rows:
        print("暂无记录。先用 add 记录一次实验。")
        return
    print(f"共 {len(rows)} 条" + (f"（status={args.status}）" if args.status else "") + ":")
    print(f"{'commit':<10}{'metric':<22}{'status':<8}{'note':<30}{'time'}")
    for r in rows:
        print(f"{r.get('commit','-'):<10}{r.get('metric','-'):<22}{r.get('status','-'):<8}{r.get('note','-'):<30}{r.get('time','')}")
    keeps = sum(1 for r in rows if r.get("status") == "keep")
    discards = sum(1 for r in rows if r.get("status") == "discard")
    crashes = sum(1 for r in rows if r.get("status") == "crash")
    print(f"\nkeep={keeps}  discard={discards}  crash={crashes}")


def main():
    ap = argparse.ArgumentParser(description="小实验记录与汇总")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="记录一次实验")
    a.add_argument("--commit", default="", help="git commit 短哈希")
    a.add_argument("--metric", default="", help="指标，如 val_bpb=0.99 或 acc=0.85")
    a.add_argument("--status", required=True, choices=VALID_STATUS, help="keep / discard / crash")
    a.add_argument("--note", default="", help="一句话：这次试了什么")
    a.set_defaults(func=cmd_add)

    l = sub.add_parser("list", help="列出实验记录")
    l.add_argument("--status", choices=VALID_STATUS, help="按状态过滤")
    l.set_defaults(func=cmd_list)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()