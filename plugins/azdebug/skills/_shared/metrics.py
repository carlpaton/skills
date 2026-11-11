#!/usr/bin/env python3
"""Read-only Azure Monitor metrics helper: prints non-empty time buckets as a table.

Usage (run with -I):
  python3 -I metrics.py --resource <resource-id> --metric AzureOpenAIRequests \
      --split ModelDeploymentName StatusCode --interval PT1H --offset 7d --exclude StatusCode=200

Only calls `az monitor metrics list`. Dimension values come back lower-cased by key.
"""
import argparse
import json
import subprocess
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--resource", required=True, help="full Azure resource id")
    p.add_argument("--metric", required=True, help="metric name, see `az monitor metrics list-definitions`")
    p.add_argument("--aggregation", nargs="+", default=["Total"], help="Total Average Maximum Minimum Count")
    p.add_argument("--interval", default="P1D", help="ISO 8601 grain, e.g. PT1H or P1D")
    p.add_argument("--offset", default="7d", help="look-back window, e.g. 24h or 7d")
    p.add_argument("--split", nargs="*", default=[], help="dimension names to split by, e.g. ModelDeploymentName")
    p.add_argument("--where", default="", help="extra raw filter, e.g. \"ModelDeploymentName eq 'gpt5'\"")
    p.add_argument("--exclude", nargs="*", default=[], help="drop rows where dimension=value, e.g. StatusCode=200")
    a = p.parse_args()

    filters = [f"{d} eq '*'" for d in a.split]
    if a.where:
        filters.insert(0, a.where)
    cmd = ["az", "monitor", "metrics", "list", "--resource", a.resource, "--metric", a.metric,
           "--aggregation", *a.aggregation, "--interval", a.interval, "--offset", a.offset, "-o", "json"]
    if filters:
        cmd += ["--filter", " and ".join(filters)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(r.stderr.strip() or "az failed")

    excl = {}
    for e in a.exclude:
        k, _, v = e.partition("=")
        excl[k.lower()] = v
    keys = [k.lower() for k in a.split]
    aggs = [x.lower() for x in a.aggregation]
    rows = []
    for ts in json.loads(r.stdout)["value"][0]["timeseries"]:
        dims = {m["name"]["value"].lower(): m["value"] for m in ts.get("metadatavalues", [])}
        if any(dims.get(k) == v for k, v in excl.items()):
            continue
        for pt in ts["data"]:
            vals = [pt.get(x) for x in aggs]
            if all(v in (None, 0) for v in vals):
                continue
            rows.append([pt["timeStamp"]] + [dims.get(k, "") for k in keys] + [round(v, 2) if v is not None else "" for v in vals])
    rows.sort()
    print("\t".join(["timeStamp(UTC)"] + keys + aggs))
    for row in rows:
        print("\t".join(str(c) for c in row))
    if not rows:
        print("(no data in window)")


if __name__ == "__main__":
    main()
