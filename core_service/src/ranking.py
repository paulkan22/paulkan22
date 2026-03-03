def rank_category(mutual_reference_count: int) -> str:
    if mutual_reference_count <= 0:
        return 'cold'
    if mutual_reference_count == 1:
        return 'warm'
    if 2 <= mutual_reference_count <= 3:
        return 'hot'
    return 'very_hot'


def reference_density(mutual_reference_count: int, total_reference_groups: int) -> float:
    if total_reference_groups <= 0:
        return 0.0
    return round(mutual_reference_count / total_reference_groups, 4)
