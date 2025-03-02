"""
contains ID types we use to differentiate between UUIDs
"""

import uuid
from typing import NewType

RunId = NewType("RunId", uuid.UUID)
"""
technically unique ID of a run
"""

RunGroupId = NewType("RunGroupId", uuid.UUID)
"""
technically unique ID of a run group
"""

RunGroupPersonRelationId = NewType("RunGroupPersonRelationId", uuid.UUID)
"""
technically unique ID the relation between a run group and a person
"""

TaskId = NewType("TaskId", uuid.UUID)
"""
technically unique ID of a task
"""

TaskDependencyId = NewType("TaskDependencyId", uuid.UUID)
"""
technically unique ID of a task dependency
"""

PersonId = NewType("PersonId", uuid.UUID)
"""
technically unique ID of a person
"""
# the __all__ fixes the mypy warning: Module "..." does not explicitly export attribute "TaskId"
__all__ = ["RunId", "RunGroupId", "RunGroupPersonRelationId", "TaskId", "TaskDependencyId", "PersonId"]
