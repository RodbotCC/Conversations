"""
Operational Method: The Operational Engine
==========================================
Implements the 10-step General Operating Loop:
1. Ingest  2. Normalize  3. Resolve Relationships  4. Score
5. Compute Composites  6. Classify (A/B)  7. Rank & Route
8. Recommend  9. Log  10. Improve (via snapshots)
"""

import copy
from datetime import datetime
from collections import defaultdict

from operational_method.models import (
    SystemObject, ObjectType, Placement, create_object
)
from operational_method.scoring import score_object
from operational_method.comparators import (
    ComparatorFrame, apply_comparator, STANDARD_FRAMES
)


class OperationalEngine:
    """The core engine implementing the 10-step General Operating Loop."""

    def __init__(self, comparator_frames: dict = None):
        self.objects: dict[str, SystemObject] = {}
        self.frames = comparator_frames or STANDARD_FRAMES
        self.snapshots: list[dict] = []
        self.action_log: list[dict] = []
        self.routing_rules: dict = {}
        self.outcome_history: list[dict] = []

    # Step 1: Ingest
    def ingest(self, obj_type: ObjectType, name: str, fields: dict = None,
               tags: list = None) -> SystemObject:
        """Bring a meaningful object into the system."""
        obj = create_object(obj_type, name, fields, tags)
        self.objects[obj.obj_id] = obj
        self._log("ingest", obj.obj_id, {"type": obj_type.value, "name": name})
        return obj

    # Step 2: Normalize
    def normalize(self, obj_id: str) -> SystemObject:
        """Apply canonical schema rules."""
        obj = self.objects[obj_id]
        if "status" not in obj.fields:
            obj.fields["status"] = "active"
        if "created_at" not in obj.fields:
            obj.fields["created_at"] = obj.created_at.isoformat()
        self._log("normalize", obj_id, {"fields_set": list(obj.fields.keys())})
        return obj

    # Step 3: Resolve Relationships
    def resolve_relationships(self, obj_id: str, relationships: list = None):
        """Connect objects to each other."""
        obj = self.objects[obj_id]
        if relationships:
            for rel_type, target_id in relationships:
                if target_id in self.objects:
                    obj.add_relationship(rel_type, target_id)
                    reverse = {"owns": "owned_by", "blocks": "blocked_by",
                              "depends_on": "dependency_of", "impacts": "impacted_by",
                              "assigned_to": "assignee_of"}
                    rev_type = reverse.get(rel_type, "related_to")
                    self.objects[target_id].add_relationship(rev_type, obj_id)
        self._log("resolve_relationships", obj_id, {"count": len(obj.relationships)})

    # Steps 4 & 5: Score + Compute Composites
    def score(self, obj_id: str, raw_scores: dict) -> SystemObject:
        """Assign base scores and compute composite outputs."""
        obj = self.objects[obj_id]
        score_object(obj, raw_scores)
        self._log("score", obj_id, {"composite": obj.composite_scores})
        return obj

    # Step 6: A/B Comparator Classification
    def classify(self, obj_id: str, frame_names: list = None) -> list:
        """Run A/B comparator classification."""
        obj = self.objects[obj_id]
        obj.comparator_placements = []
        frames_to_run = frame_names or list(self.frames.keys())
        results = []
        for fname in frames_to_run:
            if fname in self.frames:
                result = apply_comparator(obj, self.frames[fname])
                results.append(result)
        self._log("classify", obj_id, {"frames": len(results)})
        return results

    # Step 7: Rank
    def rank(self, by: str = "priority", top_n: int = None) -> list:
        """Rank all scored objects by a composite score."""
        scored = [(obj, obj.composite_scores.get(by, 0))
                  for obj in self.objects.values() if obj.composite_scores]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n] if top_n else scored

    # Step 7: Route
    def route(self, obj_id: str) -> dict:
        """Route an object based on comparator placements."""
        obj = self.objects[obj_id]
        routing = {"obj_id": obj_id, "name": obj.name,
                   "primary_queue": None, "handler": None,
                   "urgency_class": None, "explanations": []}

        for comp in obj.comparator_placements:
            p, fname = comp["placement"], comp["frame"]
            label = comp["placement_label"]

            if fname == "urgent_vs_nonurgent":
                if p in [1, 2]:
                    routing["urgency_class"] = "immediate"
                    routing["explanations"].append(f"Urgent: {label}")
                elif p in [3, 4]:
                    routing["urgency_class"] = "scheduled"
                elif p in [5, 6]:
                    routing["urgency_class"] = "review"

            elif fname == "manual_vs_automatable":
                if p in [1, 2]:
                    routing["handler"] = "human"
                    routing["explanations"].append(f"Requires human: {label}")
                elif p in [3, 4]:
                    routing["handler"] = "automation"
                    routing["explanations"].append(f"Automatable: {label}")
                elif p in [5, 6]:
                    routing["handler"] = "human_assisted_automation"

            elif fname == "strategic_vs_tactical":
                if p in [1, 2]:
                    routing["primary_queue"] = "strategy_review"
                elif p in [3, 4]:
                    routing["primary_queue"] = "execution_queue"

        routing["primary_queue"] = routing["primary_queue"] or "general_triage"
        routing["handler"] = routing["handler"] or "human"
        routing["urgency_class"] = routing["urgency_class"] or "standard"
        return routing

    # Step 8: Recommend
    def recommend(self, obj_id: str) -> dict:
        """Generate next-best-action recommendations."""
        obj = self.objects[obj_id]
        routing = self.route(obj_id)
        cs = obj.composite_scores
        recommendations = {"obj_id": obj_id, "name": obj.name,
                          "routing": routing, "actions": [], "warnings": [],
                          "composite_summary": cs}

        if cs.get("decay_risk", 0) > 65:
            recommendations["warnings"].append(
                f"HIGH DECAY RISK ({cs['decay_risk']:.1f}): Will deteriorate if ignored.")
        if cs.get("intervention_value", 0) > 70:
            recommendations["actions"].append(
                f"HIGH INTERVENTION VALUE ({cs['intervention_value']:.1f}): Engage immediately.")
        if cs.get("automation_suitability", 0) > 70:
            recommendations["actions"].append(
                f"AUTOMATION CANDIDATE ({cs['automation_suitability']:.1f}): Route to automated workflow.")
        if cs.get("priority", 0) > 75:
            recommendations["actions"].append(
                f"HIGH PRIORITY ({cs['priority']:.1f}): Elevate in queue.")

        for comp in obj.comparator_placements:
            p, fname = comp["placement"], comp["frame"]
            if fname == "clear_vs_ambiguous" and p in [3, 4]:
                recommendations["actions"].append("AMBIGUOUS: Initiate discovery phase.")
            if fname == "stable_vs_unstable" and p in [3, 4]:
                recommendations["warnings"].append("UNSTABLE: Monitor closely.")
            if fname == "active_vs_dormant" and p in [3, 4]:
                recommendations["actions"].append("DORMANT: Consider reactivation or archive.")

        neither_frames = [c["frame"] for c in obj.comparator_placements if c["placement"] in [7, 8]]
        if neither_frames:
            recommendations["warnings"].append(
                f"FRAME MISMATCH: Doesn\'t fit: {', '.join(neither_frames)}")

        return recommendations

    # Step 9: Log
    def _log(self, action: str, obj_id: str, details: dict = None):
        self.action_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action, "obj_id": obj_id, "details": details or {}})

    # Step 10: Snapshot (for Improve cycle)
    def take_snapshot(self, label: str = "") -> dict:
        """Capture full system state for temporal analysis."""
        snapshot = {"label": label, "timestamp": datetime.now().isoformat(),
                    "object_count": len(self.objects), "states": {}}
        for obj_id, obj in self.objects.items():
            snapshot["states"][obj_id] = {
                "name": obj.name, "type": obj.obj_type.value,
                "composite_scores": copy.deepcopy(obj.composite_scores),
                "placements": copy.deepcopy(obj.comparator_placements),
            }
        self.snapshots.append(snapshot)
        return snapshot

    # Full Pipeline
    def process(self, obj_type: ObjectType, name: str, raw_scores: dict,
                fields: dict = None, tags: list = None,
                relationships: list = None, frame_names: list = None) -> dict:
        """Full pipeline: Ingest through Recommend."""
        obj = self.ingest(obj_type, name, fields, tags)
        self.normalize(obj.obj_id)
        if relationships:
            self.resolve_relationships(obj.obj_id, relationships)
        self.score(obj.obj_id, raw_scores)
        self.classify(obj.obj_id, frame_names)
        return self.recommend(obj.obj_id)
