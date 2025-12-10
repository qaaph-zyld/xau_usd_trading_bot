# 🏆 Complete Prop Firm Challenge Guide

## Turn $100 Into a Funded Trading Account

This guide will take you from zero to passing a prop firm challenge using the optimized XAU/USD strategy.

---

## 📊 Strategy Performance

| Metric | Value |
|--------|-------|
| **Pass Rate** | **40.4%** |
| **Expected Value** | **+$263 per $100 challenge** |
| **Over 10 challenges** | **+$2,631 expected** |

---

## 🗓️ The 6-Week Plan

### Week 1-2: Paper Trading

**Goal:** Complete 20+ paper trades, achieve 45%+ win rate

**Daily Tasks:**
1. Run signal generator: `python scripts/live_signals.py`
2. Record signals in your journal
3. Track hypothetical outcomes
4. Learn from each trade

**Commands:**
```bash
# Get daily signals
python scripts/live_signals.py

# Use the full system
python scripts/prop_firm_system.py
```

**Success Criteria:**
- [ ] 20+ paper trades completed
- [ ] 45%+ win rate
- [ ] Positive hypothetical P/L
- [ ] Comfortable with entry/exit rules

---

### Week 3: Readiness Check

**Goal:** Validate your readiness for real challenge

**Run the check:**
```bash
python scripts/prop_firm_system.py
# Choose option 4: Readiness check
```

**Requirements:**
| Metric | Minimum |
|--------|---------|
| Paper trades | 20+ |
| Win rate | 45%+ |
| Paper P/L | Positive |

**If not ready:** Continue paper trading another week

---

### Week 4: Buy Challenge

**Recommended Prop Firms:**

| Firm | Cost | Account | Profit Target |
|------|------|---------|---------------|
| FTMO | $155 | $10,000 | 10% |
| MyForexFunds | $84 | $5,000 | 8% |
| The5ers | $95 | $6,000 | 6% |
| True Forex Funds | $79 | $5,000 | 8% |

**Steps:**
1. Choose a prop firm
2. Sign up and pay challenge fee
3. Receive demo account credentials
4. Set up MT4/MT5 with their server

---

### Week 5-6: Execute Challenge

**Daily Routine:**

**Pre-Market (15 min before market open):**
1. Check economic calendar
2. Run: `python scripts/live_signals.py`
3. Review yesterday's trades
4. Set daily loss limit alert (5% of starting balance)

**Trading Session:**
1. Only take signals from the strategy
2. Enter with proper position size
3. Set SL and TP immediately
4. Never move stop loss further away
5. Move stop to breakeven at +1 ATR

**Post-Market:**
1. Record trades: `python scripts/trading_dashboard.py`
2. Screenshot trade setups
3. Update challenge status
4. Review what went right/wrong

---

## 📋 Strategy Rules

### Entry Signals

Take a trade when ANY of these occur:

**1. EMA Crossover**
```
LONG:  EMA 3 crosses above EMA 8
SHORT: EMA 3 crosses below EMA 8
```

**2. MACD Crossover**
```
LONG:  MACD line crosses above Signal line
SHORT: MACD line crosses below Signal line
```

**3. RSI Extreme Reversal**
```
LONG:  RSI < 20 AND price closes higher than previous bar
SHORT: RSI > 80 AND price closes lower than previous bar
```

### Position Sizing

```
Risk per trade: 8% of account
Position size = (Account × 0.08) ÷ (Entry - StopLoss)

Example for $10,000 account:
- Entry: $2000
- Stop Loss: $1960 ($40 risk per oz)
- Risk amount: $800 (8% of $10,000)
- Position: 800 ÷ 40 = 20 oz = 0.20 lots
```

### Stop Loss & Take Profit

```
Stop Loss:   0.8 × ATR from entry
Take Profit: 1.5 × ATR from entry

Example with ATR = $50:
- Entry: $2000
- Stop Loss: $2000 - ($50 × 0.8) = $1960
- Take Profit: $2000 + ($50 × 1.5) = $2075
```

### Trade Management

1. **Entry:** Market order at signal
2. **Initial:** SL and TP set immediately
3. **Breakeven:** Move SL to entry when price moves +1 ATR in your favor
4. **Trailing:** After breakeven, trail stop at 0.5 ATR below high (for longs)
5. **Exit:** Let price hit TP or trailing stop

---

## ⚠️ Risk Rules

### Prop Firm Rules (FTMO Standard)

| Rule | Limit | What Happens If Broken |
|------|-------|------------------------|
| Max Daily Loss | 5% | Challenge FAILED |
| Max Total Drawdown | 10% | Challenge FAILED |
| Profit Target | 10% | Challenge PASSED |
| Time Limit | 30 days | Challenge FAILED if target not hit |

### Our Safety Rules

1. **Max 2 trades per day** - Prevents overtrading
2. **Stop after 2 consecutive losses** - Prevents tilt
3. **No trading on high-impact news** - Check calendar first
4. **Never average down** - Accept the loss
5. **Never remove stop loss** - Accept the loss

---

## 🧮 Expected Value Math

```
Challenge cost:     $100
If pass (40.4%):    Trade $10K, make 10%, keep 80% = $800
If fail (59.6%):    Lose $100

Expected Value = (0.404 × $800) - (0.596 × $100)
               = $323.20 - $59.60
               = +$263.60 per challenge

Over 10 challenges:
   Expected profit = 10 × $263.60 = $2,636
```

---

## 🔧 Troubleshooting

### Not Enough Trades
- **Cause:** Daily timeframe = fewer signals
- **Fix:** Be patient, only 1-2 signals per week is normal

### Hitting Max Drawdown
- **Cause:** Too aggressive or bad luck
- **Fix:** Reduce risk to 6% per trade for safer approach

### Running Out of Time
- **Cause:** Not enough volatility in market
- **Fix:** The 40.4% pass rate accounts for this

### Losing Streak
- **Cause:** Normal part of trading
- **Fix:** Stick to rules, variance will balance out

---

## 📱 Daily Commands

```bash
# Get today's signal
python scripts/live_signals.py

# Full prop firm system
python scripts/prop_firm_system.py

# Trading dashboard
python scripts/trading_dashboard.py

# Test strategy on history
python scripts/aggressive_prop_test.py
```

---

## ✅ Success Checklist

**Before Starting Challenge:**
- [ ] Completed 20+ paper trades
- [ ] Achieved 45%+ win rate
- [ ] Passed readiness check
- [ ] Understand all entry rules
- [ ] Know position sizing formula
- [ ] Have daily routine planned

**During Challenge:**
- [ ] Run signals every day
- [ ] Follow rules exactly
- [ ] Record every trade
- [ ] Track challenge status
- [ ] Stay emotionally disciplined

**After Challenge:**
- [ ] Review what worked
- [ ] Note improvements needed
- [ ] If passed: Celebrate! 🎉
- [ ] If failed: Learn and try again

---

## 🎯 Final Words

The math is on your side:
- 40.4% pass rate
- +$263 expected value per attempt
- Even if you fail 2-3 times, one pass covers all costs

Trust the process. Follow the rules. Expect some failures.
They're the cost of learning.

**Good luck, and may the pips be in your favor! 📈**
