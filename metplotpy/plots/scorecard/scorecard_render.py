#!/usr/bin/env python3
"""
scorecard_render.py -- database-free, HPC-friendly scorecard renderer.

Reads the scorecard_stats.txt written by the METplotpy scorecard script
(tab-separated DIFF_SIG output) and draws a METviewer-style scorecard with
matplotlib only (Agg backend: no browser, no Plotly/Kaleido, no display).

Value convention (from METcalcpy scorecard.py / perfect_score_adjustment):
  DIFF_SIG stat_value is a signed confidence level (1 - p), already adjusted
  for the statistic's perfect score:
      positive -> series 1 (first model) is BETTER than series 2
      negative -> series 1 is WORSE than series 2
  Thresholds: |v| >= 0.95 / 0.99 / 0.999 -> 95 / 99 / 99.9 % significance
  (the EMC method returns exactly +/-0.95, 0.99, 1, which map the same way).

Usage:
  python scorecard_render.py scorecard_stats.txt -o scorecard.png
  python scorecard_render.py scorecard_stats.txt -o scorecard.pdf --show-values
  python scorecard_render.py --demo -o demo.png          # synthetic data

Importable:
  from scorecard_render import load_scorecard, render_scorecard
  fig = render_scorecard(load_scorecard("scorecard_stats.txt"), "out.png")
"""
import argparse
import re
import sys
import warnings

import matplotlib
matplotlib.use("Agg")  # headless: safe on HPC login/batch nodes
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Palettes: index 0 = 95%, 1 = 99%, 2 = 99.9%
# --------------------------------------------------------------------------
PALETTES = {
    # familiar to METviewer users: green = better, pink = worse
    "metviewer": {
        "better": ["#c7e9c0", "#74c476", "#238b45"],
        "worse": ["#fcc5c0", "#f768a1", "#ae017e"],
    },
    # colour-vision-deficiency friendly: blue = better, orange = worse
    "colorblind": {
        "better": ["#c6dbef", "#6baed6", "#2171b5"],
        "worse": ["#fdd0a2", "#fd8d3c", "#d94801"],
    },
}
NOSIG_COLOR = "#d9d9d9"
LEVEL_PCT = {1: "95%", 2: "99%", 3: "99.9%"}
MISSING_VALUES = {"NA", "NAN", "", "-9999", "-9999.0"}

# Label columns: (key, header). The first three always appear; the rest only
# appear when they actually vary in the data (otherwise they go in the subtitle).
ALWAYS_COLS = [("stat", "Statistic"), ("var", "Variable"), ("level", "Level")]
OPTIONAL_COLS = [("thresh", "Threshold"), ("region", "Region"), ("obtype", "Obs type")]


# --------------------------------------------------------------------------
# Data preparation
# --------------------------------------------------------------------------
def _lead_to_hours(x):
    """HHMMSS integer/string (e.g. 60000 -> 6 h, 480000 -> 48 h) -> hours."""
    v = int(float(x))
    h, m = v // 10000, (v % 10000) // 100
    return h + m / 60.0


def _fmt_lead(hours):
    h = int(hours)
    m = int(round((hours - h) * 60))
    return f"{h}" if m == 0 else f"{h}:{m:02d}"


def _sig_code(v):
    """Signed significance code: +/-1,2,3 (95/99/99.9%), 0 = not significant,
    None = no data."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    a, s = abs(v), (1 if v >= 0 else -1)
    eps = 1e-9
    if a >= 0.999 - eps:
        return 3 * s
    if a >= 0.99 - eps:
        return 2 * s
    if a >= 0.95 - eps:
        return 1 * s
    return 0


def _parse_models(model_str):
    """'DIFF_SIG(P250 AIGEFS 0 UGRD ADPUPA MAE-P250 GEFS 0 UGRD ADPUPA MAE)'
    -> ('AIGEFS', 'GEFS'). Returns (None, None) if the layout is unexpected."""
    m = re.match(r"^DIFF_SIG\((.*)\)$", str(model_str).strip())
    if not m:
        return None, None
    tok = m.group(1).split()
    # "lev model lead var obtype stat-lev model lead var obtype stat" -> 11 tokens,
    # because the series are joined as "...stat-lev" (one token).
    if len(tok) == 11:
        return tok[1], tok[6]
    return None, None


def load_scorecard(path):
    """Read scorecard_stats.txt and return a tidy DataFrame with columns:
    stat, var, level, thresh, region, obtype, lead_hr, value, code
    plus df.attrs['model1'/'model2'/'linetype'/'valid_range']."""
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    return tidy_scorecard(df)


def tidy_scorecard(raw):
    need = ["fcst_lead", "fcst_var", "fcst_lev", "stat_name", "stat_value"]
    missing = [c for c in need if c not in raw.columns]
    if missing:
        raise ValueError(f"scorecard input is missing required columns: {missing} "
                         f"(found: {list(raw.columns)})")
    if len(raw) == 0:
        raise ValueError("scorecard input has zero rows -- nothing to draw")

    def col(name, default="NA"):
        return raw[name].astype(str) if name in raw.columns else pd.Series(default, index=raw.index)

    linetype = col("line_type").iloc[0]
    stat = col("stat_name").str.replace(rf"^{re.escape(linetype)}_", "", regex=True)

    def to_val(s):
        return np.nan if s.strip().upper() in MISSING_VALUES else float(s)

    out = pd.DataFrame({
        "stat": stat,
        "var": col("fcst_var"),
        "level": col("fcst_lev"),
        "thresh": col("fcst_thresh"),
        "region": col("vx_mask"),
        "obtype": col("obtype"),
        "lead_hr": raw["fcst_lead"].map(_lead_to_hours),
        "value": raw["stat_value"].map(to_val),
    })
    out["code"] = out["value"].map(_sig_code)

    m1, m2 = _parse_models(raw["model"].iloc[0]) if "model" in raw.columns else (None, None)
    out.attrs["model1"], out.attrs["model2"] = m1, m2
    out.attrs["linetype"] = linetype
    if "fcst_valid_end" in raw.columns:
        d = pd.to_datetime(raw["fcst_valid_end"], errors="coerce").dropna()
        out.attrs["valid_range"] = (d.min(), d.max()) if len(d) else None
    return out


def summarize(df):
    """Print what is actually in the file, so a missing statistic is obvious."""
    print("scorecard rows by statistic (cells with a value / total):", file=sys.stderr)
    for stat, g in df.groupby("stat", sort=False):
        n_ok = int(g["code"].map(lambda c: c is not None and not
                                 (isinstance(c, float) and np.isnan(c))).sum())
        print(f"  {stat:<12} {n_ok}/{len(g)} cells, "
              f"{g['var'].nunique()} var(s), {g['level'].nunique()} level(s)", file=sys.stderr)
        if n_ok == 0:
            warnings.warn(f"{stat}: every value is missing (NA/-9999). The statistic was "
                          "listed but not computed -- look upstream (SumStat/sal1l2 columns).")


def make_demo_df():
    """Synthetic data to preview the layout (no pipeline needed)."""
    rng = np.random.default_rng(7)
    rows = []
    for stat in ["MAE", "ANOM_CORR"]:
        for var, levels in [("UGRD", ["P850", "P500", "P250"]),
                            ("VGRD", ["P850", "P500", "P250"]),
                            ("TMP", ["P850", "P500"])]:
            for lev in levels:
                for hr in range(0, 121, 12):
                    if rng.random() < 0.06:
                        continue  # a few missing cells
                    sig = rng.choice([0, 0.95, 0.99, 0.999])
                    v = sig * rng.choice([-1, 1]) if sig else rng.uniform(-0.9, 0.9)
                    rows.append(dict(stat=stat, var=var, level=lev, thresh="NA",
                                     region="CONUS", obtype="ADPUPA",
                                     lead_hr=float(hr), value=float(v)))
    df = pd.DataFrame(rows)
    df["code"] = df["value"].map(_sig_code)
    df.attrs.update(model1="AIGEFS", model2="GEFS", linetype="SAL1L2",
                    valid_range=(pd.Timestamp("2026-03-01"), pd.Timestamp("2026-03-31")))
    return df


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
def render_scorecard(df, outfile=None, title=None, subtitle=None,
                     model1=None, model2=None, palette="metviewer",
                     show_values=False, markers=True, dpi=200,
                     label_map=None, date_range=None, subtitle_extra=None):
    """Draw the scorecard. Returns the matplotlib Figure; saves if outfile.

    label_map  : optional {raw label: display label} for the row labels, e.g.
                 {"UGRD": "U wind", "P250": "250 hPa"}.
    subtitle_extra : optional text appended to the auto-generated subtitle, e.g.
                 "30 of 31 days" when some dates were skipped.
    date_range : optional (start, end) shown in the auto-generated subtitle
                 (anything pandas can parse, e.g. "20260301"); overrides the
                 single valid date found in the stats file.
    """
    if palette not in PALETTES:
        raise ValueError(f"unknown palette {palette!r}; choose from {sorted(PALETTES)}")
    label_map = {str(k): str(v) for k, v in (label_map or {}).items()}

    def disp(x):
        return label_map.get(str(x), str(x))

    pal = PALETTES[palette]
    m1 = model1 or df.attrs.get("model1") or "Series 1"
    m2 = model2 or df.attrs.get("model2") or "Series 2"

    # ---- which label columns to show --------------------------------------
    cols = list(ALWAYS_COLS)
    fixed = []  # facts that don't vary -> subtitle
    for key, hdr in OPTIONAL_COLS:
        n = df[key].nunique()
        if n > 1:
            cols.append((key, hdr))
        elif n == 1 and df[key].iloc[0] not in ("NA", ""):
            fixed.append(df[key].iloc[0])
    keys = [k for k, _ in cols]

    # ---- one row per label tuple, one column per lead ---------------------
    dup = df.duplicated(subset=keys + ["lead_hr"], keep="first")
    if dup.any():
        warnings.warn(f"{int(dup.sum())} duplicate (row-label, lead) entries found; "
                      "keeping the first of each. Check subset_params in the YAML "
                      "(e.g. two obtypes or masks mixed together).")
        df = df[~dup]
    row_keys = list(dict.fromkeys(map(tuple, df[keys].itertuples(index=False, name=None))))
    leads = sorted(df["lead_hr"].unique())
    r_idx = {k: i for i, k in enumerate(row_keys)}
    c_idx = {h: j for j, h in enumerate(leads)}
    code = np.full((len(row_keys), len(leads)), np.nan)
    val = np.full_like(code, np.nan)
    for r in df.itertuples(index=False):
        i, j = r_idx[tuple(getattr(r, k) for k in keys)], c_idx[r.lead_hr]
        if r.code is not None and not (isinstance(r.code, float) and np.isnan(r.code)):
            code[i, j] = r.code
        val[i, j] = r.value
    nrow, ncol = code.shape

    # ---- geometry, all in inches ------------------------------------------
    FS = 9.0
    cw, rh = 0.55 if not show_values else 0.62, 0.34
    char_w = 0.082
    col_w = []
    for d, (k, hdr) in enumerate(cols):
        longest = max([len(disp(x[d])) for x in row_keys] + [len(hdr)])
        col_w.append(longest * char_w + 0.25)
    label_w = sum(col_w)
    grid_w = ncol * cw
    leg_col_w = max(len(f"{m1} better than {m2} (99.9%)"),
                    len(f"{m2} better than {m1} (99.9%)")) * char_w + 0.5
    content_w = max(label_w + grid_w, 2 * leg_col_w)
    margin = 0.35
    W = content_w + 2 * margin
    x0 = (W - (label_w + grid_w)) / 2           # center the table
    gx = x0 + label_w                            # left edge of the colour grid

    title_h, banner_h, lead_h = 0.95, 0.30, 0.32
    y_grid = margin + title_h + banner_h + lead_h
    y_grid_end = y_grid + nrow * rh
    leg_rows = 4
    H = y_grid_end + 0.45 + leg_rows * 0.30 + margin

    fig = plt.figure(figsize=(W, H), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")

    # ---- title block -------------------------------------------------------
    title = title or f"{m1} vs. {m2} Scorecard"
    if subtitle is None:
        bits = [f"{df.attrs.get('linetype', '')}".strip()] if df.attrs.get("linetype") not in (None, "NA") else []
        bits += fixed
        vr = date_range or df.attrs.get("valid_range")
        if vr:
            a, b = (pd.to_datetime(str(x)) for x in vr)
            bits.append(a.strftime("%Y-%m-%d") if a == b else f"{a:%Y-%m-%d} to {b:%Y-%m-%d}")
        if subtitle_extra:
            bits.append(subtitle_extra)
        subtitle = "  \u00b7  ".join(b for b in bits if b)
    ax.text(W / 2, margin + 0.18, title, ha="center", va="center",
            fontsize=15, fontweight="bold", color="#1a1a1a")
    if subtitle:
        ax.text(W / 2, margin + 0.50, subtitle, ha="center", va="center",
                fontsize=9.5, color="#555555")

    # ---- header ------------------------------------------------------------
    yb = margin + title_h
    ax.text(gx + grid_w / 2, yb + banner_h / 2, "Forecast lead time (hours)",
            ha="center", va="center", fontsize=FS + 0.5, fontweight="bold", color="#333333")
    ax.plot([gx + 0.04, gx + grid_w - 0.04], [yb + banner_h, yb + banner_h],
            color="#333333", lw=0.8)
    for j, h in enumerate(leads):
        ax.text(gx + (j + 0.5) * cw, yb + banner_h + lead_h / 2, _fmt_lead(h),
                ha="center", va="center", fontsize=FS, color="#222222")
    xs = [x0]
    for w in col_w:
        xs.append(xs[-1] + w)
    for d, (k, hdr) in enumerate(cols):
        ax.text(xs[d] + 0.06, yb + banner_h + lead_h / 2, hdr, ha="left", va="center",
                fontsize=FS, fontweight="bold", color="#333333")
    ax.plot([x0, gx + grid_w], [y_grid, y_grid], color="#1a1a1a", lw=1.4)

    # ---- cells ---------------------------------------------------------------
    def colour_for(c, dark_text=False):
        if c == 0:
            return NOSIG_COLOR
        lvl = int(abs(c)) - 1
        return pal["better" if c > 0 else "worse"][lvl]

    for i in range(nrow):
        for j in range(ncol):
            x, y = gx + j * cw, y_grid + i * rh
            c = code[i, j]
            if np.isnan(c):
                ax.add_patch(Rectangle((x, y), cw, rh, facecolor="white",
                                       edgecolor="#bdbdbd", hatch="////", lw=0.0))
                ax.add_patch(Rectangle((x, y), cw, rh, facecolor="none",
                                       edgecolor="white", lw=1.5))
                continue
            ax.add_patch(Rectangle((x, y), cw, rh, facecolor=colour_for(c),
                                   edgecolor="white", lw=1.5))
            txt_col = "white" if abs(c) == 3 else "#1a1a1a"
            cx, cy = x + cw / 2, y + rh / 2
            if markers and c != 0:
                size = {1: 14, 2: 26, 3: 42}[int(abs(c))]
                mx, my = (x + 0.12, y + 0.12) if show_values else (cx, cy)
                ax.scatter([mx], [my], marker="^" if c > 0 else "v", s=size,
                           color=txt_col, linewidths=0, zorder=3)
            if show_values and not np.isnan(val[i, j]):
                ax.text(cx, cy + (0.03 if (markers and c != 0) else 0), f"{val[i, j]:+.2f}",
                        ha="center", va="center", fontsize=7.5, color=txt_col, zorder=3)

    # ---- hierarchical row labels + separators -------------------------------
    ncols_l = len(cols)
    for d in range(ncols_l):
        prefixes = [rk[:d + 1] for rk in row_keys]
        s = 0
        while s < nrow:
            e = s
            while e + 1 < nrow and prefixes[e + 1] == prefixes[s]:
                e += 1
            yc = y_grid + (s + e + 1) / 2 * rh
            ax.text(xs[d] + 0.06, yc, disp(row_keys[s][d]), ha="left", va="center",
                    fontsize=FS, color="#1a1a1a",
                    fontweight="bold" if d == 0 else "normal")
            if s > 0:
                ys = y_grid + s * rh
                lw, colr = (1.2, "#333333") if d == 0 else (0.8, "#888888") if d == 1 else (0.4, "#cccccc")
                ax.plot([xs[d], gx + grid_w], [ys, ys], color=colr, lw=lw, zorder=2)
            s = e + 1
    ax.plot([x0, gx + grid_w], [y_grid_end, y_grid_end], color="#1a1a1a", lw=1.4)

    # ---- legend ----------------------------------------------------------------
    ly = y_grid_end + 0.45
    lx = [(W - 2 * leg_col_w) / 2, (W - 2 * leg_col_w) / 2 + leg_col_w]
    sw = 0.30

    def key(x, y, c, label):
        ax.add_patch(Rectangle((x, y - 0.10), sw, 0.20,
                               facecolor=colour_for(c) if c is not None else "white",
                               edgecolor="#999999" if c is None else "white", lw=0.8,
                               hatch="////" if c is None else None))
        if markers and c not in (None, 0):
            ax.scatter([x + sw / 2], [y], marker="^" if c > 0 else "v",
                       s={1: 14, 2: 26, 3: 42}[abs(c)], linewidths=0, zorder=3,
                       color="white" if abs(c) == 3 else "#1a1a1a")
        ax.text(x + sw + 0.12, y, label, ha="left", va="center", fontsize=8.5, color="#222222")

    for k, lvl in enumerate([3, 2, 1]):
        key(lx[0], ly + k * 0.30, lvl, f"{m1} better than {m2} ({LEVEL_PCT[lvl]})")
        key(lx[1], ly + k * 0.30, -lvl, f"{m1} worse than {m2} ({LEVEL_PCT[lvl]})")
    key(lx[0], ly + 3 * 0.30, 0, "No statistically significant difference")
    key(lx[1], ly + 3 * 0.30, None, "No data")

    if outfile:
        fig.savefig(outfile, dpi=dpi, facecolor="white")
    return fig


# --------------------------------------------------------------------------
STYLE_KEYS = {"title", "subtitle", "palette", "show_values", "markers", "formats",
              "dpi", "label_map", "model_names"}


def render_from_config(stats_file, out_base, style=None, model_names=None,
                       date_range=None, title=None, subtitle_extra=None):
    """Config-driven entry point used by scorecard_plot.py (and handy on its own).

    stats_file : path to scorecard_stats.txt
    out_base   : output path WITHOUT extension, e.g. <output_dir>/scorecard
    style      : dict, typically the `scorecard_style:` block of the YAML.
                 Recognised keys (all optional):
                   title, subtitle, palette (metviewer|colorblind),
                   show_values (bool), markers (bool), formats (list of
                   png/pdf/svg), dpi, label_map ({raw: display}),
                   model_names ([series 1, series 2])
    model_names, date_range, title : defaults used when the style block does
                 not give them (the YAML's own model list, ymd_start/ymd_end,
                 and scorecard_title).
    Returns the list of files written.
    """
    style = dict(style or {})
    unknown = sorted(set(style) - STYLE_KEYS)
    if unknown:
        warnings.warn(f"unknown scorecard_style key(s) ignored: {unknown}; "
                      f"valid keys: {sorted(STYLE_KEYS)}")
    names = style.get("model_names") or model_names or [None, None]
    formats = style.get("formats", ["png"])
    if isinstance(formats, str):
        formats = [formats]
    bad = [f for f in formats if f.lower() not in ("png", "pdf", "svg")]
    if bad:
        raise ValueError(f"unsupported scorecard format(s) {bad}; use png, pdf or svg")

    df = load_scorecard(stats_file)
    summarize(df)
    fig = render_scorecard(
        df, None,
        title=style.get("title") or title,
        subtitle=style.get("subtitle"),
        model1=names[0], model2=names[1],
        palette=style.get("palette", "metviewer"),
        show_values=bool(style.get("show_values", False)),
        markers=bool(style.get("markers", True)),
        dpi=int(style.get("dpi", 200)),
        label_map=style.get("label_map"),
        date_range=date_range, subtitle_extra=subtitle_extra)
    written = []
    for fmt in formats:
        path = f"{out_base}.{fmt.lower()}"
        fig.savefig(path, dpi=int(style.get("dpi", 200)), facecolor="white")
        written.append(path)
    plt.close(fig)
    return written


def main(argv=None):
    p = argparse.ArgumentParser(description="Render a METplus DIFF_SIG scorecard with matplotlib.")
    p.add_argument("stats_file", nargs="?", help="scorecard_stats.txt (tab-separated)")
    p.add_argument("-o", "--output", default="scorecard.png", help="png, pdf or svg")
    p.add_argument("--title")
    p.add_argument("--subtitle")
    p.add_argument("--model1", help="name of series 1 (default: parsed from file)")
    p.add_argument("--model2", help="name of series 2 (default: parsed from file)")
    p.add_argument("--palette", choices=sorted(PALETTES), default="metviewer")
    p.add_argument("--show-values", action="store_true",
                   help="print the signed DIFF_SIG confidence value in each cell")
    p.add_argument("--no-markers", action="store_true", help="colour only, no triangles")
    p.add_argument("--dpi", type=int, default=200)
    p.add_argument("--demo", action="store_true", help="use synthetic data")
    a = p.parse_args(argv)

    if a.demo:
        df = make_demo_df()
    elif a.stats_file:
        df = load_scorecard(a.stats_file)
    else:
        p.error("give a stats file or --demo")
    summarize(df)
    render_scorecard(df, a.output, title=a.title, subtitle=a.subtitle,
                     model1=a.model1, model2=a.model2, palette=a.palette,
                     show_values=a.show_values, markers=not a.no_markers, dpi=a.dpi)
    print(f"wrote {a.output}")


if __name__ == "__main__":
    sys.exit(main())
