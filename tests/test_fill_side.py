"""Run with: python tests/test_fill_side.py   (no pytest needed)"""
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "checks"))
from fill_side import check  # noqa: E402


def test_sample_finds_planted_defects():
    r = check(pd.read_csv(ROOT / "demo" / "sample_trades.csv"))
    assert r["trades"] == 8
    assert r["wrong_side"] == 2
    # the two wrong-side trades also touch their stop in the entry bar, so 2 + 2 planted
    assert r["stopped_in_entry_bar"] == 4
    assert r["wrong_side_pnl"] == 2.0


def test_clean_log_is_clean():
    t = pd.read_csv(ROOT / "demo" / "sample_trades.csv").head(4)
    r = check(t)
    assert r["wrong_side"] == 0 and r["stopped_in_entry_bar"] == 0


def test_side_is_case_insensitive():
    t = pd.read_csv(ROOT / "demo" / "sample_trades.csv")
    t["side"] = t["side"].str.upper()
    assert check(t)["wrong_side"] == 2


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("pass", name)
