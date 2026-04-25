"""
Operational Method: Core Object Model
=====================================
Layer 1 (Object Layer) and Layer 2 (Score Layer) of the framework.

Every meaningful entity is represented as a typed SystemObject, scored along
8 shared base dimensions, with 4 derived composite outputs.
"""

import uuid
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ObjectType(Enum):
    """All recognized entity types in the system."""
    PERSON = "person"
    TASK = "task"
    MESSAGE = "message"
    DOCUMENT = "document"
    EVENT = "event"
    ISSUE = "issue"
    WORKFLOW = "workflow"
    OPPORTUNITY = "opportunity"
    POLICY = "policy"
    AUTOMATION = "automation"
    RELATIONSHIP = "relationship"


class Placement(Enum):
    """The 8-outcome A/B comparator placement."""
    MORE_LIKE_A = 1
    EXACTLY_LIKE_A = 2
    MORE_LIKE_B = 3
    EXACTLY_LIKE_B = 4
    MORE_LIKE_MIDDLE = 5
    EXACTLY_LIKE_MIDDLE = 6
    MORE_LIKE_NEITHER = 7
    EXACTLY_LIKE_NEITHER = 8


# ---- Base Score Dimensions ----
BASE_DIMENSIONS = [
    "urgency",        # Cost of delay
    "momentum",       # Whether the thing is moving/alive
    "friction",       # Resistance impeding progress
    "value",          # Potential impact if successful
    "confidence",     # Trustworthiness of current data
    "effort_cost",    # Resource expenditure required
    "actionability",  # How executable the next move is
    "clarity",        # How obvious the best path is
]


@dataclass
class SystemObject:
    """
    The fundamental unit of the Operational Method.
    Every meaningful entity is a typed object with scores and placements.
    """
    obj_id: str
    obj_type: ObjectType
    name: str
    fields: dict = field(default_factory=dict)
    relationships: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    base_scores: dict = field(default_factory=dict)
    composite_scores: dict = field(default_factory=dict)
    comparator_placements: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    history: list = field(default_factory=list)

    def add_relationship(self, rel_type: str, target_id: str):
        self.relationships.append({"type": rel_type, "target": target_id})

    def summary(self) -> dict:
        return {
            "id": self.obj_id,
            "type": self.obj_type.value,
            "name": self.name,
            "base_scores": self.base_scores,
            "composite_scores": self.composite_scores,
            "comparators": self.comparator_placements,
            "relationships": self.relationships,
        }

    def __repr__(self):
        return f"SystemObject({self.obj_type.value}: \'{self.name}\' [{self.obj_id[:8]}...])"


def create_object(obj_type: ObjectType, name: str, fields: dict = None,
                   tags: list = None) -> SystemObject:
    """Factory function to create a new SystemObject."""
    return SystemObject(
        obj_id=str(uuid.uuid4()),
        obj_type=obj_type,
        name=name,
        fields=fields or {},
        tags=tags or [],
    )
