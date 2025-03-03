"""
Person domain model
"""

from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field


# pylint: disable=too-few-public-methods
# pylint: disable=duplicate-code
class Person(BaseModel):
    """
    Entity 'person' includes anyone who uses the Cut Over Tool in whichever manner.
    Persons are always humans. A person can act in multiple roles
    (e.g. as assignee of one task and manager of another)
    """

    id: UUID = Field(default_factory=uuid4)
    name: str
    email: EmailStr
    phone_number: str | None = None
    slack_id: str | None = None
    is_active: bool = True


__all__ = ["Person"]
