"""
When using the Task Dependency Graph in an application, these models are helpful to give the user feedback on whether
the can or cannot add a task/node or dependency/edge to the graph.
"""

# pylint:disable=duplicate-code
# The __all__ list mirrors the one in models/__init__.py; that's intentional re-export, not a bug.

from typing import Self

from pydantic import BaseModel, model_validator


class AddNodeToGraphPreviewResponse(BaseModel):
    """
    Response to the frontends' request to potentially add a node to the TDG.
    It's named 'preview' because the node is not actually added to the TDG yet.
    """

    can_be_added: bool  # we can 'translate' this to an 🟢🔴 icon in the FE/jinja template
    """
    true iff the node can be added to the TDG
    """
    error_message: str | None = None
    """
    error message if the node cannot be added to the TDG
    """

    @model_validator(mode="after")
    def validate_there_is_an_error_message_if_necessary(self) -> Self:
        """
        Ensure that an error message is provided if the node cannot be added
        """
        if self.can_be_added is True or (self.can_be_added is False and self.error_message):
            return self
        raise ValueError("If the task can not be added, an error message must be provided")


class AddEdgeToGraphPreviewResponse(BaseModel):
    """
    response to the frontends' request to potentially add an edge to the TDG
    It's named 'preview' because the edge is not actually added to the TDG yet.
    """

    can_be_added: bool  # we can 'translate' this to an 🟢🔴 icon in the FE/jinja template
    """
    true iff the edge can be added to the TDG
    """
    error_message: str | None = None
    """
    error message if the edge cannot be added to the TDG
    """

    @model_validator(mode="after")
    def validate_there_is_an_error_message_if_necessary(self) -> "Self":
        """
        Ensure that an error message is provided if the node cannot be added
        """
        if self.can_be_added is True or (self.can_be_added is False and self.error_message):
            return self
        raise ValueError("If the task can not be added, an error message must be provided")


class RemoveNodeFromGraphPreviewResponse(BaseModel):
    """
    Response to the frontends' request to potentially remove a node from the TDG.
    It's named 'preview' because the node is not actually removed from the TDG yet.
    """

    can_be_removed: bool
    """
    true iff the node can be removed from the TDG
    """
    error_message: str | None = None
    """
    error message if the node cannot be removed from the TDG
    """

    @model_validator(mode="after")
    def validate_there_is_an_error_message_if_necessary(self) -> Self:
        """
        Ensure that an error message is provided if the node cannot be removed
        """
        if self.can_be_removed is True or (self.can_be_removed is False and self.error_message):
            return self
        raise ValueError("If the task can not be removed, an error message must be provided")


class RemoveEdgeFromGraphPreviewResponse(BaseModel):
    """
    Response to the frontends' request to potentially remove an edge from the TDG.
    It's named 'preview' because the edge is not actually removed from the TDG yet.
    """

    can_be_removed: bool
    """
    true iff the edge can be removed from the TDG
    """
    error_message: str | None = None
    """
    error message if the edge cannot be removed from the TDG
    """

    @model_validator(mode="after")
    def validate_there_is_an_error_message_if_necessary(self) -> Self:
        """
        Ensure that an error message is provided if the edge cannot be removed
        """
        if self.can_be_removed is True or (self.can_be_removed is False and self.error_message):
            return self
        raise ValueError("If the edge can not be removed, an error message must be provided")


__all__ = [
    "AddEdgeToGraphPreviewResponse",
    "AddNodeToGraphPreviewResponse",
    "RemoveEdgeFromGraphPreviewResponse",
    "RemoveNodeFromGraphPreviewResponse",
]
