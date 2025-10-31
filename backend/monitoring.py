from prometheus_client import Counter


# Total recommendations served (any request)
RECOMMENDATIONS_TOTAL = Counter(
    "recommendations_total",
    "Total number of recommendation requests served",
)


# Top-algorithm selections labeled by algorithm
ALGORITHM_TOP_SELECTIONS = Counter(
    "algorithm_top_selections_total",
    "Number of times an algorithm was the top recommendation",
    ["algorithm"],
)


