"""
taskdependencygraph is a library to model tasks and dependencies between tasks in a networkx DiGraph
and give estimates when which task will be done
"""

from .task_dependency_graph import TaskDependencyGraph

__all__ = ["TaskDependencyGraph"]
