# Event Ribbon Visualization

[event_ribbon.py](/viz/event_ribbon.py) renders many long-running (~year-scale) integer event streams into a single grayscale PNG — one horizontal strip per stream, with day columns aligned across all strips so you can eyeball gaps, bursts, and coverage differences between sources at a glance. Typical use: per-source event counts over time, with optional coverage spans marking when each source was expected to be reporting.

```bash
pip install numpy pillow
python3 event_ribbon.py events.csv --spans spans.csv -o ribbon.png --epoch 2025-01-01T00:00:00
python3 event_ribbon.py --demo -o ribbon.png   # synthetic 3-stream example + acceptance checks
```

## Input

Plain CSV with a header row; timestamps are integer Unix nanoseconds or ISO-8601 (naive = UTC):

- `events.csv`: `stream,timestamp` — one row per event
- `spans.csv` (optional): `stream,start,end` — one row per coverage span

Or call the Python API directly with dicts of numpy `int64` ns arrays:

```python
from event_ribbon import render_ribbon
img = render_ribbon(events={"a": ts_ns}, spans={"a": (starts_ns, ends_ns)},
                    epoch_ns=None, bin_hours=0.5, label_width=200)
```

## Layout and encoding

- Each strip is `bins_per_day` px tall (48 at the default 0.5 h bins) × `n_days` px wide, followed by a white 200-px label block with the stream name — no divider column; the white background is divider enough.
- Strips are stacked with a 1-px separator row of value **75** between them. 75 is provably unachievable by any data pixel (the script verifies this at startup against the exact rescale formula; nearest achievable values are 70 and 79), so separators can always be machine-detected.
- Event layer: +1 per event into its bin, then `clip(log2(count + 1e-5) * 50, 0, 255)`.
- Span layer: +20 exactly once (clipped at 255) for every bin overlapped by ≥ 1 span.

## Time → pixel mapping

With reference epoch T0 (`--epoch`, default: next UTC midnight after the newest timestamp):
`t` = hours before T0; `H = floor(t / bin_hours)`; `day = H // bins_per_day`; `slot = H % bins_per_day`. The block is built as `A[day, slot]` then rotated once clockwise (`np.rot90(A, k=-1)`), so the **newest bin is the top-right pixel**, down = one bin (0.5 h) older, left = one day older — pixels run top-to-bottom, then right-to-left, like traditional Chinese writing.

Inverse (pixel → UTC range) for a final-image pixel `(col x, row y)` with band pitch `p = bins_per_day + 1`: stream band `r = y // p` (`y % p == bins_per_day` → separator); `i = y % p`; `x >= n_days` → label block, else `day = n_days - 1 - x`; `H = day * bins_per_day + i`; the pixel covers `[H, H+1) * bin_hours` hours before T0. The script prints this recipe with the concrete numbers filled in after every render.

## Self-checks

`--demo` renders 3 synthetic streams over a year with known probe events (2 in the newest bin, 4 one bin older, 8 one day older) and asserts output dimensions, separator-row purity (all-75 rows, no 75 in data pixels), and corner orientation (probe values 50 / 100 / 150 land at top-right / below it / left of it). Two checks also run on every invocation: separator-value unachievability and the rotation-orientation unit test.
