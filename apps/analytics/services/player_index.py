from typing import Dict, Any
from uuid import UUID
import statistics


# ============================================================
# DOMAIN: Explainable Performance Index (EPI)
# ============================================================

def calculate_epi(
    normalized_metrics: Dict[UUID, Dict[str, Any]],
) -> Dict[UUID, Dict[str, Any]]:
    """
    Calculate Explainable Performance Index (EPI).

    EPI is defined as the median percentile of all available
    normalized performance metrics for a player.

    Expected input structure per player:
    {
        "position": "MF",
        "metrics": {
            "passes": {
                "value": 42,
                "percentile": 78,
            },
            ...
        }
    }
    """

    result: Dict[UUID, Dict[str, Any]] = {}

    for player_id, data in normalized_metrics.items():
        metrics = data.get("metrics", {})

        percentiles = [
            metric_data["percentile"]
            for metric_data in metrics.values()
            if isinstance(metric_data, dict)
            and isinstance(metric_data.get("percentile"), (int, float))
        ]

        if not percentiles:
            continue

        epi_value = int(statistics.median(percentiles))

        result[player_id] = {
            "position": data.get("position"),
            "epi": epi_value,
            "metrics": metrics,
            "explanation": {
                "method": "median_percentile",
                "metric_count": len(percentiles),
            },
        }

    return result
