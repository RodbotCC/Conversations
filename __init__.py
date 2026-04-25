"""
The Operational Method: A Framework for Transforming Data into Actionable Intelligence
======================================================================================

A complex system becomes manageable when every meaningful object is represented
as a typed object, scored along a small shared set of decision-relevant dimensions,
and then classified through explicit A/B comparison frames that describe its
position between important poles.

Architecture:
    Layer 1 (Object):     Typed entities with id, type, fields, relationships
    Layer 2 (Score):      8 base dimensions → 4 composite outputs
    Layer 3 (Comparator): A/B frames with 8-outcome placement

Modules:
    models      - Core data structures (SystemObject, ObjectType, Placement)
    scoring     - Base scores (0-100) and composite formulas
    comparators - A/B comparator frames and geometric classification
    engine      - The 10-step General Operating Loop
    temporal    - Sediment detection, stability index, lattice emergence
    escalation  - Escalation Ladder of Inference for problem decomposition

Usage:
    from operational_method.engine import OperationalEngine
    from operational_method.models import ObjectType

    engine = OperationalEngine()
    rec = engine.process(
        obj_type=ObjectType.TASK,
        name="Review Q3 Report",
        raw_scores={
            "urgency": 82, "momentum": 41, "friction": 57, "value": 91,
            "confidence": 76, "effort_cost": 33, "actionability": 88, "clarity": 80,
        }
    )
"""

__version__ = "1.0.0"

from operational_method.models import SystemObject, ObjectType, Placement, create_object
from operational_method.scoring import score_object, COMPOSITE_FUNCTIONS
from operational_method.comparators import (
    ComparatorFrame, apply_comparator, STANDARD_FRAMES
)
from operational_method.engine import OperationalEngine
from operational_method.temporal import SedimentDetector
from operational_method.escalation import EscalationLadder
