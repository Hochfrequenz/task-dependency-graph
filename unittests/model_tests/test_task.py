import uuid
from datetime import timedelta

from taskdependencygraph.models.ids import TaskId
from taskdependencygraph.models.task_node import TaskNode


def test_task_is_hashable() -> None:
    """
    Test if a task instance is hashable (required for use as networkx node)
    """
    task = TaskNode(
        id=TaskId(uuid.uuid4()),
        external_id="123",
        name="the task's name",
        phase="100",
        planned_duration=timedelta(minutes=1),
    )
    _ = hash(task), "must not raise a TypeError"
