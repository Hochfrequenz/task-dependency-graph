"""models are python objects which we use to model tasks, dependencies and the graph they form"""

from .delay_impact import DelayImpact
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
from .task_dependency_update import (
    AddEdgeToGraphPreviewResponse,
    AddNodeToGraphPreviewResponse,
    RemoveEdgeFromGraphPreviewResponse,
    RemoveNodeFromGraphPreviewResponse,
)
from .task_execution_status import TaskExecutionStatus
from .task_node import TaskNode
from .task_node_as_artificial_endnode import ID_OF_ARTIFICIAL_ENDNODE, task_node_as_artificial_endnode
from .task_node_as_artificial_startnode import ID_OF_ARTIFICIAL_STARTNODE, task_node_as_artificial_startnode

__all__ = [
    "ID_OF_ARTIFICIAL_ENDNODE",
    "ID_OF_ARTIFICIAL_STARTNODE",
    "AddEdgeToGraphPreviewResponse",
    "AddNodeToGraphPreviewResponse",
    "DelayImpact",
    "GraphDefinitionValidationFinding",
    "GraphDefinitionValidationResult",
    "MermaidGanttConfig",
    "Person",
    "PersonId",
    "RemoveEdgeFromGraphPreviewResponse",
    "RemoveNodeFromGraphPreviewResponse",
    "RunGroupId",
    "RunGroupPersonRelationId",
    "RunId",
    "ScheduleEntry",
    "ScheduleReport",
    "TaskDependencyEdge",
    "TaskDependencyId",
    "TaskExecutionStatus",
    "TaskId",
    "TaskNode",
    "ValidationCode",
    "task_node_as_artificial_endnode",
    "task_node_as_artificial_startnode",
]
