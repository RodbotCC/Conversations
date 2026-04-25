"""
Operational Method: Scoring Engine
==================================
Implements the 8 base dimensions and 4 composite score formulas.

Composite formulas (from the specification):
- Priority: Total attention weight
- Decay Risk: Probability of deterioration if ignored
- Intervention Value: ROI of immediate engagement
- Automation Suitability: Safety/utility of automated execution
"""

from operational_method.models import SystemObject, BASE_DIMENSIONS


def validate_scores(scores: dict) -> dict:
    """Validate that all base scores are present and in [0, 100]."""
    validated = {}
    for dim in BASE_DIMENSIONS:
        val = scores.get(dim)
        if val is None:
            raise ValueError(f"Missing base score: {dim}")
        if not (0 <= val <= 100):
            raise ValueError(f"Score \'{dim}\' = {val} is out of range [0, 100]")
        validated[dim] = float(val)
    return validated


def compute_priority(s: dict) -> float:
    """
    Priority = 0.22*urgency + 0.20*value + 0.14*actionability + 0.12*clarity
             + 0.10*confidence + 0.08*momentum - 0.08*friction - 0.06*effort_cost
    """
    return (0.22 * s["urgency"] + 0.20 * s["value"] + 0.14 * s["actionability"] +
            0.12 * s["clarity"] + 0.10 * s["confidence"] + 0.08 * s["momentum"] -
            0.08 * s["friction"] - 0.06 * s["effort_cost"])


def compute_decay_risk(s: dict) -> float:
    """
    Decay Risk = 0.35*urgency + 0.20*friction + 0.20*(100-momentum)
               + 0.15*(100-clarity) + 0.10*(100-confidence)
    """
    return (0.35 * s["urgency"] + 0.20 * s["friction"] + 0.20 * (100 - s["momentum"]) +
            0.15 * (100 - s["clarity"]) + 0.10 * (100 - s["confidence"]))


def compute_intervention_value(s: dict) -> float:
    """
    Intervention Value = 0.26*value + 0.20*urgency + 0.18*actionability
                       + 0.14*clarity + 0.12*momentum - 0.10*effort_cost
    """
    return (0.26 * s["value"] + 0.20 * s["urgency"] + 0.18 * s["actionability"] +
            0.14 * s["clarity"] + 0.12 * s["momentum"] - 0.10 * s["effort_cost"])


def compute_automation_suitability(s: dict) -> float:
    """
    Automation Suitability = 0.28*clarity + 0.24*actionability
                           + 0.18*confidence + 0.14*momentum - 0.16*friction
    """
    return (0.28 * s["clarity"] + 0.24 * s["actionability"] +
            0.18 * s["confidence"] + 0.14 * s["momentum"] - 0.16 * s["friction"])


COMPOSITE_FUNCTIONS = {
    "priority": compute_priority,
    "decay_risk": compute_decay_risk,
    "intervention_value": compute_intervention_value,
    "automation_suitability": compute_automation_suitability,
}


def score_object(obj: SystemObject, raw_scores: dict) -> SystemObject:
    """Score an object: validate base scores and compute all composites."""
    obj.base_scores = validate_scores(raw_scores)
    obj.composite_scores = {
        name: round(func(obj.base_scores), 2)
        for name, func in COMPOSITE_FUNCTIONS.items()
    }
    return obj
