from typing import Dict, List
from uuid import UUID


# ============================================================
# DOMAIN: Percentile normalization
# ============================================================

def percentile_rank(value: float, population: List[float]) -> int:
    """
    Calculate percentile rank of a value within a population.

    Percentile is defined as:
    percentage of population values less than or equal to the given value.
    """

    if not population:
        return 0

    sorted_population = sorted(population)
    count = sum(1 for x in sorted_population if x <= value)

    percentile = int((count / len(sorted_population)) * 100)

    # Safety clamp
    if percentile < 0:
        return 0
    if percentile > 100:
        return 100

    return percentile


def normalize_player_metrics(
    player_values: Dict[UUID, Dict[str, float]],
    position_map: Dict[UUID, str],
) -> Dict[UUID, Dict]:
    """
    Normalize player metrics by position using percentiles.

    player_values:
        {
            player_id: {
                metric_name: raw_value,
                ...
            }
        }

    position_map:
        {
            player_id: position_code
        }

    Output:
        {
            player_id: {
                "position": "MF",
                "metrics": {
                    "passes": {
                        "value": 42.3,
                        "percentile": 78
                    },
                    ...
                }
            }
        }
    """

    result: Dict[UUID, Dict] = {}

    # --------------------------------------------------------
    # Build population per position & metric
    # --------------------------------------------------------
    population: Dict[str, Dict[str, List[float]]] = {}

    for player_id, metrics in player_values.items():
        position = position_map.get(player_id)
        if not position:
            continue

        population.setdefault(position, {})

        for metric, value in metrics.items():
            if value is None:
                continue
            population[position].setdefault(metric, []).append(value)

    # --------------------------------------------------------
    # Normalize per player
    # --------------------------------------------------------
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
