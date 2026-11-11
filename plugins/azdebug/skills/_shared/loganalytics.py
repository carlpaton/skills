#!/usr/bin/env python3
"""Read-only Log Analytics helper. Only lists workspaces and runs KQL queries.

Run with -I:
  python3 -I loganalytics.py workspaces
  python3 -I loganalytics.py presets
  python3 -I loganalytics.py run   --workspace GUID --preset NAME [--window 7d]
  python3 -I loganalytics.py query --workspace GUID --kql "KQL" [--max-rows N] [--width N]

`--workspace` is the workspace customer id (GUID) from `workspaces`. Needs the Log Analytics Reader
role. The az `log-analytics` extension is required: az offers to install it on first use.

Safety: control commands (starting with `.`) are refused, output rows and cell width are capped,
and the presets never print raw log message bodies, only counts, timestamps and logger or
exception headers.
"""
import argparse
import json
import re
import subprocess
import sys

# Each preset is (description, read-only KQL, output column order). {window} is replaced with a
# validated look-back such as 7d. The column order matches the tables in report.md.tmpl.
PRESETS = {
    "tables": (
        "Which tables have data, with row counts and first/last time.",
        "union withsource=TableName_ * | where TimeGenerated > ago({window}) "
        "| summarize rows=count(), oldest=min(TimeGenerated), newest=max(TimeGenerated) "
        "by TableName_ | order by rows desc "
        "| project Table=TableName_, rows, oldest, newest",
        ["Table", "rows", "oldest", "newest"],
    ),
    "console-levels": (
        "Container App console lines by log level and logger (the header line only).",
        "ContainerAppConsoleLogs_CL | where TimeGenerated > ago({window}) "
        "| where Log_s matches regex @'^(info|warn|fail|crit|dbug|trce):' "
        "| extend level=extract(@'^(\\w+):', 1, Log_s), "
        "logger=extract(@'^\\w+: ([^\\[]+)', 1, Log_s) "
        "| summarize lines=count(), newest=max(TimeGenerated) by level, logger "
        "| order by lines desc | project level, logger, lines, newest",
        ["level", "logger", "lines", "newest"],
    ),
    "app-failures": (
        "Each `fail:` log line in time order, with its logger. No message bodies.",
        "ContainerAppConsoleLogs_CL | where TimeGenerated > ago({window}) "
        "| where Log_s startswith 'fail:' "
        "| project at=format_datetime(TimeGenerated, 'yyyy-MM-dd HH:mm:ss'), "
        "app=ContainerAppName_s, revision=RevisionName_s, "
        "logger=extract(@'^fail: ([^\\[]+)', 1, Log_s) "
        "| order by at asc",
        ["at", "app", "logger", "revision"],
    ),
    "exceptions": (
        "Exception type and message first line, counted. Shows why requests failed.",
        "ContainerAppConsoleLogs_CL | where TimeGenerated > ago({window}) "
        "| where Log_s matches regex @'^\\s*[A-Za-z.]+Exception: ' "
        "| extend exception=substring(trim(@'\\s+', Log_s), 0, 160) "
        "| summarize count=count(), oldest=min(TimeGenerated), newest=max(TimeGenerated) "
        "by exception | order by count desc | project exception, count, oldest, newest",
        ["exception", "count", "oldest", "newest"],
    ),
    "failures-by-hour": (
        "`fail:` lines per hour (UTC), to see when failures cluster.",
        "ContainerAppConsoleLogs_CL | where TimeGenerated > ago({window}) "
        "| where Log_s startswith 'fail:' "
        "| summarize failures=count() by hour=bin(TimeGenerated, 1h) | order by hour asc",
        ["hour", "failures"],
    ),
    "system-events": (
        "Container Apps platform events: scaling, revisions, restarts, warnings.",
        "ContainerAppSystemLogs_CL | where TimeGenerated > ago({window}) "
        "| summarize events=count(), newest=max(TimeGenerated) by Type_s, Reason_s "
        "| order by events desc | project Type=Type_s, Reason=Reason_s, events, newest",
        ["Type", "Reason", "events", "newest"],
    ),
    "restarts": (
        "Revision and replica lifecycle events in time order.",
        "ContainerAppSystemLogs_CL | where TimeGenerated > ago({window}) "
        "| where Reason_s in ('ContainerAppReady','RevisionUpdate','RevisionDeactivating',"
        "'ContainerAppUpdate','ContainerTerminated','ReplicaUnhealthy','ContainerBackOff') "
        "| project at=format_datetime(TimeGenerated, 'yyyy-MM-dd HH:mm:ss'), "
        "app=ContainerAppName_s, Reason_s, revision=RevisionName_s | order by at asc",
        ["at", "app", "Reason_s", "revision"],
    ),
}


def az(args):
    r = subprocess.run(["az", *args, "-o", "json"], capture_output=True, text=True)
    if r.returncode != 0:
        err = "\n".join(l for l in r.stderr.splitlines() if not l.startswith("WARNING")).strip()
        if "AuthorizationFailed" in err or "InsufficientAccess" in err or "403" in err:
            err = ("No access to this workspace. Ask the user to grant Log Analytics Reader on it.\n"
                   + err)
        sys.exit(err or "az failed")
    return json.loads(r.stdout or "[]")


def render(rows, max_rows, width, cols=None):
    # az adds TableName="PrimaryResult" to every row; drop it only when it is that artifact.
    if rows and all(r.get("TableName") == "PrimaryResult" for r in rows):
        rows = [{k: v for k, v in r.items() if k != "TableName"} for r in rows]
    if not rows:
        print("(no rows)")
        return
    cols = [c for c in (cols or []) if c in rows[0]] or sorted(rows[0].keys())
    shown = rows[:max_rows]

    def cell(v):
        s = "" if v is None else str(v).replace("\n", " ")
        return s if len(s) <= width else s[: width - 1] + "…"

    print("| " + " | ".join(cols) + " |")
    print("|" + "|".join("---" for _ in cols) + "|")
    for r in shown:
        print("| " + " | ".join(cell(r.get(c)) for c in cols) + " |")
    note = f"# {len(rows)} rows"
    if len(rows) > max_rows:
        note += f", showing the first {max_rows}"
    print(note)


def run_kql(workspace, kql, max_rows, width, cols=None):
    if kql.lstrip().startswith("."):
        sys.exit("Refused: control commands are not allowed, only read-only queries.")
    rows = az(["monitor", "log-analytics", "query", "-w", workspace, "--analytics-query", kql])
    render(rows, max_rows, width, cols)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["workspaces", "presets", "run", "query"])
    p.add_argument("--workspace")
    p.add_argument("--preset")
    p.add_argument("--kql")
    p.add_argument("--window", default="7d")
    p.add_argument("--max-rows", type=int, default=50)
    p.add_argument("--width", type=int, default=160)
    a = p.parse_args()

    if a.cmd == "workspaces":
        rows = az(["monitor", "log-analytics", "workspace", "list", "--query",
                   "[].{name:name, resourceGroup:resourceGroup, location:location, "
                   "workspaceId:customerId, retentionDays:retentionInDays}"])
        render(rows, 200, 80)
        return
    if a.cmd == "presets":
        for name, (desc, _, _c) in PRESETS.items():
            print(f"{name}\t{desc}")
        return

    if not a.workspace:
        sys.exit("--workspace is required (the workspaceId GUID from `workspaces`)")
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", a.workspace):
        sys.exit("--workspace must be the workspace GUID, not its name")

    if a.cmd == "run":
        if a.preset not in PRESETS:
            sys.exit(f"Unknown preset. Choose one of: {', '.join(PRESETS)}")
        if not re.fullmatch(r"\d+[mhd]", a.window):
            sys.exit("--window must look like 30m, 24h or 7d")
        run_kql(a.workspace, PRESETS[a.preset][1].replace("{window}", a.window),
                a.max_rows, a.width, PRESETS[a.preset][2])
    else:
        if not a.kql:
            sys.exit("--kql is required")
        run_kql(a.workspace, a.kql, a.max_rows, a.width)


if __name__ == "__main__":
    main()
