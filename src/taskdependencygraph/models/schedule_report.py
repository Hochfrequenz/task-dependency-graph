"""
Schedule report models: ScheduleEntry and ScheduleReport.
"""

from datetime import timedelta
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from taskdependencygraph.models.ids import TaskId


class ScheduleEntry(BaseModel):
    """Planned scheduling data for a single task within a TaskDependencyGraph."""

    model_config = ConfigDict(frozen=True)

    task_id: TaskId
    external_id: str
    name: str
    phase: str | None
    tags: list[Annotated[str, Field(min_length=1)]] | None
    planned_start: AwareDatetime
    planned_finish: AwareDatetime
    planned_duration: timedelta
    is_milestone: bool
    is_on_critical_path: bool
    total_slack: timedelta
    """Maximum delay the task can absorb without pushing out the graph finish time."""
    predecessor_task_ids: list[TaskId]
    successor_task_ids: list[TaskId]


class ScheduleReport(BaseModel):
    """Summary of the planned schedule for an entire TaskDependencyGraph."""

    model_config = ConfigDict(frozen=True)

    graph_start: AwareDatetime
    graph_finish: AwareDatetime
    total_duration: timedelta
    critical_path_task_ids: list[TaskId]
    """Ordered list of task IDs on the critical path, from graph start to graph finish."""
    entries: list[ScheduleEntry]


__all__ = ["ScheduleEntry", "ScheduleReport"]
