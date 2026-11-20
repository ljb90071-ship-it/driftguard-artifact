"""Replay a common timestamped offer stream against wait and one rebuild."""
import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.driftguard import Range
from src.observations import ResidenceCap


def observed_prefix(config, case):
    bin_ms = config['observation_bin_ms']
    offers = config['point_offers_per_second'] * bin_ms // 1000
    counts = []
    for duration_ms in case['ages_ms']:
        counts.extend([offers] * (duration_ms // bin_ms))
        counts.extend([0, 0])
    counts.extend([offers] * (case['elapsed_hot_ms'] // bin_ms))
    detector = ResidenceCap(bin_s=bin_ms / 1000)
    for i, count in enumerate(counts, 1):
        detector.observe(i * bin_ms / 1000, count, offers, config['ranges'])
    return detector


def evaluate(config, case):
    window_ms = config['window_ms']
    build_ms = config['build_ms']
    step = config['trace_bin_ms']
    writes = config['writes_during_build']
    case_ms = case['realized_hot_left_ms']
    observation_ms = config['observation_bin_ms']
    offer_rate = config['point_offers_per_second']
    if min(step, observation_ms, offer_rate) <= 0 or not 0 < build_ms < window_ms or writes <= 0:
        raise ValueError('positive rates, bins, writes and post-build window required')
    if not 0 <= case_ms <= window_ms or any(duration % step for duration in [build_ms, window_ms, case_ms]):
        raise ValueError('use trace-bin boundaries for the build, window and switch within that window')
    if any(duration < 2 * observation_ms or duration % observation_ms for duration in
           [*case['ages_ms'], case['elapsed_hot_ms']]):
        raise ValueError('hot episodes require at least two closed observation bins')
    bins_during_build = build_ms // step
    if offer_rate * step % 1000 or offer_rate * observation_ms % 1000 or writes % bins_during_build:
        raise ValueError('fixed-size bins require integral read and write counts')
    offers_per_bin = offer_rate * step // 1000
    writes_per_bin = writes // bins_during_build

    detector = observed_prefix(config, case)
    dispatch = detector.last_end
    duration_ms = round(detector.horizon(dispatch, configured=window_ms / 1000) * 1000)
    remaining_ms = round(detector.conditioned_horizon(dispatch, configured=window_ms / 1000) * 1000)

    # Point reads target the immutable base. The paired streams contain the
    # same updates, including tombstones, independent of the read hotspot.
    base = {key: key for key in range(writes + 64)}
    wait = Range(base)
    build = Range(base)
    for key in range(64):
        wait.write(key, -key)
        build.write(key, -key)
    token = build.freeze()
    candidate = build.construct(token)
    active = build.active
    costs = config['cost_ns']
    installed_cost = costs['clean_point'] + costs['published_delta_probe']
    wait_cpu = 0
    build_cpu = costs['transition']
    local_reads = 0
    post_reads = 0
    checked_writes = 0
    for elapsed in range(0, window_ms, step):
        if elapsed < build_ms:
            last_write = checked_writes + writes_per_bin
            for key in range(checked_writes, last_write):
                value = None if key % 8 == 0 else key + 1
                wait.write(key, value)
                build.write(key, value)
            checked_writes = last_write
        if elapsed == build_ms:
            build.publish(token, candidate)
            assert build.active is active and len(active) == writes
        if elapsed >= case_ms:
            continue  # The same offers move to an unchanged range in both arms.
        local_reads += offers_per_bin
        if elapsed >= build_ms:
            post_reads += offers_per_bin
        path_cost = costs['building_point'] if elapsed < build_ms else installed_cost
        for request in range(offers_per_bin):
            key = writes + request % 64
            assert wait.get(key) == build.get(key) == key
            wait_cpu += costs['wait_point']
            build_cpu += path_cost
    assert wait.scan(0, writes + 64) == build.scan(0, writes + 64)

    def forecast(horizon_ms, published_cost):
        build_ms_in_horizon = min(build_ms, horizon_ms)
        post_ms = max(0, horizon_ms - build_ms)
        pre_ns = offer_rate * build_ms_in_horizon * (costs['wait_point'] - costs['building_point']) / 1000
        post_ns = offer_rate * post_ms * (costs['wait_point'] - published_cost) / 1000
        gain_ms = (pre_ns + post_ns - costs['transition']) / 1e6
        return round(gain_ms, 6), 'Build' if horizon_ms > build_ms and gain_ms > 0 else 'Wait'

    duration_gain, duration_decision = forecast(duration_ms, installed_cost)
    remaining_gain, remaining_decision = forecast(remaining_ms, installed_cost)
    clean_gain, clean_decision = forecast(remaining_ms, costs['clean_point'])
    return {
        'case': case['case'],
        'build_ms': build_ms,
        'elapsed_hot_ms': case['elapsed_hot_ms'],
        'realized_hot_left_ms': case_ms,
        'duration_cap_ms': duration_ms,
        'remaining_cap_ms': remaining_ms,
        'duration_cap_gain_cpu_ms': duration_gain,
        'remaining_cap_gain_cpu_ms': remaining_gain,
        'duration_cap_action': duration_decision,
        'remaining_cap_action': remaining_decision,
        'empty_delta_gain_cpu_ms': clean_gain,
        'empty_delta_action': clean_decision,
        'offered_point_reads': offer_rate * window_ms // 1000,
        'local_point_reads': local_reads,
        'local_post_publication_reads': post_reads,
        'publication_entries': len(active),
        'applied_writes': checked_writes,
        'replayed_gain_cpu_ms': (wait_cpu - build_cpu) / 1e6,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', nargs='?', type=Path,
                        default=ROOT / 'configs/residence_replay.json')
    parser.add_argument('--csv', type=Path, help='write result rows to this path')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    rows = [evaluate(config, case) for case in config['cases']]
    if args.csv:
        with args.csv.open('w', encoding='utf-8', newline='') as output:
            writer = csv.DictWriter(output, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(rows)
    else:
        print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
