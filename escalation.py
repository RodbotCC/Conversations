"""
Operational Method: Escalation Ladder of Inference
===================================================
Implements geometric search and problem decomposition.
Chains A/B placements to progressively narrow complex decisions
into sequences of atomic, answerable claims.
"""

from operational_method.engine import OperationalEngine
from operational_method.models import SystemObject


class EscalationLadder:
    """
    The Escalation Ladder of Inference:
    1. Identify the active comparator (lens)
    2. Place the object within the A/B geometry
    3. Infer consequences (what must also be true)
    4. Refine: ask the next discriminating question
    5. Resolve: reach an actionable conclusion
    """

    def __init__(self, engine: OperationalEngine):
        self.engine = engine
        self.inference_rules = {
            "urgent_vs_nonurgent": {
                "A": ["Requires same-day attention",
                      "Escalate if not addressed in 4 hours",
                      "Check: is the handler currently available?"],
                "B": ["Can be scheduled for next sprint",
                      "No escalation needed",
                      "Safe to batch with similar items"],
                "Middle": ["Review within 24 hours",
                          "Check if conditions are deteriorating",
                          "May need reclassification tomorrow"],
                "Neither": ["Urgency frame may be wrong lens",
                           "Consider: is this recurring vs one-time?"],
            },
            "manual_vs_automatable": {
                "A": ["Route to human specialist",
                      "Estimate effort hours",
                      "Check: does handler have domain expertise?"],
                "B": ["Route to automation pipeline",
                      "Verify automation rules exist",
                      "Set monitoring alerts for automated execution"],
                "Middle": ["Human-in-the-loop automation",
                          "Create runbook for partial automation",
                          "Track which steps are manual vs automated"],
                "Neither": ["May require novel approach",
                           "Consult with process architect"],
            },
            "clear_vs_ambiguous": {
                "A": ["Execute immediately",
                      "Minimal discovery needed",
                      "Document decision for audit trail"],
                "B": ["Initiate discovery phase",
                      "Assign research time before committing",
                      "Schedule stakeholder alignment meeting"],
                "Middle": ["Prototype before full commitment",
                          "Time-box discovery to 2 days",
                          "Identify the specific unknowns"],
                "Neither": ["Object may be poorly defined",
                           "Needs decomposition into sub-objects"],
            },
            "strategic_vs_tactical": {
                "A": ["Connect to long-term roadmap",
                      "Review with leadership",
                      "Measure impact in quarterly terms"],
                "B": ["Execute within current sprint",
                      "Focus on completion speed",
                      "Measure impact in daily/weekly terms"],
                "Middle": ["Dual-track: tactical execution with strategic alignment",
                          "Review both short-term and long-term implications"],
                "Neither": ["May be operational/maintenance",
                           "Categorize differently"],
            },
        }

    def escalate(self, obj_id: str, frame_sequence: list = None) -> dict:
        """Run the escalation ladder through a sequence of frames."""
        obj = self.engine.objects[obj_id]
        if frame_sequence is None:
            frame_sequence = ["urgent_vs_nonurgent", "clear_vs_ambiguous",
                            "manual_vs_automatable", "strategic_vs_tactical"]

        ladder = {"obj_id": obj_id, "name": obj.name,
                  "steps": [], "accumulated_constraints": [],
                  "final_action": None}

        for step_num, frame_name in enumerate(frame_sequence, 1):
            comp = next((c for c in obj.comparator_placements
                        if c["frame"] == frame_name), None)
            if not comp:
                continue

            p = comp["placement"]
            pole = ("A" if p in [1, 2] else "B" if p in [3, 4]
                    else "Middle" if p in [5, 6] else "Neither")
            precision = "exact" if p in [2, 4, 6, 8] else "approximate"
            implications = self.inference_rules.get(frame_name, {}).get(pole, [])

            step = {"step": step_num, "frame": frame_name,
                    "placement": comp["placement_label"],
                    "axis_position": comp["axis_position"],
                    "pole": pole, "precision": precision,
                    "implications": implications}

            ladder["steps"].append(step)
            ladder["accumulated_constraints"].extend(implications)

        ladder["final_action"] = self._synthesize(obj, ladder["accumulated_constraints"])
        return ladder

    def _synthesize(self, obj: SystemObject, constraints: list) -> str:
        cs = obj.composite_scores
        if cs.get("priority", 0) > 65 and cs.get("intervention_value", 0) > 65:
            urgency = "IMMEDIATE"
        elif cs.get("priority", 0) > 50:
            urgency = "SOON"
        else:
            urgency = "SCHEDULED"

        auto = cs.get("automation_suitability", 0) > 60
        decay = cs.get("decay_risk", 0) > 55

        parts = [f"[{urgency}]"]
        parts.append("Route to automation." if auto else "Assign to human specialist.")
        if decay:
            parts.append("Set decay monitoring alert.")
        if constraints:
            parts.append(f"Key: {constraints[0]}")
        return " ".join(parts)
