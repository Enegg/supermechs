from supermechs.typeshed import twotuple


def mean_and_deviation(*numbers: float) -> twotuple[float]:
    """Returns the arithmetric mean and the standard deviation of a sequence of numbers."""
    import statistics

    mean = statistics.fmean(numbers)
    return mean, statistics.pstdev(numbers, mean)
