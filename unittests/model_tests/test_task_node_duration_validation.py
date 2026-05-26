"""
Tests for TaskNode timedelta field validation — ensures constraints work correctly
and that no PydanticDeprecatedSince20 warnings are emitted.
"""

import uuid
import warnings
from datetime import timedelta
from typing import Any

import pytest
from pydantic import ValidationError

from taskdependencygraph.models.ids import TaskId
from taskdependencygraph.models.task_node import TaskNode


def _make_task(**kwargs: Any) -> TaskNode:
    defaults: dict[str, Any] = {
        "id": TaskId(uuid.uuid4()),
        "external_id": "T1",
        "name": "Task",
        "planned_duration": timedelta(minutes=5),
    }
    defaults.update(kwargs)
    return TaskNode(**defaults)


class TestPlannedDuration:
    def test_accepts_zero_duration(self) -> None:
        task = _make_task(planned_duration=timedelta(0))
        assert task.planned_duration == timedelta(0)

    def test_accepts_positive_duration(self) -> None:
        task = _make_task(planned_duration=timedelta(hours=2))
        assert task.planned_duration == timedelta(hours=2)

    def test_rejects_negative_duration(self) -> None:
        with pytest.raises(ValidationError):
            _make_task(planned_duration=timedelta(minutes=-1))


class TestPlannedDurationOfPredecessorTasks:
    def test_accepts_none(self) -> None:
        task = _make_task(planned_duration_of_predecessor_tasks=None)
        assert task.planned_duration_of_predecessor_tasks is None

    def test_accepts_zero(self) -> None:
        task = _make_task(planned_duration_of_predecessor_tasks=timedelta(0))
        assert task.planned_duration_of_predecessor_tasks == timedelta(0)

    def test_accepts_positive(self) -> None:
        task = _make_task(planned_duration_of_predecessor_tasks=timedelta(minutes=30))
        assert task.planned_duration_of_predecessor_tasks == timedelta(minutes=30)

    def test_rejects_negative(self) -> None:
        with pytest.raises(ValidationError):
            _make_task(planned_duration_of_predecessor_tasks=timedelta(seconds=-1))


class TestNoDeprecationWarnings:
    def test_constructing_task_node_emits_no_pydantic_deprecation_warnings(self) -> None:
        # Passes implicitly if no warning is raised; PydanticDeprecatedSince20 inherits
        # from DeprecationWarning, which simplefilter("error") converts to an exception.
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            _make_task(planned_duration=timedelta(minutes=5))
