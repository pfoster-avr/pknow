#!/usr/bin/env python3
"""
event_ribbon.py -- "ribbon" visualization of many long-running integer event
streams at once, as a single grayscale PNG.

Each stream (a named source emitting timestamped events, e.g. per-source event
counts over a year) becomes one horizontal strip.  Event density is drawn as a
log-scaled heat layer; an optional set of coverage spans per stream is drawn
as a flat brightness boost on the bins they overlap.

LAYOUT -- stacked rows of `data | label`, one row per stream:
         data    | label
    -------------------- <- 1-px-tall separator row (value 75)
         data    | label
    --------------------
         data    | label
    data  = `bins_per_day` px tall x n_days px wide (n_days is shared by all
    streams so the day-columns align); label = same height x `label_width` px,
    bright white, stream name in black.  NO separator column between data and
    label -- the white label background is divider enough.

USAGE
    python3 event_ribbon.py EVENTS.csv [--spans SPANS.csv] [-o OUT.png]
                            [--epoch ISO_UTC] [--bin-hours 0.5]
                            [--label-width 200]
    python3 event_ribbon.py --demo [-o OUT.png]     # synthetic self-test

INPUT FILES (plain CSV with a header row)
    EVENTS.csv : columns  stream,timestamp        (one row per event)
    SPANS.csv  : columns  stream,start,end        (one row per coverage span)
    Timestamps are either integer nanoseconds since the Unix epoch or ISO-8601
    strings (naive strings are taken as UTC).  Streams present in the spans
    file but with zero events still get a strip (span overlay only).

PYTHON API
    from event_ribbon import render_ribbon
    img = render_ribbon(events, spans=None, epoch_ns=None, bin_hours=0.5,
                        label_width=200)          # -> uint8 ndarray (H, W)
    events : dict[str, np.ndarray]  int64 ns event times per stream
    spans  : dict[str, tuple[np.ndarray, np.ndarray]]  (starts, ends) int64 ns

TIME <-> PIXEL MAPPING  (exact; T0 = the reference epoch, newest time drawn)
    t    = hours before T0 = (T0_ns - ts_ns) / 3.6e12
    H    = floor(t / bin_hours)     # bin index before T0 (0 = newest)
    day  = H // bins_per_day        # 0 == most recent day (nearest T0)
    slot = H %  bins_per_day        # slot within that day, 0 == most recent
    (H is computed by integer floor-division of nanoseconds; ns values near
     1e18 exceed float64 integer precision, so we never go through float.)

    The data block is FIRST built in NUMPY order as A[day, slot], shape
    [n_days, bins_per_day] (row-major flat index day*bins_per_day + slot == H
    itself), THEN rotated once CLOCKWISE (np.rot90(A, k=-1)) into the final
    block F, shape [bins_per_day, n_days], with F[i, j] = A[n_days-1-j, i].
    Final orientation: the bin CLOSEST to T0 is the TOP-RIGHT pixel, the
    2nd-closest is directly BELOW it, and the pixel to the LEFT of top-right
    is one day older -- pixels run top-to-bottom, then right-to-left, like
    traditional Chinese writing.

    INVERSE (to turn a suspicious final-image pixel (col x, row y) back into a
    UTC time range; stream bands have a pitch of bins_per_day+1 px):
        pitch = bins_per_day + 1
        r = y // pitch   -> stream band;  y % pitch == bins_per_day -> on a
                            separator row
        i = y %  pitch   -> row within the band's data block  (= slot)
        x >= n_days      -> in the label block;  else  day = n_days - 1 - x
        H = day*bins_per_day + i;  t = H*bin_hours hours before T0; the pixel
        covers [t, t + bin_hours) hours before T0, i.e. the UTC range
            ( T0 - (t+bin_hours)*3.6e12 ns ,  T0 - t*3.6e12 ns ]

PER-STREAM STRIP (spec) -- assembled in this order:
    1. build_data_block(): FIRST accumulate both layers in NUMPY order
       (left-to-right = slot, top-to-bottom = day) into A[day, slot]:
         * UNBUFFERED +1 per event at its (day, slot) cell (counts may
           exceed 255);
         * rescale  i = clip(log2(i + 1e-5) * 50, 0, 255);
         * BUFFERED +20 exactly once (clip 255) for every cell overlapping
           >= 1 coverage span;
       THEN one clockwise rotation -> the final bins_per_day-tall x
       n_days-wide block.
    2. build_label_block(): the bins_per_day-tall x label_width-wide white
       label block.
    3. hcat  data | label  ->  bins_per_day x (n_days + label_width).
    4. vcat with the 1-px-tall separator row (value 75) between consecutive
       strips.  75 is verified at startup to be UNACHIEVABLE by any data
       pixel (nearest achievable values: 70 and 79; see
       verify_separator_value()).
    5. vcat all strips -> final image:
       (bins_per_day*n_streams + n_streams-1) tall x (n_days+label_width)
       wide.

DEPENDENCIES:  numpy, Pillow  (pip install numpy pillow)
"""

import argparse
import csv
import os
import time
from datetime import datetime, timezone

import numpy as np
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None

# --------------------------------------------------------------------------- #
DEFAULT_BIN_HOURS = 0.5               # bin size in hours == one pixel
DEFAULT_LABEL_W = 200                 # label-block width in px
WHITE = 255
SEP_VALUE = 75                        # 1-px-tall separator; NOT achievable
SPAN_ADD = 20                         # flat boost for span-covered cells
NS_PER_HOUR = 3_600_000_000_000
DAY_HOURS = 24.0


def parse_ts_ns(s):
    """One timestamp -> int64 ns since the Unix epoch.

    Accepts integer nanoseconds ('1735689600000000000') or ISO-8601
    ('2025-01-01T00:00:00', '2025-01-01 12:30:00+00:00').  Naive ISO strings
    are taken as UTC."""
    s = s.strip()
    try:
        return int(s)
    except ValueError:
        pass
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1e9)


def bin_of(ts_ns, epoch_ns, bin_ns):
    """bin index before the reference epoch (exact integer arithmetic)."""
    return (epoch_ns - ts_ns.astype(np.int64)) // bin_ns


def expand_ranges(base, counts):
    """group i -> base[i] + [0..counts[i]-1], fully vectorized."""
    counts = counts.astype(np.int64)
    total = int(counts.sum())
    if total == 0:
        return np.empty(0, np.int64)
    grp_start = np.repeat(np.cumsum(counts) - counts, counts)
    local = np.arange(total, dtype=np.int64) - grp_start
    return np.repeat(base, counts) + local


def load_font():
    try:
        return ImageFont.load_default(size=18)
    except TypeError:
        return ImageFont.load_default()


def verify_separator_value():
    """The separator row must use a value NO data pixel can ever take.

    Recompute the exact achievable data-pixel set from the real rescale:
        base = clip(log2(count + 1e-5) * 50, 0, 255)   over integer count >= 0
        span-covered cells additionally get  min(base + 20, 255)
        then uint8 truncation (astype).
    base is monotone in count and saturates at 255 by count 35 (26 with the
    +20), so counts 0..199 reproduce the full infinite-count set exactly."""
    counts = np.arange(0, 200, dtype=np.float64)
    base = np.clip(np.log2(counts + 1e-5) * 50.0, 0.0, 255.0)
    achievable = np.union1d(
        base.astype(np.uint8),                                # events only
        np.minimum(base + SPAN_ADD, 255.0).astype(np.uint8))  # + span boost
    if SEP_VALUE in achievable:
        raise SystemExit("[check] FATAL: separator value %d IS achievable by "
                         "data pixels; pick a value outside %s"
                         % (SEP_VALUE, achievable.tolist()))
    below = int(achievable[achievable < SEP_VALUE].max())
    above = int(achievable[achievable > SEP_VALUE].min())
    print("[check] separator %d is unachievable by data pixels "
          "(nearest achievable: %d and %d; whole gap %d..%d is free)"
          % (SEP_VALUE, below, above, below + 1, above - 1))


def check_orientation():
    """Acceptance test on a tiny synthetic A[day, slot] (3 days x 4 slots):
    ONE clockwise rotation must put A[0,0] (closest to the epoch) at
    TOP-RIGHT, A[0,1] (one bin older) directly BELOW it, and A[1,0] (one day
    older) one pixel LEFT of it."""
    A = np.arange(12, dtype=np.uint8).reshape(3, 4)
    F = np.rot90(A, k=-1)
    assert F.shape == (4, 3), "rotation must flip the aspect"
    assert F[0, -1] == A[0, 0], "closest-to-epoch must land TOP-RIGHT"
    assert F[1, -1] == A[0, 1], "one bin older must land directly BELOW"
    assert F[0, -2] == A[1, 0], "one day older must land LEFT of top-right"
    print("[check] orientation: np.rot90(A, k=-1) corners OK "
          "(A[0,0]->top-right, A[0,1]->below it, A[1,0]->left of it)")


def build_data_block(event_ts, span_s, span_e, n_days, epoch_ns, bin_ns,
                     bins_per_day):
    """Step 1: one stream's data block, uint8 shape (bins_per_day, n_days).

    FIRST accumulate both layers in NUMPY order (left-to-right = slot,
    top-to-bottom = day) into A[day, slot], shape [n_days, bins_per_day].
    Its row-major flat index day*bins_per_day + slot is exactly the bin
    index H, so events bincount straight onto H and spans mark their covered
    H-range.  THEN apply the single clockwise rotation (np.rot90(A, k=-1))
    to reach the final orientation: top-right = closest to the epoch,
    downward = older within the day, leftward = one day older per column."""
    n_cells = n_days * bins_per_day
    # event layer: unbuffered +1 per event (counts may exceed 255)
    flat = np.zeros(n_cells, dtype=np.float64)
    if event_ts.size:
        flat = np.bincount(bin_of(event_ts, epoch_ns, bin_ns),
                           minlength=n_cells).astype(np.float64)
    # log2 rescale
    flat = np.clip(np.log2(flat + 1e-5) * 50.0, 0.0, 255.0)
    # span layer: buffered +20 once per covered cell, clipped to 255
    if span_s.size:
        h_s = np.maximum(bin_of(span_s, epoch_ns, bin_ns), 0)  # older->LARGER
        h_e = np.maximum(bin_of(span_e, epoch_ns, bin_ns), 0)
        covered = np.unique(expand_ranges(h_e, h_s - h_e + 1))
        flat[covered] = np.minimum(flat[covered] + SPAN_ADD, 255.0)

    A = flat.reshape(n_days, bins_per_day).astype(np.uint8)  # numpy order
    return np.rot90(A, k=-1)                     # CW -> (bins_per_day, n_days)


def build_label_block(name, font, bins_per_day, label_width):
    """Step 2: the white label block, uint8 (bins_per_day, label_width).

    Bright-white background with the stream name in black (bitmap font).  The
    white background doubles as the visual divider, so NO separator column is
    inserted between the data block and this one."""
    img = Image.fromarray(
        np.full((bins_per_day, label_width), WHITE, dtype=np.uint8), mode="L")
    d = ImageDraw.Draw(img)
    try:
        bb = d.textbbox((0, 0), name, font=font)
        th, oy = bb[3] - bb[1], bb[1]
    except Exception:
        th, oy = 12, 0
    d.text((6, max(0, (bins_per_day - th) // 2 - oy)), name, fill=0, font=font)
    return np.asarray(img)


def render_ribbon(events, spans=None, epoch_ns=None,
                  bin_hours=DEFAULT_BIN_HOURS, label_width=DEFAULT_LABEL_W,
                  verbose=True):
    """Render the full ribbon image.  Returns a uint8 ndarray (H, W), mode L.

    events   : dict  stream name -> int64 ns array of event times
    spans    : dict  stream name -> (starts, ends) int64 ns arrays, or None
    epoch_ns : reference epoch T0 in ns; time is drawn as "before T0".
               Defaults to the newest timestamp in the data, rounded UP to the
               next whole UTC day, so the newest bin sits at the top-right.
    """

    def log(msg):
        if verbose:
            print(msg)

    verify_separator_value()
    if verbose:
        check_orientation()

    spans = spans or {}
    bin_ns = int(round(bin_hours * NS_PER_HOUR))
    bins_per_day = int(round(DAY_HOURS / bin_hours))
    assert bins_per_day * bin_hours == DAY_HOURS, \
        "bin_hours must divide 24 evenly"

    if epoch_ns is None:
        newest = max(
            [int(ts.max()) for ts in events.values() if ts.size] +
            [int(e.max()) for _, e in spans.values() if e.size] or [0])
        day_ns = bin_ns * bins_per_day
        epoch_ns = -(-newest // day_ns) * day_ns  # ceil to next UTC day
        log("[epoch] auto: %s (next UTC midnight after newest timestamp)"
            % np.datetime64(epoch_ns, "ns"))

    # drop events at/after the epoch (they would map to a negative pixel)
    dropped = 0
    clean_events = {}
    for name, ts in events.items():
        ok = (ts > 0) & (ts < epoch_ns)
        dropped += int((~ok).sum())
        clean_events[name] = ts[ok]
    if dropped:
        log("[load] dropped %d events at/after the epoch" % dropped)

    names = sorted(set(clean_events) | set(spans))
    if not names:
        raise SystemExit("no streams to render")

    # global data-block width: enough days to cover every event and every
    # span start across ALL streams, so the day-columns align vertically
    h_max = 0
    for ts in clean_events.values():
        if ts.size:
            h_max = max(h_max, int(bin_of(ts, epoch_ns, bin_ns).max()))
    for s, _ in spans.values():
        if s.size:
            h_max = max(h_max,
                        int(np.maximum(bin_of(s, epoch_ns, bin_ns), 0).max()))
    n_days = h_max // bins_per_day + 1
    log("[build] %d streams; data blocks %d px tall x %d px wide "
        "(= days before the epoch)" % (len(names), bins_per_day, n_days))

    empty = np.empty(0, np.int64)
    font = load_font()
    t_start = time.time()
    strips = []
    for i, name in enumerate(names):
        ts = clean_events.get(name, empty)
        s, e = spans.get(name, (empty, empty))
        data_blk = build_data_block(ts, np.asarray(s, np.int64),
                                    np.asarray(e, np.int64), n_days,
                                    epoch_ns, bin_ns, bins_per_day)  # step 1
        label_blk = build_label_block(name, font, bins_per_day,
                                      label_width)                   # step 2
        strips.append(np.hstack([data_blk, label_blk]))              # step 3
        if (i + 1) % 25 == 0 or i + 1 == len(names):
            log("        %3d/%3d streams  (%.1fs)"
                % (i + 1, len(names), time.time() - t_start))

    # step 4: 1-px separator between consecutive strips;  step 5: vcat all
    sep = np.full((1, n_days + label_width), SEP_VALUE, dtype=np.uint8)
    parts = []
    for i, strip in enumerate(strips):
        if i:
            parts.append(sep)
        parts.append(strip)
    big = np.vstack(parts)
    log("[render] combined array %d x %d (H x W), %s px"
        % (big.shape[0], big.shape[1], f"{big.size:,}"))
    return big


# --------------------------------------------------------------------------- #
# CSV loading                                                                 #
# --------------------------------------------------------------------------- #
def load_events_csv(path):
    """CSV with header 'stream,timestamp' -> {stream: int64 ns array}."""
    per = {}
    with open(path, newline="") as f:
        rd = csv.DictReader(f)
        if not {"stream", "timestamp"} <= set(rd.fieldnames or []):
            raise SystemExit("[events] %s must have columns 'stream' and "
                             "'timestamp'; got %s" % (path, rd.fieldnames))
        for row in rd:
            per.setdefault(row["stream"], []).append(
                parse_ts_ns(row["timestamp"]))
    return {k: np.asarray(v, np.int64) for k, v in per.items()}


def load_spans_csv(path):
    """CSV with header 'stream,start,end' -> {stream: (starts, ends)} ns."""
    per = {}
    with open(path, newline="") as f:
        rd = csv.DictReader(f)
        if not {"stream", "start", "end"} <= set(rd.fieldnames or []):
            raise SystemExit("[spans] %s must have columns 'stream', 'start' "
                             "and 'end'; got %s" % (path, rd.fieldnames))
        for row in rd:
            per.setdefault(row["stream"], []).append(
                (parse_ts_ns(row["start"]), parse_ts_ns(row["end"])))
    out = {}
    for k, pairs in per.items():
        arr = np.asarray(pairs, np.int64).reshape(-1, 2)
        out[k] = (arr[:, 0], arr[:, 1])
    return out


# --------------------------------------------------------------------------- #
# synthetic demo + acceptance checks                                          #
# --------------------------------------------------------------------------- #
def make_demo_data(epoch_ns, bin_ns, bins_per_day):
    """3 synthetic streams over ~1 year, plus known probe pixels on 'alpha':
    2 events in the newest bin, 4 in the next-newest, 8 one day older.
    Expected top-right data pixels: 50, 100 below it, 150 to its left."""
    rng = np.random.default_rng(7)
    day_ns_ = bins_per_day * bin_ns
    year_ns = 365 * day_ns_

    def mid(h):  # a timestamp safely inside bin index h
        return epoch_ns - h * bin_ns - bin_ns // 2

    events = {
        # random bulk starts 2 days back so it cannot touch the probe bins
        "alpha": np.concatenate([
            epoch_ns - rng.integers(2 * day_ns_, year_ns, 20_000),
            np.full(2, mid(0)), np.full(4, mid(1)),
            np.full(8, mid(bins_per_day))]),
        "bravo": epoch_ns - rng.integers(0, year_ns // 2, 5_000),
        "charlie": epoch_ns - rng.integers(year_ns // 4, year_ns, 500),
    }
    events = {k: v.astype(np.int64) for k, v in events.items()}
    day_ns = bins_per_day * bin_ns
    spans = {
        "alpha": (np.asarray([epoch_ns - 30 * day_ns], np.int64),
                  np.asarray([epoch_ns - 10 * day_ns], np.int64)),
        "bravo": (np.asarray([epoch_ns - 100 * day_ns], np.int64),
                  np.asarray([epoch_ns - 90 * day_ns], np.int64)),
    }
    return events, spans


def run_demo_checks(img, n_streams, bins_per_day, label_width):
    """Verify dimensions, separator purity and corner orientation on the
    rendered demo image (probe pixels were placed on the FIRST stream)."""
    h, w = img.shape
    pitch = bins_per_day + 1
    assert h == bins_per_day * n_streams + n_streams - 1, "bad height %d" % h
    n_days = w - label_width
    assert 300 <= n_days <= 370, "expected ~365 day columns, got %d" % n_days
    # separator purity: separator rows are all 75; no DATA pixel is ever 75
    # (label text is anti-aliased, so the guarantee covers data columns only)
    for r in range(1, n_streams):
        row = r * pitch - 1
        assert (img[row] == SEP_VALUE).all(), "separator row %d impure" % row
    data_rows = np.delete(img, [r * pitch - 1 for r in range(1, n_streams)],
                          axis=0)[:, :w - label_width]
    assert not (data_rows == SEP_VALUE).any(), "75 leaked into data pixels"
    # corner orientation on the first stream's probe pixels:
    # newest bin (2 events -> 50) at TOP-RIGHT of the data block,
    # next bin (4 -> 100) directly BELOW, 1 day older (8 -> 150) to the LEFT
    tr = n_days - 1
    assert img[0, tr] == 50, "top-right: want 50, got %d" % img[0, tr]
    assert img[1, tr] == 100, "below top-right: want 100, got %d" % img[1, tr]
    assert img[0, tr - 1] == 150, ("left of top-right: want 150, got %d"
                                   % img[0, tr - 1])
    print("[check] demo: dimensions %dx%d, separator purity and corner "
          "orientation (newest->top-right, +1 bin below, +1 day left) OK"
          % (w, h))


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("events", nargs="?",
                    help="events CSV with columns stream,timestamp")
    ap.add_argument("--spans", help="coverage-spans CSV: stream,start,end")
    ap.add_argument("-o", "--out", default="ribbon.png")
    ap.add_argument("--epoch",
                    help="reference epoch T0 as ISO-8601 UTC (default: next "
                         "UTC midnight after the newest timestamp)")
    ap.add_argument("--bin-hours", type=float, default=DEFAULT_BIN_HOURS,
                    help="bin size in hours; must divide 24 (default 0.5)")
    ap.add_argument("--label-width", type=int, default=DEFAULT_LABEL_W)
    ap.add_argument("--demo", action="store_true",
                    help="render a synthetic 3-stream example and run "
                         "acceptance checks instead of reading CSVs")
    args = ap.parse_args()

    t_start = time.time()
    epoch_ns = parse_ts_ns(args.epoch) if args.epoch else None
    bin_ns = int(round(args.bin_hours * NS_PER_HOUR))
    bins_per_day = int(round(DAY_HOURS / args.bin_hours))

    if args.demo:
        if epoch_ns is None:
            epoch_ns = parse_ts_ns("2025-01-01T00:00:00")
        events, spans = make_demo_data(epoch_ns, bin_ns, bins_per_day)
    elif args.events:
        print("[load] events: %s" % args.events)
        events = load_events_csv(args.events)
        print("[load] %s events over %d streams"
              % (f"{sum(v.size for v in events.values()):,}", len(events)))
        spans = {}
        if args.spans:
            print("[load] spans: %s" % args.spans)
            spans = load_spans_csv(args.spans)
            print("[load] %s spans over %d streams"
                  % (f"{sum(s.size for s, _ in spans.values()):,}",
                     len(spans)))
    else:
        ap.error("provide an events CSV or --demo")

    img = render_ribbon(events, spans, epoch_ns=epoch_ns,
                        bin_hours=args.bin_hours,
                        label_width=args.label_width)
    if args.demo:
        run_demo_checks(img, len(events), bins_per_day, args.label_width)

    Image.fromarray(img, mode="L").save(args.out)
    with Image.open(args.out) as chk:
        chk.load()
        w, h = chk.size
    sz = os.path.getsize(args.out)
    n_days = w - args.label_width
    n_streams = (h + 1) // (bins_per_day + 1)
    print("[done] wrote %s (%.2f MiB) in %.1fs"
          % (args.out, sz / 2**20, time.time() - t_start))

    print("\n===== SUMMARY =====")
    print("output PNG        : %s" % args.out)
    print("output dimensions : %d x %d  (W x H), mode L, %.2f MiB"
          % (w, h, sz / 2**20))
    print("layout            : %d strips of %d px (data | label) + %d 1-px"
          " separators (value %d)"
          % (n_streams, bins_per_day, n_streams - 1, SEP_VALUE))
    print("data block width  : %d px == %d days before the epoch"
          % (n_days, n_days))
    print("PIXEL -> TIME inverse : band pitch = %d px (%d data rows + 1 sep)"
          % (bins_per_day + 1, bins_per_day))
    print("    given final-image (col x, row y): stream band r = y // %d;"
          " y %% %d == %d -> on a separator"
          % (bins_per_day + 1, bins_per_day + 1, bins_per_day))
    print("    i = y %% %d (row within the band = slot);"
          " x >= %d -> label block" % (bins_per_day + 1, n_days))
    print("    else day = %d - 1 - x;  H = day*%d + i;"
          "  t = H*%g hours before T0" % (n_days, bins_per_day,
                                          args.bin_hours))
    print("    pixel covers [t, t+%g) h before T0, i.e. the UTC range"
          % args.bin_hours)
    print("    ( T0 - (t+%g)*3.6e12 ns , T0 - t*3.6e12 ns ]" % args.bin_hours)


if __name__ == "__main__":
    main()
