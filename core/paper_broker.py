# core/paper_broker.py

import csv
import os
from datetime import datetime

class PaperBroker:
    def __init__(self, initial_balance=10000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = None  # {symbol, qty, entry_price, sl, tp}
        self.trades = []
        self.open_orders = []  # pending limit orders
        self.log_path = "paper_trades.csv"

        # Create file with headers if it doesn't exist
        if not os.path.exists(self.log_path):
            with open(self.log_path, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "side", "symbol", "qty", "price", "balance"])

    def buy(self, symbol, qty, price, sl=None, tp=None, timestamp=None):
        cost = qty * price
        if self.balance < cost:
            return f"❌ Insufficient balance to buy {qty} {symbol} at ${price:.2f}"

        self.position = {
            'symbol': symbol,
            'qty': qty,
            'entry_price': price,
            'stop_loss': sl,
            'take_profit': tp
        }
        self.balance -= cost
        self._log_trade('buy', symbol, qty, price, timestamp)
        return f"✅ Bought {qty} {symbol} at ${price:.2f}"

    def sell(self, symbol, price, timestamp=None):
        if not self.position or self.position['symbol'] != symbol:
            return f"❌ No open position in {symbol} to sell"

        qty = self.position['qty']
        proceeds = qty * price
        self.balance += proceeds
        self._log_trade('sell', symbol, qty, price, timestamp)
        self.position = None
        return f"✅ Sold {qty} {symbol} at ${price:.2f}"

    def place_limit_order(self, symbol, qty, limit_price, side):
        self.open_orders.append({
            'symbol': symbol,
            'qty': qty,
            'limit_price': limit_price,
            'side': side,
            'status': 'open',
            'timestamp': datetime.utcnow().isoformat()
        })
        return f"✅ Placed {side.upper()} LIMIT order for {qty} {symbol} at ${limit_price:.2f}"

    def check_orders(self, current_price):
        executed = []
        for order in self.open_orders:
            if order['status'] == 'open':
                if order['side'] == 'buy' and current_price <= order['limit_price']:
                    executed.append(self.buy(order['symbol'], order['qty'], current_price))
                    order['status'] = 'filled'
                elif order['side'] == 'sell' and current_price >= order['limit_price']:
                    executed.append(self.sell(order['symbol'], current_price))
                    order['status'] = 'filled'
        return executed

    def check_stop_loss_take_profit(self, current_price, timestamp=None):
        if not self.position:
            return None

        sl = self.position.get('stop_loss')
        tp = self.position.get('take_profit')
        entry = self.position['entry_price']
        symbol = self.position['symbol']

        if sl and current_price <= sl:
            return self.sell(symbol, current_price, timestamp=timestamp) + f" (SL hit at ${sl})"
        elif tp and current_price >= tp:
            return self.sell(symbol, current_price, timestamp=timestamp) + f" (TP hit at ${tp})"
        return None

    def _log_trade(self, side, symbol, qty, price, timestamp=None):
        trade = {
            'timestamp': timestamp or datetime.utcnow().isoformat(),
            'side': side,
            'symbol': symbol,
            'qty': qty,
            'price': price,
            'balance': self.balance
        }
        self.trades.append(trade)
        self.log_to_csv(trade)

    def log_to_csv(self, trade):
        with open(self.log_path, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                trade["timestamp"],
                trade["side"],
                trade["symbol"],
                trade["qty"],
                trade["price"],
                trade["balance"]
            ])

    def get_open_position(self):
        return self.position

    def get_trade_log(self):
        return self.trades

    def get_balance(self):
        return self.balance

    def get_unrealized_pnl(self, current_price):
        if not self.position:
            return 0.0
        entry = self.position['entry_price']
        qty = self.position['qty']
        return (current_price - entry) * qty

    def get_open_orders(self):
        return self.open_orders
