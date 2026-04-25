"""
Operational Method: Temporal Analysis
=====================================
Implements Sediment Detection, Stability Index, and the foundations
for the Emergent Ratio Lattice.

Sediment = meaningful deviations from stable baselines.
Snapshots = captured system states at specific moments.
Lattice = emergent structure from accumulated stable observations.
"""

from collections import Counter, defaultdict
from operational_method.engine import OperationalEngine


class SedimentDetector:
    """
    Analyzes snapshot history to identify:
    - Stable patterns (baseline)
    - Sediment (meaningful deviations)
    - Emerging structural shifts
    """

    def __init__(self, engine: OperationalEngine):
        self.engine = engine

    def detect_sediment(self, snapshot_a_idx: int = -2,
                        snapshot_b_idx: int = -1,
                        score_threshold: float = 5.0) -> dict:
        """Compare two snapshots to find sediment."""
        if len(self.engine.snapshots) < 2:
            return {"error": "Need at least 2 snapshots"}

        snap_a = self.engine.snapshots[snapshot_a_idx]
        snap_b = self.engine.snapshots[snapshot_b_idx]
        ids_a = set(snap_a["states"].keys())
        ids_b = set(snap_b["states"].keys())

        sediment = {
            "comparison": f"{snap_a['label']} -> {snap_b['label']}",
            "score_shifts": [], "placement_shifts": [],
            "new_objects": [{"id": oid, "name": snap_b["states"][oid]["name"]}
                           for oid in (ids_b - ids_a)],
            "removed_objects": [{"id": oid, "name": snap_a["states"][oid]["name"]}
                               for oid in (ids_a - ids_b)],
        }

        for oid in ids_a & ids_b:
            sa, sb = snap_a["states"][oid], snap_b["states"][oid]

            for metric in ["priority", "decay_risk", "intervention_value",
                          "automation_suitability"]:
                va = sa["composite_scores"].get(metric, 0)
                vb = sb["composite_scores"].get(metric, 0)
                delta = vb - va
                if abs(delta) > score_threshold:
                    sediment["score_shifts"].append({
                        "obj_id": oid, "name": sa["name"], "metric": metric,
                        "old": round(va, 2), "new": round(vb, 2),
                        "delta": round(delta, 2),
                        "severity": "high" if abs(delta) > 15 else "moderate",
                    })

            pa = {p["frame"]: p for p in sa.get("placements", [])}
            pb = {p["frame"]: p for p in sb.get("placements", [])}
            for frame in set(pa.keys()) & set(pb.keys()):
                if pa[frame]["placement"] != pb[frame]["placement"]:
                    sediment["placement_shifts"].append({
                        "obj_id": oid, "name": sa["name"], "frame": frame,
                        "old_placement": pa[frame]["placement"],
                        "old_label": pa[frame]["placement_label"],
                        "new_placement": pb[frame]["placement"],
                        "new_label": pb[frame]["placement_label"],
                        "is_neither_shift": pb[frame]["placement"] in [7, 8],
                    })

        return sediment

    def compute_stability_index(self) -> dict:
        """Compute system-wide stability across all snapshots."""
        if len(self.engine.snapshots) < 2:
            return {"error": "Need at least 2 snapshots"}

        stability = {}
        all_ids = set()
        for snap in self.engine.snapshots:
            all_ids.update(snap["states"].keys())

        for oid in all_ids:
            priorities = []
            placements_by_frame = defaultdict(list)

            for snap in self.engine.snapshots:
                if oid in snap["states"]:
                    state = snap["states"][oid]
                    priorities.append(state["composite_scores"].get("priority", 0))
                    for p in state.get("placements", []):
                        placements_by_frame[p["frame"]].append(p["placement"])

            # Score stability
            if len(priorities) > 1:
                mean_p = sum(priorities) / len(priorities)
                cv = ((sum((p - mean_p)**2 for p in priorities) / len(priorities))**0.5
                      / mean_p if mean_p > 0 else 0)
                score_stab = max(0, 1 - cv)
            else:
                score_stab = 1.0

            # Placement stability
            frame_stabs = []
            for placements in placements_by_frame.values():
                if len(placements) > 1:
                    changes = sum(1 for i in range(1, len(placements))
                                 if placements[i] != placements[i-1])
                    frame_stabs.append(1 - changes / (len(placements) - 1))
                else:
                    frame_stabs.append(1.0)

            place_stab = sum(frame_stabs) / len(frame_stabs) if frame_stabs else 1.0

            name = None
            for snap in reversed(self.engine.snapshots):
                if oid in snap["states"]:
                    name = snap["states"][oid]["name"]
                    break

            stability[oid] = {
                "name": name,
                "score_stability": round(score_stab, 3),
                "placement_stability": round(place_stab, 3),
                "overall_stability": round(0.5 * score_stab + 0.5 * place_stab, 3),
            }

        overall = (sum(v["overall_stability"] for v in stability.values()) / len(stability)
                   if stability else 1.0)

        return {"system_stability": round(overall, 3), "object_stability": stability}
