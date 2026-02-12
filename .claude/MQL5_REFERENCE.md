# MQL5 Complete Reference Guide

> Comprehensive reference for Claude agents working with MQL5/MetaTrader 5 Expert Advisors
> Source: https://www.mql5.com/en/docs

---

## Table of Contents

1. [Language Overview](#language-overview)
2. [Program Types](#program-types)
3. [Event Handlers](#event-handlers)
4. [Predefined Variables](#predefined-variables)
5. [Data Structures](#data-structures)
6. [Trade Functions](#trade-functions)
7. [Order Types & Constants](#order-types--constants)
8. [Trade Return Codes](#trade-return-codes)
9. [Timeseries & Indicators Access](#timeseries--indicators-access)
10. [Technical Indicators](#technical-indicators)
11. [Account Information](#account-information)
12. [Market Information](#market-information)
13. [Symbol Properties](#symbol-properties)
14. [Timeframe Constants](#timeframe-constants)
15. [Common Functions](#common-functions)
16. [Standard Library](#standard-library)
17. [Best Practices](#best-practices)

---

## Language Overview

MQL5 is an object-oriented high-level programming language designed for writing automated trading strategies and custom technical indicators for the MetaTrader 5 platform. It builds upon C++ principles.

### Key Features
- Object-Oriented Programming (classes, inheritance, encapsulation)
- Enumerations for type-safe constants
- Structures for data organization
- Event handling mechanisms
- Namespaces for code organization

### Documentation Sections
1. **Syntax** - Language grammar and structure
2. **Data Types** - Built-in and custom types
3. **Operations and Expressions** - Computational mechanics
4. **Operators** - Functional symbols
5. **Functions** - Reusable code blocks
6. **Variables** - Data storage and scope
7. **Preprocessor** - Compilation directives
8. **Object-Oriented Programming** - Classes, inheritance
9. **Namespaces** - Scope control

---

## Program Types

MQL5 supports five application categories:

| Type | Purpose |
|------|---------|
| **Expert Advisors (EA)** | Automated trading systems that execute trades |
| **Custom Indicators** | User-developed technical analysis tools |
| **Scripts** | Single-execution programs for one-time tasks |
| **Services** | Background applications running continuously |
| **Libraries** | Reusable function repositories |
| **Include Files** | Code modules for sharing between programs |

---

## Event Handlers

### Core Event Handlers

```cpp
// Initialization - called once when EA/indicator starts
int OnInit() {
    // Return INIT_SUCCEEDED or error code
    return INIT_SUCCEEDED;
}

// Deinitialization - called when EA/indicator stops
void OnDeinit(const int reason) {
    // Cleanup code here
}

// New tick event - called on every price change (EAs only)
void OnTick() {
    // Main trading logic here
}

// Timer event - called at fixed intervals
void OnTimer() {
    // Periodic tasks
}

// Chart event - mouse clicks, key presses, object events
void OnChartEvent(const int id, const long& lparam,
                  const double& dparam, const string& sparam) {
    // Handle chart interactions
}
```

### Trading Event Handlers

```cpp
// Trade event - after trading operation completes
void OnTrade() {
    // React to trade changes
}

// Trade transaction - detailed trade operation info
void OnTradeTransaction(const MqlTradeTransaction& trans,
                        const MqlTradeRequest& request,
                        const MqlTradeResult& result) {
    // Process trade transactions
}

// Market depth changes
void OnBookEvent(const string& symbol) {
    // Handle order book updates
}
```

### Indicator-Specific Handler

```cpp
// Calculate event - process price data changes
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime& time[],
                const double& open[],
                const double& high[],
                const double& low[],
                const double& close[],
                const long& tick_volume[],
                const long& volume[],
                const int& spread[]) {
    // Indicator calculation logic
    return rates_total;
}
```

### Script Handler

```cpp
// Start event - scripts only
void OnStart() {
    // Script execution code
}
```

### Strategy Tester Handlers

```cpp
double OnTester()                    // After backtesting
void OnTesterInit()                  // Before optimization
void OnTesterDeinit()                // After optimization
void OnTesterPass()                  // Process optimization pass
```

---

## Predefined Variables

| Variable | Type | Purpose |
|----------|------|---------|
| `_Symbol` | string | Current chart symbol name |
| `_Period` | ENUM_TIMEFRAMES | Current chart timeframe |
| `_Digits` | int | Decimal places for symbol |
| `_Point` | double | Point size in quote currency |
| `_LastError` | int | Last error code (resettable) |
| `_UninitReason` | int | Deinitialization reason |
| `_AppliedTo` | int | Data type for indicator calculation |
| `_RandomSeed` | int | Pseudo-random generator state |
| `_StopFlag` | bool | Program stop flag |
| `_IsX64` | bool | 64-bit terminal flag |

---

## Data Structures

### MqlRates - Bar/Candlestick Data

```cpp
struct MqlRates {
    datetime time;         // Period start time
    double   open;         // Open price
    double   high;         // Highest price
    double   low;          // Lowest price
    double   close;        // Close price
    long     tick_volume;  // Tick volume
    int      spread;       // Spread
    long     real_volume;  // Trade volume
};
```

### MqlTick - Tick Data

```cpp
struct MqlTick {
    datetime time;         // Time of last update
    double   bid;          // Current Bid price
    double   ask;          // Current Ask price
    double   last;         // Last deal price
    ulong    volume;       // Volume for Last price
    long     time_msc;     // Time in milliseconds
    uint     flags;        // Tick flags
    double   volume_real;  // Volume with greater accuracy
};
```

### MqlTradeRequest - Trade Operation Request

```cpp
struct MqlTradeRequest {
    ENUM_TRADE_REQUEST_ACTIONS action;    // Trade operation type
    ulong                      magic;     // EA identifier
    ulong                      order;     // Order ticket
    string                     symbol;    // Trade symbol
    double                     volume;    // Volume in lots
    double                     price;     // Execution price
    double                     stoplimit; // StopLimit level
    double                     sl;        // Stop Loss
    double                     tp;        // Take Profit
    ulong                      deviation; // Max price deviation (points)
    ENUM_ORDER_TYPE            type;      // Order type
    ENUM_ORDER_TYPE_FILLING    type_filling; // Execution type
    ENUM_ORDER_TYPE_TIME       type_time;    // Expiration type
    datetime                   expiration;   // Expiration time
    string                     comment;      // Order comment
    ulong                      position;     // Position ticket
    ulong                      position_by;  // Opposite position ticket
};
```

### MqlTradeResult - Trade Operation Result

```cpp
struct MqlTradeResult {
    uint   retcode;          // Return code
    ulong  deal;             // Deal ticket (if executed)
    ulong  order;            // Order ticket (if placed)
    double volume;           // Confirmed volume
    double price;            // Confirmed price
    double bid;              // Current Bid
    double ask;              // Current Ask
    string comment;          // Broker comment
    uint   request_id;       // Request ID
    int    retcode_external; // External system code
};
```

---

## Trade Functions

### Order Execution

```cpp
// Send trade request (synchronous)
bool OrderSend(MqlTradeRequest& request, MqlTradeResult& result);

// Send trade request (asynchronous)
bool OrderSendAsync(MqlTradeRequest& request, MqlTradeResult& result);

// Check if trade request is valid
bool OrderCheck(MqlTradeRequest& request, MqlTradeCheckResult& result);

// Calculate required margin
bool OrderCalcMargin(ENUM_ORDER_TYPE action, string symbol,
                     double volume, double price, double& margin);

// Calculate potential profit
bool OrderCalcProfit(ENUM_ORDER_TYPE action, string symbol,
                     double volume, double price_open,
                     double price_close, double& profit);
```

### Active Orders

```cpp
int    OrdersTotal();                    // Number of active orders
ulong  OrderGetTicket(int index);        // Order ticket by index
bool   OrderSelect(ulong ticket);        // Select order for queries
double OrderGetDouble(ENUM_ORDER_PROPERTY_DOUBLE property);
long   OrderGetInteger(ENUM_ORDER_PROPERTY_INTEGER property);
string OrderGetString(ENUM_ORDER_PROPERTY_STRING property);
```

### Position Management

```cpp
int    PositionsTotal();                       // Number of open positions
string PositionGetSymbol(int index);           // Symbol by index
bool   PositionSelect(string symbol);          // Select by symbol
bool   PositionSelectByTicket(ulong ticket);   // Select by ticket
ulong  PositionGetTicket(int index);           // Ticket by index
double PositionGetDouble(ENUM_POSITION_PROPERTY_DOUBLE property);
long   PositionGetInteger(ENUM_POSITION_PROPERTY_INTEGER property);
string PositionGetString(ENUM_POSITION_PROPERTY_STRING property);
```

### History Access

```cpp
bool  HistorySelect(datetime from_date, datetime to_date);
bool  HistorySelectByPosition(long position_id);
int   HistoryOrdersTotal();
ulong HistoryOrderGetTicket(int index);
bool  HistoryOrderSelect(ulong ticket);
int   HistoryDealsTotal();
ulong HistoryDealGetTicket(int index);
bool  HistoryDealSelect(ulong ticket);
```

---

## Order Types & Constants

### ENUM_TRADE_REQUEST_ACTIONS

| Constant | Purpose |
|----------|---------|
| `TRADE_ACTION_DEAL` | Place market order |
| `TRADE_ACTION_PENDING` | Place pending order |
| `TRADE_ACTION_SLTP` | Modify SL/TP of position |
| `TRADE_ACTION_MODIFY` | Modify pending order |
| `TRADE_ACTION_REMOVE` | Delete pending order |
| `TRADE_ACTION_CLOSE_BY` | Close by opposite position |

### ENUM_ORDER_TYPE

| Constant | Purpose |
|----------|---------|
| `ORDER_TYPE_BUY` | Market buy |
| `ORDER_TYPE_SELL` | Market sell |
| `ORDER_TYPE_BUY_LIMIT` | Buy limit pending |
| `ORDER_TYPE_SELL_LIMIT` | Sell limit pending |
| `ORDER_TYPE_BUY_STOP` | Buy stop pending |
| `ORDER_TYPE_SELL_STOP` | Sell stop pending |
| `ORDER_TYPE_BUY_STOP_LIMIT` | Buy stop limit |
| `ORDER_TYPE_SELL_STOP_LIMIT` | Sell stop limit |
| `ORDER_TYPE_CLOSE_BY` | Close by opposite |

### ENUM_ORDER_TYPE_FILLING

| Constant | Description |
|----------|-------------|
| `ORDER_FILLING_FOK` | Fill or Kill - complete fill or cancel |
| `ORDER_FILLING_IOC` | Immediate or Cancel - fill available, cancel rest |
| `ORDER_FILLING_BOC` | Book or Cancel - passive orders only |
| `ORDER_FILLING_RETURN` | Partial fill, keep remainder |

### ENUM_ORDER_TYPE_TIME

| Constant | Description |
|----------|-------------|
| `ORDER_TIME_GTC` | Good Till Cancelled |
| `ORDER_TIME_DAY` | Good till end of day |
| `ORDER_TIME_SPECIFIED` | Good till specified time |
| `ORDER_TIME_SPECIFIED_DAY` | Good till 23:59:59 of specified day |

### ENUM_ORDER_STATE

| Constant | Description |
|----------|-------------|
| `ORDER_STATE_STARTED` | Order checked, not yet accepted |
| `ORDER_STATE_PLACED` | Order accepted |
| `ORDER_STATE_CANCELED` | Order canceled by client |
| `ORDER_STATE_PARTIAL` | Order partially executed |
| `ORDER_STATE_FILLED` | Order fully executed |
| `ORDER_STATE_REJECTED` | Order rejected |
| `ORDER_STATE_EXPIRED` | Order expired |

---

## Trade Return Codes

### Success Codes

| Code | Constant | Description |
|------|----------|-------------|
| 10008 | `TRADE_RETCODE_PLACED` | Order placed |
| 10009 | `TRADE_RETCODE_DONE` | Request completed |
| 10010 | `TRADE_RETCODE_DONE_PARTIAL` | Partial execution |

### Error Codes

| Code | Constant | Description |
|------|----------|-------------|
| 10004 | `TRADE_RETCODE_REQUOTE` | Requote |
| 10006 | `TRADE_RETCODE_REJECT` | Request rejected |
| 10007 | `TRADE_RETCODE_CANCEL` | Canceled by trader |
| 10011 | `TRADE_RETCODE_ERROR` | Processing error |
| 10012 | `TRADE_RETCODE_TIMEOUT` | Request timeout |
| 10013 | `TRADE_RETCODE_INVALID` | Invalid request |
| 10014 | `TRADE_RETCODE_INVALID_VOLUME` | Invalid volume |
| 10015 | `TRADE_RETCODE_INVALID_PRICE` | Invalid price |
| 10016 | `TRADE_RETCODE_INVALID_STOPS` | Invalid stops |
| 10017 | `TRADE_RETCODE_TRADE_DISABLED` | Trading disabled |
| 10018 | `TRADE_RETCODE_MARKET_CLOSED` | Market closed |
| 10019 | `TRADE_RETCODE_NO_MONEY` | Insufficient funds |
| 10022 | `TRADE_RETCODE_INVALID_EXPIRATION` | Invalid expiration |
| 10030 | `TRADE_RETCODE_INVALID_FILL` | Invalid fill type |
| 10031 | `TRADE_RETCODE_CONNECTION` | No connection |
| 10035 | `TRADE_RETCODE_INVALID_ORDER` | Invalid order |

---

## Timeseries & Indicators Access

### Data Copy Functions

```cpp
// Copy OHLCV data as MqlRates structures
int CopyRates(string symbol, ENUM_TIMEFRAMES timeframe,
              int start_pos, int count, MqlRates rates[]);

// Copy individual price arrays
int CopyTime(string symbol, ENUM_TIMEFRAMES tf, int start, int count, datetime time[]);
int CopyOpen(string symbol, ENUM_TIMEFRAMES tf, int start, int count, double open[]);
int CopyHigh(string symbol, ENUM_TIMEFRAMES tf, int start, int count, double high[]);
int CopyLow(string symbol, ENUM_TIMEFRAMES tf, int start, int count, double low[]);
int CopyClose(string symbol, ENUM_TIMEFRAMES tf, int start, int count, double close[]);
int CopyTickVolume(string symbol, ENUM_TIMEFRAMES tf, int start, int count, long volume[]);
int CopyRealVolume(string symbol, ENUM_TIMEFRAMES tf, int start, int count, long volume[]);
int CopySpread(string symbol, ENUM_TIMEFRAMES tf, int start, int count, int spread[]);

// Copy tick data
int CopyTicks(string symbol, MqlTick ticks[], uint flags, ulong from, uint count);
int CopyTicksRange(string symbol, MqlTick ticks[], uint flags,
                   ulong from_msc, ulong to_msc);

// Copy indicator buffer
int CopyBuffer(int indicator_handle, int buffer_num,
               int start_pos, int count, double buffer[]);

// Copy synchronized series
int CopySeries(string symbol, ENUM_TIMEFRAMES tf, ulong series_mask,
               int start, int count, ...);
```

### Indicator Management

```cpp
// Create indicator by enum type
int IndicatorCreate(string symbol, ENUM_TIMEFRAMES period,
                    ENUM_INDICATOR type, int parameters_cnt,
                    const MqlParam& parameters[]);

// Get indicator parameters
int IndicatorParameters(int handle, ENUM_INDICATOR& type, MqlParam parameters[]);

// Release indicator handle
bool IndicatorRelease(int handle);
```

### Information Functions

```cpp
int  Bars(string symbol, ENUM_TIMEFRAMES tf);                    // Bar count
int  BarsCalculated(int handle);                                 // Calculated bars
int  iBars(string symbol, ENUM_TIMEFRAMES tf);                   // Bar count
int  iBarShift(string symbol, ENUM_TIMEFRAMES tf, datetime time, bool exact=false);
long SeriesInfoInteger(string symbol, ENUM_TIMEFRAMES tf, ENUM_SERIES_INFO_INTEGER prop);
```

### Important Notes

- **Index 0** = current (unfinished) bar
- **Indexing is reversed** from standard arrays (newest first)
- Use `ArraySetAsSeries()` to control indexing direction
- Use **dynamic arrays** with Copy functions (auto-allocate)
- For frequent access (OnTick), use **static arrays** for performance

---

## Technical Indicators

All indicator functions return a **handle** for use with `CopyBuffer()`.

### Trend Indicators

```cpp
int iMA(string symbol, ENUM_TIMEFRAMES tf, int period, int shift,
        ENUM_MA_METHOD method, ENUM_APPLIED_PRICE applied_price);

int iMACD(string symbol, ENUM_TIMEFRAMES tf, int fast_ema, int slow_ema,
          int signal_period, ENUM_APPLIED_PRICE applied_price);

int iBands(string symbol, ENUM_TIMEFRAMES tf, int period, int shift,
           double deviation, ENUM_APPLIED_PRICE applied_price);

int iSAR(string symbol, ENUM_TIMEFRAMES tf, double step, double maximum);

int iADX(string symbol, ENUM_TIMEFRAMES tf, int period);

int iIchimoku(string symbol, ENUM_TIMEFRAMES tf,
              int tenkan_sen, int kijun_sen, int senkou_span_b);

int iEnvelopes(string symbol, ENUM_TIMEFRAMES tf, int period, int shift,
               ENUM_MA_METHOD method, ENUM_APPLIED_PRICE applied_price, double deviation);

int iAlligator(string symbol, ENUM_TIMEFRAMES tf,
               int jaw_period, int jaw_shift,
               int teeth_period, int teeth_shift,
               int lips_period, int lips_shift,
               ENUM_MA_METHOD method, ENUM_APPLIED_PRICE applied_price);
```

### Oscillators

```cpp
int iRSI(string symbol, ENUM_TIMEFRAMES tf, int period, ENUM_APPLIED_PRICE applied_price);

int iStochastic(string symbol, ENUM_TIMEFRAMES tf, int k_period, int d_period,
                int slowing, ENUM_MA_METHOD method, ENUM_STO_PRICE price_field);

int iCCI(string symbol, ENUM_TIMEFRAMES tf, int period, ENUM_APPLIED_PRICE applied_price);

int iMomentum(string symbol, ENUM_TIMEFRAMES tf, int period, ENUM_APPLIED_PRICE applied_price);

int iWPR(string symbol, ENUM_TIMEFRAMES tf, int period);

int iRVI(string symbol, ENUM_TIMEFRAMES tf, int period);

int iDeMarker(string symbol, ENUM_TIMEFRAMES tf, int period);

int iAO(string symbol, ENUM_TIMEFRAMES tf);   // Awesome Oscillator

int iAC(string symbol, ENUM_TIMEFRAMES tf);   // Accelerator Oscillator
```

### Volatility Indicators

```cpp
int iATR(string symbol, ENUM_TIMEFRAMES tf, int period);

int iStdDev(string symbol, ENUM_TIMEFRAMES tf, int period, int shift,
            ENUM_MA_METHOD method, ENUM_APPLIED_PRICE applied_price);
```

### Volume Indicators

```cpp
int iVolumes(string symbol, ENUM_TIMEFRAMES tf, ENUM_APPLIED_VOLUME applied_volume);

int iOBV(string symbol, ENUM_TIMEFRAMES tf, ENUM_APPLIED_VOLUME applied_volume);

int iMFI(string symbol, ENUM_TIMEFRAMES tf, int period, ENUM_APPLIED_VOLUME applied_volume);

int iAD(string symbol, ENUM_TIMEFRAMES tf, ENUM_APPLIED_VOLUME applied_volume);

int iChaikin(string symbol, ENUM_TIMEFRAMES tf, int fast_period, int slow_period,
             ENUM_MA_METHOD method, ENUM_APPLIED_VOLUME applied_volume);

int iForce(string symbol, ENUM_TIMEFRAMES tf, int period,
           ENUM_MA_METHOD method, ENUM_APPLIED_VOLUME applied_volume);
```

### Other Indicators

```cpp
int iFractals(string symbol, ENUM_TIMEFRAMES tf);

int iGator(string symbol, ENUM_TIMEFRAMES tf,
           int jaw_period, int jaw_shift,
           int teeth_period, int teeth_shift,
           int lips_period, int lips_shift,
           ENUM_MA_METHOD method, ENUM_APPLIED_PRICE applied_price);

int iBWMFI(string symbol, ENUM_TIMEFRAMES tf, ENUM_APPLIED_VOLUME applied_volume);

int iOsMA(string symbol, ENUM_TIMEFRAMES tf, int fast_ema, int slow_ema,
          int signal_period, ENUM_APPLIED_PRICE applied_price);

// Custom indicator
int iCustom(string symbol, ENUM_TIMEFRAMES tf, string name, ...);
```

### MA Methods (ENUM_MA_METHOD)

| Constant | Method |
|----------|--------|
| `MODE_SMA` | Simple Moving Average |
| `MODE_EMA` | Exponential Moving Average |
| `MODE_SMMA` | Smoothed Moving Average |
| `MODE_LWMA` | Linear Weighted Moving Average |

### Applied Price (ENUM_APPLIED_PRICE)

| Constant | Price |
|----------|-------|
| `PRICE_CLOSE` | Close price |
| `PRICE_OPEN` | Open price |
| `PRICE_HIGH` | High price |
| `PRICE_LOW` | Low price |
| `PRICE_MEDIAN` | (High + Low) / 2 |
| `PRICE_TYPICAL` | (High + Low + Close) / 3 |
| `PRICE_WEIGHTED` | (High + Low + Close + Close) / 4 |

---

## Account Information

### ENUM_ACCOUNT_INFO_INTEGER

```cpp
long login        = AccountInfoInteger(ACCOUNT_LOGIN);          // Account number
long leverage     = AccountInfoInteger(ACCOUNT_LEVERAGE);       // Leverage
int  limit_orders = (int)AccountInfoInteger(ACCOUNT_LIMIT_ORDERS);  // Max orders
bool trade_allowed = AccountInfoInteger(ACCOUNT_TRADE_ALLOWED); // Trading permitted
bool ea_allowed    = AccountInfoInteger(ACCOUNT_TRADE_EXPERT);  // EA trading permitted
bool hedge_allowed = AccountInfoInteger(ACCOUNT_HEDGE_ALLOWED); // Hedging allowed
```

### ENUM_ACCOUNT_INFO_DOUBLE

```cpp
double balance      = AccountInfoDouble(ACCOUNT_BALANCE);       // Balance
double credit       = AccountInfoDouble(ACCOUNT_CREDIT);        // Credit
double profit       = AccountInfoDouble(ACCOUNT_PROFIT);        // Current profit
double equity       = AccountInfoDouble(ACCOUNT_EQUITY);        // Equity
double margin       = AccountInfoDouble(ACCOUNT_MARGIN);        // Used margin
double margin_free  = AccountInfoDouble(ACCOUNT_MARGIN_FREE);   // Free margin
double margin_level = AccountInfoDouble(ACCOUNT_MARGIN_LEVEL);  // Margin level %
double margin_call  = AccountInfoDouble(ACCOUNT_MARGIN_SO_CALL);// Margin call level
double margin_stop  = AccountInfoDouble(ACCOUNT_MARGIN_SO_SO);  // Stop out level
```

### ENUM_ACCOUNT_INFO_STRING

```cpp
string name     = AccountInfoString(ACCOUNT_NAME);     // Client name
string server   = AccountInfoString(ACCOUNT_SERVER);   // Server name
string currency = AccountInfoString(ACCOUNT_CURRENCY); // Deposit currency
string company  = AccountInfoString(ACCOUNT_COMPANY);  // Broker company
```

---

## Market Information

### Symbol Functions

```cpp
int    SymbolsTotal(bool selected);              // Symbol count
bool   SymbolExist(string name, bool& in_mw);    // Check if exists
string SymbolName(int pos, bool selected);       // Get name by index
bool   SymbolSelect(string name, bool select);   // Add/remove from Market Watch
bool   SymbolIsSynchronized(string name);        // Check synchronization
```

### Symbol Info Functions

```cpp
double SymbolInfoDouble(string symbol, ENUM_SYMBOL_INFO_DOUBLE property);
long   SymbolInfoInteger(string symbol, ENUM_SYMBOL_INFO_INTEGER property);
string SymbolInfoString(string symbol, ENUM_SYMBOL_INFO_STRING property);
bool   SymbolInfoTick(string symbol, MqlTick& tick);  // Current tick
double SymbolInfoMarginRate(string symbol, ENUM_ORDER_TYPE type,
                            double& initial_margin_rate, double& maintenance_margin_rate);
```

### Market Depth (DOM)

```cpp
bool MarketBookAdd(string symbol);           // Subscribe to DOM
bool MarketBookRelease(string symbol);       // Unsubscribe from DOM
bool MarketBookGet(string symbol, MqlBookInfo& book[]);  // Get DOM data
```

---

## Symbol Properties

### Price Properties (SymbolInfoDouble)

| Constant | Description |
|----------|-------------|
| `SYMBOL_BID` | Current Bid price |
| `SYMBOL_ASK` | Current Ask price |
| `SYMBOL_LAST` | Last deal price |
| `SYMBOL_BIDHIGH` / `SYMBOL_BIDLOW` | Daily Bid range |
| `SYMBOL_ASKHIGH` / `SYMBOL_ASKLOW` | Daily Ask range |

### Contract Properties (SymbolInfoDouble)

| Constant | Description |
|----------|-------------|
| `SYMBOL_POINT` | Point value |
| `SYMBOL_TRADE_TICK_SIZE` | Minimal price change |
| `SYMBOL_TRADE_TICK_VALUE` | Tick value |
| `SYMBOL_TRADE_CONTRACT_SIZE` | Contract size |
| `SYMBOL_VOLUME_MIN` | Minimum volume |
| `SYMBOL_VOLUME_MAX` | Maximum volume |
| `SYMBOL_VOLUME_STEP` | Volume step |
| `SYMBOL_SWAP_LONG` | Long swap |
| `SYMBOL_SWAP_SHORT` | Short swap |

### Trading Properties (SymbolInfoInteger)

| Constant | Description |
|----------|-------------|
| `SYMBOL_SPREAD` | Spread in points |
| `SYMBOL_SPREAD_FLOAT` | Floating spread flag |
| `SYMBOL_DIGITS` | Decimal places |
| `SYMBOL_TRADE_MODE` | Trade mode |
| `SYMBOL_FILLING_MODE` | Allowed filling modes |
| `SYMBOL_ORDER_MODE` | Allowed order types |

### Currency Properties (SymbolInfoString)

| Constant | Description |
|----------|-------------|
| `SYMBOL_CURRENCY_BASE` | Base currency |
| `SYMBOL_CURRENCY_PROFIT` | Profit currency |
| `SYMBOL_CURRENCY_MARGIN` | Margin currency |
| `SYMBOL_DESCRIPTION` | Symbol description |

---

## Timeframe Constants

### ENUM_TIMEFRAMES

| Constant | Period |
|----------|--------|
| `PERIOD_CURRENT` | Current timeframe |
| `PERIOD_M1` | 1 minute |
| `PERIOD_M2` | 2 minutes |
| `PERIOD_M3` | 3 minutes |
| `PERIOD_M4` | 4 minutes |
| `PERIOD_M5` | 5 minutes |
| `PERIOD_M6` | 6 minutes |
| `PERIOD_M10` | 10 minutes |
| `PERIOD_M12` | 12 minutes |
| `PERIOD_M15` | 15 minutes |
| `PERIOD_M20` | 20 minutes |
| `PERIOD_M30` | 30 minutes |
| `PERIOD_H1` | 1 hour |
| `PERIOD_H2` | 2 hours |
| `PERIOD_H3` | 3 hours |
| `PERIOD_H4` | 4 hours |
| `PERIOD_H6` | 6 hours |
| `PERIOD_H8` | 8 hours |
| `PERIOD_H12` | 12 hours |
| `PERIOD_D1` | 1 day |
| `PERIOD_W1` | 1 week |
| `PERIOD_MN1` | 1 month |

---

## Common Functions

### Output Functions

```cpp
void Alert(argument, ...);           // Display alert dialog
void Comment(argument, ...);         // Display on chart corner
void Print(argument, ...);           // Print to Experts log
int  PrintFormat(string format, ...); // Formatted print
int  MessageBox(string text, string caption = "", int flags = 0);
bool PlaySound(string filename);     // Play WAV file
```

### System Functions

```cpp
void   Sleep(int milliseconds);      // Pause execution (scripts/EAs only)
uint   GetTickCount();               // Milliseconds since system start
ulong  GetTickCount64();             // 64-bit version
ulong  GetMicrosecondCount();        // Microseconds since program start
bool   TerminalClose(int ret_code);  // Close terminal
```

### Error Handling

```cpp
void ResetLastError();               // Reset _LastError to 0
void SetUserError(ushort error);     // Set custom error code
```

### Testing Functions

```cpp
void   TesterStop();                 // Stop testing
double TesterStatistics(ENUM_STATISTICS stat);  // Get test statistics
bool   TesterDeposit(double money);  // Simulate deposit
bool   TesterWithdrawal(double money); // Simulate withdrawal
void   TesterHideIndicators(bool hide); // Hide indicators
```

### Pointer Functions

```cpp
void* GetPointer(object);            // Get object pointer
void  ZeroMemory(variable);          // Reset to zero
ENUM_POINTER_TYPE CheckPointer(object*); // Check pointer validity
```

---

## Standard Library

Located in `Include` folder of MetaTrader 5 terminal.

### Directory Structure

| Directory | Purpose |
|-----------|---------|
| `Include\Trade\` | Trading classes |
| `Include\Indicators\` | Indicator classes |
| `Include\Arrays\` | Data collection classes |
| `Include\Generic\` | Generic data structures |
| `Include\Files\` | File operation classes |
| `Include\Strings\` | String manipulation |
| `Include\Charts\` | Chart management |
| `Include\Objects\` | Graphic object classes |
| `Include\Canvas\` | Custom/3D graphics |
| `Include\Controls\` | UI panels and dialogs |
| `Include\Expert\` | Strategy modules |
| `Include\Math\` | Mathematical functions |
| `Include\OpenCL\` | GPU computing |
| `Include\Graphics\` | Scientific charts |

### Key Trade Classes

```cpp
#include <Trade\Trade.mqh>           // CTrade class
#include <Trade\PositionInfo.mqh>    // CPositionInfo class
#include <Trade\OrderInfo.mqh>       // COrderInfo class
#include <Trade\SymbolInfo.mqh>      // CSymbolInfo class
#include <Trade\AccountInfo.mqh>     // CAccountInfo class
#include <Trade\DealInfo.mqh>        // CDealInfo class
#include <Trade\HistoryOrderInfo.mqh> // CHistoryOrderInfo class
```

### CTrade Usage Example

```cpp
#include <Trade\Trade.mqh>

CTrade trade;
trade.SetExpertMagicNumber(123456);
trade.SetDeviationInPoints(10);
trade.SetTypeFilling(ORDER_FILLING_FOK);

// Market buy
trade.Buy(0.1, _Symbol, 0, 0, 0, "Buy order");

// Market sell
trade.Sell(0.1, _Symbol, 0, 0, 0, "Sell order");

// Buy limit
trade.BuyLimit(0.1, price, _Symbol, sl, tp, ORDER_TIME_GTC, 0, "Buy limit");

// Close position
trade.PositionClose(_Symbol);
```

---

## Best Practices

### 1. Error Handling

```cpp
MqlTradeRequest request = {};
MqlTradeResult result = {};

// Fill request...

if(!OrderSend(request, result)) {
    Print("OrderSend error: ", GetLastError());
    return;
}

if(result.retcode != TRADE_RETCODE_DONE && result.retcode != TRADE_RETCODE_PLACED) {
    Print("Trade failed: ", result.retcode, " - ", result.comment);
    return;
}

Print("Order placed: ticket=", result.order);
```

### 2. Proper Price Normalization

```cpp
double NormalizePrice(string symbol, double price) {
    double tick_size = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
    return NormalizeDouble(MathRound(price / tick_size) * tick_size,
                           (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS));
}

double NormalizeLots(string symbol, double lots) {
    double min_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double max_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
    double lot_step = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);

    lots = MathMax(min_lot, MathMin(max_lot, lots));
    return NormalizeDouble(MathRound(lots / lot_step) * lot_step, 2);
}
```

### 3. Check Trading Conditions

```cpp
bool IsTradingAllowed() {
    if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) return false;
    if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)) return false;
    if(!AccountInfoInteger(ACCOUNT_TRADE_EXPERT)) return false;
    if(!MQLInfoInteger(MQL_TRADE_ALLOWED)) return false;
    return true;
}

bool IsMarketOpen(string symbol) {
    MqlTick tick;
    if(!SymbolInfoTick(symbol, tick)) return false;

    datetime server_time = TimeCurrent();
    datetime from, to;

    if(!SymbolInfoSessionTrade(symbol, DayOfWeek(), 0, from, to)) return false;

    return (server_time >= from && server_time <= to);
}
```

### 4. Reliable Data Access

```cpp
bool GetRates(string symbol, ENUM_TIMEFRAMES tf, int count, MqlRates& rates[]) {
    ArraySetAsSeries(rates, true);
    int copied = CopyRates(symbol, tf, 0, count, rates);

    if(copied < count) {
        Print("Failed to copy rates: ", GetLastError());
        return false;
    }
    return true;
}
```

### 5. Position Tracking by Magic Number

```cpp
int CountPositions(long magic = 0, string symbol = "") {
    int count = 0;
    for(int i = PositionsTotal() - 1; i >= 0; i--) {
        if(PositionSelectByTicket(PositionGetTicket(i))) {
            if(magic != 0 && PositionGetInteger(POSITION_MAGIC) != magic) continue;
            if(symbol != "" && PositionGetString(POSITION_SYMBOL) != symbol) continue;
            count++;
        }
    }
    return count;
}
```

---

## Quick Reference Card

### Market Order (Buy)

```cpp
MqlTradeRequest request = {};
MqlTradeResult result = {};

request.action = TRADE_ACTION_DEAL;
request.symbol = _Symbol;
request.volume = 0.1;
request.type = ORDER_TYPE_BUY;
request.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
request.deviation = 10;
request.magic = 123456;
request.comment = "Buy order";
request.type_filling = ORDER_FILLING_FOK;

OrderSend(request, result);
```

### Pending Order (Buy Limit)

```cpp
MqlTradeRequest request = {};
MqlTradeResult result = {};

request.action = TRADE_ACTION_PENDING;
request.symbol = _Symbol;
request.volume = 0.1;
request.type = ORDER_TYPE_BUY_LIMIT;
request.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK) - 100 * _Point;
request.sl = request.price - 50 * _Point;
request.tp = request.price + 100 * _Point;
request.deviation = 10;
request.magic = 123456;
request.type_filling = ORDER_FILLING_FOK;
request.type_time = ORDER_TIME_GTC;

OrderSend(request, result);
```

### Modify SL/TP

```cpp
MqlTradeRequest request = {};
MqlTradeResult result = {};

request.action = TRADE_ACTION_SLTP;
request.symbol = _Symbol;
request.sl = new_sl;
request.tp = new_tp;
request.position = position_ticket;

OrderSend(request, result);
```

### Close Position

```cpp
MqlTradeRequest request = {};
MqlTradeResult result = {};

request.action = TRADE_ACTION_DEAL;
request.symbol = _Symbol;
request.volume = PositionGetDouble(POSITION_VOLUME);
request.type = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
               ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
request.price = (request.type == ORDER_TYPE_SELL)
                ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
request.position = position_ticket;
request.deviation = 10;
request.type_filling = ORDER_FILLING_FOK;

OrderSend(request, result);
```

---

## Additional Resources

- **Official Documentation**: https://www.mql5.com/en/docs
- **Code Examples**: https://www.mql5.com/en/code
- **Articles**: https://www.mql5.com/en/articles
- **Forum**: https://www.mql5.com/en/forum
- **Books**:
  - "MQL5 Programming for Traders"
  - "Neural Networks for Algorithmic Trading with MQL5"

---

*Last Updated: December 2025*
*Source: MQL5 Reference Documentation*
