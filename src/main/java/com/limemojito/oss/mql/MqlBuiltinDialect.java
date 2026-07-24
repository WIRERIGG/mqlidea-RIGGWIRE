/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql;

import com.limemojito.oss.mql.inspection.ModernMQL5IdiomInspection;
import org.jetbrains.annotations.NotNull;

import java.util.HashSet;
import java.util.Set;

/**
 * Curated sets of built-in function names that exist in exactly one MQL dialect, used by
 * completion (REVAMP_PLAN.md Phase 6) to stop proposing calls the compiler would reject in the
 * current file's dialect (e.g. {@code IsTradeContextBusy}/{@code RefreshRates}/{@code OrderClose}/
 * {@code MarketInfo}/{@code AccountBalance} in a {@code .mq5} file, or {@code PositionGetTicket}/
 * {@code CopyBuffer}/{@code SymbolInfoDouble} in a {@code .mq4} file).
 *
 * <p>The MQL4-only half of this reuses {@link ModernMQL5IdiomInspection}'s already-curated
 * deprecated-function map rather than duplicating it, plus a handful of additional MQL4-only
 * names that inspection doesn't need (it only cares about functions with a direct MQL5
 * replacement, not e.g. the {@code Window*}/{@code SetIndex*} family that simply has no MQL5
 * equivalent at all).</p>
 *
 * <p>Best-effort, not exhaustive: MQL has ~2,000 built-ins and a few names exist in both dialects
 * with different signatures (e.g. {@code OrderSend}, {@code SetIndexBuffer}) -- those are
 * deliberately left out of both sets so completion never wrongly hides a legal call. Coverage can
 * grow over time; the intent is "never propose something the compiler will reject", not "propose
 * every dialect nuance".</p>
 */
public final class MqlBuiltinDialect {

    private MqlBuiltinDialect() {
    }

    /** Functions that exist in MQL4 but have no MQL5 equivalent at all (or a different name entirely). */
    public static final Set<String> MQL4_ONLY_FUNCTIONS = buildMql4OnlySet();

    /** Functions that exist only in MQL5 (position/order-history/symbol-info API, absent from MQL4). */
    public static final Set<String> MQL5_ONLY_FUNCTIONS = Set.of(
            // Positions (MQL5 has no concept of "positions" as distinct from orders in MQL4)
            "PositionSelect", "PositionSelectByTicket", "PositionGetDouble", "PositionGetInteger",
            "PositionGetString", "PositionGetSymbol", "PositionGetTicket", "PositionsTotal",
            // Order/deal history (HistorySelect family replaces OrdersHistoryTotal + OrderSelect(MODE_HISTORY))
            "OrderGetTicket", "OrderGetDouble", "OrderGetInteger", "OrderGetString",
            "OrderCheck", "OrderCalcMargin", "OrderCalcProfit",
            "HistorySelect", "HistorySelectByPosition",
            "HistoryDealsTotal", "HistoryDealGetTicket", "HistoryDealGetDouble", "HistoryDealGetInteger", "HistoryDealGetString",
            "HistoryOrdersTotal", "HistoryOrderGetTicket", "HistoryOrderGetDouble", "HistoryOrderGetInteger", "HistoryOrderGetString",
            // Symbol/account info (replaces MarketInfo()/Account*() single-purpose calls)
            "SymbolInfoDouble", "SymbolInfoInteger", "SymbolInfoString", "SymbolInfoTick", "SymbolInfoSessionQuote", "SymbolInfoSessionTrade",
            "AccountInfoDouble", "AccountInfoInteger", "AccountInfoString",
            "TerminalInfoDouble", "TerminalInfoInteger", "TerminalInfoString",
            "MQLInfoInteger", "MQLInfoString",
            // Series copy API (replaces the raw array-based MQL4 series access)
            "CopyRates", "CopyTime", "CopyOpen", "CopyHigh", "CopyLow", "CopyClose",
            "CopyTickVolume", "CopyRealVolume", "CopySpread", "CopyBuffer", "CopyTicks", "CopyTicksRange",
            "IndicatorRelease", "BarsCalculated",
            // Plot/indicator buffer setup (replaces SetIndexStyle/SetIndexLabel/...)
            "PlotIndexSetDouble", "PlotIndexSetInteger", "PlotIndexSetString", "PlotIndexGetInteger",
            "IndicatorSetDouble", "IndicatorSetInteger", "IndicatorSetString",
            // Chart-attached indicators (replaces WindowHandle/iCustom-on-window plumbing)
            "ChartIndicatorAdd", "ChartIndicatorDelete", "ChartIndicatorGet", "ChartIndicatorName", "ChartIndicatorsTotal",
            // Object property access (replaces ObjectGet/ObjectSet single-purpose calls)
            "ObjectGetDouble", "ObjectGetInteger", "ObjectGetString",
            "ObjectSetDouble", "ObjectSetInteger", "ObjectSetString",
            "ResetLastError"
    );

    @NotNull
    private static Set<String> buildMql4OnlySet() {
        Set<String> names = new HashSet<>(ModernMQL5IdiomInspection.deprecatedMql4OnlyFunctionNames());
        names.addAll(Set.of(
                // Trade-context / environment checks with no MQL5 equivalent function
                "RefreshRates", "IsTradeContextBusy", "IsTradeAllowed", "IsExpertEnabled",
                "IsOptimization", "IsTesting", "IsVisualMode", "IsDllsAllowed", "IsLibrariesAllowed",
                "HideTestIndicators",
                // Order operations only meaningful in MQL4's ticket model
                "OrderCloseBy", "OrdersHistoryTotal",
                // Custom-indicator buffer setup (replaced by Plot*/IndicatorSet* in MQL5)
                "SetIndexStyle", "SetIndexLabel", "SetIndexArrow", "SetIndexDrawBegin", "SetIndexShift",
                "IndicatorDigits", "IndicatorShortName", "IndicatorCounted", "IndicatorBuffers",
                // Window/chart-subwindow API removed in MQL5 (replaced by Chart* functions)
                "WindowHandle", "WindowOnDropped", "WindowsTotal", "WindowBarsPerChart", "WindowExpertName",
                "WindowFind", "WindowFirstVisibleBar", "WindowIsVisible", "WindowPriceMax", "WindowPriceMin",
                "WindowPriceOnDropped", "WindowRedraw", "WindowScreenShot", "WindowTimeOnDropped",
                "WindowTimePerSegment", "WindowXOnDropped", "WindowYOnDropped"
        ));
        return names;
    }

    /** True when {@code name} is known to not exist in the given dialect and should not be completed there. */
    public static boolean isExcludedFromDialect(@NotNull String name, boolean isMql5) {
        return isMql5 ? MQL4_ONLY_FUNCTIONS.contains(name) : MQL5_ONLY_FUNCTIONS.contains(name);
    }
}
