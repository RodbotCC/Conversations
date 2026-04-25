"""
Operational Method: A/B Comparator System
==========================================
Layer 3 of the framework. Implements the geometric search mechanism
through comparative classification with 8-outcome placement.

The comparator creates a constrained search space that enables:
- Direction (which pole the object leans toward)
- Precision (exact vs approximate match)
- Mixed-state handling (genuine Middle placements)
- Out-of-frame detection (Neither placements)
"""

from dataclasses import dataclass, field
from operational_method.models import SystemObject, Placement


@dataclass
class ComparatorFrame:
    """
    A named evaluative axis defined by two poles.
    Creates the frame that gives A and B scale, direction,
    and inferential consequences.
    """
    name: str
    pole_a: str
    pole_b: str
    description: str = ""
    dimension_weights: dict = field(default_factory=dict)
    a_strong_threshold: float = 80.0
    a_lean_threshold: float = 60.0
    b_strong_threshold: float = 20.0
    b_lean_threshold: float = 40.0
    middle_tight: float = 5.0
    middle_wide: float = 10.0
    neither_threshold: float = 0.3

    def __repr__(self):
        return f"ComparatorFrame(\'{self.name}\': {self.pole_a} vs {self.pole_b})"


def compute_axis_score(obj: SystemObject, frame: ComparatorFrame) -> tuple:
    """
    Compute where an object sits on the A-B axis (0-100).

    Uses deviation-from-midpoint scoring: each dimension contributes
    weight * (score - 50), normalized to [0, 100].

    Returns: (axis_position, relevance)
    """
    if not obj.base_scores:
        raise ValueError(f"Object {obj.obj_id} has no base scores")
    if not frame.dimension_weights:
        raise ValueError(f"Frame \'{frame.name}\' has no dimension weights")

    deviation_sum = 0.0
    total_abs_weight = 0.0

    for dim, weight in frame.dimension_weights.items():
        if dim in obj.base_scores:
            score = obj.base_scores[dim]
            deviation_sum += weight * (score - 50)
            total_abs_weight += abs(weight)

    if total_abs_weight == 0:
        return 50.0, 0.0

    max_deviation = 50 * total_abs_weight
    normalized = (deviation_sum / max_deviation) * 50
    axis_position = max(0, min(100, 50 + normalized))

    # Relevance: how spread out are the relevant dimensions?
    relevant_scores = [obj.base_scores[d] for d in frame.dimension_weights if d in obj.base_scores]
    if len(relevant_scores) > 1:
        mean_s = sum(relevant_scores) / len(relevant_scores)
        variance = sum((s - mean_s)**2 for s in relevant_scores) / len(relevant_scores)
        spread = (variance / 2500) ** 0.5
        relevance = min(1.0, 0.4 + 0.6 * spread)
    else:
        relevance = 0.6

    return axis_position, relevance


def classify_placement(axis_position: float, relevance: float,
                        frame: ComparatorFrame) -> Placement:
    """Classify into one of 8 placements based on axis position and relevance."""
    if relevance < frame.neither_threshold:
        if relevance < frame.neither_threshold * 0.5:
            return Placement.EXACTLY_LIKE_NEITHER
        return Placement.MORE_LIKE_NEITHER

    dist_from_mid = abs(axis_position - 50)

    if dist_from_mid <= frame.middle_tight:
        return Placement.EXACTLY_LIKE_MIDDLE
    if dist_from_mid <= frame.middle_wide:
        return Placement.MORE_LIKE_MIDDLE

    if axis_position >= frame.a_strong_threshold:
        return Placement.EXACTLY_LIKE_A
    if axis_position >= frame.a_lean_threshold:
        return Placement.MORE_LIKE_A
    if axis_position <= frame.b_strong_threshold:
        return Placement.EXACTLY_LIKE_B
    if axis_position <= frame.b_lean_threshold:
        return Placement.MORE_LIKE_B

    return Placement.MORE_LIKE_MIDDLE


def apply_comparator(obj: SystemObject, frame: ComparatorFrame) -> dict:
    """Apply a single A/B comparator frame to an object."""
    axis_pos, relevance = compute_axis_score(obj, frame)
    placement = classify_placement(axis_pos, relevance, frame)

    result = {
        "frame": frame.name,
        "pole_a": frame.pole_a,
        "pole_b": frame.pole_b,
        "axis_position": round(axis_pos, 2),
        "relevance": round(relevance, 4),
        "placement": placement.value,
        "placement_label": placement.name,
    }

    obj.comparator_placements.append(result)
    return result


# ---- Standard Frame Library ----
STANDARD_FRAMES = {
    "urgent_vs_nonurgent": ComparatorFrame(
        name="urgent_vs_nonurgent",
        pole_a="urgent", pole_b="nonurgent",
        description="Is immediate action required or can this wait?",
        dimension_weights={"urgency": 1.0, "momentum": 0.3, "friction": -0.2},
    ),
    "strategic_vs_tactical": ComparatorFrame(
        name="strategic_vs_tactical",
        pole_a="strategic", pole_b="tactical",
        description="Long-term positioning vs immediate execution",
        dimension_weights={"value": 0.4, "effort_cost": 0.2, "clarity": -0.3,
                          "actionability": -0.4, "urgency": -0.2},
    ),
    "clear_vs_ambiguous": ComparatorFrame(
        name="clear_vs_ambiguous",
        pole_a="clear", pole_b="ambiguous",
        description="Is the path forward obvious or needs discovery?",
        dimension_weights={"clarity": 1.0, "confidence": 0.6, "actionability": 0.4},
    ),
    "manual_vs_automatable": ComparatorFrame(
        name="manual_vs_automatable",
        pole_a="manual", pole_b="automatable",
        description="Requires human judgment vs machine-executable",
        dimension_weights={"friction": 0.3, "effort_cost": 0.2, "clarity": -0.3,
                          "confidence": -0.2, "actionability": -0.2},
    ),
    "stable_vs_unstable": ComparatorFrame(
        name="stable_vs_unstable",
        pole_a="stable", pole_b="unstable",
        description="Is the state reliable or likely to change?",
        dimension_weights={"confidence": 0.4, "clarity": 0.3, "friction": -0.2,
                          "urgency": -0.3, "momentum": -0.1},
    ),
    "active_vs_dormant": ComparatorFrame(
        name="active_vs_dormant",
        pole_a="active", pole_b="dormant",
        description="Is this currently in motion or stalled?",
        dimension_weights={"momentum": 1.0, "actionability": 0.5, "urgency": 0.3},
    ),
    "high_value_vs_low_value": ComparatorFrame(
        name="high_value_vs_low_value",
        pole_a="high-value", pole_b="low-value",
        description="Potential impact assessment",
        dimension_weights={"value": 1.0, "confidence": 0.3},
    ),
    "trustworthy_vs_uncertain": ComparatorFrame(
        name="trustworthy_vs_uncertain",
        pole_a="trustworthy", pole_b="uncertain",
        description="Quality of the current data read",
        dimension_weights={"confidence": 1.0, "clarity": 0.5, "friction": -0.3},
    ),
}
