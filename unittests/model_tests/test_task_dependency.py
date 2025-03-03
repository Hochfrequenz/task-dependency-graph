import uuid

from taskdependencygraph.models.ids import TaskDependencyId, TaskId
from taskdependencygraph.models.task_dependency_edge import TaskDependencyEdge


def test_task_dependency_can_be_instantiated() -> None:
    task_dependency = TaskDependencyEdge(
        id=TaskDependencyId(uuid.uuid4()),
        task_predecessor=TaskId(uuid.uuid4()),
        task_successor=TaskId(uuid.uuid4()),
    )
    assert isinstance(task_dependency, TaskDependencyEdge)
