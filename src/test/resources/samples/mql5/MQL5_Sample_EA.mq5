//+------------------------------------------------------------------+
//| MQL5_Sample_EA.mq5 — Sample MQL5 Expert Advisor for parser tests |
//+------------------------------------------------------------------+
#property copyright "Test"
#property version   "1.00"
#property description "MQL5 sample EA for parser validation"

sinput int InpMagicNumber = 12345;
input  double InpLotSize = 0.1;
input  int InpStopLoss = 100;
input  int InpTakeProfit = 200;

int maHandle;
int rsiHandle;

//+------------------------------------------------------------------+
//| OnInit                                                           |
//+------------------------------------------------------------------+
int OnInit()
{
   maHandle = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE);
   rsiHandle = iRSI(_Symbol, PERIOD_H1, 14, PRICE_CLOSE);

   if(maHandle == INVALID_HANDLE || rsiHandle == INVALID_HANDLE)
   {
      Print("Failed to create indicator handles");
      return INIT_FAILED;
   }
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| OnDeinit                                                         |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   IndicatorRelease(maHandle);
   IndicatorRelease(rsiHandle);
}

//+------------------------------------------------------------------+
//| OnTick                                                           |
//+------------------------------------------------------------------+
void OnTick()
{
   static datetime lastBar = 0;
   datetime curBar = iTime(_Symbol, PERIOD_H1, 0);
   if(curBar == lastBar) return;
   lastBar = curBar;

   double maBuffer[];
   double rsiBuffer[];
   ArraySetAsSeries(maBuffer, true);
   ArraySetAsSeries(rsiBuffer, true);

   if(CopyBuffer(maHandle, 0, 0, 3, maBuffer) < 0) return;
   if(CopyBuffer(rsiHandle, 0, 0, 3, rsiBuffer) < 0) return;

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   if(rsiBuffer[0] < 30 && maBuffer[0] > maBuffer[1])
   {
      MqlTradeRequest request;
      MqlTradeResult result;
      ZeroMemory(request);
      ZeroMemory(result);
      request.action = TRADE_ACTION_DEAL;
      request.symbol = _Symbol;
      request.volume = InpLotSize;
      request.type = ORDER_TYPE_BUY;
      request.price = ask;
      request.sl = NormalizeDouble(ask - InpStopLoss * _Point, _Digits);
      request.tp = NormalizeDouble(ask + InpTakeProfit * _Point, _Digits);
      request.deviation = 10;
      request.magic = InpMagicNumber;
      if(!OrderSend(request, result))
      {
         Print("OrderSend error: ", GetLastError());
      }
   }
}

//+------------------------------------------------------------------+
//| OnTrade                                                          |
//+------------------------------------------------------------------+
void OnTrade()
{
   int total = PositionsTotal();
   for(int i = total - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket))
      {
         string symbol = PositionGetString(POSITION_SYMBOL);
         double profit = PositionGetDouble(POSITION_PROFIT);
      }
   }
}

//+------------------------------------------------------------------+
//| Abstract base class                                              |
//+------------------------------------------------------------------+
abstract class CBaseStrategy
{
public:
   virtual bool CheckEntry() = 0;
   virtual bool CheckExit() = 0;
   virtual void OnNewBar() {}
};

//+------------------------------------------------------------------+
//| Derived class with override and final                            |
//+------------------------------------------------------------------+
class CMyStrategy final : public CBaseStrategy
{
private:
   int m_period;
public:
   CMyStrategy(int period) : m_period(period) {}

   bool CheckEntry() override { return false; }
   bool CheckExit() override final { return false; }
   void OnNewBar() override {}
};
