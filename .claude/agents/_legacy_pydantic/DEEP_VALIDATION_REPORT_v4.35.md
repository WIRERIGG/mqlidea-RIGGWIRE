# RIGGWIRE EA v4.35 - Deep Validation Report

**Date**: 2026-02-09
**Validated by**: Awareness Orchestrator (Analysis + Architecture + Validation agents)
**Target Files**: 9 MQL5 source files in `RIGGWIRE-EA-FTMO/`
**Scope**: Logical errors, performance, runtime safety, MT5-specific issues, v4.34-4.35 regression

---

## EXECUTIVE SUMMARY

| Severity | Count | Production Blockers |
|----------|-------|-------------------|
| CRITICAL | 3     | 2 (C-1, C-2)     |
| HIGH     | 7     | 0                 |
| MEDIUM   | 8     | 0                 |
| LOW      | 5     | 0                 |
| **TOTAL**| **23**|                   |

**Overall Assessment**: v4.35 has 2 CRITICAL production blockers and 7 HIGH issues that should be addressed before live deployment. The v4.34-4.35 changes (array compaction, fast profit locking, input validation) are structurally correct but introduced 1 new CRITICAL and 2 new HIGH issues.

---

## CRITICAL FINDINGS (Production Blockers)

### C-1: FastProfitLocker profit_pct ignores trade direction (WRONG CALCULATION)

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\FastProfitLocker.mqh`
**Lines**: 213-214

```mql5
double price_change = MathAbs(current_price - open_price);
double profit_pct = (price_change / open_price) * 100.0;
```

**Root Cause**: `MathAbs()` makes profit_pct ALWAYS positive regardless of whether the trade is winning or losing. A SHORT trade that moves UP (a loss) will report a positive profit_pct equal to the absolute price movement.

**Impact**: FastProfitLocker will trigger breakeven locks on LOSING short positions. When a short position drops 0.5% in value (price rises 0.5%), the code calculates `profit_pct = 0.5` and triggers `ShouldTriggerFastLock()`, which moves SL to breakeven+buffer on a losing trade. This either:
1. Locks in a loss if the SL is above the entry (for shorts)
2. Creates an invalid SL modification (SL on wrong side of entry)

The `ApplyFastProfitLock()` function does check position direction for SL placement (line 130-157), but `ShouldTriggerFastLock()` uses the unsigned profit_pct to decide WHETHER to lock, meaning it fires on losses.

**Recommended Fix**:
```mql5
// Replace lines 207-214 in ProcessFastProfitLocks()
double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
double current_price = PositionGetDouble(POSITION_PRICE_CURRENT);
bool is_buy = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY);

// Direction-aware profit calculation
double price_change;
if (is_buy)
    price_change = current_price - open_price;   // Positive when winning
else
    price_change = open_price - current_price;    // Positive when winning

double profit_pct = (price_change / open_price) * 100.0;

// Only track and check when actually profitable
if (profit_pct <= 0) continue;
```

---

### C-2: g_velocity_tracker array has NO size cap (unbounded growth)

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\FastProfitLocker.mqh`
**Lines**: 47-48

```mql5
index = ArraySize(g_velocity_tracker);
ArrayResize(g_velocity_tracker, index + 1);
```

**Root Cause**: Unlike `g_active_dual_orders` (capped at 100), `g_exit_tracking` (capped at 1000), and `g_crossover_cache` (capped at 100), the `g_velocity_tracker` array grows without any size limit. Every new position adds an entry, and cleanup only runs when `CleanupVelocityTracker()` is called.

**Impact**: During extended running (multi-week FTMO challenges with many trades), the array can grow unbounded. `FindVelocityIndex()` performs O(n) linear search on every tick for every open position, degrading to O(n*m) per tick where n = tracker size and m = open positions. With 500+ entries and 3 positions, this becomes measurable latency in OnTick().

**Recommended Fix**:
```mql5
// Add constant after line 49 in DualOrderManager.mqh style
const int MAX_VELOCITY_ENTRIES = 200;  // Cap tracker size

// In TrackTradeVelocity(), before ArrayResize:
if (index == -1)
{
    int current_size = ArraySize(g_velocity_tracker);
    if (current_size >= MAX_VELOCITY_ENTRIES)
    {
        Print("[Fast Profit Lock] WARNING: Tracker full (", current_size,
              "/", MAX_VELOCITY_ENTRIES, ") - forcing cleanup");
        CleanupVelocityTracker();
        current_size = ArraySize(g_velocity_tracker);
        if (current_size >= MAX_VELOCITY_ENTRIES)
        {
            Print("[Fast Profit Lock] ERROR: Still full after cleanup - skipping");
            return;
        }
    }
    // ... existing ArrayResize code ...
}
```

---

### C-3: PositionManagement division by zero when atr == 0 in separation_atr_ratio

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\PositionManagement.mqh`
**Line**: 586

```mql5
double separation_atr_ratio = st_separation / atr;
```

**Root Cause**: While `atr` is initialized to 0.0015 and falls back to `last_good_atr`, the fallback value `last_good_atr` starts at 0.0015 (line 423). However, if the first-ever ATR read returns exactly 0.0 (which passes `atr <= 0` check on line 570 and uses `last_good_atr`), and `last_good_atr` was never updated from its default, the calculation is safe. BUT: the `atr` variable on line 554 is initialized to `0.0015` which is later overwritten. If `SafeCopyBuffer` succeeds but returns `atr_buffer[0] == 0.0` (not <= 0, not EMPTY_VALUE - e.g., ATR during zero-volume bars), line 570-571 does NOT catch it (condition is `atr <= 0`, and 0.0 IS <= 0, so it IS caught). After re-analysis, this is protected for exact zero but NOT for very small ATR values like 0.0000001 that would produce extremely large ratios.

**Impact**: While exact division by zero is protected, extremely small ATR values (possible during very low volatility or data gaps) could produce separation_atr_ratio values of 10000+, causing Phase 4 ultra-aggressive trailing on every position regardless of actual conditions. This is a logic error rather than a crash.

**Severity Downgrade**: CRITICAL -> HIGH after analysis. The exact zero case is handled. Reclassifying as H-1.

---

## HIGH FINDINGS

### H-1: Extremely small ATR causes incorrect phase selection

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\PositionManagement.mqh`
**Line**: 586

(Reclassified from C-3 above)

```mql5
double separation_atr_ratio = st_separation / atr;
```

**Root Cause**: ATR values like 0.00001 (possible during Asian session on low-volatility pairs) would produce separation_atr_ratio of 15000+, always triggering Phase 4 ultra-aggressive trailing.

**Impact**: Premature tightening of stops in low-volatility conditions, leading to unnecessary stop-outs.

**Recommended Fix**:
```mql5
// After line 586:
double separation_atr_ratio = (atr > 0.0001) ? (st_separation / atr) : 1.0;
```

---

### H-2: g_managed_positions array has NO size cap

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\StrategyManager.mqh`
**Lines**: 775-776

```mql5
int size = ArraySize(g_managed_positions);
ArrayResize(g_managed_positions, size + 1);
```

**Root Cause**: `RegisterPosition()` grows the array without any limit check. While `CleanupManagedPositions()` runs periodically, in extreme scenarios (rapid automated trading, position churn), the array can grow faster than cleanup runs.

**Impact**: Same unbounded growth pattern as C-2. The `ManageAllPositions()` function iterates `PositionsTotal()` (not the managed array), but `StrategyManager_ExportPositions()` and `CleanupManagedPositions()` both iterate the full array.

**Recommended Fix**: Add `MAX_MANAGED_POSITIONS = 200` constant and check before ArrayResize, with forced cleanup on overflow.

---

### H-3: MustCloseForWeekend unreachable code path

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\RiskManager.mqh`
**Lines**: 1536-1537

```mql5
if (m_ftmo.phase != FTMO_PHASE_FUNDED) return false;
if (m_ftmo.phase == FTMO_PHASE_SWING) return false;
```

**Root Cause**: The second condition is NEVER reached. If `phase == FTMO_PHASE_SWING`, the first condition (`phase != FTMO_PHASE_FUNDED`) is TRUE, so it returns false before reaching the second check. The SWING phase weekend exemption is dead code.

**Impact**: If a user sets phase to SWING, weekend closure is already skipped (correctly, by accident). However, if the enum order or values change, or if the first check is modified, the SWING exemption would silently break. This is a logic error that happens to be benign.

**Recommended Fix**:
```mql5
if (m_ftmo.phase != FTMO_PHASE_FUNDED) return false;
// Remove unreachable SWING check (FUNDED is the only phase that requires weekend close)
```

---

### H-4: DualOrderManager CleanupInactiveDualOrders uses O(n) temp array copy

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\DualOrderManager.mqh`
**Lines**: 806-844

```mql5
DualPendingOrders temp[];
ArrayResize(temp, active_count);
// ... copy active to temp ...
ArrayFree(g_active_dual_orders);
ArrayResize(g_active_dual_orders, active_count);
// ... copy temp back ...
ArrayFree(temp);
```

**Root Cause**: Unlike the v4.35 O(n) compaction fix applied to `CleanupManagedPositions()` and `CleanupVelocityTracker()`, `CleanupInactiveDualOrders()` still uses the old double-copy pattern: original -> temp -> original. This is 3N operations instead of N.

**Impact**: Performance inefficiency. With MAX_DUAL_ORDER_PAIRS=100, the practical impact is minimal, but this is inconsistent with the v4.35 optimization pattern applied elsewhere.

**Recommended Fix**: Apply the same single-pass compaction pattern used in StrategyManager.mqh line 896-917.

---

### H-5: Sleep() calls in MoneyProtector myOrderModifyCore retry loop

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\MoneyProtector.mqh`
**Line**: 614

```mql5
Sleep(OrderWait*1000);
```

**Root Cause**: `OrderWait = 5` seconds. With `OrderRetry = 5`, this means the retry loop can block OnTick() for up to 25 seconds. During this time, no other position management, trailing stops, or safety checks execute.

**Impact**: During high-volatility events (news, flash crashes), a failed order modification blocks ALL trade management for up to 25 seconds. Other positions cannot have their SL tightened, exits cannot fire, and new entries are delayed. This is particularly dangerous when multiple positions need simultaneous SL updates.

**Recommended Fix**: Reduce OrderWait to 1 second and OrderRetry to 3, or implement asynchronous retry via OnTimer().

---

### H-6: myOrderModifyRel Sleep(150) blocks OnTick

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\MoneyProtector.mqh`
**Line**: 1030

```mql5
Sleep(150);  // Initial wait for position registration
```

Plus up to 20 * 100ms = 2 seconds in the retry loop (lines 1037-1059).

**Root Cause**: After every market order, `myOrderModifyRel` is called to set SL/TP. This blocks for 150ms minimum plus up to 2150ms for position selection retries.

**Impact**: Combined with H-5, a single trade execution + SL/TP setup can block OnTick for 2.3+ seconds. If the trade then fails SL modification and enters the retry loop, total blocking can reach 27+ seconds.

---

### H-7: EntryIntelligence uses EMPTY_VALUE != EMPTY_VALUE comparison for extrema_confirmed

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\EntryIntelligence.mqh`
**Lines**: 343-345

```mql5
double confirmed_bottom = GetLEIBuffer(lei_handle, 1, 0);
double confirmed_top = GetLEIBuffer(lei_handle, 0, 0);
score.extrema_confirmed = is_buy ? (confirmed_bottom != EMPTY_VALUE) : (confirmed_top != EMPTY_VALUE);
```

**Root Cause**: `GetLEIBuffer` returns `EMPTY_VALUE` on failure (lines 92, 97). The extrema_confirmed check treats ANY non-EMPTY_VALUE as confirmed, including 0.0 or any garbage value. LEIlight buffers 0 and 1 are for confirmed extrema prices, so a value of 0.0 should not count as "confirmed".

**Impact**: False positive extrema confirmation when buffer returns 0.0 instead of EMPTY_VALUE, inflating confluence count and possibly allowing lower-quality entries.

**Recommended Fix**:
```mql5
score.extrema_confirmed = is_buy
    ? (confirmed_bottom != EMPTY_VALUE && confirmed_bottom > 0)
    : (confirmed_top != EMPTY_VALUE && confirmed_top > 0);
```

---

## MEDIUM FINDINGS

### M-1: IsDaylightSavingTime incorrect lastDay for October

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\RiskManager.mqh`
**Line**: 1057

```mql5
int lastDay = (dt.mon == 3) ? 31 : 31;
```

**Root Cause**: Copy-paste error. October has 31 days so the value is accidentally correct, but the ternary is meaningless. More critically, the `lastSunday` calculation on line 1058 uses `dt.day_of_week` and `dt.day` which may not be correct for determining the last Sunday of the month using MQL5's `MqlDateTime.day_of_week` field.

**Impact**: DST detection may be incorrect on the transition dates (last Sunday of March/October), causing 1-hour offset in CET time calculation. This affects FTMO news blackout timing and daily reset timing, but only for the ~6 hours around the DST transition.

---

### M-2: TrendConfirmation g_processed_boxes compaction only removes empty-name entries

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\TrendConfirmation.mqh`
**Lines**: 700-720

```mql5
if(arr_size > 200)
{
    int write_idx = 0;
    for(int k = 0; k < arr_size; k++)
    {
        if(g_processed_boxes[k].name != "")
        {
            if(write_idx != k)
                g_processed_boxes[write_idx] = g_processed_boxes[k];
            write_idx++;
        }
    }
```

**Root Cause**: The compaction only removes entries where `name == ""` (set by age filter on line 759). But if no boxes age out (MaxBoxAgeHours=24 and boxes are younger than 24h), the array never compacts. In a high-signal environment, the array grows past 200 and stays there permanently because no entries have empty names.

**Impact**: Slow O(n) linear search for every box on every tick, with n growing unbounded over the EA's lifetime.

---

### M-3: TrailingStopTrail pipValue calculation may be incorrect for non-forex

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\MoneyProtector.mqh`
**Line**: 686

```mql5
double pipValue = tickValue * (10.0 / tickSize);
```

**Root Cause**: This assumes `tickSize` is in 5-digit format (e.g., 0.00001) and that a pip is 10 ticks. For indices (US30, NAS100), metals (XAUUSD), and 4-digit pairs, this multiplier is wrong.

**Impact**: Incorrect profit locking calculations and SL adjustment distances in the trailing stop for non-standard forex pairs.

---

### M-4: ProcessFastProfitLocks unused `profit` and `volume` variables

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\FastProfitLocker.mqh`
**Lines**: 208-209

```mql5
double profit = PositionGetDouble(POSITION_PROFIT);
double volume = PositionGetDouble(POSITION_VOLUME);
```

**Root Cause**: These variables are declared and assigned but never used. The actual profit percentage is calculated from price_change (line 213-214), not from the `profit` dollar amount.

**Impact**: Wasted API calls (2 per position per tick). Minor performance waste but no correctness issue.

---

### M-5: ApplyFastProfitLock creates new CTrade instance on every call

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\FastProfitLocker.mqh`
**Line**: 160

```mql5
CTrade trade;
trade.SetDeviationInPoints(30);
```

**Root Cause**: A new CTrade object is constructed and configured on every call to `ApplyFastProfitLock()`, which runs every tick for every qualifying position.

**Impact**: Unnecessary object construction/destruction overhead. Should use a module-level CTrade instance (like DualOrderManager's `g_dual_order_trade`).

---

### M-6: CalculateEntryConfluence hardcoded ATR thresholds

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\EntryIntelligence.mqh`
**Line**: 272

```mql5
if (current_atr > 0.0005 && current_atr < 0.005)
```

**Root Cause**: ATR range 0.0005-0.005 is hardcoded for 5-digit forex pairs. For XAUUSD (ATR ~20), USDJPY (ATR ~0.5), or indices, this threshold is meaningless.

**Impact**: Volatility quality factor always returns 50.0 (no confluence point) for non-EURUSD-like pairs, effectively disabling this factor from the scoring system.

---

### M-7: MoneyProtector ValidatePrice type check uses modulo arithmetic

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\MoneyProtector.mqh`
**Lines**: 255, 262

```mql5
if(type > ORDER_TYPE_SELL) {
    // ...
    double currentPrice = (type % 2 == 0) ? tick.ask : tick.bid;
```

**Root Cause**: Uses `type % 2 == 0` to determine if order is buy-side. This works for standard types (BUY_LIMIT=2, BUY_STOP=4, BUY_STOP_LIMIT=6 are all even) but relies on enum value ordering that is implementation-specific.

**Impact**: Currently correct, but fragile. If MT5 adds new order types or changes enum values, this breaks silently.

---

### M-8: PositionManagement static variables inside TrailingStopST2 loop scope

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\PositionManagement.mqh`
**Lines**: 346-348, 358-360, 373-376, 387-389

```mql5
static bool warning_shown = false;
static bool copy_fail_logged_st1 = false;
static bool copy_fail_logged_long = false;
static bool copy_fail_logged_short = false;
```

**Root Cause**: These static booleans permanently suppress warnings after the first occurrence. Once set to true, they never reset. If the indicator handle becomes temporarily invalid (e.g., indicator reload), warnings are permanently silenced.

**Impact**: Silent failures in production. If LEIlight crashes and restarts, the EA continues without trailing stop updates and never logs the problem again.

---

## LOW FINDINGS

### L-1: DualOrderManager Cleanup runs every 3600 seconds (too infrequent)

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\DualOrderManager.mqh`
**Line**: 702

```mql5
if(TimeCurrent() - last_cleanup > 3600)  // Every hour
```

Stale entries accumulate for up to 1 hour. Consider reducing to 300 seconds (5 minutes).

### L-2: MoneyProtector hardcoded log filename "testlll.txt"

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\MoneyProtector.mqh`
**Line**: 402

```mql5
int handle = FileOpen("testlll.txt", ...);
```

Development-era filename left in production code. Should use a descriptive name like "RIGGWIRE_trade_log.txt".

### L-3: RiskManager verbose logging flag is global mutable

**File**: `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO\RiskManager.mqh`
**Line**: 332

```mql5
bool g_rm_verbose = false;
```

Global mutable state. Should be an input parameter or class member.

### L-4: StrategyManager uses emoji in Print statements

**File**: Multiple files

Emoji characters in Print() and Alert() calls may display as garbage on non-UTF8 terminals or in log files.

### L-5: Multiple magic number validation patterns across files

MoneyProtector uses `IsOurMagicNumber()` (magic > Base && <= Base+12), while PositionManagement uses `pos.magic < BaseMagicNumber + 1 || pos.magic > BaseMagicNumber + 12`, and FastProfitLocker uses `magic < BaseMagicNumber + 1 || magic > BaseMagicNumber + 12`. These are equivalent but having 3 different patterns increases maintenance risk.

---

## v4.34-4.35 CHANGES VALIDATION

### Array Compaction Optimization (v4.35 MEDIUM-8)

**Files Affected**: StrategyManager.mqh (CleanupManagedPositions), FastProfitLocker.mqh (CleanupVelocityTracker)

**Verdict**: CORRECT. Both implementations use the standard O(n) single-pass compaction pattern:
1. Read index advances through entire array
2. Write index only advances when valid entry found
3. Entries copied forward in-place
4. Single ArrayResize at end

**Validation Points**:
- Self-assignment check (`if(write_idx != read_idx)`) is present -- prevents unnecessary copies
- ArrayResize only called if entries were removed (`write_idx < size`)
- PositionSelectByTicket correctly validates existence before copying

**Regression Risk**: NONE. The optimization is correct and does not change behavior.

### Fast Profit Locking (v4.33-4.35)

**Files Affected**: FastProfitLocker.mqh (new file)

**Verdict**: HAS CRITICAL BUG (C-1 above). The direction-agnostic profit calculation will trigger locks on losing short positions.

**Other v4.35 Issues**:
- Missing array cap (C-2)
- Unused variables (M-4)
- Per-call CTrade construction (M-5)

### Input Validation (v4.35 LOW-2)

**File**: EntryIntelligence.mqh (ValidateEntryIntelligenceInputs)

**Verdict**: CORRECT. Validates all input parameters with sensible ranges. Returns false on any failure with descriptive error messages. One minor note: it is only called if the caller invokes it; there is no evidence it is called from OnInit() in RIGGWIRE_FINAL.mq5 (would need to verify).

### Logging Additions (v4.35 MEDIUM-2, MEDIUM-4)

**Files**: EntryIntelligence.mqh (CalculateRisk_ST1_Distance, CalculateReward_ST2_Distance, ShouldEnter_Intelligent)

**Verdict**: CORRECT. Added Print statements for default value usage and bypass mode. No performance impact (prints only on specific conditions, not every tick).

---

## ARCHITECTURE OBSERVATIONS

### Positive Patterns
1. **PositionSnapshot**: Atomic position data access prevents mid-read state changes
2. **SafePositionClose/SafeOrderModify**: Retry wrappers with proper error handling
3. **Magic number range**: Consistent BaseMagicNumber + 1..12 pattern across files
4. **Buffer validation**: EMPTY_VALUE checks present on most CopyBuffer calls
5. **v4.35 compaction**: O(n) single-pass pattern is well-implemented

### Areas of Concern
1. **Sleep() blocking**: Multiple Sleep() calls in critical paths (H-5, H-6) can block OnTick for 25+ seconds
2. **Inconsistent array caps**: Some arrays capped (dual orders: 100, exit tracking: 1000), others not (velocity tracker, managed positions)
3. **No centralized position iteration**: Each file iterates PositionsTotal() independently, leading to 4-5 full scans per tick
4. **Hardcoded constants**: ATR thresholds, timeframe assumptions, and pip calculations assume 5-digit forex

---

## RECOMMENDED PRIORITY ORDER

1. **C-1** (FastProfitLocker direction bug) -- Fix immediately, production blocker
2. **C-2** (velocity tracker cap) -- Fix immediately, memory growth
3. **H-1** (ATR floor for separation ratio) -- Fix before deployment
4. **H-2** (managed positions cap) -- Fix before deployment
5. **H-5/H-6** (Sleep blocking) -- Fix for next version (requires architecture change)
6. **H-7** (extrema confirmation) -- Fix before deployment
7. **H-3** (dead SWING code) -- Clean up
8. **H-4** (cleanup optimization) -- Nice to have

---

## CONCLUSION

RIGGWIRE EA v4.35 contains **2 production-blocking issues** that must be fixed before live deployment:

1. **C-1**: FastProfitLocker will lock breakeven on LOSING short trades (direction-blind profit calculation)
2. **C-2**: FastProfitLocker velocity tracker grows without bound (memory leak over time)

The v4.34-4.35 array compaction optimizations are correctly implemented and introduce no regression. The input validation and logging additions are appropriate. The remaining HIGH and MEDIUM issues are important for robustness but are not immediate production blockers.

**Recommendation**: Fix C-1 and C-2, then deploy. Address H-1 through H-7 in a v4.36 maintenance release.
