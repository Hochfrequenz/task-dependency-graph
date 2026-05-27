"""
DelayImpact: describes how much a task's planned finish exceeds its late finish
when an upstream task is delayed.
"""

from datetime import timedelta

from pydantic import BaseModel, ConfigDict

from taskdependencygraph.models.ids import TaskId


class DelayImpact(BaseModel):
    """Describes the knock-on effect of an upstream delay on a single downstream task."""

    model_config = ConfigDict(frozen=True)

    task_id: TaskId
    additional_delay: timedelta
    """
    How much this task's planned finish exceeds its original late finish as a result of the
    upstream delay. Equals max(0, propagated_delay - total_slack). Tasks for which total slack
    fully absorbs the propagated delay are omitted from the result list entirely.
    """


__all__ = ["DelayImpact"]
