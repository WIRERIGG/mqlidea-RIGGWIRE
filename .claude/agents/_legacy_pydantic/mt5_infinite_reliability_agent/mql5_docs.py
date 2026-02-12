"""
MQL5 Documentation Access Module

Provides permanent access to MQL5 documentation for the MT5 Infinite Reliability Agent.
Includes built-in reference data and web fetch capabilities.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# BUILT-IN MQL5 REFERENCE DATA
# ============================================================================

MQL5_DOCUMENTATION = {
    "event_handlers": {
        "OnInit": {
            "signature": "int OnInit(void)",
            "description": "Called during EA/indicator initialization",
            "return_values": {
                "INIT_SUCCEEDED": "Successful initialization",
                "INIT_FAILED": "Initialization failed",
                "INIT_PARAMETERS_INCORRECT": "Invalid input parameters"
            },
            "best_practices": [
                "Initialize indicator handles here, NOT in OnTick()",
                "Validate input parameters",
                "Set up global variables",
                "Return INIT_FAILED if critical resources unavailable"
            ],
            "url": "https://www.mql5.com/en/docs/event_handlers/oninit"
        },
        "OnDeinit": {
            "signature": "void OnDeinit(const int reason)",
            "description": "Called during EA/indicator deinitialization",
            "reason_codes": {
                "REASON_PROGRAM": "Expert removed from chart",
                "REASON_REMOVE": "Program removed from chart",
                "REASON_RECOMPILE": "Program recompiled",
                "REASON_CHARTCHANGE": "Symbol or period changed",
                "REASON_CHARTCLOSE": "Chart closed",
                "REASON_PARAMETERS": "Input parameters changed",
                "REASON_ACCOUNT": "Account changed"
            },
            "best_practices": [
                "Release indicator handles with IndicatorRelease()",
                "Clean up dynamic arrays",
                "Close open files",
                "Save state if needed"
            ],
            "url": "https://www.mql5.com/en/docs/event_handlers/ondeinit"
        },
        "OnTick": {
            "signature": "void OnTick(void)",
            "description": "Called on every new tick for the symbol",
            "best_practices": [
                "Minimize computation - called frequently",
                "Use NewBarTrigger() pattern for heavy calculations",
                "Cache indicator values, don't recalculate every tick",
                "Check IsStopped() for graceful termination"
            ],
            "performance_tips": [
                "Move indicator handle creation to OnInit()",
                "Use static variables for state persistence",
                "Avoid string operations in tight loops",
                "Batch CopyBuffer() calls"
            ],
            "url": "https://www.mql5.com/en/docs/event_handlers/ontick"
        },
        "OnCalculate": {
            "signature": "int OnCalculate(const int rates_total, const int prev_calculated, ...)",
            "description": "Called for indicator calculations on each new tick",
            "parameters": {
                "rates_total": "Total number of bars",
                "prev_calculated": "Bars calculated in previous call",
                "time[]": "Time array",
                "open[]": "Open prices",
                "high[]": "High prices",
                "low[]": "Low prices",
                "close[]": "Close prices",
                "tick_volume[]": "Tick volumes",
                "volume[]": "Real volumes",
                "spread[]": "Spreads"
            },
            "optimization_pattern": """
// Optimized calculation loop
int start = (prev_calculated == 0) ? 0 : prev_calculated - 1;
for(int i = start; i < rates_total; i++)
{
    // Calculate only new bars
}
return rates_total;
""",
            "url": "https://www.mql5.com/en/docs/event_handlers/oncalculate"
        }
    },

    "indicator_functions": {
        "iMA": {
            "signature": "int iMA(symbol, timeframe, ma_period, ma_shift, ma_method, applied_price)",
            "description": "Creates Moving Average indicator handle",
            "ma_methods": {
                "MODE_SMA": "Simple Moving Average",
                "MODE_EMA": "Exponential Moving Average",
                "MODE_SMMA": "Smoothed Moving Average",
                "MODE_LWMA": "Linear Weighted Moving Average"
            },
            "caching_pattern": """
// Cache MA handle in OnInit()
int ma_handle;
int OnInit()
{
    ma_handle = iMA(_Symbol, PERIOD_CURRENT, 14, 0, MODE_SMA, PRICE_CLOSE);
    if(ma_handle == INVALID_HANDLE) return INIT_FAILED;
    return INIT_SUCCEEDED;
}
""",
            "url": "https://www.mql5.com/en/docs/indicators/ima"
        },
        "iRSI": {
            "signature": "int iRSI(symbol, timeframe, period, applied_price)",
            "description": "Creates RSI indicator handle",
            "typical_periods": [14, 7, 21],
            "interpretation": {
                "overbought": "> 70",
                "oversold": "< 30",
                "neutral": "30-70"
            },
            "url": "https://www.mql5.com/en/docs/indicators/irsi"
        },
        "iATR": {
            "signature": "int iATR(symbol, timeframe, period)",
            "description": "Creates Average True Range indicator handle",
            "use_cases": [
                "Stop loss calculation",
                "Position sizing",
                "Volatility filtering"
            ],
            "url": "https://www.mql5.com/en/docs/indicators/iatr"
        },
        "CopyBuffer": {
            "signature": "int CopyBuffer(indicator_handle, buffer_num, start_pos, count, buffer[])",
            "description": "Copies indicator buffer data to array",
            "best_practices": [
                "Call ArraySetAsSeries() before accessing",
                "Check return value for errors",
                "Minimize calls by copying multiple values at once",
                "Cache results to avoid repeated calls"
            ],
            "error_handling": """
double buffer[];
ArraySetAsSeries(buffer, true);
if(CopyBuffer(handle, 0, 0, 10, buffer) <= 0)
{
    Print("CopyBuffer failed: ", GetLastError());
    return;
}
""",
            "url": "https://www.mql5.com/en/docs/indicators/copybuffer"
        }
    },

    "trading_functions": {
        "OrderSend": {
            "signature": "bool OrderSend(MqlTradeRequest& request, MqlTradeResult& result)",
            "description": "Sends trade request to server",
            "request_fields": {
                "action": "TRADE_ACTION_DEAL, TRADE_ACTION_PENDING, etc.",
                "symbol": "Trading symbol",
                "volume": "Lot size",
                "type": "ORDER_TYPE_BUY, ORDER_TYPE_SELL, etc.",
                "price": "Order price",
                "sl": "Stop Loss",
                "tp": "Take Profit",
                "deviation": "Maximum price deviation",
                "magic": "Expert Advisor ID",
                "comment": "Order comment"
            },
            "error_handling": """
MqlTradeRequest request = {};
MqlTradeResult result = {};
request.action = TRADE_ACTION_DEAL;
// ... fill request ...
if(!OrderSend(request, result))
{
    Print("OrderSend failed: ", result.retcode);
    return false;
}
""",
            "url": "https://www.mql5.com/en/docs/trading/ordersend"
        },
        "PositionSelect": {
            "signature": "bool PositionSelect(string symbol)",
            "description": "Selects position by symbol for further operations",
            "related_functions": [
                "PositionGetDouble()",
                "PositionGetInteger()",
                "PositionGetString()"
            ],
            "url": "https://www.mql5.com/en/docs/trading/positionselect"
        }
    },

    "array_functions": {
        "ArraySetAsSeries": {
            "signature": "bool ArraySetAsSeries(array[], bool flag)",
            "description": "Sets array indexing direction (true = newest at [0])",
            "critical_note": "MUST be called before accessing time series data",
            "example": """
double close[];
ArraySetAsSeries(close, true);  // Now close[0] = most recent bar
CopyClose(_Symbol, PERIOD_CURRENT, 0, 100, close);
""",
            "url": "https://www.mql5.com/en/docs/array/arraysetasseries"
        },
        "ArrayResize": {
            "signature": "int ArrayResize(array[], int new_size, int reserve_size=0)",
            "description": "Resizes dynamic array",
            "performance_tip": "Use reserve_size for arrays that grow frequently",
            "url": "https://www.mql5.com/en/docs/array/arrayresize"
        }
    },

    "ftmo_compliance": {
        "rules": {
            "daily_loss_limit": {
                "threshold": "5% of initial balance",
                "description": "Maximum loss allowed per trading day",
                "implementation": """
double GetDailyLossPercent()
{
    double initial_balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double current_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    // Get today's starting balance from history
    return ((initial_balance - current_equity) / initial_balance) * 100;
}

bool IsDailyLossExceeded()
{
    return GetDailyLossPercent() >= 4.5; // Warning at 4.5%
}
"""
            },
            "max_drawdown": {
                "threshold": "10% of initial balance",
                "description": "Maximum overall drawdown allowed",
                "implementation": """
double GetCurrentDrawdown()
{
    static double peak_equity = 0;
    double current_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    if(current_equity > peak_equity) peak_equity = current_equity;
    return ((peak_equity - current_equity) / peak_equity) * 100;
}

bool IsMaxDrawdownExceeded()
{
    return GetCurrentDrawdown() >= 9.5; // Warning at 9.5%
}
"""
            },
            "trading_days": {
                "minimum": "4 trading days during evaluation",
                "description": "Must trade on at least 4 different days"
            },
            "profit_target": {
                "phase1": "10% profit target",
                "phase2": "5% profit target"
            }
        },
        "emergency_stop": {
            "description": "Immediate halt when limits approached",
            "implementation": """
bool IsTradingAllowed()
{
    if(IsDailyLossExceeded())
    {
        Print("EMERGENCY: Daily loss limit reached!");
        return false;
    }
    if(IsMaxDrawdownExceeded())
    {
        Print("EMERGENCY: Max drawdown limit reached!");
        return false;
    }
    return true;
}

void OnTick()
{
    if(!IsTradingAllowed()) return;
    // ... trading logic ...
}
"""
        }
    },

    "optimization_patterns": {
        "new_bar_trigger": {
            "description": "Execute heavy logic only on new bars",
            "code": """
bool NewBarTrigger()
{
    static datetime last_bar_time = 0;
    datetime current_bar_time = iTime(_Symbol, PERIOD_CURRENT, 0);
    if(current_bar_time != last_bar_time)
    {
        last_bar_time = current_bar_time;
        return true;
    }
    return false;
}

void OnTick()
{
    if(!NewBarTrigger()) return; // Skip if same bar
    // Heavy calculations here...
}
"""
        },
        "indicator_caching": {
            "description": "Cache indicator values to avoid repeated calculations",
            "code": """
class CachedIndicator
{
private:
    int m_handle;
    double m_values[];
    datetime m_last_update;

public:
    bool Init(string symbol, ENUM_TIMEFRAMES tf, int period)
    {
        m_handle = iMA(symbol, tf, period, 0, MODE_SMA, PRICE_CLOSE);
        ArraySetAsSeries(m_values, true);
        return m_handle != INVALID_HANDLE;
    }

    double GetValue(int shift)
    {
        datetime bar_time = iTime(_Symbol, PERIOD_CURRENT, 0);
        if(bar_time != m_last_update)
        {
            CopyBuffer(m_handle, 0, 0, shift + 1, m_values);
            m_last_update = bar_time;
        }
        return m_values[shift];
    }
};
"""
        }
    }
}


class MQL5DocumentationService:
    """Service for accessing MQL5 documentation."""

    def __init__(self):
        self.docs = MQL5_DOCUMENTATION
        self.cache = {}
        self.last_fetch = None

    def search(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        """
        Search MQL5 documentation for relevant information.

        Args:
            query: Search query
            category: Optional category filter

        Returns:
            List of matching documentation entries
        """
        results = []
        query_lower = query.lower()

        categories_to_search = [category] if category else self.docs.keys()

        for cat in categories_to_search:
            if cat not in self.docs:
                continue

            cat_docs = self.docs[cat]
            for name, info in cat_docs.items():
                # Check if query matches
                if query_lower in name.lower():
                    results.append({
                        "category": cat,
                        "name": name,
                        "info": info,
                        "relevance": "high"
                    })
                elif isinstance(info, dict):
                    desc = info.get("description", "")
                    if query_lower in desc.lower():
                        results.append({
                            "category": cat,
                            "name": name,
                            "info": info,
                            "relevance": "medium"
                        })

        return results

    def get_event_handler(self, name: str) -> Optional[Dict[str, Any]]:
        """Get documentation for an event handler."""
        return self.docs.get("event_handlers", {}).get(name)

    def get_indicator_function(self, name: str) -> Optional[Dict[str, Any]]:
        """Get documentation for an indicator function."""
        return self.docs.get("indicator_functions", {}).get(name)

    def get_trading_function(self, name: str) -> Optional[Dict[str, Any]]:
        """Get documentation for a trading function."""
        return self.docs.get("trading_functions", {}).get(name)

    def get_ftmo_rules(self) -> Dict[str, Any]:
        """Get FTMO compliance rules and implementations."""
        return self.docs.get("ftmo_compliance", {})

    def get_optimization_pattern(self, name: str) -> Optional[Dict[str, Any]]:
        """Get an optimization pattern."""
        return self.docs.get("optimization_patterns", {}).get(name)

    def get_best_practices(self, topic: str) -> List[str]:
        """Get best practices for a specific topic."""
        practices = []

        # Search all categories for best_practices
        for category in self.docs.values():
            if isinstance(category, dict):
                for name, info in category.items():
                    if topic.lower() in name.lower() and isinstance(info, dict):
                        if "best_practices" in info:
                            practices.extend(info["best_practices"])

        return practices

    def get_code_template(self, template_type: str) -> Optional[str]:
        """Get a code template for common patterns."""
        templates = {
            "new_bar_trigger": self.docs["optimization_patterns"]["new_bar_trigger"]["code"],
            "indicator_caching": self.docs["optimization_patterns"]["indicator_caching"]["code"],
            "ftmo_daily_loss": self.docs["ftmo_compliance"]["rules"]["daily_loss_limit"]["implementation"],
            "ftmo_drawdown": self.docs["ftmo_compliance"]["rules"]["max_drawdown"]["implementation"],
            "ftmo_emergency_stop": self.docs["ftmo_compliance"]["emergency_stop"]["implementation"],
            "copybuffer_error": self.docs["indicator_functions"]["CopyBuffer"]["error_handling"],
            "ordersend_error": self.docs["trading_functions"]["OrderSend"]["error_handling"]
        }
        return templates.get(template_type)

    def generate_documentation_report(self, code: str) -> Dict[str, Any]:
        """
        Analyze code and generate relevant documentation references.

        Args:
            code: MQL5 source code

        Returns:
            Report with relevant documentation and recommendations
        """
        report = {
            "detected_functions": [],
            "recommendations": [],
            "best_practices": [],
            "ftmo_compliance": {"checks": [], "missing": []}
        }

        # Detect event handlers
        for handler in ["OnInit", "OnDeinit", "OnTick", "OnCalculate"]:
            if handler + "()" in code or handler + "(" in code:
                doc = self.get_event_handler(handler)
                if doc:
                    report["detected_functions"].append({
                        "name": handler,
                        "type": "event_handler",
                        "documentation": doc.get("url")
                    })
                    report["best_practices"].extend(doc.get("best_practices", []))

        # Detect indicator functions
        indicators = ["iMA", "iRSI", "iATR", "iMACD", "iBands", "CopyBuffer"]
        for ind in indicators:
            if ind + "(" in code:
                doc = self.get_indicator_function(ind)
                if doc:
                    report["detected_functions"].append({
                        "name": ind,
                        "type": "indicator",
                        "documentation": doc.get("url") if doc else None
                    })

        # Check FTMO compliance
        ftmo_checks = [
            ("GetDailyLossPercent", "Daily loss tracking"),
            ("GetCurrentDrawdown", "Drawdown monitoring"),
            ("IsTradingAllowed", "Emergency stop mechanism"),
            ("daily", "Daily loss reference"),
            ("drawdown", "Drawdown reference")
        ]

        for pattern, description in ftmo_checks:
            if pattern.lower() in code.lower():
                report["ftmo_compliance"]["checks"].append(description)
            else:
                report["ftmo_compliance"]["missing"].append(description)

        return report


# Global documentation service instance
mql5_docs = MQL5DocumentationService()


def get_mql5_documentation(query: str, category: str = None) -> List[Dict[str, Any]]:
    """
    Search MQL5 documentation.

    Args:
        query: Search query
        category: Optional category filter

    Returns:
        Matching documentation entries
    """
    return mql5_docs.search(query, category)


def get_ftmo_compliance_guide() -> Dict[str, Any]:
    """Get complete FTMO compliance guide."""
    return mql5_docs.get_ftmo_rules()


def get_optimization_template(template_type: str) -> Optional[str]:
    """Get optimization code template."""
    return mql5_docs.get_code_template(template_type)


def analyze_code_documentation_needs(code: str) -> Dict[str, Any]:
    """Analyze code and return relevant documentation."""
    return mql5_docs.generate_documentation_report(code)


__all__ = [
    "MQL5DocumentationService",
    "mql5_docs",
    "get_mql5_documentation",
    "get_ftmo_compliance_guide",
    "get_optimization_template",
    "analyze_code_documentation_needs",
    "MQL5_DOCUMENTATION"
]
