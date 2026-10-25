# Backtest defects: real bugs from a real system

I built an automated intraday breakout system for US index CFDs and spent months auditing it. These
are defects I found in my own backtest engine, with the before and after numbers. The strategy code
stays private; the bugs were in the engine, not the strategy, so none of that is needed to show them.

Every check here can be run on your own trade log.

## Case 1: half the profit came from trades that can't exist

The largest session-close winner on one instrument was a long that closed at **13.8 times its
configured target**.
Its stop was 0.3 points *above* its own fill.

The engine filled at the next bar's open after a signal. When price reversed between the signal and
the fill, that open could land past the stop: a long whose stop sits above its entry. A broker
rejects that order, and the live code refused those days. The backtest traded them anyway.

On one instrument it opened **49** of them, and they were the most profitable group in the whole
dataset: **+£7,001 of the strategy's £14,766 total net profit.** 40 of the 49 exited through the
stop branch, because a stop above a long's fill is a stop-out at a profit.

A second defect sat next to it: **the entry bar was never checked against the stop.** The position
was created at the end of the loop for bar *i*, and exits were only checked from bar *i+1*. Any stop
hit inside the fill bar was ignored. **93 trades** affected.

A third: the WIN/LOSS label came from which code branch fired, not from the P&L, so 40 trades were
labelled LOSS while showing a profit. Any stat grouped on that label was wrong.

| | profit factor |
|---|---|
| Original engine | 1.534 |
| After fixing the three defects above | 1.096 |

My prediction before running the fix was 1.282, from removing the wrong-side trades alone. I'd
assumed the entry-bar check would "barely move PF". It was most of the damage. Guessing a magnitude
before measuring it is how the original number got published.

A second instrument on the same engine went from **1.344 to 0.812**.

## Case 2: a bug that made the backtest look worse

The take-profit was built from a price 15 minutes before the fill, while position size and R were
measured from the fill. A configured target landed anywhere from **0.007x to 6.3x** its intended
distance.

This one **suppressed** results by cashing winners out early. Fixing it moved profit factor back up
from **1.096 to 1.202**.

Two lessons from this pair:
- **A defect can cut either way.** A backtest that looks bad isn't proof the engine is right.
- **The corrected strategy still failed** my pre-set bar (PF 1.25). Fixing the engine didn't rescue
  it, and that's the point: the number you trade on has to come from an engine you've checked.

## Run the check on your own trades

Your trade log needs: `side`, `entry_price`, `stop_price`, `entry_bar_low`, `entry_bar_high`, `pnl`.

```
pip install pandas
python checks/fill_side.py your_trades.csv
```

Try it on the sample first (8 trades, 4 with planted defects):

```
python checks/fill_side.py demo/sample_trades.csv
python tests/test_fill_side.py
```

How to read the output:
- Any wrong-side trades at all means the engine trades orders a broker would reject.
- Entry-bar touches are a flag, not a verdict. If you fill at the bar's open, they're real stops. If
  you fill at the close, the touch may have come before your entry. Bar data can't tell you the
  order, so the honest default is to assume the stop hit.

## More to come

Lookahead leaks that profit factor can't detect, costs that drift across a decade of data,
statistics that pass until you cluster trades by day. Each gets its own case and check.
