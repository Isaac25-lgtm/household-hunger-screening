"""Locked multi-country test of single-contact timing rules (LSMS high-frequency phone surveys).

Implements reports/investigation/10_LOCKED_PROTOCOL_MULTICOUNTRY_HFPS.md with parameters
read only from config/multicountry_protocol.yaml. Two stages:

  1. structure(): per country, the food-security rounds, median interview dates,
     12-month horizons, usability and calendar-rule eligibility. No outcome rates.
  2. run(): hypotheses H1 (calendar rule vs random), H2 (data-driven transfer),
     H3 (second-contact warning rule), H4 (rural vs urban), plus exact missing-data
     ranges and a weighted sensitivity for H1.

Item identification (deviation D1 from the protocol's label rule, which assumed full
English labels): items are mapped to the standard FIES order 1 worried ... 6 ran out of
food, 7 hungry but did not eat, 8 whole day without eating, by label keywords (English
or French) and, where Stata's 80-character label limit truncates the wording, by the
item number in the variable name. Ethiopia's own numbering (fi6 = whole day, fi7 = ran
out, fi8 = hungry) is mapped by label.

Microdata stay in data/raw/multicountry (gitignored); only aggregates are written.
"""

from __future__ import annotations

import glob
import json
import re
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import history_bounds as hb
from . import schedule_metrics as sm
from .config import Paths
from .hfps import second_contact, select_candidate
from .provenance import sha256_file, utc_now

FIES_PATTERNS = {
    1: r"worr|inquiet|enough food to eat",
    2: r"health|nutritious|preferred|sain|nutriti",
    3: r"few kinds|kinds of food|peu de sortes|quelques sortes|variet",
    4: r"skip|sauter|saut",
    5: r"ate less|less than|moins que",
    6: r"ran out|out of food|outoffood|plus de nourriture|n.avait plus",
    7: r"hungry but|hungrynoteat|faim mais",
    8: r"whole day|full day|fullday|toute une",
}


def _map_items(labs: dict[str, str], candidates: list[str]) -> dict[int, str]:
    """FIES position -> variable name, by label keywords then by trailing item number."""
    found: dict[int, str] = {}
    for v in candidates:
        lab = (labs.get(v) or "").lower()
        for k, pat in FIES_PATTERNS.items():
            if k not in found and re.search(pat, lab + " " + v.lower()):
                # Ethiopia-style names carry the meaning in the name; other surveys in the label
                found[k] = v
                break
    for v in candidates:  # truncated labels: fall back to the item number in the name
        m = re.search(r"q0?([1-8])$", v)
        if m and int(m.group(1)) not in found and v not in found.values():
            found[int(m.group(1))] = v
    return found


def _read(path: Path, cols: list[str] | None = None):
    with pd.io.stata.StataReader(path) as rd:
        labs = rd.variable_labels()
        df = rd.read(convert_categoricals=False, columns=cols)
    return df, labs


def _decode(path: Path, df: pd.DataFrame, items: dict[int, str]) -> tuple[pd.DataFrame, dict]:
    """Add it1..it8 (1 = yes, 0 = no, NaN otherwise) using each item's value labels."""
    with pd.io.stata.StataReader(path) as rd:
        rd.read(convert_categoricals=False)  # a column subset misaligns pandas' label list
        vl = rd.value_labels()
        lblmap = dict(zip(rd._varlist, rd._lbllist))
    codes, new = {}, {}
    for k, v in items.items():
        labels = vl.get(lblmap.get(v)) or {}
        m = {}
        for code, text in labels.items():
            t = re.sub(r"^\d+\s*[.)-]?\s*", "", str(text).strip().lower())
            if re.match(r"(yes|oui)\b", t):
                m[code] = 1.0
            elif re.match(r"(no|non)\b", t):
                m[code] = 0.0
        codes[k] = m
        new[f"it{k}"] = df[v].map(m) if m else pd.Series(np.nan, index=df.index)
    return pd.concat([df, pd.DataFrame(new, index=df.index)], axis=1), codes


def _parse_dates(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        return s.dt.normalize()
    return pd.to_datetime(s.astype(str).str[:19], errors="coerce").dt.normalize()


# ---------------------------------------------------------------- country loaders
def _std(df: pd.DataFrame, r: int, hh: str, date: pd.Series, cluster, urban, zone, weight) -> pd.DataFrame:
    out = pd.DataFrame({"hh": df[hh].astype(str).str.strip(), "round": r, "date": date.values})
    for k in range(1, 9):
        out[f"it{k}"] = df[f"it{k}"].values if f"it{k}" in df else np.nan
    out["cluster"] = cluster.astype(str).values if cluster is not None else "all"
    out["urban"] = urban.values if urban is not None else np.nan
    out["zone"] = zone.values if zone is not None else None
    out["weight"] = weight.values if weight is not None else np.nan
    return out


def _bfa_static(d: Path) -> pd.DataFrame:
    """Cluster (grappe) and urban (milieu) per household from the first cover file that has them."""
    parts = []
    for f in sorted(glob.glob(str(d / "r*_sec0_cover.dta")), key=lambda x: int(re.match(r"r(\d+)_", Path(x).name).group(1))):
        with pd.io.stata.StataReader(f) as rd:
            cols = [c for c in ("hhid", "grappe", "milieu") if c in rd.variable_labels()]
            if set(cols) != {"hhid", "grappe", "milieu"}:
                continue
            df = rd.read(convert_categoricals=False, columns=cols)
            ml = rd.value_labels().get(dict(zip(rd._varlist, rd._lbllist)).get("milieu")) or {}
        urb = [k for k, v in ml.items() if re.search(r"(?i)urb", str(v))]
        df["urban"] = df["milieu"].isin(urb).astype(float).where(df["milieu"].notna())
        parts.append(df[["hhid", "grappe", "urban"]])
    st = pd.concat(parts).dropna(subset=["grappe"]).drop_duplicates("hhid")
    return st.set_index("hhid")


def load_bfa(d: Path, log: list) -> pd.DataFrame:
    frames = []
    static = _bfa_static(d)
    for f in sorted(glob.glob(str(d / "r*_sec7_securite_alimentaire.dta"))):
        r = int(re.match(r"r(\d+)_", Path(f).name).group(1))
        df, labs = _read(Path(f))
        items = _map_items(labs, [c for c in df.columns if re.match(r"s07q0[1-8]$", c)])
        if 7 not in items:
            continue
        df, codes = _decode(Path(f), df, items)
        bil, _ = _read(d / f"r{r}_sec12_bilan_entretien.dta")
        dates = bil.set_index("hhid")["s12q14"].pipe(_parse_dates)
        cov, clabs = _read(d / f"r{r}_sec0_cover.dta")
        cov = cov.set_index("hhid")
        wcol = next((c for c in cov.columns if re.match(r"(?i)hhw", c) and "panel" not in (clabs.get(c) or "").lower()), None)
        df = df.set_index("hhid")
        idx = df.index
        frames.append(_std(df.reset_index(), r, "hhid", dates.reindex(idx), static["grappe"].reindex(idx),
                           static["urban"].reindex(idx), None, cov[wcol].reindex(idx) if wcol else None))
        log.append({"country": "BFA", "round": r, "file": Path(f).name, "items": items, "yes_no_codes": codes[7],
                    "date_var": "sec12 s12q14", "cluster_var": "grappe", "weight_var": wcol})
    return pd.concat(frames, ignore_index=True)


def load_eth(d: Path, log: list) -> pd.DataFrame:
    frames = []
    files = {int(re.match(r"r(\d+)_", Path(f).name).group(1)): Path(f) for f in glob.glob(str(d / "r*_wb_lsms_hfpm_hh_survey_public_microdata*.dta"))}
    files[11] = d / "wb_lsms_hfpm_hh_survey_round11_clean_microdata.dta"
    for r in (15, 17, 18):
        files[r] = d / f"wb_lsms_hfpm_hh_survey_round{r}_fies_public.dta"
    for r, f in sorted(files.items()):
        if not f.exists():
            continue
        df, labs = _read(f)
        cand = [c for c in df.columns if re.match(r"(fi\d_|fies_\d$)", c)]
        items = _map_items(labs, cand)
        if 7 not in items:
            continue
        df, codes = _decode(f, df, items)
        if r >= 13:
            cov, _ = _read(d / f"wb_lsms_hfpm_hh_survey_round{r}_cover_interview_public.dta")
            cov = cov.drop_duplicates("household_id").set_index("household_id")
            df = df.join(cov[["cs_startdate"]], on="household_id")
        wcol = f"phw{r}" if f"phw{r}" in df else None
        frames.append(_std(df, r, "household_id", _parse_dates(df["cs_startdate"]), df["ea_id"], None, None,
                           df[wcol] if wcol else None))
        log.append({"country": "ETH", "round": r, "file": f.name, "items": items, "yes_no_codes": codes[7],
                    "date_var": "cs_startdate", "cluster_var": "ea_id", "weight_var": wcol})
    return pd.concat(frames, ignore_index=True)


def _load_nga(d: Path, log: list, prefix: str, tag: str) -> pd.DataFrame:
    frames = []
    for f in sorted(glob.glob(str(d / f"{prefix}*_sect_a*.dta"))):
        r = int(re.match(rf"{prefix}(\d+)_", Path(f).name).group(1))
        with pd.io.stata.StataReader(f) as rd:
            labs = rd.variable_labels()
        cand = [c for c in labs if re.match(r"s8q[1-8]$", c)]
        items = _map_items(labs, cand)
        if 7 not in items or not re.search(FIES_PATTERNS[7] + "|during the last 30 days", (labs.get(items[7]) or "").lower()):
            continue
        df, _ = _read(Path(f))
        df, codes = _decode(Path(f), df, items)
        s1, _ = _read(d / f"{prefix}{r}_sect_1.dta", ["hhid", "s1q2"])
        dates = s1.assign(dt=_parse_dates(s1["s1q2"])).groupby("hhid").dt.max()
        with pd.io.stata.StataReader(f) as rd:
            rd.read(convert_categoricals=False)
            vl = rd.value_labels()
            lm = dict(zip(rd._varlist, rd._lbllist))
        zl = vl.get(lm.get("zone")) or {}
        sl = vl.get(lm.get("sector")) or {}
        zone = df["zone"].map(zl)
        urban = df["sector"].map(lambda x, sl=sl: 1.0 if re.search(r"(?i)urban", str(sl.get(x, ""))) else 0.0)
        wcol = next((c for c in df.columns if re.match(rf"wt_(p2)?round{r}$", c)), None)
        clus = df["cluster"] if "cluster" in df else df["ea"]
        frames.append(_std(df, r, "hhid", df["hhid"].map(dates), clus, urban, zone, df[wcol] if wcol else None))
        log.append({"country": tag, "round": r, "file": Path(f).name, "items": items, "yes_no_codes": codes[7],
                    "date_var": "sect_1 s1q2 (latest attempt)", "cluster_var": "cluster" if "cluster" in df else "ea",
                    "weight_var": wcol})
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_uga(d: Path, log: list) -> pd.DataFrame:
    frames = []
    for f in sorted(glob.glob(str(d / "round*" / "SEC8.dta"))):
        r = int(re.search(r"round(\d+)", f).group(1))
        df, labs = _read(Path(f))
        cand = [c for c in df.columns if re.match(r"s8q0[1-8]$", c)]
        if not any("30 days" in (labs.get(c) or "") or re.search(FIES_PATTERNS[7], (labs.get(c) or "").lower()) for c in cand):
            continue
        items = _map_items(labs, cand)
        if 7 not in items:
            continue
        df, codes = _decode(Path(f), df, items)
        cov, cl = _read(Path(f).parent / "Cover.dta")
        cov = cov.drop_duplicates("hhid").set_index("hhid")
        dcol = next((c for c in cov.columns if re.search(r"(?i)date of (the )?interview", cl.get(c) or "")), None)
        if dcol is None:  # rounds 13+: end-of-interview timestamp in interview_result.dta
            ir, _ = _read(Path(f).parent / "interview_result.dta", ["hhid", "Rq14"])
            cov = cov.join(ir.drop_duplicates("hhid").set_index("hhid")["Rq14"])
            dcol = "Rq14"
        wcol = "wfinal" if "wfinal" in cov else next((c for c in cov.columns if re.search(r"(?i)final.*weight|weight.*final", cl.get(c) or "")), None)
        cov = cov.rename(columns={dcol: "Sq02"})
        if wcol is None:
            cov["wfinal"] = np.nan
        elif wcol != "wfinal":
            cov["wfinal"] = cov[wcol]
        keep = ["Sq02", "DistrictCode", "urban", "wfinal"]
        df = df.drop(columns=[c for c in keep if c in df]).join(cov[keep], on="hhid")
        with pd.io.stata.StataReader(Path(f).parent / "Cover.dta") as rd:
            rd.read(convert_categoricals=False)
            ul = rd.value_labels().get(dict(zip(rd._varlist, rd._lbllist)).get("urban")) or {}
        urb = df["urban"].map(lambda x, ul=ul: 1.0 if re.search(r"(?i)urban", str(ul.get(x, ""))) else 0.0)
        frames.append(_std(df, r, "hhid", _parse_dates(df["Sq02"]), df["DistrictCode"], urb, None, df["wfinal"]))
        log.append({"country": "UGA", "round": r, "file": f"round{r}/SEC8.dta", "items": items, "yes_no_codes": codes[7],
                    "date_var": f"Cover {dcol}", "cluster_var": "DistrictCode", "weight_var": wcol})
    return pd.concat(frames, ignore_index=True)


def load_tza(d: Path, log: list) -> pd.DataFrame:
    frames = []
    for f in sorted(glob.glob(str(d / "r*_sect_a*.dta"))):
        r = int(re.match(r"r(\d+)_", Path(f).name).group(1))
        with pd.io.stata.StataReader(f) as rd:
            labs = rd.variable_labels()
        cand = [c for c in labs if re.match(r"(s6q0[1-8]|s12aq[1-8])$", c)]
        items = _map_items(labs, cand)
        if 7 not in items:
            continue
        try:
            df, _ = _read(Path(f))
            df, codes = _decode(Path(f), df, items)
        except ValueError as e:  # published file truncated (round 9): use the CSV release if supplied
            csv = d.parent / "csv_extracted" / (Path(f).stem + ".csv")
            if not csv.exists():
                log.append({"country": "TZA", "round": r, "file": Path(f).name, "items": items, "yes_no_codes": {},
                            "date_var": None, "cluster_var": None, "weight_var": None, "status": f"unreadable: {e}"})
                continue
            raise NotImplementedError("CSV fallback: add reader once the CSV release is available") from e
        with pd.io.stata.StataReader(f) as rd:
            rd.read(convert_categoricals=False)
            ul = rd.value_labels().get(dict(zip(rd._varlist, rd._lbllist)).get("urban_rural")) or {}
        urb = df["urban_rural"].map(lambda x, ul=ul: 1.0 if re.search(r"(?i)urban", str(ul.get(x, ""))) else 0.0)
        wcol = f"wt_round{r}" if f"wt_round{r}" in df else None
        frames.append(_std(df, r, "hhid", _parse_dates(df["s10q10"]), df["clusterID"], urb, None, df[wcol] if wcol else None))
        log.append({"country": "TZA", "round": r, "file": Path(f).name, "items": items, "yes_no_codes": codes[7],
                    "date_var": "s10q10", "cluster_var": "clusterID", "weight_var": wcol})
    return pd.concat(frames, ignore_index=True)


LOADERS = {"BFA": load_bfa, "ETH": load_eth, "UGA": load_uga, "TZA": load_tza,
           "NGA2020": lambda d, log: _load_nga(d, log, "r", "NGA2020"),
           "NGA2021": lambda d, log: _load_nga(d, log, "p2r", "NGA2021")}


# ---------------------------------------------------------------- stage 1: structure
def _horizon_year(date: pd.Timestamp, start_month: int) -> int:
    return date.year if date.month >= start_month else date.year - 1


def structure(long: pd.DataFrame, spec: dict, rules: dict, first_round_2020: int | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for r, g in long.groupby("round"):
        d = g["date"].dropna()
        med = d.median() if len(d) else pd.NaT
        rows.append({"round": r, "records": len(g), "item7_nonmissing": int(g.it7.notna().sum()),
                     "dates_nonmissing": int(len(d)), "date_min": d.min(), "date_median": med, "date_max": d.max()})
    rounds = pd.DataFrame(rows).sort_values("date_median").reset_index(drop=True)
    rounds["horizon"] = [(_horizon_year(m, spec["horizon_start_month"]) if pd.notna(m) else None) for m in rounds.date_median]
    hz = []
    for h, g in rounds.dropna(subset=["horizon"]).groupby("horizon"):
        rs = list(g["round"])
        sub = long[long["round"].isin(rs)].pivot_table(index="hh", columns="round", values="it7", aggfunc="first")
        complete = int(sub.reindex(columns=rs).dropna().shape[0]) if len(rs) else 0
        usable = len(rs) >= rules["min_candidate_rounds"] and complete >= rules["min_complete_households"]
        hz.append({"horizon_start_year": int(h), "rounds": rs, "round_dates": [str(x.date()) for x in g.date_median],
                   "n_rounds": len(rs), "complete_households": complete, "usable": usable,
                   "pandemic_onset_flag": first_round_2020 in rs if first_round_2020 is not None else False})
    return rounds, pd.DataFrame(hz)


def _rule_index(dates: list[pd.Timestamp], spec: dict, zone: str | None = None) -> int | None:
    if zone is not None:
        months = spec["lean_months_by_zone"][zone]
        mid = spec["lean_midpoint_by_zone"][zone]
    else:
        months, mid = spec.get("lean_months"), spec.get("lean_midpoint")
    if not months:
        return None
    best, bestd = None, None
    for j, d in enumerate(dates):
        if d.month in months:
            m = pd.Timestamp(f"{d.year}-{mid}")
            dist = min(abs((d - m).days), abs((d - m.replace(year=d.year - 1)).days), abs((d - m.replace(year=d.year + 1)).days))
            if bestd is None or dist < bestd:
                best, bestd = j, dist
    return best


# ---------------------------------------------------------------- stage 2: hypotheses
def _cohort(long: pd.DataFrame, rounds: list[int], item: str = "it7") -> pd.DataFrame:
    sub = long[long["round"].isin(rounds)]
    mat = sub.pivot_table(index="hh", columns="round", values=item, aggfunc="first").reindex(columns=rounds)
    return mat


def _hh_attr(long: pd.DataFrame, rounds: list[int], col: str) -> pd.Series:
    sub = long[long["round"].isin(rounds)].sort_values("round")
    return sub.groupby("hh")[col].last()


def h1(long, country, spec, hrow, boot) -> dict | None:
    rs = hrow["rounds"]
    dates = [pd.Timestamp(x) for x in hrow["round_dates"]]
    mat = _cohort(long, rs).dropna()
    H = mat.to_numpy().astype(int)
    clusters = _hh_attr(long, rs, "cluster").reindex(mat.index).to_numpy()
    if "lean_months_by_zone" in spec:
        zone = _hh_attr(long, rs, "zone").reindex(mat.index)
        zkey = zone.map(lambda z: "north" if str(z) in spec["north_zones"] else ("south" if pd.notna(z) else None))
        idx = np.array([_rule_index(dates, spec, z) if z else None for z in zkey], dtype=object)
        if any(i is None for i in idx):
            return None
        rule_desc = "zone-specific"
    else:
        j = _rule_index(dates, spec)
        if j is None:
            return None
        idx = np.full(len(mat), j, dtype=object)
        rule_desc = f"R{rs[j]} ({dates[j].date()})"
    pos = (H.max(axis=1) > 0).astype(float)
    rmiss, _ = sm.household_terms(H, m=1)
    fmiss = pos * (H[np.arange(len(H)), idx.astype(int)] == 0)
    urb = _hh_attr(long, rs, "urban").reindex(mat.index).to_numpy()
    stats = {"rule": (fmiss, pos), "random": (rmiss, pos)}
    for name, msk in (("rural", urb == 0), ("urban", urb == 1)):
        stats[f"rule_{name}"] = (fmiss * msk, pos * msk)
        stats[f"random_{name}"] = (rmiss * msk, pos * msk)
    reps, zero = sm.ratio_bootstrap(clusters, stats, boot["draws"], boot["seed"])
    d = reps["rule"] - reps["random"]
    out = {"country": country, "horizon_start_year": hrow["horizon_start_year"], "rounds": rs,
           "round_dates": hrow["round_dates"], "rule_round": rule_desc, "n_complete": int(len(H)),
           "n_reference_positive": int(pos.sum()), "rule_missed": float(fmiss.sum() / pos.sum()),
           "random_missed": float(rmiss.sum() / pos.sum()),
           "diff": float((fmiss.sum() - rmiss.sum()) / pos.sum()),
           "diff_ci_low": sm.interval(d, boot["level"])[0], "diff_ci_high": sm.interval(d, boot["level"])[1],
           "clusters": int(np.unique(clusters).size), "zero_denominator_draws": zero["rule"],
           "pandemic_onset_flag": hrow["pandemic_onset_flag"]}
    # H4: rural minus urban in (rule - random)
    for name in ("rural", "urban"):
        msk = urb == (0 if name == "rural" else 1)
        p = pos[msk].sum()
        out[f"diff_{name}"] = float((fmiss[msk].sum() - rmiss[msk].sum()) / p) if p else np.nan
        out[f"n_reference_positive_{name}"] = int(p)
    g = (reps["rule_rural"] - reps["random_rural"]) - (reps["rule_urban"] - reps["random_urban"])
    out["rural_minus_urban"] = out["diff_rural"] - out["diff_urban"]
    out["rural_minus_urban_ci_low"], out["rural_minus_urban_ci_high"] = sm.interval(g, boot["level"])
    # weighted sensitivity (last round's cross-sectional weight; not a panel weight)
    w = long[long["round"] == rs[-1]].drop_duplicates("hh").set_index("hh")["weight"].reindex(mat.index).to_numpy()
    if np.isfinite(w).sum() == len(w) and len(w):
        out["weighted_diff"] = float((w * (fmiss - rmiss)).sum() / (w * pos).sum())
    else:
        out["weighted_diff"] = np.nan
    # exact missing-data range and tipping point (national rules only)
    if rule_desc != "zone-specific":
        j = int(idx[0])
        frame = _cohort(long, rs)
        frame = frame[frame.notna().any(axis=1)]
        HF = frame.fillna(-1).astype(int).to_numpy()
        c = hb.fixed_minus_random([j], len(rs), 1)
        b = hb.contrast_bounds(HF, c, 0)
        out.update({"frame_households": int(len(HF)), "range_low": float(b["lower"].value), "range_high": float(b["upper"].value),
                    "tipping_flips": hb.tipping_budget(HF, c, "max", Fraction(0)), "observed_screens": int((HF >= 0).sum())})
    return out


def _circ_days(a: pd.Timestamp, b: pd.Timestamp) -> int:
    x = abs(a.day_of_year - b.day_of_year)
    return min(x, 365 - x)


def h2(long, country, spec, hz, maxd, boot) -> list[dict]:
    rows = []
    usable = hz[hz.usable].sort_values("horizon_start_year")
    for _, tr in usable.iterrows():
        for _, te in usable[usable.horizon_start_year > tr.horizon_start_year].iterrows():
            trm = _cohort(long, tr.rounds).dropna()
            T = trm.to_numpy().astype(int)
            tdates = [pd.Timestamp(x) for x in tr.round_dates]
            sel, miss = select_candidate(T, list(range(len(tr.rounds))))
            edates = [pd.Timestamp(x) for x in te.round_dates]
            dist = [_circ_days(tdates[sel], e) for e in edates]
            k = int(np.argmin(dist))
            row = {"country": country, "train_horizon": tr.horizon_start_year, "test_horizon": te.horizon_start_year,
                   "train_selected_round": tr.rounds[sel], "train_selected_date": tr.round_dates[sel],
                   "train_selected_missed": miss[sel], "train_pandemic_onset_flag": tr.pandemic_onset_flag}
            # selection stability (cluster bootstrap of training data)
            cl = _hh_attr(long, tr.rounds, "cluster").reindex(trm.index).to_numpy()
            uniq = np.unique(cl)
            groups = {u: np.flatnonzero(cl == u) for u in uniq}
            rng = np.random.default_rng(boot["seed"] + 1)
            same = 0
            for _ in range(boot["draws"]):
                ix = np.concatenate([groups[u] for u in rng.choice(uniq, size=uniq.size, replace=True)])
                same += select_candidate(T[ix], list(range(len(tr.rounds))))[0] == sel
            row["selection_stability"] = same / boot["draws"]
            if dist[k] > maxd:
                row.update({"testable": False, "note": f"no test round within {maxd} days (closest {dist[k]})"})
                rows.append(row)
                continue
            tem = _cohort(long, te.rounds).dropna()
            E = tem.to_numpy().astype(int)
            pos = (E.max(axis=1) > 0).astype(float)
            fmiss = pos * (E[:, k] == 0)
            rmiss, _ = sm.household_terms(E, m=1)
            stats = {"frozen": (fmiss, pos), "random": (rmiss, pos)}
            rj = _rule_index(edates, spec) if spec.get("lean_months") else None
            if rj is not None:
                stats["rule"] = (pos * (E[:, rj] == 0), pos)
            clu = _hh_attr(long, te.rounds, "cluster").reindex(tem.index).to_numpy()
            reps, _ = sm.ratio_bootstrap(clu, stats, boot["draws"], boot["seed"])
            dd = reps["frozen"] - reps["random"]
            row.update({"testable": True, "test_round": te.rounds[k], "test_date": te.round_dates[k], "day_distance": dist[k],
                        "n_test_complete": len(E), "n_test_reference_positive": int(pos.sum()),
                        "frozen_missed": float(fmiss.sum() / pos.sum()), "random_missed": float(rmiss.sum() / pos.sum()),
                        "frozen_minus_random": float((fmiss.sum() - rmiss.sum()) / pos.sum()),
                        "ci_low": sm.interval(dd, boot["level"])[0], "ci_high": sm.interval(dd, boot["level"])[1]})
            if rj is not None:
                rm = stats["rule"][0]
                row["rule_round"] = te.rounds[rj]
                row["frozen_minus_rule"] = float((fmiss.sum() - rm.sum()) / pos.sum())
                row["frozen_minus_rule_ci_low"], row["frozen_minus_rule_ci_high"] = sm.interval(reps["frozen"] - reps["rule"], boot["level"])
            rows.append(row)
    return rows


def h3(long, country, hrow, boot) -> dict:
    rs = hrow["rounds"]
    mat = _cohort(long, rs).dropna()
    first = long[long["round"] == rs[0]].drop_duplicates("hh").set_index("hh")
    mild = first[[f"it{k}" for k in range(1, 7)]].reindex(mat.index)
    keep = mild.notna().all(axis=1).to_numpy()
    H = mat.to_numpy().astype(int)[keep]
    warning = (mild.to_numpy()[keep] == 1).any(axis=1)
    cl = _hh_attr(long, rs, "cluster").reindex(mat.index).to_numpy()[keep]
    res = second_contact(H[:, 0], H[:, 1:], warning, np.zeros(len(H)), cl, boot, f"{country} {hrow['horizon_start_year']}")
    r = res.set_index("rule")
    w = r.loc[r.index.str.startswith("warning")].iloc[0]
    rnd = r.loc[r.index.str.startswith("random")].iloc[0]
    return {"country": country, "horizon_start_year": hrow["horizon_start_year"], "first_round": rs[0],
            "first_contact_negatives": int(w.first_contact_negatives), "recontact_budget": int(w.recontact_budget_households),
            "warning_per_100": float(w.captured_per_100_recontacted), "random_per_100": float(rnd.captured_per_100_recontacted),
            "difference": float(w.captured_per_100_recontacted - rnd.captured_per_100_recontacted),
            "ci_low": float(w.warning_minus_random_per_100_ci_low), "ci_high": float(w.warning_minus_random_per_100_ci_high)}


def _decide_h1(df: pd.DataFrame) -> str:
    if df.empty:
        return "untestable"
    n = len(df)
    neg = (df["diff"] < 0).sum()
    pos_ci = (df["diff_ci_low"] > 0).sum()
    if (df["diff"] > 0).sum() > n / 2 or pos_ci >= 2:
        return "contradicted"
    if neg >= 2 * n / 3 and pos_ci == 0:
        return "supported"
    return "mixed"


def run(paths: Paths | None = None) -> dict:
    paths = paths or Paths()
    proto = yaml.safe_load(open(paths.root / "config" / "multicountry_protocol.yaml", encoding="utf-8"))
    raw = paths.root / "data" / "raw" / "multicountry"
    out = paths.public / "multicountry"
    out.mkdir(parents=True, exist_ok=True)
    boot = proto["bootstrap"]
    summary = {"generated_utc": utc_now(), "protocol_sha256": sha256_file(paths.root / "reports" / "investigation" / "10_LOCKED_PROTOCOL_MULTICOUNTRY_HFPS.md"),
               "archives": {}}
    struct_rows, hz_rows, h1_rows, h2_rows, h3_rows, mapping = [], [], [], [], [], []
    for c, spec in proto["countries"].items():
        zips = list((raw / c).glob("*.zip"))
        summary["archives"][c] = {z.name: {"sha256": sha256_file(z), "bytes": z.stat().st_size} for z in zips}
        log: list = []
        long = LOADERS[c](raw / c / "extracted", log)
        mapping += [{**m, "items": json.dumps(m["items"]), "yes_no_codes": json.dumps({str(k): v for k, v in m["yes_no_codes"].items()})} for m in log]
        if long.empty:
            hz_rows.append({"country": c, "note": "no food-security round with item 7"})
            continue
        long = long.dropna(subset=["hh"])
        dup = int(long.duplicated(["hh", "round"]).sum())
        long = long.drop_duplicates(["hh", "round"], keep="first")
        # protocol: the country's first 2020 survey round (round 1 of panels that began in 2020), whether or
        # not it carried the food-security module
        first_round_2020 = 1 if spec["idno"].split("_")[1].startswith("2020") else None
        rounds, hz = structure(long, spec, proto["usable_horizon"], first_round_2020)
        rounds.insert(0, "country", c)
        rounds["duplicate_household_rounds_dropped"] = dup
        struct_rows.append(rounds)
        hz.insert(0, "country", c)
        hz["calendar_rule_testable"] = [spec.get("h1", False) and u and (
            _rule_index([pd.Timestamp(x) for x in d], spec) is not None if "lean_months" in spec else True)
            for u, d in zip(hz.usable, hz.round_dates)]
        hz_rows.append(hz)
        for _, hr in hz[hz.usable].iterrows():
            if spec.get("h1"):
                r = h1(long, c, spec, hr, boot)
                if r is not None:
                    h1_rows.append({**r, "analysis": "primary (locked rules)"})
            h3_rows.append({**h3(long, c, hr, boot), "analysis": "primary (locked rules)"})
        h2_rows += h2(long, c, spec, hz, proto["transfer"]["max_circular_day_distance"], boot)
        # Deviation D2 (sensitivity only): split-sample horizons with no household observed at every
        # round are re-formed as one panel per response pattern (sample group) with >= 3 rounds.
        for _, hr in hz[(hz.complete_households < proto["usable_horizon"]["min_complete_households"])].iterrows():
            sub = _cohort(long, hr.rounds)
            pattern = sub.notna().apply(lambda row, rs=hr.rounds: tuple(r for r, ok in zip(rs, row) if ok), axis=1)
            for pat, n in pattern.value_counts().items():
                if len(pat) < proto["usable_horizon"]["min_candidate_rounds"] or n < proto["usable_horizon"]["min_complete_households"]:
                    continue
                dates = [d for r, d in zip(hr.rounds, hr.round_dates) if r in pat]
                g = {"horizon_start_year": hr.horizon_start_year, "rounds": list(pat), "round_dates": dates,
                     "pandemic_onset_flag": hr.pandemic_onset_flag}
                gl = long[long.hh.isin(pattern.index[pattern == pat])]
                hz_rows.append(pd.DataFrame([{"country": c, **g, "n_rounds": len(pat), "complete_households": int(n),
                                              "usable": True, "deviation": "D2 sample-group panel"}]))
                if spec.get("h1"):
                    r = h1(gl, c, spec, pd.Series(g), boot)
                    if r is not None:
                        h1_rows.append({**r, "analysis": "deviation D2: sample-group panel"})
                h3_rows.append({**h3(gl, c, pd.Series(g), boot), "analysis": "deviation D2: sample-group panel"})
    pd.DataFrame(mapping).to_csv(out / "item_mapping_and_sources.csv", index=False)
    pd.concat(struct_rows).to_csv(out / "rounds_structure.csv", index=False)
    hzdf = pd.concat([h if isinstance(h, pd.DataFrame) else pd.DataFrame([h]) for h in hz_rows], ignore_index=True)
    hzdf.to_csv(out / "horizons.csv", index=False)
    h1df = pd.DataFrame(h1_rows)
    h1df.to_csv(out / "h1_calendar_rule.csv", index=False)
    pd.DataFrame(h2_rows).to_csv(out / "h2_transfer.csv", index=False)
    h3df = pd.DataFrame(h3_rows)
    h3df.to_csv(out / "h3_second_contact.csv", index=False)
    for tag, sel in (("primary", "primary"), ("with_D2", None)):
        a = h1df if sel is None or h1df.empty else h1df[h1df.analysis.str.startswith(sel)]
        b = h3df if sel is None or h3df.empty else h3df[h3df.analysis.str.startswith(sel)]
        b = b[b["difference"].notna()]  # horizons whose first round lacks FIES items 1-6 are untestable for H3
        summary[f"h1_decision_{tag}"] = _decide_h1(a)
        summary[f"h1_testable_horizons_{tag}"] = int(len(a))
        summary[f"h3_positive_share_{tag}"] = float((b["difference"] > 0).mean()) if len(b) else None
        summary[f"h3_decision_{tag}"] = ("supported" if (b["difference"] > 0).mean() >= 2 / 3 else "not supported") if len(b) else "untestable"
    with open(out / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)
    return summary
