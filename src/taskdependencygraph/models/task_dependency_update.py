"""
DTOs related to updating a Task Dependency Graph (TDG).
These DTO may e.g. provide the frontend _instant_ feedback on whether a specific update would be successful or not.
"""

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
    def validate_there_is_an_error_message_if_necessary(cls, values):  # pylint:disable=no-self-argument
        """
        Ensure that an error message is provided if the node cannot be added
        """
        if values.can_be_added is True or (values.can_be_added is False and values.error_message):
            return values
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
    def validate_there_is_an_error_message_if_necessary(cls, values):  # pylint:disable=no-self-argument
        """
        Ensure that an error message is provided if the node cannot be added
        """
        if values.can_be_added is True or (values.can_be_added is False and values.error_message):
            return values
        raise ValueError("If the task can not be added, an error message must be provided")
