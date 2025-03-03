"""contains the taskexecutionstatus enum"""

from enum import StrEnum


class TaskExecutionStatus(StrEnum):
    """
    The task_execution_status specifies which status the execution of one task has.
    The TaskExecutionStatus class makes sure that there are only four possible values for the execution_status of
    tasks, which don't report an error.
    """

    NOT_YET_REQUESTED = "NOT_YET_REQUESTED"
    """
    The execution of the task has not yet been requested.
    """
    REQUESTED = "REQUESTED"
    """
    The execution of the task has been requested, but the assignee hasn't reported yet
    that s/he has started the task.
    """
    STARTED = "STARTED"
    """
    The execution of the task has been requested and the assignee has reported that s/he has started
    executing the task
    """
    COMPLETED = "COMPLETED"
    """
    The assignee has reported that the execution of the task has been completed.
    """
    OBSOLETE = "OBSOLETE"
    """
    The assignee has reported that the task is obsolete and does not need to be executed anymore.
    """


__all__ = ["TaskExecutionStatus"]
