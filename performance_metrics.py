# performance_metrics.py
import pandas as pd


def compute_performance_metrics(trades_df, initial_balance, final_balance):
    if trades_df.empty:
        return {
            "PnL": 0,
            "Return %": 0,
            "Total Trades": 0,
            "Win Rate %": 0,
            "Avg Win": 0,
            "Avg Loss": 0,
            "Max Drawdown %": 0,
        }

    trades_df = trades_df.copy()
    trades_df["timestamp"] = pd.to_datetime(trades_df["timestamp"])
    trades_df.sort_values("timestamp", inplace=True)

    # Track equity
    equity = [initial_balance]
    position = 0
    entry_price = 0
    max_equity = initial_balance
    drawdowns = []
    results = []

    for _, row in trades_df.iterrows():
        if "BUY" in row["action"]:
            entry_price = row["price"]
            position = equity[-1] / entry_price
            equity.append(0)
        else:
            exit_price = row["price"]
            value = position * exit_price
            pnl = value - initial_balance
            results.append(pnl)
            equity.append(value)
            position = 0

            max_equity = max(max_equity, value)
            dd = (max_equity - value) / max_equity
            drawdowns.append(dd)

    wins = [r for r in results if r > 0]
    losses = [r for r in results if r <= 0]

    return {
        "PnL": round(final_balance - initial_balance, 2),
        "Return %": round(100 * (final_balance - initial_balance) / initial_balance, 2),
        "Total Trades": len(results),
        "Win Rate %": round(100 * len(wins) / len(results), 2) if results else 0,
        "Avg Win": round(sum(wins) / len(wins), 2) if wins else 0,
        "Avg Loss": round(sum(losses) / len(losses), 2) if losses else 0,
        "Max Drawdown %": round(100 * max(drawdowns), 2) if drawdowns else 0,
    }
