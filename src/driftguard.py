"""Executable range semantics and cost primitives. Times and costs use SI units."""
from bisect import bisect_left
from dataclasses import dataclass
from hashlib import blake2b
from math import expm1, log2, ceil
from statistics import median
from threading import RLock


class Range:
    """Integer-key/value range. None denotes a tombstone, never a stored value.

    A single reentrant mutex provides serialized reference semantics. Construction
    is performed outside the mutex against captured immutable input copies.
    """
    def __init__(self, base=None):
        self.base = dict(base or {})
        if any(v is None for v in self.base.values()):
            raise ValueError('base contains a tombstone')
        self.frozen = None
        self.active = {}
        self.generation = 0
        self.lock = RLock()

    def get(self, key):
        with self.lock:
            for layer in (self.active, self.frozen, self.base):
                if layer is not None and key in layer:
                    return layer[key]
            return None

    def write(self, key, value):
        with self.lock:
            is_new_entry = key not in self.active
            self.active[key] = value
            return is_new_entry

    def scan(self, low, high):
        with self.lock:
            logical = dict(self.base)
            if self.frozen is not None:
                logical.update(self.frozen)
            logical.update(self.active)
            return [(k, v) for k, v in sorted(logical.items())
                    if low <= k < high and v is not None]

    def freeze(self):
        with self.lock:
            if self.frozen is not None:
                raise RuntimeError('one build already in flight')
            self.frozen, self.active = self.active, {}
            self.generation += 1
            return self.generation

    def construct(self, token, fail=False):
        with self.lock:
            if token != self.generation or self.frozen is None:
                raise RuntimeError('stale build token')
            base, frozen = dict(self.base), dict(self.frozen)
        if fail:
            raise MemoryError('candidate allocation failed')
        base.update(frozen)
        return {k: v for k, v in sorted(base.items()) if v is not None}

    def publish(self, token, candidate):
        with self.lock:
            if token != self.generation or self.frozen is None:
                raise RuntimeError('stale publication')
            self.base = dict(candidate)
            self.frozen = None
            # The active object is deliberately neither replaced nor replayed.


def checked_lower_bound(keys, key, proposed_rank):
    """Validate a learned rank globally; fall back to exact binary search."""
    n = len(keys)
    j = proposed_rank
    if (0 <= j <= n and (j == 0 or keys[j-1] < key)
            and (j == n or key <= keys[j])):
        return j
    return bisect_left(keys, key)


class KMV:
    def __init__(self, k=4096):
        if k < 2:
            raise ValueError('k must be >= 2')
        self.k, self.hashes = k, set()

    def add(self, key):
        h = int.from_bytes(blake2b(str(key).encode(), digest_size=8).digest(), 'big')
        self.hashes.add((h + 1) / (2**64 + 1))
        if len(self.hashes) > self.k:
            self.hashes.remove(max(self.hashes))

    def union(self, other):
        if self.k != other.k:
            raise ValueError('incompatible sketch sizes')
        result = KMV(self.k)
        result.hashes = set(sorted(self.hashes | other.hashes)[:self.k])
        return result

    def estimate(self):
        return (len(self.hashes) if len(self.hashes) < self.k
                else (self.k - 1) / max(self.hashes))


def fit_growth(times, counts, write_rate):
    """Least-squares nonnegative linear or paper's power-of-two saturation fit."""
    if len(times) != len(counts) or not times or any(t <= 0 for t in times):
        raise ValueError('positive aligned observation times required')
    if write_rate < 0 or any(c < 0 for c in counts):
        raise ValueError('negative counts/rate')
    rate = max(0.0, sum(t*c for t, c in zip(times, counts))/sum(t*t for t in times))
    candidates = [('linear', rate, lambda t: rate*t)]
    for exponent in range(10, 25):
        k = 2**exponent
        candidates.append(('saturating', k, lambda t, k=k: k*(-expm1(-write_rate*t/k))))
    kind, parameter, predict = min(candidates,
        key=lambda c: sum((c[2](t)-n)**2 for t, n in zip(times, counts)))
    return kind, parameter, predict


def affine_gain(horizon_s, build_s, query_rate, old_s, base_s,
                residual_penalty_s, build_cpu_s, interference_cpu_s=0):
    if not 0 < build_s < horizon_s:
        raise ValueError('affine example requires 0 < T < H')
    return ((horizon_s-build_s)*query_rate*(old_s-base_s-residual_penalty_s)
            - build_cpu_s - interference_cpu_s)


def trajectory_gain(horizon_s, build_s, no_action, construction, published,
                    build_cpu_s, bin_s=0.1):
    """Equation 2 quadrature; callbacks return aggregate CPU seconds / second.

    Split a bin exactly at publication. Midpoint service rates approximate each
    subinterval. published(t) receives elapsed time since freeze, not since publish.
    """
    if horizon_s <= 0 or build_s < 0 or bin_s <= 0 or build_cpu_s < 0:
        raise ValueError('invalid duration/cost')
    edges = {0.0, horizon_s, min(build_s, horizon_s)}
    i = 1
    while i*bin_s < horizon_s:
        edges.add(i*bin_s)
        i += 1
    edges = sorted(edges)
    gain = -build_cpu_s
    for a, b in zip(edges, edges[1:]):
        t = (a+b)/2
        action = construction(t) if t < build_s else published(t)
        gain += (b-a)*(no_action(t)-action)
    return gain


def point_cost(probability, delta_term_s, delta_miss_s, base_s):
    if not 0 <= probability <= 1:
        raise ValueError('invalid probability')
    return probability*delta_term_s + (1-probability)*(delta_miss_s+base_s)


def adverse_costs(old_paths, rebuild_paths):
    """Unsupported composition: lower no-action cost, upper action cost."""
    if not old_paths or not rebuild_paths:
        raise ValueError('required path cost unsupported')
    return min(old_paths), max(rebuild_paths)


def dispatch(*, frozen, mandatory, memory_reserved, gain_envelope,
             horizon_s, build_s, measurement_cpu_s=0, supported=True):
    """Table 1 decision, with reservation and history supplied by the host."""
    if frozen:
        return 'retry_or_finish'
    if mandatory:
        return 'mandatory' if memory_reserved else 'wait_capacity'
    if horizon_s <= 0 or build_s < 0 or build_s >= horizon_s:
        return 'continue_serving'
    if not supported or not gain_envelope:
        return 'wait_evidence'
    if memory_reserved and min(gain_envelope) > measurement_cpu_s:
        return 'voluntary'
    return 'continue_serving'


@dataclass(frozen=True)
class BuildRecord:
    base_entries: int
    delta_entries: int
    live_entries: int
    base_segments: int
    input_bytes: int
    output_entries: int
    output_segments: int
    cpu_s: float
    probe_cpu_s: float
    wall_s: float
    worker_share: float

    def features(self):
        return [log2(1+x) for x in (self.base_entries, self.delta_entries,
                self.live_entries, self.base_segments)] + [log2(self.worker_share)]


def predict_candidate(current, history):
    """Equations 8--11 for nonempty output; history is one compatible host stratum."""
    if current.live_entries <= 0 or current.worker_share <= 0:
        raise ValueError('nonempty candidate and positive worker share required')
    records = [r for r in history[-128:] if r.output_entries > 0 and r.cpu_s > 0
               and .5 <= r.output_entries/current.live_entries <= 2
               and .5 <= r.worker_share/current.worker_share <= 2]
    if len(records) < 4:
        return None
    x = current.features()
    records.sort(key=lambda r: sum(abs(a-b) for a, b in zip(x, r.features())))
    donors = records[:8]
    cpu = (current.input_bytes+16*current.live_entries)*median(
        r.cpu_s/(r.input_bytes+16*r.output_entries) for r in donors)
    return {'segments': min(current.live_entries, max(1, ceil(current.live_entries*
                median(r.output_segments/r.output_entries for r in donors)))),
            'cpu_s': cpu, 'build_cpu_s': cpu+median(r.probe_cpu_s for r in donors),
            'wall_s': cpu*median(r.wall_s/r.cpu_s for r in donors),
            'donors': len(donors)}
