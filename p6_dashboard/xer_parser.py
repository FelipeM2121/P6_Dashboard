"""Parse Primavera P6 XER files into structured data."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


def _parse_tables(content: str) -> dict[str, list[dict]]:
    tables: dict[str, list[dict]] = {}
    current: Optional[str] = None
    fields: list[str] = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("%T\t"):
            current = line.split("\t")[1]
            tables[current] = []
            fields = []
        elif line.startswith("%F\t") and current:
            fields = line.split("\t")[1:]
        elif line.startswith("%R\t") and current:
            vals = line.split("\t")[1:]
            row = dict(zip(fields, vals + [""] * (len(fields) - len(vals))))
            tables[current].append(row)
    return tables


def _dt(s: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except (ValueError, AttributeError):
            pass
    return None


def _float(s: str) -> float:
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


@dataclass
class WBSNode:
    wbs_id: str
    parent_id: str
    short_name: str
    name: str
    level: int = 0


@dataclass
class Task:
    task_id: str
    task_code: str
    name: str
    wbs_id: str
    status: str
    pct_complete: float
    early_start: Optional[datetime]
    early_finish: Optional[datetime]
    target_start: Optional[datetime]
    target_finish: Optional[datetime]
    duration_hrs: float
    total_float_hrs: float
    is_critical: bool = False


@dataclass
class Resource:
    rsrc_id: str
    name: str
    rsrc_type: str
    cost_per_qty: float


@dataclass
class TaskResource:
    task_id: str
    rsrc_id: str
    target_qty: float
    target_cost: float


@dataclass
class P6Project:
    proj_id: str
    short_name: str
    name: str
    plan_start: Optional[datetime]
    plan_end: Optional[datetime]
    wbs: dict[str, WBSNode] = field(default_factory=dict)
    tasks: list[Task] = field(default_factory=list)
    resources: dict[str, Resource] = field(default_factory=dict)
    task_resources: list[TaskResource] = field(default_factory=list)


def parse_xer(path: str) -> P6Project:
    with open(path, encoding="latin-1") as f:
        content = f.read()
    tables = _parse_tables(content)

    proj_row = tables["PROJECT"][0]
    project = P6Project(
        proj_id=proj_row["proj_id"],
        short_name=proj_row["proj_short_name"],
        name=tables["PROJWBS"][0]["wbs_name"] if tables.get("PROJWBS") else proj_row["proj_short_name"],
        plan_start=_dt(proj_row.get("plan_start_date", "")),
        plan_end=_dt(proj_row.get("plan_end_date", "")),
    )

    # WBS
    raw_wbs = {w["wbs_id"]: w for w in tables.get("PROJWBS", [])}
    for wid, w in raw_wbs.items():
        level = 0
        pid = w.get("parent_wbs_id", "")
        cur = pid
        while cur and cur in raw_wbs:
            level += 1
            cur = raw_wbs[cur].get("parent_wbs_id", "")
        project.wbs[wid] = WBSNode(
            wbs_id=wid,
            parent_id=pid,
            short_name=w.get("wbs_short_name", ""),
            name=w.get("wbs_name", ""),
            level=level,
        )

    # Resources
    for r in tables.get("RSRC", []):
        project.resources[r["rsrc_id"]] = Resource(
            rsrc_id=r["rsrc_id"],
            name=r.get("rsrc_name", ""),
            rsrc_type=r.get("rsrc_type", ""),
            cost_per_qty=_float(r.get("cost_per_qty", "0")),
        )

    # Tasks
    for t in tables.get("TASK", []):
        dur = _float(t.get("target_drtn_hr_cnt", "0"))
        tf = _float(t.get("total_float_hr_cnt", "0"))
        project.tasks.append(Task(
            task_id=t["task_id"],
            task_code=t.get("task_code", ""),
            name=t.get("task_name", ""),
            wbs_id=t.get("wbs_id", ""),
            status=t.get("status_code", ""),
            pct_complete=_float(t.get("phys_complete_pct", "0")),
            early_start=_dt(t.get("early_start_date", "")),
            early_finish=_dt(t.get("early_end_date", "")),
            target_start=_dt(t.get("target_start_date", "")),
            target_finish=_dt(t.get("target_end_date", "")),
            duration_hrs=dur,
            total_float_hrs=tf,
            is_critical=(tf == 0),
        ))

    # Task resources
    for tr in tables.get("TASKRSRC", []):
        project.task_resources.append(TaskResource(
            task_id=tr.get("task_id", ""),
            rsrc_id=tr.get("rsrc_id", ""),
            target_qty=_float(tr.get("target_qty", "0")),
            target_cost=_float(tr.get("target_cost", "0")),
        ))

    return project
