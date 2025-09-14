#!/usr/bin/env python3
import csv, json, argparse
from pathlib import Path

def load_json(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def check_row(row, glossary, length_limits):
    issues = []
    key, src, tgt, lang = row["key"], row["source"], row["target"], row["lang"]

    # glossary preferred / forbidden
    pref = glossary.get("preferred_terms", {})
    forb = glossary.get("forbidden", {}).get(lang, [])
    for term, trans in pref.items():
        if term in src:
            expected = trans.get(lang)
            if expected and expected not in tgt:
                issues.append(("glossary","warn", f"Preferred term for '{term}' should be '{expected}'"))
    for bad in forb:
        if bad and bad in tgt:
            issues.append(("glossary","blocker", f"Forbidden term '{bad}' found"))

    # placeholders (simple)
    for ph in ["{{", "}}", "%s"]:
        if ph in src and ph not in tgt:
            issues.append(("placeholder","blocker", f"Missing placeholder '{ph}'"))

    # length limits
    limit = length_limits.get(key)
    if limit and len(tgt) > int(limit):
        issues.append(("length","blocker", f"Over length limit {limit} (got {len(tgt)})"))

    # style (toy)
    if "!" in tgt:
        issues.append(("style","warn","Avoid exclamation marks"))
    return issues

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--glossary", required=True)
    ap.add_argument("--lengths", required=False, default="")
    ap.add_argument("--out", default="qa_agent_report.json")
    args = ap.parse_args()

    glossary = load_json(args.glossary)
    lengths = {}
    if args.lengths:
        meta = load_json(args.lengths)
        lengths = meta.get("length_limits", meta)

    checks, total = [], 0
    with open(args.csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            res = check_row(row, glossary, lengths)
            total += len(res)
            for kind, sev, msg in res:
                checks.append({"key": row["key"], "type": kind, "severity": sev, "message": msg})

    report = {"summary": {"pass": total==0, "issues": total}, "checks": checks}
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}. Pass={report['summary']['pass']} Issues={total}")

if __name__ == "__main__":
    main()
