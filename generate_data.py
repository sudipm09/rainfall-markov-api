"""Create two synthetic sequences, 30 days each (January/July 1–30, 2026)."""
import csv
import json
from datetime import date, timedelta
from pathlib import Path
import numpy as np

BASE = Path(__file__).parent
rng = np.random.default_rng(20260701)
def sample(initial, p_rain):
    seq = [initial]
    for _ in range(29):
        seq.append(int(rng.random() < p_rain[seq[-1]]))
    return seq

sequences = {
    'july': sample(1, [0.68, 0.83]),
    'january': sample(0, [0.16, 0.40]),
}
(BASE / 'data').mkdir(exist_ok=True)
for month, sequence in sequences.items():
    start = date(2026, 7 if month == 'july' else 1, 1)
    with (BASE / 'data' / f'{month}_rainfall_30days.csv').open('w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['date', 'rain'])
        writer.writerows([ (start + timedelta(days=i)).isoformat(), v] for i, v in enumerate(sequence))
(BASE / 'data' / 'fastapi_input.json').write_text(json.dumps({**sequences, 'bootstrap_iterations': 5000, 'random_seed': 2026}, indent=2) + '\n')
print({k: {"rainy_days": sum(v), "sequence": v} for k,v in sequences.items()})
