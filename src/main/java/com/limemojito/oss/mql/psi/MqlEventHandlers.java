/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi;

import java.util.Set;

/**
 * The canonical set of MQL4/MQL5 event-handler function names ({@code OnInit}, {@code OnTick},
 * ...). Several inspections and editor features independently need "is this function an event
 * handler" -- this is the single shared catalog for that question, so the list only lives in one
 * place. Consumers that mean "the full event-handler set" should reference {@link #NAMES}
 * directly; a consumer that intentionally targets a narrower subset (e.g. just the tick-driven
 * handlers {@code OnTick}/{@code OnCalculate}) should keep its own smaller set rather than
 * filtering this one, since that subset is a deliberate design choice, not a duplicate of the
 * full catalog.
 */
public final class MqlEventHandlers {

    public static final Set<String> NAMES = Set.of(
            "OnInit", "OnDeinit", "OnTick", "OnCalculate", "OnStart", "OnTimer",
            "OnTrade", "OnTradeTransaction", "OnBookEvent", "OnChartEvent",
            "OnTester", "OnTesterInit", "OnTesterDeinit", "OnTesterPass"
    );

    private MqlEventHandlers() {
    }
}
