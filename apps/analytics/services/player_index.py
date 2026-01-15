from typing import Dict
from uuid import UUID
import statistics


def calculate_epi(
    normalized_metrics: Dict[UUID, Dict],
) -> Dict[UUID, Dict]:
    """
    Calculate Explainable Performance Index (EPI)
    based on median percentile of metrics.
    """

    result: Dict[UUID, Dict] = {}

    for player_id, data in normalized_metrics.items():
        percentiles = [
            metric_data["percentile"]
            for metric_data in data["metrics"].values()
        ]

        if not percentiles:
            continue

        epi = int(statistics.median(percentiles))

        result[player_id] = {
            "position": data["position"],
            "epi": epi,
            "metrics": data["metrics"],
        }

    return result
