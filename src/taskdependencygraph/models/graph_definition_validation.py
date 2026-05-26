"""
Graph definition validation models.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict

from taskdependencygraph.models.ids import TaskDependencyId, TaskId


class ValidationCode(str, Enum):
    """Stable codes identifying the kind of graph definition problem found."""

    DUPLICATE_TASK_ID = "DUPLICATE_TASK_ID"
    DUPLICATE_EXTERNAL_ID = "DUPLICATE_EXTERNAL_ID"
    MISSING_EDGE_ENDPOINT = "MISSING_EDGE_ENDPOINT"
    DUPLICATE_DEPENDENCY_ID = "DUPLICATE_DEPENDENCY_ID"
    DUPLICATE_EDGE_PAIR = "DUPLICATE_EDGE_PAIR"
    CYCLE = "CYCLE"
    INVALID_MILESTONE_DURATION = "INVALID_MILESTONE_DURATION"


class GraphDefinitionValidationFinding(BaseModel):
    """A single validation problem found in a graph definition."""

    model_config = ConfigDict(frozen=True)

    code: ValidationCode
    message: str
    task_id: TaskId | None = None
    dependency_id: TaskDependencyId | None = None


class GraphDefinitionValidationResult(BaseModel):
    """The aggregated result of validating a raw task/dependency list before graph construction."""

    model_config = ConfigDict(frozen=True)

    is_valid: bool
    findings: list[GraphDefinitionValidationFinding]


__all__ = [
    "GraphDefinitionValidationFinding",
    "GraphDefinitionValidationResult",
    "ValidationCode",
]
