from typing import Dict, List
from uuid import UUID

import numpy as np


def percentile_rank(value: float, population: List[float]) -> int:
    """
    Calculate percentile rank of a value within a population.
    """
    if not population:
        return 0

    count = sum(1 for x in population if x <= value)
    percentile = int((count / len(population)) * 100)

    return percentile


def normalize_player_metrics(
    player_values: Dict[UUID, Dict[str, float]],
    position_map: Dict[UUID, str],
) -> Dict[UUID, Dict]:
    """
    Normalize player metrics by position using percentiles.

    player_values:
        {player_id: {metric_name: value}}

    position_map:
        {player_id: position_code}
    """

    result: Dict[UUID, Dict] = {}

    # Collect population per position & metric
    population: Dict[str, Dict[str, List[float]]] = {}

    for player_id, metrics in player_values.items():
        position = position_map.get(player_id)
        if not position:
            continue

        population.setdefault(position, {})

        for metric, value in metrics.items():
            population[position].setdefault(metric, []).append(value)

    # Calculate percentiles
    for player_id, metrics in player_values.items():
        position = position_map.get(player_id)
        if not position or position not in population:
            continue

        result[player_id] = {
            "position": position,
            "metrics": {},
        }

        for metric, value in metrics.items():
            values = population[position].get(metric, [])
            percentile = percentile_rank(value, values)

            result[player_id]["metrics"][metric] = {
                "value": round(value, 2),
                "percentile": percentile,
            }

    return result
