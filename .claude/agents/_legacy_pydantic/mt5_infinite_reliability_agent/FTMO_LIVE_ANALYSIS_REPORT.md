# RIGGWIRE-EA-FTMO-LIVE Comprehensive Analysis

**Generated:** 2026-02-04T21:18:34.372248

**Directory:** `C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO-LIVE`

## Executive Summary

- **Files Analyzed:** 29
- **Total Lines:** 26,060
- **Unused Logic Patterns:** 1003
- **Files with Issues:** 25

## Files Analyzed

| File | Lines | Size (KB) | Unused Patterns |
|------|-------|-----------|------------------|
| CleanupCrossoverObjects.mq5 | 41 | 1.2 | 0 |
| DashboardStructs.mqh | 138 | 4.4 | 0 |
| DELETE_MTF_LINES.mq5 | 49 | 1.6 | 0 |
| DIAGNOSTIC_ENABLE_TRADING.mqh | 70 | 2.9 | 1 |
| DisplayTrendAnalysis.mqh | 134 | 3.9 | 3 |
| IsConsolidating.mqh | 114 | 4.6 | 5 |
| LEIlight.mq5 | 3133 | 146.5 | 100 |
| LossAnalyzer.mqh | 439 | 15.5 | 10 |
| M15AlignmentChecker.mqh | 101 | 4.2 | 2 |
| M15VirtualBoxFilter.mqh | 484 | 19.5 | 20 |
| MagicNumbers.mqh | 26 | 1.2 | 0 |
| MoneyProtector.mqh | 1228 | 48.8 | 55 |
| MQL5ReliabilityHelpers.mqh | 186 | 7.8 | 3 |
| MTFWeightedAnalysis.mqh | 286 | 11.5 | 1 |
| NEWS.mqh | 999 | 34.0 | 31 |
| PositionManagement.mqh | 1356 | 53.7 | 38 |
| RIGGWIRE_FINAL.mq5 | 1897 | 92.2 | 88 |
| RiggwireDashboard.mqh | 1900 | 103.8 | 76 |
| RiskManager.mqh | 4195 | 160.6 | 180 |
| SessionRules.mqh | 997 | 38.2 | 39 |
| SignalRouter_Refactored.mqh | 532 | 23.6 | 24 |
| StrategyManager.mqh | 949 | 38.0 | 29 |
| TradeDisciplineVerifier.mqh | 176 | 6.7 | 5 |
| TradeOperationWrapper.mqh | 569 | 19.8 | 6 |
| TradingConstants.mqh | 90 | 5.7 | 29 |
| TradingSessionsCandles.mq5 | 208 | 7.6 | 16 |
| TrendCipher.mq5 | 3374 | 157.8 | 152 |
| TrendConfirmation.mqh | 2028 | 86.7 | 81 |
| WinAnalyzer.mqh | 361 | 13.3 | 9 |

## Detailed Findings

### DIAGNOSTIC_ENABLE_TRADING.mqh

#### Potentially Unused Variable (1)

- **Severity:** medium
  - **Variable:** `totalPos`


### DisplayTrendAnalysis.mqh

#### Potentially Unused Variable (1)

- **Severity:** medium
  - **Variable:** `s_H1`

#### Unreachable Code (2)

- **Severity:** high
  - **Content:** `return 0;

   double wt1[], wt2[];
   ArraySetAsSeries(wt1, true);
   ArraySetAs...`

- **Severity:** high
  - **Content:** `return 1;   // Bullish
   if (rates[0].close < rates[0].open) return -1;   // Be...`


### IsConsolidating.mqh

#### Commented Code (2)

- **Severity:** low
  - **Line:** 20
  - **Content:** `// FIX ERROR #2 & #3: Removed unused time parameters, changed return convention...`

- **Severity:** low
  - **Line:** 86
  - **Content:** `// Determine the return signal based on consolidation status change...`

#### Potentially Unused Variable (2)

- **Severity:** medium
  - **Variable:** `tradingRange`

- **Severity:** medium
  - **Variable:** `isConsolidating`

#### Unreachable Code (1)

- **Severity:** high
  - **Content:** `return signal based on consolidation status change
    int returnSignal = 0; // ...`


### LEIlight.mq5

#### Commented Code (47)

- **Severity:** low
  - **Line:** 163
  - **Content:** `//|   double long_stop = iCustom(_Symbol, _Period, "LEIlight", ..., 20, 1);|...`

- **Severity:** low
  - **Line:** 164
  - **Content:** `//|   double short_stop = iCustom(_Symbol, _Period, "LEIlight", ..., 21, 1);|...`

- **Severity:** low
  - **Line:** 165
  - **Content:** `//|   if(position is LONG) ModifySL(long_stop);                     |...`

- **Severity:** low
  - **Line:** 166
  - **Content:** `//|   if(position is SHORT) ModifySL(short_stop);                   |...`

- **Severity:** low
  - **Line:** 178
  - **Content:** `//|   double buy = iCustom(_Symbol, _Period, "LEIlight", ..., 18, 1);|...`

- **Severity:** low
  - **Line:** 179
  - **Content:** `//|   double sell = iCustom(_Symbol, _Period, "LEIlight", ..., 19, 1);|...`

- **Severity:** low
  - **Line:** 180
  - **Content:** `//|   if(buy != EMPTY_VALUE) OpenBuyTrade();                        |...`

- **Severity:** low
  - **Line:** 181
  - **Content:** `//|   if(sell != EMPTY_VALUE) OpenSellTrade();                      |...`

- **Severity:** low
  - **Line:** 191
  - **Content:** `//|   * Result: Signals no longer repaint or disappear              |...`

- **Severity:** low
  - **Line:** 295
  - **Content:** `//| - EXACT intersection point using linear interpolation formula   |...`

#### Potentially Unused Variable (36)

- **Severity:** medium
  - **Variable:** `long_stop`

- **Severity:** medium
  - **Variable:** `short_stop`

- **Severity:** medium
  - **Variable:** `ShowSigmaBands`

- **Severity:** medium
  - **Variable:** `PreventOverlappingBoxes`

- **Severity:** medium
  - **Variable:** `OneActiveBoxOnly`

- **Severity:** medium
  - **Variable:** `BreachOnClose`

- **Severity:** medium
  - **Variable:** `UseATRSqueezeFilter`

- **Severity:** medium
  - **Variable:** `ATR_Squeeze_Threshold`

- **Severity:** medium
  - **Variable:** `ADX_Filter_Period`

- **Severity:** medium
  - **Variable:** `min_required`

#### Unreachable Code (17)

- **Severity:** high
  - **Content:** `return g_cache.adx_value;

    // Fetch fresh ADX value
    if(ADX_Filter_Handle...`

- **Severity:** high
  - **Content:** `return g_cache.atr_avg;

    // Calculate fresh ATR average
    double atr_sum =...`

- **Severity:** high
  - **Content:** `return fallback_atr;

    // Get M5 ATR value
    double m5_atr[];
    int m5_ba...`

- **Severity:** high
  - **Content:** `return;

    // Check if crossover display is enabled
    if(!ShowCrossovers) re...`

- **Severity:** high
  - **Content:** `return;

    // Get H1 ST1 and ST2 buffers (buffer indices: 6=ST2, 7=ST1 in LEIl...`

- **Severity:** high
  - **Content:** `return true;

    // v2.48: FILTERED messages only if debug or measurement mode ...`

- **Severity:** high
  - **Content:** `return true;

    if(UseDebug || H1_MeasurementMode)
    {
        if(crossovers...`

- **Severity:** high
  - **Content:** `return false;

    const double v = data[currIndex];
    int leftIndex = currInd...`

- **Severity:** high
  - **Content:** `return false;

    const double v = data[currIndex];
    int leftIndex = currInd...`

- **Severity:** high
  - **Content:** `return false;

    double currentHigh = high[index];

    // Check lookback bars...`


### LossAnalyzer.mqh

#### Commented Code (5)

- **Severity:** low
  - **Line:** 33
  - **Content:** `// Trend states (cast enums to int for storage)...`

- **Severity:** low
  - **Line:** 142
  - **Content:** `//| Deinit — print summary                                            |...`

- **Severity:** low
  - **Line:** 259
  - **Content:** `//| On trade close — if losing, print structured block                |...`

- **Severity:** low
  - **Line:** 338
  - **Content:** `// ===== PRINT STRUCTURED BLOCK =====...`

- **Severity:** low
  - **Line:** 395
  - **Content:** `// ===== WRITE CSV ROW =====...`

#### Potentially Unused Variable (1)

- **Severity:** medium
  - **Variable:** `duration_sec`

#### Unreachable Code (4)

- **Severity:** high
  - **Content:** `return;
   ArrayResize(g_la_snapshots, 0);
   g_la_count = 0;
   g_la_total_loss...`

- **Severity:** high
  - **Content:** `return;
   if(g_la_total_losses > 0)
   {
      Print("=== LOSS ANALYZER SUMMARY...`

- **Severity:** high
  - **Content:** `return;
   // Allocate slot
   int idx = g_la_count;
   g_la_count++;
   ArrayRe...`

- **Severity:** high
  - **Content:** `return;
   int idx = LA_FindSlot(ticket);
   if(idx < 0) return;  // Not tracked...`


### M15AlignmentChecker.mqh

#### Potentially Unused Variable (1)

- **Severity:** medium
  - **Variable:** `m15_bearish_cross`

#### Unreachable Code (1)

- **Severity:** high
  - **Content:** `return true;  // Filter disabled or handle failed - allow M5 box

   // Get M15 ...`


### M15VirtualBoxFilter.mqh

#### Commented Code (1)

- **Severity:** low
  - **Line:** 402
  - **Content:** `// v3.11: FIX CRITICAL-3 - Validate _Point before division to prevent division b...`

#### Potentially Unused Variable (10)

- **Severity:** medium
  - **Variable:** `M15_BoxRangeMultiplier`

- **Severity:** medium
  - **Variable:** `CheckM15CrossoverPrice`

- **Severity:** medium
  - **Variable:** `bearishCross`

- **Severity:** medium
  - **Variable:** `m15_high`

- **Severity:** medium
  - **Variable:** `m15_low`

- **Severity:** medium
  - **Variable:** `excess`

- **Severity:** medium
  - **Variable:** `hours_old`

- **Severity:** medium
  - **Variable:** `start_time`

- **Severity:** medium
  - **Variable:** `label_price`

- **Severity:** medium
  - **Variable:** `label_text`

#### Unreachable Code (9)

- **Severity:** high
  - **Content:** `return true;

   // Initialize LEI indicator on M15
   g_M15_LEI_Handle = iCusto...`

- **Severity:** high
  - **Content:** `return;

   // Get M15 Supertrend buffers
   double ST1_M15[], ST2_M15[], ST1_AT...`

- **Severity:** high
  - **Content:** `return;

   bool bullishCross = (ST1_M15[2] < ST2_M15[2]) && (ST1_M15[1] > ST2_M...`

- **Severity:** high
  - **Content:** `return;

   // Create unique name for M15 box
   string box_name = "M15_AlignedB...`

- **Severity:** high
  - **Content:** `return;

   // Create unique name for alignment marker
   string marker_name = "...`

- **Severity:** high
  - **Content:** `return;

   string label_name = "M15_Label_" + TimeToString(box_time, TIME_DATE|...`

- **Severity:** high
  - **Content:** `return true;  // Filter disabled - allow all M5 boxes

   if(ArraySize(g_M15_Vir...`

- **Severity:** high
  - **Content:** `return true;

   // Check if M5 direction matches M15 direction
   bool m15_is_b...`

- **Severity:** high
  - **Content:** `return "[M15 FILTER] Disabled";

   int active_count = 0;
   int bullish_count =...`


### MoneyProtector.mqh

#### Commented Code (6)

- **Severity:** low
  - **Line:** 376
  - **Content:** `// Simple print - no formatting needed...`

- **Severity:** low
  - **Line:** 387
  - **Content:** `// Always print to terminal...`

- **Severity:** low
  - **Line:** 616
  - **Content:** `// v7.2 FIX: Re-select position/order before retry to avoid stale data...`

- **Severity:** low
  - **Line:** 709
  - **Content:** `// v7.2 FIX: Get fresh tick data for each position (avoid stale data in long loo...`

- **Severity:** low
  - **Line:** 1008
  - **Content:** `// For pending orders, return order ticket...`

- **Severity:** low
  - **Line:** 1110
  - **Content:** `// myOrderModifyCore will re-select and validate (eliminates 20ms race window fr...`

#### Potentially Unused Variable (40)

- **Severity:** medium
  - **Variable:** `MM_Percent`

- **Severity:** medium
  - **Variable:** `TradeSunday`

- **Severity:** medium
  - **Variable:** `TradeMonday`

- **Severity:** medium
  - **Variable:** `TradeTuesday`

- **Severity:** medium
  - **Variable:** `TradeWednesday`

- **Severity:** medium
  - **Variable:** `TradeThursday`

- **Severity:** medium
  - **Variable:** `TradeFriday`

- **Severity:** medium
  - **Variable:** `TradeSaturday`

- **Severity:** medium
  - **Variable:** `Audible_Alerts`

- **Severity:** medium
  - **Variable:** `Push_Notifications`

#### Unreachable Code (9)

- **Severity:** high
  - **Content:** `returns error
int OrderWait = 5; //# of seconds to wait if sending order returns...`

- **Severity:** high
  - **Content:** `return true;

   // v7.2 FIX: Use correct price based on order type
   // BUY po...`

- **Severity:** high
  - **Content:** `return true;

   // v7.2 FIX: Use correct price based on order type
   // BUY po...`

- **Severity:** high
  - **Content:** `return TradeSunday;     // Sunday
      case 1: return TradeMonday;     // Monda...`

- **Severity:** high
  - **Content:** `returns # of open trades for order type, current symbol and magic number
  {
   ...`

- **Severity:** high
  - **Content:** `return(-1);

   bool netting = AccountInfoInteger(ACCOUNT_MARGIN_MODE) != ACCOUN...`

- **Severity:** high
  - **Content:** `return(0);

   // v7.2: Validate inputs with correct price reference for positio...`

- **Severity:** high
  - **Content:** `return ticket ("price" is irrelevant for market orders)
  {
   if(!TerminalInfoI...`

- **Severity:** high
  - **Content:** `return = true;  // ORDER_FILLING_RETURN is always available as fallback

   if(r...`


### MQL5ReliabilityHelpers.mqh

#### Commented Code (1)

- **Severity:** low
  - **Line:** 113
  - **Content:** `// SymbolInfoInteger returns -1 on error or invalid values...`

#### Potentially Unused Variable (2)

- **Severity:** medium
  - **Variable:** `pos_success_rate`

- **Severity:** medium
  - **Variable:** `buf_success_rate`


### MTFWeightedAnalysis.mqh

#### Potentially Unused Variable (1)

- **Severity:** medium
  - **Variable:** `EnableHTFVeto`


### NEWS.mqh

#### Commented Code (20)

- **Severity:** low
  - **Line:** 100
  - **Content:** `//==========================================================...`

- **Severity:** low
  - **Line:** 102
  - **Content:** `//==========================================================...`

- **Severity:** low
  - **Line:** 230
  - **Content:** `//==========================================================...`

- **Severity:** low
  - **Line:** 232
  - **Content:** `//==========================================================...`

- **Severity:** low
  - **Line:** 312
  - **Content:** `//==========================================================...`

- **Severity:** low
  - **Line:** 314
  - **Content:** `//==========================================================...`

- **Severity:** low
  - **Line:** 422
  - **Content:** `//==========================================================...`

- **Severity:** low
  - **Line:** 424
  - **Content:** `//==========================================================...`

- **Severity:** low
  - **Line:** 476
  - **Content:** `//==========================================================...`

- **Severity:** low
  - **Line:** 478
  - **Content:** `//==========================================================...`

#### Potentially Unused Variable (7)

- **Severity:** medium
  - **Variable:** `timing`

- **Severity:** medium
  - **Variable:** `today`

- **Severity:** medium
  - **Variable:** `tomorrow`

- **Severity:** medium
  - **Variable:** `url`

- **Severity:** medium
  - **Variable:** `timeout`

- **Severity:** medium
  - **Variable:** `response_len`

- **Severity:** medium
  - **Variable:** `tightBlackoutSec`

#### Unreachable Code (4)

- **Severity:** high
  - **Content:** `return true;

      // Special cases for indices
      if(currency == "USD")
   ...`

- **Severity:** high
  - **Content:** `return NEWS_HIGH;
         case CALENDAR_IMPORTANCE_MODERATE: return NEWS_MEDIUM...`

- **Severity:** high
  - **Content:** `return 1.0; // No news, full risk

      switch(impact)
      {
         case NE...`

- **Severity:** high
  - **Content:** `return false;

      // Then check broad window based on impact
      NewsImpact...`


### PositionManagement.mqh

#### Commented Code (5)

- **Severity:** low
  - **Line:** 142
  - **Content:** `//| Caches crossover prices per position to avoid O(n) search        |...`

- **Severity:** low
  - **Line:** 324
  - **Content:** `// v3.06: ADAPTIVE OFFSET LOGIC - More breathing room to avoid premature stops...`

- **Severity:** low
  - **Line:** 764
  - **Content:** `// Cache hit - return cached price...`

- **Severity:** low
  - **Line:** 1135
  - **Content:** `//+==================================================================+...`

- **Severity:** low
  - **Line:** 1138
  - **Content:** `//+==================================================================+...`

#### Potentially Unused Variable (23)

- **Severity:** medium
  - **Variable:** `EnableSafetyTimeout`

- **Severity:** medium
  - **Variable:** `EnableLEICrossoverExit`

- **Severity:** medium
  - **Variable:** `EnableTrendCipherExit`

- **Severity:** medium
  - **Variable:** `EnableExtremeSignalExit`

- **Severity:** medium
  - **Variable:** `SPREAD_OFFSET_BEFORE_BE`

- **Severity:** medium
  - **Variable:** `OPEN_OFFSET_PCT_BEFORE_BE`

- **Severity:** medium
  - **Variable:** `SPREAD_OFFSET_AFTER_BE`

- **Severity:** medium
  - **Variable:** `min_stop_level`

- **Severity:** medium
  - **Variable:** `last_open`

- **Severity:** medium
  - **Variable:** `current_bid`

#### Unreachable Code (10)

- **Severity:** high
  - **Content:** `return false;  // Can't read - block exit (require alignment)
   if(CopyBuffer(g...`

- **Severity:** high
  - **Content:** `return;  // Only execute if EXIT signal active (v10.6 extreme levels)

   int to...`

- **Severity:** high
  - **Content:** `return;  // Only execute if ADD POSITION signal active

   // Check if we alread...`

- **Severity:** high
  - **Content:** `return;

   // v3.06: ADAPTIVE OFFSET LOGIC - More breathing room to avoid prema...`

- **Severity:** high
  - **Content:** `return;

   datetime timeout_threshold = TimeCurrent() - (SafetyTimeout_Minutes ...`

- **Severity:** high
  - **Content:** `return;

   // v11.0: Update MTF trend states first
   UpdateMTFTrendStates();

...`

- **Severity:** high
  - **Content:** `return;

   // v3.08: ALL exits require M5+M15 alignment (consistent with entry ...`

- **Severity:** high
  - **Content:** `return;

   // v2.45: Skip buffer reads when no positions open
   if(PositionsTo...`

- **Severity:** high
  - **Content:** `return;  // No exit signals

   // v3.08: LEI exit signals are already M15-valid...`

- **Severity:** high
  - **Content:** `return;

   if(g_trendCipherHandle == INVALID_HANDLE) return;

   // v2.45: Skip...`


### RIGGWIRE_FINAL.mq5

#### Commented Code (18)

- **Severity:** low
  - **Line:** 51
  - **Content:** `//| - g_leiHandle double declaration removed                          |...`

- **Severity:** low
  - **Line:** 223
  - **Content:** `//| PURPOSE: Pinpoint exact filter blocking SNIPER mode trades      |...`

- **Severity:** low
  - **Line:** 457
  - **Content:** `// Object prefix for EA-specific objects (to avoid deleting unrelated ones)...`

- **Severity:** low
  - **Line:** 566
  - **Content:** `//| Reads ATR directly from TrendCipher to avoid creating separate   |...`

- **Severity:** low
  - **Line:** 614
  - **Content:** `// Risk = Lot Size * SL Distance (points) * Point Value...`

- **Severity:** low
  - **Line:** 814
  - **Content:** `// v7.4 CRITICAL FIX: myPoint should ALWAYS equal _Point (not multiplied by 10)...`

- **Severity:** low
  - **Line:** 815
  - **Content:** `// RiskManager.GetDynamicSL() returns values in POINTS, not pips...`

- **Severity:** low
  - **Line:** 816
  - **Content:** `// Previous bug: 137 points * 0.0001 (myPoint * 10) = 0.0137 = 1370 points SL!...`

- **Severity:** low
  - **Line:** 821
  - **Content:** `// Note: Do NOT multiply myPoint by 10 for 5-digit brokers...`

- **Severity:** low
  - **Line:** 919
  - **Content:** `// CRITICAL: Print trading hours configuration for verification...`

#### Potentially Unused Variable (56)

- **Severity:** medium
  - **Variable:** `EnableDashboard`

- **Severity:** medium
  - **Variable:** `DashboardRefreshMs`

- **Severity:** medium
  - **Variable:** `Auto_Load_FTMO_Calendar`

- **Severity:** medium
  - **Variable:** `Auto_Close_Weekend`

- **Severity:** medium
  - **Variable:** `Enable_30Percent_Safety_Rule`

- **Severity:** medium
  - **Variable:** `ShowArrows`

- **Severity:** medium
  - **Variable:** `TRAILING_SL`

- **Severity:** medium
  - **Variable:** `STEPS`

- **Severity:** medium
  - **Variable:** `ATRMultiplier1`

- **Severity:** medium
  - **Variable:** `ATRPeriod1`

#### Empty Function (2)

- **Severity:** medium
  - **Content:** `void SimpleDiagnostics() { }...`

- **Severity:** medium
  - **Content:** `void AggressiveDiagnostics() { }...`

#### Unreachable Code (12)

- **Severity:** high
  - **Content:** `return 0.0;

   // v10.21: Read ATR from TrendCipher buffer 37 (avoids creating ...`

- **Severity:** high
  - **Content:** `return 0.0;

   // v10.21: Read ATR from TrendCipher buffer 37 (avoids creating ...`

- **Severity:** high
  - **Content:** `return 0.0;

   // v10.21: Read ATR from TrendCipher buffer 37 (avoids creating ...`

- **Severity:** high
  - **Content:** `return Min_Signal_Quality;

   // v10.21: Read ATR from TrendCipher buffer 37 (a...`

- **Severity:** high
  - **Content:** `return Min_Trend_Strength;

   // v10.21: Read ATR from TrendCipher buffer 37 (a...`

- **Severity:** high
  - **Content:** `returns values in POINTS, not pips
   // Previous bug: 137 points * 0.0001 (myPo...`

- **Severity:** high
  - **Content:** `return;

   // PERFORMANCE: Update daily profit cache (incremental, not full sca...`

- **Severity:** high
  - **Content:** `return;

   Print("========== FTMO COMPLIANCE STATUS ==========");

   // Phase ...`

- **Severity:** high
  - **Content:** `return; // Same bar - exit early
   totalBars = bars;

   // RISK MANAGER: Sync ...`

- **Severity:** high
  - **Content:** `return; // Skip redundant checks
   lastCheckedTime = currentTime;
   double dai...`


### RiggwireDashboard.mqh

#### Commented Code (12)

- **Severity:** low
  - **Line:** 1366
  - **Content:** `// ============ LEFT COLUMN ============...`

- **Severity:** low
  - **Line:** 1402
  - **Content:** `// ============ RIGHT COLUMN ============...`

- **Severity:** low
  - **Line:** 1482
  - **Content:** `// ============ SYSTEM STATUS ============...`

- **Severity:** low
  - **Line:** 1487
  - **Content:** `// ============ TRADING HOURS ============...`

- **Severity:** low
  - **Line:** 1494
  - **Content:** `// ============ DAILY PERFORMANCE ============...`

- **Severity:** low
  - **Line:** 1505
  - **Content:** `// ============ EA STATUS ============...`

- **Severity:** low
  - **Line:** 1516
  - **Content:** `// ============ SIGNAL STATUS ============...`

- **Severity:** low
  - **Line:** 1527
  - **Content:** `// ============ TREND ANALYSIS - FROM ACTUAL MTF STATE ============...`

- **Severity:** low
  - **Line:** 1578
  - **Content:** `// ============ FTMO COMPLIANCE - FROM ACTUAL RISK STATE ============...`

- **Severity:** low
  - **Line:** 1746
  - **Content:** `// ===== PIE CHARTS SECTION (TOP) =====...`

#### Potentially Unused Variable (52)

- **Severity:** medium
  - **Variable:** `DashboardRefreshMs`

- **Severity:** medium
  - **Variable:** `g_dash_reset_equity_requested`

- **Severity:** medium
  - **Variable:** `font_size`

- **Severity:** medium
  - **Variable:** `anchor`

- **Severity:** medium
  - **Variable:** `decimals`

- **Severity:** medium
  - **Variable:** `decimal_part`

- **Severity:** medium
  - **Variable:** `total_positions`

- **Severity:** medium
  - **Variable:** `deals_total`

- **Severity:** medium
  - **Variable:** `deal_commission`

- **Severity:** medium
  - **Variable:** `deal_swap`

#### Unreachable Code (12)

- **Severity:** high
  - **Content:** `return false;
   ObjectSetInteger(ChartID(), obj_name, OBJPROP_XDISTANCE, x);
  ...`

- **Severity:** high
  - **Content:** `return false;
   ObjectSetInteger(ChartID(), obj_name, OBJPROP_XDISTANCE, x);
  ...`

- **Severity:** high
  - **Content:** `return "N/A";
   string result = DoubleToString(MathAbs(value), decimals);
   in...`

- **Severity:** high
  - **Content:** `return;
   int chart_width = 200;  // Increased for bigger pie charts
   int cha...`

- **Severity:** high
  - **Content:** `return;
   int chart_width = 200;  // Increased for bigger pie charts
   int cha...`

- **Severity:** high
  - **Content:** `return;
   dash_collapsed = true;
   // Hide full dashboard
   Dash_ShowFullDash...`

- **Severity:** high
  - **Content:** `return;
   dash_collapsed = false;
   // Hide collapsed bar
   Dash_ShowCollapse...`

- **Severity:** high
  - **Content:** `return;
   Dash_DestroyPieCharts();
   ObjectsDeleteAll(ChartID(), dash_prefix);...`

- **Severity:** high
  - **Content:** `return;
   // v3.07: Auto-revert reset button after 5s timeout
   if (g_dash_res...`

- **Severity:** high
  - **Content:** `return;
   // DEBUG: Log all click events
   if(id == CHARTEVENT_OBJECT_CLICK) {...`


### RiskManager.mqh

#### Commented Code (122)

- **Severity:** low
  - **Line:** 478
  - **Content:** `//==================================================...`

- **Severity:** low
  - **Line:** 480
  - **Content:** `//==================================================...`

- **Severity:** low
  - **Line:** 976
  - **Content:** `// FIXED v4.1: Removed redundant * point multiplication...`

- **Severity:** low
  - **Line:** 977
  - **Content:** `// sl_dist is already in points, no need to multiply by point again...`

- **Severity:** low
  - **Line:** 1011
  - **Content:** `// SYMBOL_TRADE_TICK_VALUE is value per tick (usually = value per point for fore...`

- **Severity:** low
  - **Line:** 1040
  - **Content:** `//==================================================...`

- **Severity:** low
  - **Line:** 1042
  - **Content:** `//==================================================...`

- **Severity:** low
  - **Line:** 1368
  - **Content:** `//==================================================...`

- **Severity:** low
  - **Line:** 1370
  - **Content:** `//==================================================...`

- **Severity:** low
  - **Line:** 1399
  - **Content:** `//==================================================...`

#### Potentially Unused Variable (20)

- **Severity:** medium
  - **Variable:** `cache_valid`

- **Severity:** medium
  - **Variable:** `needs_refresh`

- **Severity:** medium
  - **Variable:** `scale_factor`

- **Severity:** medium
  - **Variable:** `win_rate_score`

- **Severity:** medium
  - **Variable:** `dd_score`

- **Severity:** medium
  - **Variable:** `profit_factor`

- **Severity:** medium
  - **Variable:** `pf_score`

- **Severity:** medium
  - **Variable:** `hours_locked`

- **Severity:** medium
  - **Variable:** `is_dst`

- **Severity:** medium
  - **Variable:** `old_initial`

#### Unreachable Code (38)

- **Severity:** high
  - **Content:** `return risk_pct;

      if (m_equity >= m_peak_equity)
         return risk_pct;...`

- **Severity:** high
  - **Content:** `return false;
      if (m_vol_data[idx].last_atr_time == 0) return false;

     ...`

- **Severity:** high
  - **Content:** `return;

      // Check symbol limit
      if (ArraySize(m_vol_data) >= m_max_sy...`

- **Severity:** high
  - **Content:** `return risk_pct;

      int idx = FindVolDataIndex(symbol);
      if (idx < 0) {...`

- **Severity:** high
  - **Content:** `return risk_pct;

      double vol_factor = m_vol_data[idx].last_atr_base / m_vo...`

- **Severity:** high
  - **Content:** `return SESSION_QUIET;

      datetime now = TimeGMT();
      MqlDateTime dt;
   ...`

- **Severity:** high
  - **Content:** `return risk_pct;

      TradingSession session = GetCurrentSession();
      doub...`

- **Severity:** high
  - **Content:** `return false;

      // Delegate to consolidated NEWS.mqh
      // g_news is the...`

- **Severity:** high
  - **Content:** `return risk_pct;

      double days_active = (TimeCurrent() - m_account_start_da...`

- **Severity:** high
  - **Content:** `return false;  // Jan, Feb, Nov, Dec
      if (dt.mon > 3 && dt.mon < 10) return...`


### SessionRules.mqh

#### Potentially Unused Variable (15)

- **Severity:** medium
  - **Variable:** `EnableSessionCandles`

- **Severity:** medium
  - **Variable:** `SessionBarsToScan`

- **Severity:** medium
  - **Variable:** `ATR_London_MinPips`

- **Severity:** medium
  - **Variable:** `ATR_NY_MinPips`

- **Severity:** medium
  - **Variable:** `ATR_Overlap_MinPips`

- **Severity:** medium
  - **Variable:** `IndicesFlattenMinutes`

- **Severity:** medium
  - **Variable:** `EnableAutoFlatten`

- **Severity:** medium
  - **Variable:** `CloseLosingPositions`

- **Severity:** medium
  - **Variable:** `RemoveSLOnProfitable`

- **Severity:** medium
  - **Variable:** `secondSunday`

#### Unreachable Code (24)

- **Severity:** high
  - **Content:** `return 0.0;

   int deals = HistoryDealsTotal();
   for(int i = 0; i < deals; i+...`

- **Severity:** high
  - **Content:** `return -4; // EDT
      else
         return...`

- **Severity:** high
  - **Content:** `return -4; // EDT
      else
         return...`

- **Severity:** high
  - **Content:** `return INST_GOLD;
   if(StringFind(sym, "XAGUSD") >= 0 || StringFind(sym, "SILVE...`

- **Severity:** high
  - **Content:** `return 0;

   // Tokyo Session: EUR/GBP crosses, JPY pairs, Gold (Asian range ru...`

- **Severity:** high
  - **Content:** `return 1;
         case INST_FOREX_CROSS:  return 1;
         case INST_GOLD:   ...`

- **Severity:** high
  - **Content:** `return 1;
         case INST_FOREX_CROSS:  return 1;
         case INST_GOLD:   ...`

- **Severity:** high
  - **Content:** `return 1;
         case INST_FOREX_CROSS:  return 1;
         case INST_GOLD:   ...`

- **Severity:** high
  - **Content:** `return 1;
         case INST_FOREX_CROSS:  return 1;
         case INST_GOLD:   ...`

- **Severity:** high
  - **Content:** `return true;

   if(symbol == "") symbol = _Symbol;

   SESSION_RULE_TYPE sessio...`


### SignalRouter_Refactored.mqh

#### Commented Code (14)

- **Severity:** low
  - **Line:** 119
  - **Content:** `// myPoint is initialized in main EA OnInit()...`

- **Severity:** low
  - **Line:** 125
  - **Content:** `// CRITICAL: Print trading hours configuration for verification...`

- **Severity:** low
  - **Line:** 217
  - **Content:** `// (removed to avoid duplicate definitions)...`

- **Severity:** low
  - **Line:** 244
  - **Content:** `//==================================================================...`

- **Severity:** low
  - **Line:** 247
  - **Content:** `//==================================================================...`

- **Severity:** low
  - **Line:** 252
  - **Content:** `//==================================================================...`

- **Severity:** low
  - **Line:** 259
  - **Content:** `//==================================================================...`

- **Severity:** low
  - **Line:** 269
  - **Content:** `//==================================================================...`

- **Severity:** low
  - **Line:** 272
  - **Content:** `//==================================================================...`

- **Severity:** low
  - **Line:** 284
  - **Content:** `//==================================================================...`

#### Potentially Unused Variable (6)

- **Severity:** medium
  - **Variable:** `EnableMTFAlignment`

- **Severity:** medium
  - **Variable:** `pass_rate`

- **Severity:** medium
  - **Variable:** `any_signal`

- **Severity:** medium
  - **Variable:** `remaining`

- **Severity:** medium
  - **Variable:** `EXTREME_BULLISH`

- **Severity:** medium
  - **Variable:** `EXTREME_BEARISH`

#### Unreachable Code (4)

- **Severity:** high
  - **Content:** `returned 0. Cannot set NextTradeTime.");
      NextTradeTime = 0; // Fallback: a...`

- **Severity:** high
  - **Content:** `return;  // No signal, nothing to do

   g_filterDiag.signals_received++;

   //...`

- **Severity:** high
  - **Content:** `return 0.0;

   double wt_fast[], wt_slow[];
   ArraySetAsSeries(wt_fast, true);...`

- **Severity:** high
  - **Content:** `return false;

   // Read Buffer 10 (addPositionBuffer)
   double add_signal[];
...`


### StrategyManager.mqh

#### Commented Code (8)

- **Severity:** low
  - **Line:** 26
  - **Content:** `//| - Prevents negative SL when ST2 buffer returns EMPTY_VALUE      |...`

- **Severity:** low
  - **Line:** 137
  - **Content:** `// const int MAX_SL_TP_RETRIES = 5;      // Removed: Defined in TradingConstants...`

- **Severity:** low
  - **Line:** 138
  - **Content:** `// const int RETRY_DELAY_MS = 500;        // Removed: Defined in TradingConstant...`

- **Severity:** low
  - **Line:** 175
  - **Content:** `// v13.4: Always returns single breakout config...`

- **Severity:** low
  - **Line:** 363
  - **Content:** `//| v3.03: Renamed to avoid conflict with TradeOperationWrapper.mqh   |...`

- **Severity:** low
  - **Line:** 406
  - **Content:** `// const int MAX_CLOSE_RETRIES = 5;  // Removed: Defined in TradingConstants.mqh...`

- **Severity:** low
  - **Line:** 617
  - **Content:** `//=================================================================...`

- **Severity:** low
  - **Line:** 620
  - **Content:** `//=================================================================...`

#### Potentially Unused Variable (14)

- **Severity:** medium
  - **Variable:** `MAX_SL_TP_RETRIES`

- **Severity:** medium
  - **Variable:** `isConsolidating`

- **Severity:** medium
  - **Variable:** `mtf_direction`

- **Severity:** medium
  - **Variable:** `max_lot`

- **Severity:** medium
  - **Variable:** `st2_buf_index`

- **Severity:** medium
  - **Variable:** `pip_factor`

- **Severity:** medium
  - **Variable:** `current_ask`

- **Severity:** medium
  - **Variable:** `current_bid`

- **Severity:** medium
  - **Variable:** `current_tp`

- **Severity:** medium
  - **Variable:** `profit_points`

#### Unreachable Code (7)

- **Severity:** high
  - **Content:** `returns EMPTY_VALUE      |
//| - Falls back to 500pt SL if ST2 invalid          ...`

- **Severity:** high
  - **Content:** `return 0;

   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
 ...`

- **Severity:** high
  - **Content:** `return false;

   double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);...`

- **Severity:** high
  - **Content:** `return false;

   string comment = PositionGetString(POSITION_COMMENT);
   retur...`

- **Severity:** high
  - **Content:** `return false;

   string comment = PositionGetString(POSITION_COMMENT);
   retur...`

- **Severity:** high
  - **Content:** `return;

   if(PositionSelectByTicket(ticket))
   {
      double tp = PositionGe...`

- **Severity:** high
  - **Content:** `return;

   // Check total position limit
   int total_positions = CountAllStrat...`


### TradeDisciplineVerifier.mqh

#### Potentially Unused Variable (4)

- **Severity:** medium
  - **Variable:** `EmergencySL_ATR_Mult`

- **Severity:** medium
  - **Variable:** `EmergencySL_Max_Pts`

- **Severity:** medium
  - **Variable:** `sl_price`

- **Severity:** medium
  - **Variable:** `current_tp`

#### Unreachable Code (1)

- **Severity:** high
  - **Content:** `return false;

   double entry_price = PositionGetDouble(POSITION_PRICE_OPEN);
 ...`


### TradeOperationWrapper.mqh

#### Potentially Unused Variable (1)

- **Severity:** medium
  - **Variable:** `is_position`

#### Unreachable Code (5)

- **Severity:** high
  - **Content:** `return true;
            default:
                return...`

- **Severity:** high
  - **Content:** `return true;

            // MULTI-AGENT FIX: Non-retryable errors with explicit...`

- **Severity:** high
  - **Content:** `return;

        string prefix = exhausted ? "FAILED" : "ERROR";
        Print(p...`

- **Severity:** high
  - **Content:** `return;

        string prefix = exhausted ? "FAILED" : "ERROR";
        Print(p...`

- **Severity:** high
  - **Content:** `return "Server busy";
            case 6:    return "No connection";
           ...`


### TradingConstants.mqh

#### Potentially Unused Variable (29)

- **Severity:** medium
  - **Variable:** `ST2_SPREAD_OFFSET_MULTIPLIER`

- **Severity:** medium
  - **Variable:** `ST2_OPEN_PRICE_OFFSET_PCT`

- **Severity:** medium
  - **Variable:** `WT_OVERBOUGHT_EXIT`

- **Severity:** medium
  - **Variable:** `WT_OVERSOLD_EXIT`

- **Severity:** medium
  - **Variable:** `TC_EXTREME_LEVEL`

- **Severity:** medium
  - **Variable:** `TC_EXIT_THRESHOLD`

- **Severity:** medium
  - **Variable:** `TC_MTF_EXIT_REQUIREMENT`

- **Severity:** medium
  - **Variable:** `SAFETY_TIMEOUT_MINUTES`

- **Severity:** medium
  - **Variable:** `RETRY_DELAY_MS`

- **Severity:** medium
  - **Variable:** `MAX_SL_TP_RETRIES`


### TradingSessionsCandles.mq5

#### Potentially Unused Variable (14)

- **Severity:** medium
  - **Variable:** `Comment1`

- **Severity:** medium
  - **Variable:** `TokyoStart`

- **Severity:** medium
  - **Variable:** `TokyoEnd`

- **Severity:** medium
  - **Variable:** `LondonStart`

- **Severity:** medium
  - **Variable:** `LondonEnd`

- **Severity:** medium
  - **Variable:** `NewYorkStart`

- **Severity:** medium
  - **Variable:** `NewYorkEnd`

- **Severity:** medium
  - **Variable:** `Comment2`

- **Severity:** medium
  - **Variable:** `ColorTokyo`

- **Severity:** medium
  - **Variable:** `ColorLondon`

#### Unreachable Code (2)

- **Severity:** high
  - **Content:** `return CLR_OVERLAP_LN;
      if(in_tokyo && in_london)
         return...`

- **Severity:** high
  - **Content:** `return CLR_TOKYO;
   if(in_london && ColorLondon)
      return CLR_LONDON;
   if...`


### TrendCipher.mq5

#### Commented Code (47)

- **Severity:** low
  - **Line:** 153
  - **Content:** `//=== STEP 10 NOTE: MQL5 compiler optimization ===...`

- **Severity:** low
  - **Line:** 157
  - **Content:** `//====================================================...`

- **Severity:** low
  - **Line:** 477
  - **Content:** `//=== STEP 9 OPTIMIZATION: Static const alert strings ===...`

- **Severity:** low
  - **Line:** 489
  - **Content:** `//=======================================================...`

- **Severity:** low
  - **Line:** 722
  - **Content:** `//=================================================================...`

- **Severity:** low
  - **Line:** 725
  - **Content:** `//=================================================================...`

- **Severity:** low
  - **Line:** 727
  - **Content:** `// ALWAYS print startup diagnostic (helps debug compilation issues)...`

- **Severity:** low
  - **Line:** 904
  - **Content:** `// if(bullishSignInverted || bearishSignInverted) {...`

- **Severity:** low
  - **Line:** 1233
  - **Content:** `// Other instruments: Use point value directly...`

- **Severity:** low
  - **Line:** 1246
  - **Content:** `// ALWAYS print success message (helps confirm correct version loaded)...`

#### Potentially Unused Variable (86)

- **Severity:** medium
  - **Variable:** `useADXEntryFilter`

- **Severity:** medium
  - **Variable:** `showAllCrossovers`

- **Severity:** medium
  - **Variable:** `enableMTF_Filter`

- **Severity:** medium
  - **Variable:** `showZones`

- **Severity:** medium
  - **Variable:** `showEntryExit`

- **Severity:** medium
  - **Variable:** `showTrendMarkers`

- **Severity:** medium
  - **Variable:** `showConsolidation`

- **Severity:** medium
  - **Variable:** `showRSIMFI`

- **Severity:** medium
  - **Variable:** `useVolFilter`

- **Severity:** medium
  - **Variable:** `enableConfluenceFilter`

#### Unreachable Code (19)

- **Severity:** high
  - **Content:** `return false;

        datetime current = TimeCurrent();

        // v7.4 FIX: C...`

- **Severity:** high
  - **Content:** `return true;

    datetime now = TimeCurrent();
    MqlDateTime dt;
    TimeToSt...`

- **Severity:** high
  - **Content:** `return true;

    MqlDateTime dt;
    TimeToStruct(barTime, dt);

    int barMin...`

- **Severity:** high
  - **Content:** `return false;

    // MEDIUM-5 FIX: Validate that parts contain numeric content
...`

- **Severity:** high
  - **Content:** `return false;

    minutes = hours * 60 + mins;
    return...`

- **Severity:** high
  - **Content:** `return value
    datetime barTime = iTime(_Symbol, indicatorTimeframe, barIndex)...`

- **Severity:** high
  - **Content:** `return 0;

    double ema9_value[1];
    // PHASE 1 FIX: Use SafeCopyBuffer for ...`

- **Severity:** high
  - **Content:** `return value
    double price = iClose(_Symbol, tf, tfBar);
    if(price == 0 ||...`

- **Severity:** high
  - **Content:** `return true;  // Filter disabled

    // Get ATR value at this bar
    double cu...`

- **Severity:** high
  - **Content:** `return;

    double wt1 = BUFFER_SAFE_GET_DOUBLE(wt1Buffer, barIndex, 0.0);
    ...`


### TrendConfirmation.mqh

#### Commented Code (14)

- **Severity:** low
  - **Line:** 29
  - **Content:** `//| CRITICAL-3: Division by zero protection (_Point validation)      |...`

- **Severity:** low
  - **Line:** 39
  - **Content:** `//| HIGH-11: ArrayResize validation (check return value)             |...`

- **Severity:** low
  - **Line:** 521
  - **Content:** `// if(EnableTrendCipher && g_trendCipherHandle != INVALID_HANDLE && !g_trendCiph...`

- **Severity:** low
  - **Line:** 633
  - **Content:** `//| - Tracks processed boxes to avoid duplicate signals              |...`

- **Severity:** low
  - **Line:** 649
  - **Content:** `// MAX_PROCESSED_BOXES constant moved to TradingConstants.mqh to avoid duplicati...`

- **Severity:** low
  - **Line:** 785
  - **Content:** `// Only log each box skip once per minute to avoid spam...`

- **Severity:** low
  - **Line:** 838
  - **Content:** `// v3.11: FIX HIGH-7 - M15 filter now returns status code (check return value)...`

- **Severity:** low
  - **Line:** 871
  - **Content:** `// v3.11: FIX HIGH-7 - M15 filter now returns status code (check return value)...`

- **Severity:** low
  - **Line:** 1211
  - **Content:** `// === LOG SIGNAL DETECTION ===...`

- **Severity:** low
  - **Line:** 1247
  - **Content:** `// === CONFLICT CHECK ===...`

#### Potentially Unused Variable (55)

- **Severity:** medium
  - **Variable:** `ATRMultiplier1`

- **Severity:** medium
  - **Variable:** `ATRPeriod1`

- **Severity:** medium
  - **Variable:** `ATRMaxBars`

- **Severity:** medium
  - **Variable:** `g_tcHandle_M5`

- **Severity:** medium
  - **Variable:** `g_tcHandle_H2`

- **Severity:** medium
  - **Variable:** `g_tcHandle_H4`

- **Severity:** medium
  - **Variable:** `g_trendFlipPrice_M15`

- **Severity:** medium
  - **Variable:** `g_trendFlipPrice_H1`

- **Severity:** medium
  - **Variable:** `g_trendFlipPrice_H2`

- **Severity:** medium
  - **Variable:** `g_trendFlipPrice_H4`

#### Unreachable Code (12)

- **Severity:** high
  - **Content:** `return value)             |
//| HIGH-12: Box price from LEIlight crossover (not ...`

- **Severity:** high
  - **Content:** `returned handle: ", g_leiHandle);
      if(g_leiHandle == INVALID_HANDLE)
      ...`

- **Severity:** high
  - **Content:** `return;  // Only try once
   g_firstTickProcessed = true;

   // Retry LEIlight ...`

- **Severity:** high
  - **Content:** `return;  // Already preloaded

   int total_objects = ObjectsTotal(ChartID(), 0,...`

- **Severity:** high
  - **Content:** `return;

   // Read discrete entry signals (Buffer 23/24 - Zone + ADX filtered)
...`

- **Severity:** high
  - **Content:** `return;

   if(general_signal.bullish)
   {
      datetime signal_time = iTime(_...`

- **Severity:** high
  - **Content:** `return;  // Already drawn

   // Determine marker properties based on direction
...`

- **Severity:** high
  - **Content:** `return false;

   double lowestPrice = priceLows[lowestPriceIndex];
   double lo...`

- **Severity:** high
  - **Content:** `return -1;

   double sum = 0.0;
   for(int i = 0; i < copied; ++i)
   {
      s...`

- **Severity:** high
  - **Content:** `return sum / (double)copied;

   return...`


### WinAnalyzer.mqh

#### Commented Code (4)

- **Severity:** low
  - **Line:** 86
  - **Content:** `//| Deinit — print summary                                            |...`

- **Severity:** low
  - **Line:** 190
  - **Content:** `//| On trade close — if winning, print structured block               |...`

- **Severity:** low
  - **Line:** 260
  - **Content:** `// ===== PRINT STRUCTURED BLOCK =====...`

- **Severity:** low
  - **Line:** 317
  - **Content:** `// ===== WRITE CSV ROW =====...`

#### Potentially Unused Variable (1)

- **Severity:** medium
  - **Variable:** `duration_sec`

#### Unreachable Code (4)

- **Severity:** high
  - **Content:** `return;
   ArrayResize(g_wa_snapshots, 0);
   g_wa_count = 0;
   g_wa_total_wins...`

- **Severity:** high
  - **Content:** `return;
   if(g_wa_total_wins > 0)
   {
      Print("=== WIN ANALYZER SUMMARY ==...`

- **Severity:** high
  - **Content:** `return;
   int idx = g_wa_count;
   g_wa_count++;
   ArrayResize(g_wa_snapshots,...`

- **Severity:** high
  - **Content:** `return;
   int idx = WA_FindSlot(ticket);
   if(idx < 0) return;

   double tota...`


