"""models are python objects which we use to model tasks, dependencies and the graph they form"""

from .graph_definition_validation import (
    GraphDefinitionValidationFinding,
    GraphDefinitionValidationResult,
    ValidationCode,
)
from .ids import PersonId, RunGroupId, RunGroupPersonRelationId, RunId, TaskDependencyId, TaskId
from .mermaid_gantt_config import MermaidGanttConfig
from .person import Person
from .schedule_report import ScheduleEntry, ScheduleReport
from .task_dependency_edge import TaskDependencyEdge
from .task_execution_status import TaskExecutionStatus
from .task_node import TaskNode
from .task_node_as_artificial_endnode import ID_OF_ARTIFICIAL_ENDNODE
from .task_node_as_artificial_startnode import ID_OF_ARTIFICIAL_STARTNODE

__all__ = [
    "MermaidGanttConfig",
    "GraphDefinitionValidationFinding",
    "GraphDefinitionValidationResult",
    "ValidationCode",
    "Person",
    "RunId",
    "RunGroupId",
    "RunGroupPersonRelationId",
    "TaskId",
    "TaskDependencyId",
    "PersonId",
    "ScheduleEntry",
    "ScheduleReport",
    "TaskNode",
    "TaskDependencyEdge",
    "TaskExecutionStatus",
    "ID_OF_ARTIFICIAL_ENDNODE",
    "ID_OF_ARTIFICIAL_STARTNODE",
]
