//+------------------------------------------------------------------+
//|                                                     ${NAME}.mq5 |
//|                                        Copyright 2026, ${USER}   |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, ${USER}"
#property version   "1.00"
#property indicator_chart_window

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
  {
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                 const int prev_calculated,
                 const datetime &time[],
                 const double &open[],
                 const double &high[],
                 const double &low[],
                 const double &close[],
                 const long &tick_volume[],
                 const long &volume[],
                 const int &spread[])
  {
   return(rates_total);
  }
//+------------------------------------------------------------------+
