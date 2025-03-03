"""
The task_node_as_artificial_startnode is a task node with a duration of 0 minutes, which is added to the
task dependency graph in order to have one single starting point - rather than one or more.
This single startnode makes calculations with Networkx easier, i.e. the calculation of the duration of predecessor
tasks on the critical path --> see app/core/task_dependency_graph/task_dependency_graph.py ->
calculate_planned_duration_of_predecessor_tasks_on_critical_path
"""

from datetime import timedelta
from uuid import UUID

from taskdependencygraph.models.ids import TaskId
from taskdependencygraph.models.task_node import TaskNode

ID_OF_ARTIFICIAL_STARTNODE: TaskId = TaskId(UUID("11111111-1111-1111-1111-111111111111"))
task_node_as_artificial_startnode = TaskNode(
    id=ID_OF_ARTIFICIAL_STARTNODE,
    external_id="__START__",
    name="START",
    planned_duration=timedelta(minutes=0),
)
__all__ = ["ID_OF_ARTIFICIAL_STARTNODE", "task_node_as_artificial_startnode"]
