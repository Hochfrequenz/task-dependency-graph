# pylint:disable=anomalous-backslash-in-string
"""
The task_node_as_artificial_endnode is a task node, which is added to the task dependency graph due to
practical reasons: The artificial final task is needed in order to make the duration of the formerly last
node(s)/task(s) count, when identifying the critical path.

For more information: see app/core/task_dependency_graph/task_dependency_graph.py
--> add_artificial_nodes_and_edges
"""


from datetime import timedelta
from uuid import UUID

from taskdependencygraph.models.ids import TaskId
from taskdependencygraph.models.task_node import TaskNode

ID_OF_ARTIFICIAL_ENDNODE: TaskId = TaskId(UUID("99999999-9999-9999-9999-999999999999"))
task_node_as_artificial_endnode = TaskNode(
    id=ID_OF_ARTIFICIAL_ENDNODE,
    external_id="__END__",
    name="END",
    planned_duration=timedelta(minutes=0),
)
__all__ = ["ID_OF_ARTIFICIAL_ENDNODE", "task_node_as_artificial_endnode"]
