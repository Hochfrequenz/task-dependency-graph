"""
task_dependency domain model object
"""

from pydantic import BaseModel, ConfigDict

from taskdependencygraph.models.ids import TaskDependencyId, TaskId


class TaskDependencyEdge(BaseModel):
    """
    Task dependencies form the edges - i.e. interconnect task nodes - of the task dependency graph
    """

    model_config = ConfigDict(frozen=True)
    # the Task has to be frozen/hashable to be used as a node in a networkx graph
    # How to use model_config: https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.frozen
    # NetworkX restrictions regarding "nodes have to be hashable":
    # https://networkx.org/documentation/stable/reference/classes/generated/networkx.DiGraph.add_node.html

    id: TaskDependencyId
    """
    Unique ID of this TaskDependency
    """

    task_predecessor: TaskId

    """
    Refers to the preceding task by means of its uuid
    """

    task_successor: TaskId
    """
    Refers to the succeeding task by means of its uuid
    """

    def to_dot(self) -> str:
        """
        returns a dot representation of this edge;
        For details on the dot language see https://graphviz.org/doc/info/lang.html
        """
        return f'"{self.task_predecessor}" -> "{self.task_successor}"\n'


__all__ = ["TaskDependencyEdge"]
