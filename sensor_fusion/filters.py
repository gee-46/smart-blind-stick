"""
filters.py
----------
Task 3: Filter sensor noise.

Ultrasonic and IR sensors both produce occasional spurious readings
(spikes, dropouts, echo interference). Each physical sensor should get
its OWN filter instance that keeps a rolling history of its readings.
"""

from collections import deque
import statistics


class MovingAverageFilter:
    """Smooths out small jitter. Good for generally stable readings."""

    def __init__(self, window_size=5):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)

    def update(self, value):
        """Feed in a new raw reading (can be None), get back a filtered value."""
        if value is not None:
            self.history.append(value)
        if not self.history:
            return None
        return round(sum(self.history) / len(self.history), 1)


class MedianFilter:
    """
    More robust to sudden spikes/outliers than a moving average
    (e.g. one bad ultrasonic echo bouncing off an angled surface).
    Recommended as the default for obstacle-detection safety logic.
    """

    def __init__(self, window_size=5):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)

    def update(self, value):
        if value is not None:
            self.history.append(value)
        if not self.history:
            return None
        return round(statistics.median(self.history), 1)


class OutlierRejectingFilter:
    """
    Combines a median filter with outlier rejection: if a new reading
    deviates too much from the recent median, it's treated as noise
    and discarded rather than being allowed to skew the average.
    """

    def __init__(self, window_size=5, max_deviation_cm=60):
        self.window_size = window_size
        self.max_deviation_cm = max_deviation_cm
        self.history = deque(maxlen=window_size)

    def update(self, value):
        if value is not None:
            if self.history:
                current_median = statistics.median(self.history)
                if abs(value - current_median) > self.max_deviation_cm:
                    value = None  # reject as noise/outlier
            if value is not None:
                self.history.append(value)
        if not self.history:
            return None
        return round(statistics.median(self.history), 1)
