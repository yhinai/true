# Controller Benchmark Comparison

- Sequential verified success rate: `1.00`
- Gearbox verified success rate: `1.00`
- Sequential unsafe claim rate: `0.83`
- Gearbox unsafe claim rate: `0.83`
- Sequential average model calls: `1.83`
- Gearbox average model calls: `2.83`
- Delta verified success rate: `0.00`
- Delta unsafe claim rate: `0.00`
- Recommended controller: `sequential`
- Promote to default: `False`

## Rationale
Keep gearbox opt-in for now because no verified-success lift, gearbox spends more model calls on the checked-in controller benchmark subset.
