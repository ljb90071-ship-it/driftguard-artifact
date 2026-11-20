"""Reference bin-state and CPU-accounting rules; no native sampling engine."""
from collections import deque
from statistics import median


class ResidenceCap:
    """Call once per contiguous closed bin using that bin's point counts."""
    def __init__(self, bin_s=.1, retention_s=64, history=8):
        self.bin_s, self.retention_s = bin_s, retention_s
        self.intervals = deque(maxlen=history)
        self.hot = False
        self.streak = 0
        self.start = None
        self.last_end = None

    def observe(self, end_s, range_count, total_count, ranges):
        if ranges <= 0 or not 0 <= range_count <= total_count:
            raise ValueError('invalid request counts')
        if self.last_end is not None and abs(end_s-self.last_end-self.bin_s)>1e-8:
            raise ValueError('bins must be contiguous and increasing')
        self.last_end = end_s
        hot = total_count > 0 and range_count*ranges >= 2*total_count
        self.streak = self.streak+1 if hot != self.hot else 0
        if self.streak == 2:
            boundary = end_s-2*self.bin_s
            if hot:
                self.start = boundary
            else:
                self.intervals.append((boundary, boundary-self.start))
                self.start = None
            self.hot, self.streak = hot, 0
        self._expire(end_s)

    def _expire(self, now):
        while self.intervals and now-self.intervals[0][0] > self.retention_s:
            self.intervals.popleft()

    def horizon(self, now, configured=2, capacity=float('inf')):
        """Cap by completed total durations, without conditioning on age."""
        self._expire(now)
        bounds = [configured, capacity]
        if len(self.intervals) >= 2:
            bounds.append(median(duration for _, duration in self.intervals))
        return max(0, min(bounds))

    def conditioned_horizon(self, now, configured=2, capacity=float('inf')):
        """For a hot range, cap by the median remaining time of comparable spells."""
        self._expire(now)
        bounds = [configured, capacity]
        if self.hot:
            # One unconfirmed cold bin contributes delay, not observed hot age.
            last_hot_end = self.last_end - self.streak * self.bin_s
            age = last_hot_end - self.start
            delay = max(0.0, now - last_hot_end)
            remaining = [max(0.0, duration - age)
                         for _, duration in self.intervals
                         if duration + 1e-8 >= age]
            if len(remaining) >= 2:
                bounds.append(median(remaining) - delay)
        return max(0.0, min(bounds))


def interference_residual(structural_cpu, active_cpu):
    if min(structural_cpu, active_cpu) < 0:
        raise ValueError('CPU costs must be nonnegative')
    return max(0, active_cpu-structural_cpu)


def class_point_cost(sample_count, terminated, delta_term, delta_miss, base_fallthrough):
    """All inputs belong to ONE logical hit/miss class and structural cell."""
    if sample_count < 64 or not 0 <= terminated <= sample_count:
        raise ValueError('unsupported class cell')
    p = terminated/sample_count
    return p*delta_term+(1-p)*(delta_miss+base_fallthrough)
