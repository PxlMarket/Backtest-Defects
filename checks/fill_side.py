"""Check a trade log for two engine defects that inflate backtests.

1. Fills on the wrong side of their own stop (a long filled below its stop, a short above it).
   A broker rejects these orders. A backtest that trades them usually books an instant "stop-out"
   at a better price than the fill, which is a guaranteed winner that cannot exist.
2. Stops touched inside the entry bar but ignored because the engine only checks exits from the
   next bar onwards.

Needed columns: side ("long"/"short"), entry_price, stop_price, entry_bar_low, entry_bar_high, pnl

Usage:
    python checks/fill_side.py your_trades.csv
"""
import sys

import pandas as pd


def check(t: pd.DataFrame) -> dict:
    long = t["side"].str.lower() == "long"
    wrong_side = (long & (t.entry_price <= t.stop_price)) | (~long & (t.entry_price >= t.stop_price))
    stopped_in_bar = (long & (t.entry_bar_low <= t.stop_price)) | (~long & (t.entry_bar_high >= t.stop_price))
    return {
        "trades": len(t),
        "wrong_side": int(wrong_side.sum()),
        "wrong_side_pnl": float(t.pnl[wrong_side].sum()),
        "total_pnl": float(t.pnl.sum()),
        "stopped_in_entry_bar": int(stopped_in_bar.sum()),
        "by_cohort": t.groupby(wrong_side.rename("wrong_side")).pnl.agg(["count", "sum", "mean"]),
    }


def main(path: str) -> None:
    r = check(pd.read_csv(path))
    print(r["by_cohort"], "\n")
    print(f"{r['wrong_side']} of {r['trades']} trades were filled on the wrong side of their stop.")
    if r["total_pnl"]:
        print(f"They made {r['wrong_side_pnl']:.2f} of {r['total_pnl']:.2f} total pnl.")
    print(f"{r['stopped_in_entry_bar']} trades touched their stop inside the entry bar.")
    print("\nIf you fill at the bar's OPEN, entry-bar touches are real stops. If you fill at the CLOSE,")
    print("the touch may have come before your entry; bar data can't tell you, so assume it hit.")


if __name__ == "__main__":
    main(sys.argv[1])
