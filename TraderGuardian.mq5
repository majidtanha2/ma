//+------------------------------------------------------------------+
//|                                           TraderGuardian.mq5     |
//|                        Copyright 2024, Trader's Guardian System  |
//|                                        https://tradersguardian.ir|
//+------------------------------------------------------------------+
#property copyright "Trader's Guardian System v2.0"
#property link      "https://tradersguardian.ir"
#property version   "2.0"
#property description "سیستم نیمه‌خودکار معاملاتی با کنترل روانشناسی"
#property description "برای تریدرهای حرفه‌ای با مشکل انضباط"

#include <Trade/Trade.mqh>
#include <Trade/AccountInfo.mqh>
#include <Trade/PositionInfo.mqh>
#include <Trade/SymbolInfo.mqh>
#include <Trade/HistoryOrderInfo.mqh>
#include <Trade/DealInfo.mqh>

//--- input parameters
input double   RiskPercent      = 1.0;      // درصد ریسک هر معامله
input double   DailyRiskLimit   = 1.5;      // حداکثر ریسک روزانه
input int      MaxPositions     = 3;        // حداکثر پوزیشن همزمان
input bool     EnableStopLossLock = true;   // قفل استاپ‌لاس
input bool     EnableAlerts     = true;     // فعال‌سازی هشدارها
input color    PanelColor       = clrGray;  // رنگ پنل
input bool     EnableAutoRisk   = true;     // مدیریت خودکار ریسک

//--- متغیرهای سراسری
CTrade               trade;
CAccountInfo         account;
CPositionInfo        position;
CSymbolInfo          symbolInfo;
CHistoryOrderInfo    historyOrder;
CDealInfo            dealInfo;

//--- متغیرهای مدیریت ریسک
double               dailyProfit, dailyLoss;
datetime             lastResetTime;
bool                 tradingAllowed = true;
bool                 emergencyLocked = false;

//--- متغیرهای پنل
int                  panelHandle;
bool                 panelVisible = true;

//--- متغیرهای داخلی (برای جلوگیری از تغییر inputها)
double               currentRiskPercent;
double               currentDailyRiskLimit;
int                  currentMaxPositions;

//--- آرایه‌های ذخیره استاپ‌های اصلی
double               originalSLs[100];
bool                 slInitialized[100];
double               originalPrices[100];

//--- متغیرهای زمان
datetime             tradingStartTime;
datetime             tradingEndTime;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   // مقداردهی متغیرهای داخلی با مقادیر input
   currentRiskPercent = RiskPercent;
   currentDailyRiskLimit = DailyRiskLimit;
   currentMaxPositions = MaxPositions;
   
   // تنظیم زمان معاملات (10:00-18:00)
   MqlDateTime timeStruct;
   TimeToStruct(TimeCurrent(), timeStruct);  // تغییر اینجا
   timeStruct.hour = 10;
   timeStruct.min = 0;
   timeStruct.sec = 0;
   tradingStartTime = StructToTime(timeStruct);
   
   timeStruct.hour = 18;
   tradingEndTime = StructToTime(timeStruct);
   
   // صفر کردن آرایه‌ها
   ArrayInitialize(originalSLs, 0);
   ArrayInitialize(slInitialized, false);
   ArrayInitialize(originalPrices, 0);
   
   // بررسی اتصال
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
   {
      Alert("معاملات در ترمینال غیرفعال است!");
      return(INIT_FAILED);
   }
   
   // تنظیم ساعت بازنشانی روزانه
   lastResetTime = GetStartOfDay(TimeCurrent());
   
   // ایجاد پنل کنترل
   CreateControlPanel();
   
   // بارگذاری تنظیمات از فایل
   LoadSettings();
   
   // شروع تایمر برای نظارت
   EventSetTimer(1);
   
   Print("==========================================");
   Print("🛡️ Trader's Guardian System v2.0 راه‌اندازی شد");
   Print("👤 اکانت: ", AccountInfoString(ACCOUNT_NAME));
   Print("💰 سرمایه: ", AccountInfoDouble(ACCOUNT_BALANCE));
   Print("📊 حداکثر ریسک روزانه: ", currentDailyRiskLimit, "%");
   Print("🎯 ریسک هر معامله: ", currentRiskPercent, "%");
   Print("⏰ زمان معاملات: ", TimeToString(tradingStartTime), " - ", TimeToString(tradingEndTime));
   Print("==========================================");
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // پاک‌سازی پنل
   ObjectDelete(0, "MainPanel");
   ObjectDelete(0, "Lbl_Title");
   ObjectDelete(0, "Btn_Checklist");
   ObjectDelete(0, "Btn_Analyze");
   ObjectDelete(0, "Btn_Emergency");
   ObjectDelete(0, "Btn_Reset");
   ObjectDelete(0, "Btn_Hide");
   ObjectDelete(0, "Lbl_Account");
   ObjectDelete(0, "Lbl_Risk");
   ObjectDelete(0, "Lbl_Trading");
   ObjectDelete(0, "Lbl_Time");
   ObjectDelete(0, "Lbl_Positions");
   
   // متوقف کردن تایمر
   EventKillTimer();
   
   Print("سیستم خاموش شد");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // به‌روزرسانی وضعیت روزانه
   UpdateDailyStats();
   
   // بررسی محدودیت ریسک
   CheckRiskLimits();
   
   // نظارت بر پوزیشن‌های باز
   MonitorOpenPositions();
   
   // قفل استاپ‌لاس
   if(EnableStopLossLock)
   {
      LockStopLoss();
   }
   
   // به‌روزرسانی پنل
   UpdateControlPanel();
   
   // بررسی زمان معاملات
   CheckTradingTime();
}

//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
{
   // هر ثانیه بررسی‌های ایمنی
   CheckForViolations();
   
   // ارتباط با بک‌اند پایتون
   CommunicateWithPython();
   
   // به‌روزرسانی زمان در پنل
   UpdateTimeDisplay();
}

//+------------------------------------------------------------------+
//| تابع ایجاد پنل کنترل                                            |
//+------------------------------------------------------------------+
void CreateControlPanel()
{
   // پس‌زمینه پنل
   ObjectCreate(0, "MainPanel", OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, "MainPanel", OBJPROP_XDISTANCE, 10);
   ObjectSetInteger(0, "MainPanel", OBJPROP_YDISTANCE, 50);
   ObjectSetInteger(0, "MainPanel", OBJPROP_XSIZE, 280);
   ObjectSetInteger(0, "MainPanel", OBJPROP_YSIZE, 380);
   ObjectSetInteger(0, "MainPanel", OBJPROP_BGCOLOR, PanelColor);
   ObjectSetInteger(0, "MainPanel", OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, "MainPanel", OBJPROP_BORDER_COLOR, clrWhite);
   
   // عنوان
   ObjectCreate(0, "Lbl_Title", OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, "Lbl_Title", OBJPROP_XDISTANCE, 70);
   ObjectSetInteger(0, "Lbl_Title", OBJPROP_YDISTANCE, 60);
   ObjectSetString(0, "Lbl_Title", OBJPROP_TEXT, "🛡️ TRADER'S GUARDIAN");
   ObjectSetInteger(0, "Lbl_Title", OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, "Lbl_Title", OBJPROP_FONTSIZE, 12);
   
   // دکمه چک‌لیست
   CreateButton("Btn_Checklist", 20, 100, 240, 30, "📋 باز کردن چک‌لیست", clrDodgerBlue);
   
   // دکمه تحلیل خودکار
   CreateButton("Btn_Analyze", 20, 140, 240, 30, "🔍 تحلیل خودکار بازار", clrGreen);
   
   // وضعیت حساب
   ObjectCreate(0, "Lbl_Account", OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, "Lbl_Account", OBJPROP_XDISTANCE, 20);
   ObjectSetInteger(0, "Lbl_Account", OBJPROP_YDISTANCE, 190);
   
   // وضعیت ریسک
   ObjectCreate(0, "Lbl_Risk", OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, "Lbl_Risk", OBJPROP_XDISTANCE, 20);
   ObjectSetInteger(0, "Lbl_Risk", OBJPROP_YDISTANCE, 210);
   
   // وضعیت پوزیشن‌ها
   ObjectCreate(0, "Lbl_Positions", OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, "Lbl_Positions", OBJPROP_XDISTANCE, 20);
   ObjectSetInteger(0, "Lbl_Positions", OBJPROP_YDISTANCE, 230);
   
   // وضعیت زمان
   ObjectCreate(0, "Lbl_Time", OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, "Lbl_Time", OBJPROP_XDISTANCE, 20);
   ObjectSetInteger(0, "Lbl_Time", OBJPROP_YDISTANCE, 250);
   
   // وضعیت مجوز معامله
   ObjectCreate(0, "Lbl_Trading", OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, "Lbl_Trading", OBJPROP_XDISTANCE, 20);
   ObjectSetInteger(0, "Lbl_Trading", OBJPROP_YDISTANCE, 270);
   
   // دکمه ریست سیستم
   CreateButton("Btn_Reset", 20, 310, 115, 40, "🔄 ریست سیستم", clrBlue);
   
   // دکمه قفل اضطراری
   CreateButton("Btn_Emergency", 145, 310, 115, 40, "🔴 قفل اضطراری", clrRed);
   
   // دکمه مخفی کردن پنل
   CreateButton("Btn_Hide", 250, 50, 20, 20, "X", clrGray);
}

//+------------------------------------------------------------------+
//| تابع ایجاد دکمه                                                 |
//+------------------------------------------------------------------+
bool CreateButton(string name, int x, int y, int width, int height, string text, color bgColor)
{
   ObjectCreate(0, name, OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_XSIZE, width);
   ObjectSetInteger(0, name, OBJPROP_YSIZE, height);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_BGCOLOR, bgColor);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR, clrWhite);
   ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   
   return true;
}

//+------------------------------------------------------------------+
//| تابع به‌روزرسانی پنل                                            |
//+------------------------------------------------------------------+
void UpdateControlPanel()
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double dailyPL = CalculateDailyPL();
   double riskPercent = 0;
   
   if(balance > 0 && dailyPL < 0)
   {
      riskPercent = (MathAbs(dailyPL) / balance) * 100;
   }
   
   // وضعیت حساب
   string accountText = StringFormat("💰 حساب: $%.2f | اکویتی: $%.2f", balance, equity);
   ObjectSetString(0, "Lbl_Account", OBJPROP_TEXT, accountText);
   
   // وضعیت ریسک
   string riskText = StringFormat("📊 ریسک امروز: %.2f%% ($%.2f)", riskPercent, dailyPL);
   ObjectSetString(0, "Lbl_Risk", OBJPROP_TEXT, riskText);
   
   // وضعیت پوزیشن‌ها
   int positions = PositionsTotal();
   string posText = StringFormat("📈 پوزیشن‌های باز: %d/%d", positions, currentMaxPositions);
   ObjectSetString(0, "Lbl_Positions", OBJPROP_TEXT, posText);
   
   // وضعیت زمان
   string timeText = StringFormat("⏰ ساعت: %s", TimeToString(TimeCurrent(), TIME_MINUTES));
   ObjectSetString(0, "Lbl_Time", OBJPROP_TEXT, timeText);
   
   // وضعیت مجوز معامله
   string tradingText;
   if(emergencyLocked)
   {
      tradingText = "🔴 قفل اضطراری فعال";
   }
   else if(!tradingAllowed)
   {
      tradingText = "⛔ معاملات مسدود";
   }
   else
   {
      tradingText = "✅ مجوز معامله فعال";
   }
   ObjectSetString(0, "Lbl_Trading", OBJPROP_TEXT, tradingText);
   
   // تغییر رنگ بر اساس ریسک
   color riskColor;
   if(riskPercent > currentDailyRiskLimit * 0.8)
   {
      riskColor = clrRed;
   }
   else if(riskPercent > currentDailyRiskLimit * 0.5)
   {
      riskColor = clrOrange;
   }
   else
   {
      riskColor = clrLimeGreen;
   }
   ObjectSetInteger(0, "Lbl_Risk", OBJPROP_COLOR, riskColor);
   
   // تغییر رنگ وضعیت پوزیشن
   color posColor = (positions >= currentMaxPositions) ? clrOrange : clrWhite;
   ObjectSetInteger(0, "Lbl_Positions", OBJPROP_COLOR, posColor);
}

//+------------------------------------------------------------------+
//| تابع به‌روزرسانی نمایش زمان                                     |
//+------------------------------------------------------------------+
void UpdateTimeDisplay()
{
   string timeText = StringFormat("⏰ ساعت: %s", TimeToString(TimeCurrent(), TIME_MINUTES));
   ObjectSetString(0, "Lbl_Time", OBJPROP_TEXT, timeText);
}

//+------------------------------------------------------------------+
//| تابع محاسبه شروع روز                                            |
//+------------------------------------------------------------------+
datetime GetStartOfDay(datetime time)
{
   MqlDateTime mql_time;
   TimeToStruct(time, mql_time);
   mql_time.hour = 0;
   mql_time.min = 0;
   mql_time.sec = 0;
   return StructToTime(mql_time);
}

//+------------------------------------------------------------------+
//| تابع محاسبه سود/ضرر روزانه                                      |
//+------------------------------------------------------------------+
double CalculateDailyPL()
{
   double total = 0;
   datetime today = GetStartOfDay(TimeCurrent());
   
   // انتخاب تاریخچه امروز
   if(HistorySelect(today, TimeCurrent()))
   {
      int totalDeals = HistoryDealsTotal();
      
      for(int i = 0; i < totalDeals; i++)
      {
         ulong ticket = HistoryDealGetTicket(i);
         if(ticket > 0)
         {
            datetime dealTime = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
            
            // فقط معاملات امروز
            if(dealTime >= today)
            {
               double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
               double swap = HistoryDealGetDouble(ticket, DEAL_SWAP);
               double commission = HistoryDealGetDouble(ticket, DEAL_COMMISSION);
               
               total += profit + swap + commission;
            }
         }
      }
   }
   
   return total;
}

//+------------------------------------------------------------------+
//| تابع محاسبه دراودان                                             |
//+------------------------------------------------------------------+
double CalculateDrawdown()
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   
   if(balance <= 0) return 0;
   
   double drawdown = ((balance - equity) / balance) * 100;
   return drawdown;
}

//+------------------------------------------------------------------+
//| تابع بررسی محدودیت‌های ریسک                                     |
//+------------------------------------------------------------------+
void CheckRiskLimits()
{
   double dailyPL = CalculateDailyPL();
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   
   // فقط اگر ضرر داشته باشیم ریسک محاسبه شود
   if(dailyPL >= 0)
   {
      if(!tradingAllowed && !emergencyLocked)
      {
         tradingAllowed = true;
         Print("✅ سود روزانه مثبت است. معاملات فعال شد.");
      }
      return;
   }
   
   double lossAmount = MathAbs(dailyPL);
   double riskPercent = (lossAmount / balance) * 100;
   
   // بررسی ریسک روزانه
   if(riskPercent >= currentDailyRiskLimit)
   {
      if(tradingAllowed && !emergencyLocked)
      {
         tradingAllowed = false;
         Alert("⛔ ریسک روزانه تکمیل شد! معاملات مسدود گردید.");
         Alert(StringFormat("ضرر امروز: $%.2f (%.2f%%) | حد مجاز: %.1f%%", 
               lossAmount, riskPercent, currentDailyRiskLimit));
         SendNotification("ریسک روزانه تکمیل شد - سیستم قفل شد");
      }
   }
   
   // بررسی دراودان
   double drawdown = CalculateDrawdown();
   if(drawdown > 5.0)
   {
      Alert("⚠️ دراودان بیش از ۵٪! مقدار: ", drawdown, "%");
   }
}

//+------------------------------------------------------------------+
//| تابع بررسی زمان معاملات                                         |
//+------------------------------------------------------------------+
void CheckTradingTime()
{
   datetime currentTime = TimeCurrent();
   
   // اگر خارج از ساعت معاملات هستیم و پوزیشن باز داریم
   if((currentTime < tradingStartTime || currentTime > tradingEndTime) && PositionsTotal() > 0)
   {
      LogViolation("OUT_OF_TRADING_HOURS", 
                  StringFormat("ساعت: %s", TimeToString(currentTime)));
   }
}

//+------------------------------------------------------------------+
//| تابع نظارت بر پوزیشن‌های باز                                    |
//+------------------------------------------------------------------+
void MonitorOpenPositions()
{
   int positions = PositionsTotal();
   
   for(int i = 0; i < positions; i++)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket))
      {
         double currentPrice = PositionGetDouble(POSITION_PRICE_CURRENT);
         double stopLoss = PositionGetDouble(POSITION_SL);
         double takeProfit = PositionGetDouble(POSITION_TP);
         
         // ذخیره قیمت اصلی برای تشخیص تغییرات
         int index = (int)(ticket % 100);
         
         if(!slInitialized[index])
         {
            originalSLs[index] = stopLoss;
            originalPrices[index] = currentPrice;
            slInitialized[index] = true;
         }
         
         // هشدار نزدیکی به استاپ
         if(stopLoss > 0)
         {
            double distanceToSL = MathAbs(currentPrice - stopLoss);
            double distancePercent = (distanceToSL / currentPrice) * 100;
            
            if(distancePercent < 0.1) // 0.1% فاصله
            {
               Alert("⚠️ پوزیشن ", ticket, " نزدیک استاپ‌لاس! فاصله: ", 
                     StringFormat("%.4f", distanceToSL), 
                     " (", StringFormat("%.2f", distancePercent), "%)");
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| تابع قفل استاپ‌لاس                                              |
//+------------------------------------------------------------------+
void LockStopLoss()
{
   int positions = PositionsTotal();
   
   for(int i = 0; i < positions; i++)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket))
      {
         double currentSL = PositionGetDouble(POSITION_SL);
         double currentTP = PositionGetDouble(POSITION_TP);
         double currentPrice = PositionGetDouble(POSITION_PRICE_CURRENT);
         
         int index = (int)(ticket % 100);
         
         // اگر استاپ تغییر کرده باشد
         if(slInitialized[index] && currentSL != originalSLs[index])
         {
            // بررسی آیا تغییر مجاز است (حرکت به سمت سود)
            bool allowedChange = false;
            
            // اگر پوزیشن خرید است و استاپ بالاتر رفته (به نفع معامله)
            if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
            {
               if(currentSL > originalSLs[index])
               {
                  allowedChange = true;
                  originalSLs[index] = currentSL; // به‌روزرسانی استاپ جدید
               }
            }
            // اگر پوزیشن فروش است و استاپ پایین‌تر رفته (به نفع معامله)
            else if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL)
            {
               if(currentSL < originalSLs[index])
               {
                  allowedChange = true;
                  originalSLs[index] = currentSL; // به‌روزرسانی استاپ جدید
               }
            }
            
            // اگر تغییر غیرمجاز بود
            if(!allowedChange)
            {
               Alert("⛔ تغییر استاپ ممنوع! استاپ به حالت قبل برگردانده می‌شود.");
               
               // بازگرداندن به استاپ اصلی
               trade.PositionModify(ticket, originalSLs[index], currentTP);
               
               // ثبت تخلف
               LogViolation("STOPLOSS_VIOLATION", 
                          StringFormat("پوزیشن %I64d: از %.5f به %.5f تغییر یافت", 
                                      ticket, originalSLs[index], currentSL));
            }
            else
            {
               Print("✅ تغییر استاپ مجاز: پوزیشن ", ticket, 
                     " از ", originalSLs[index], " به ", currentSL);
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| تابع بررسی تخلفات                                               |
//+------------------------------------------------------------------+
void CheckForViolations()
{
   // بررسی تعداد پوزیشن
   int positions = PositionsTotal();
   if(positions > currentMaxPositions)
   {
      LogViolation("MAX_POSITIONS_VIOLATION", StringFormat("تعداد پوزیشن: %d", positions));
      if(EnableAlerts && positions > currentMaxPositions + 1)
      {
         Alert("⛔ تعداد پوزیشن بیش از حد مجاز!");
      }
   }
   
   // بررسی معاملات خارج از ساعت (فقط هشدار)
   if(!IsTradingTime())
   {
      if(positions > 0)
      {
         static bool warned = false;
         if(!warned)
         {
            Alert("⚠️ توجه: شما خارج از ساعت معاملات پوزیشن باز دارید.");
            warned = true;
         }
      }
   }
   else
   {
      static bool warned = false;
      warned = false;
   }
}

//+------------------------------------------------------------------+
//| تابع بررسی زمان معاملات                                         |
//+------------------------------------------------------------------+
bool IsTradingTime()
{
   datetime currentTime = TimeCurrent();
   return (currentTime >= tradingStartTime && currentTime <= tradingEndTime);
}

//+------------------------------------------------------------------+
//| تابع ثبت تخلف                                                   |
//+------------------------------------------------------------------+
void LogViolation(string violationType, string details)
{
   string filename = "violations_" + TimeToString(TimeCurrent(), TIME_DATE) + ".txt";
   int handle = FileOpen(filename, FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI);
   
   if(handle != INVALID_HANDLE)
   {
      FileSeek(handle, 0, SEEK_END);
      string logEntry = StringFormat("[%s] %s: %s\r\n", 
                                     TimeToString(TimeCurrent(), TIME_SECONDS), 
                                     violationType, 
                                     details);
      FileWriteString(handle, logEntry);
      FileClose(handle);
   }
   
   // ارسال هشدار
   if(EnableAlerts)
   {
      Print("تخلف ثبت شد: ", violationType, " - ", details);
   }
}

//+------------------------------------------------------------------+
//| تابع ارتباط با پایتون                                           |
//+------------------------------------------------------------------+
void CommunicateWithPython()
{
   // خواندن سیگنال از فایل مشترک
   string filename = "shared_signals.txt";
   int handle = FileOpen(filename, FILE_READ|FILE_TXT|FILE_ANSI);
   
   if(handle != INVALID_HANDLE)
   {
      string signal = FileReadString(handle);
      FileClose(handle);
      
      if(signal != "")
      {
         ProcessPythonSignal(signal);
         
         // پاک کردن فایل بعد از خواندن
         FileDelete(filename);
      }
   }
}

//+------------------------------------------------------------------+
//| تابع پردازش سیگنال پایتون                                       |
//+------------------------------------------------------------------+
void ProcessPythonSignal(string signal)
{
   // فرمت سیگنال: ACTION|SYMBOL|PRICE|SL|TP|LOT
   string parts[];
   int count = StringSplit(signal, '|', parts);
   
   if(count >= 6)
   {
      string action = parts[0];
      string symbolName = parts[1];
      double price = StringToDouble(parts[2]);
      double sl = StringToDouble(parts[3]);
      double tp = StringToDouble(parts[4]);
      double lot = StringToDouble(parts[5]);
      
      if(tradingAllowed && !emergencyLocked)
      {
         if(action == "BUY")
         {
            if(EnableAutoRisk)
            {
               double calculatedLot = CalculateLotSize(symbolName, price, sl);
               lot = MathMin(lot, calculatedLot);
            }
            
            if(trade.Buy(lot, symbolName, price, sl, tp, "سیگنال پایتون"))
            {
               Print("✅ معامله خرید از پایتون اجرا شد: ", symbolName, 
                     " حجم: ", lot, " قیمت: ", price);
            }
            else
            {
               Print("❌ خطا در معامله خرید: ", trade.ResultRetcodeDescription());
            }
         }
         else if(action == "SELL")
         {
            if(EnableAutoRisk)
            {
               double calculatedLot = CalculateLotSize(symbolName, price, sl);
               lot = MathMin(lot, calculatedLot);
            }
            
            if(trade.Sell(lot, symbolName, price, sl, tp, "سیگنال پایتون"))
            {
               Print("✅ معامله فروش از پایتون اجرا شد: ", symbolName, 
                     " حجم: ", lot, " قیمت: ", price);
            }
            else
            {
               Print("❌ خطا در معامله فروش: ", trade.ResultRetcodeDescription());
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| تابع محاسبه حجم بر اساس ریسک                                    |
//+------------------------------------------------------------------+
double CalculateLotSize(string symbol, double entry, double stoploss)
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = balance * (currentRiskPercent / 100);
   
   // بارگذاری اطلاعات نماد
   if(!symbolInfo.Name(symbol))  // این تابع درست است
   {
      // اگر نماد بارگذاری نشد، سعی کنیم بارگذاری کنیم
      if(!symbolInfo.Name(symbol))
      {
         Print("❌ نماد ", symbol, " یافت نشد.");
         return 0.01;
      }
   }
   
   // استفاده از توابع درست
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   double tickSize = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   
   if(point == 0 || tickValue == 0)
   {
      Print("❌ اطلاعات نماد ناقص است. Point=", point, ", TickValue=", tickValue);
      return 0.01;
   }
   
   double stopDistance = MathAbs(entry - stoploss);
   
   // برای جفت‌های فارکس، point معمولاً 0.00001 است (5 رقم اعشار)
   // برای جفت‌های ین، point 0.001 است (3 رقم اعشار)
   double stopDistancePoints;
   
   if(point == 0.00001 || point == 0.001)
   {
      // برای فارکس
      stopDistancePoints = stopDistance / point;
   }
   else if(point >= 0.01)
   {
      // برای شاخص‌ها و طلا
      stopDistancePoints = stopDistance / point;
   }
   else
   {
      stopDistancePoints = stopDistance / 0.00001; // مقدار پیش‌فرض
   }
   
   if(stopDistancePoints == 0)
   {
      Print("⚠️ فاصله استاپ صفر است.");
      return 0.01;
   }
   
   // محاسبه حجم
   double lotSize = riskAmount / (stopDistancePoints * tickValue);
   
   // محدود کردن به حداقل و حداکثر مجاز
   double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   
   lotSize = MathMax(lotSize, minLot);
   lotSize = MathMin(lotSize, maxLot);
   
   // گرد کردن به نزدیک‌ترین مرحله حجم
   if(lotStep > 0)
   {
      lotSize = MathRound(lotSize / lotStep) * lotStep;
   }
   
   lotSize = NormalizeDouble(lotSize, 2);
   
   Print(StringFormat("📊 محاسبه حجم: نماد=%s, ورود=%.5f, استاپ=%.5f, فاصله=%.1f پیپ, حجم=%.2f", 
                     symbol, entry, stoploss, stopDistancePoints, lotSize));
   
   return lotSize;
}

//+------------------------------------------------------------------+
//| تابع مدیریت رویدادهای چارت                                      |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
   // مدیریت کلیک روی دکمه‌ها
   if(id == CHARTEVENT_OBJECT_CLICK)
   {
      if(sparam == "Btn_Checklist")
      {
         OpenChecklist();
      }
      else if(sparam == "Btn_Analyze")
      {
         RunAnalysis();
      }
      else if(sparam == "Btn_Emergency")
      {
         EmergencyLock();
      }
      else if(sparam == "Btn_Reset")
      {
         ResetSystem();
      }
      else if(sparam == "Btn_Hide")
      {
         TogglePanelVisibility();
      }
   }
}

//+------------------------------------------------------------------+
//| تابع تغییر دید پنل                                              |
//+------------------------------------------------------------------+
void TogglePanelVisibility()
{
   panelVisible = !panelVisible;
   
   // نمایش/مخفی کردن همه اشیاء پنل
   string objects[] = {"MainPanel", "Lbl_Title", "Btn_Checklist", "Btn_Analyze", 
                      "Btn_Emergency", "Btn_Reset", "Btn_Hide", "Lbl_Account", 
                      "Lbl_Risk", "Lbl_Trading", "Lbl_Time", "Lbl_Positions"};
   
   for(int i = 0; i < ArraySize(objects); i++)
   {
      ObjectSetInteger(0, objects[i], OBJPROP_TIMEFRAMES, 
                      panelVisible ? OBJ_ALL_PERIODS : OBJ_NO_PERIODS);
   }
   
   Alert(panelVisible ? "✅ پنل نمایش داده شد" : "📁 پنل مخفی شد");
}

//+------------------------------------------------------------------+
//| تابع بازکردن چک‌لیست                                            |
//+------------------------------------------------------------------+
void OpenChecklist()
{
   double dailyPL = CalculateDailyPL();
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskPercent = 0;
   
   if(balance > 0 && dailyPL < 0)
   {
      riskPercent = (MathAbs(dailyPL) / balance) * 100;
   }
   
   string checklist = 
      "═══════════════════════════════════════════\n" +
      "              📋 چک‌لیست معاملاتی           \n" +
      "═══════════════════════════════════════════\n" +
      "1. ✅ روند در تایم‌فریم بالاتر تأیید شد؟\n" +
      "2. ✅ نسبت R:R حداقل ۱:۱.۵ است؟\n" +
      "3. ✅ اخبار مهم امروز بررسی شد؟\n" +
      "4. ✅ ریسک امروز از " + DoubleToString(currentDailyRiskLimit) + "% کمتر است؟\n" +
      "5. ✅ خواب و حالت روانی مناسب است؟\n" +
      "6. ✅ در ساعت معاملات (10-18) هستیم؟\n" +
      "7. ✅ تعداد پوزیشن‌ها از " + IntegerToString(currentMaxPositions) + " کمتر است؟\n" +
      "═══════════════════════════════════════════\n" +
      "📊 وضعیت فعلی:\n" +
      "   • ریسک امروز: " + DoubleToString(riskPercent, 2) + "%\n" +
      "   • پوزیشن‌های باز: " + IntegerToString(PositionsTotal()) + "\n" +
      "   • ساعت: " + TimeToString(TimeCurrent(), TIME_MINUTES) + "\n" +
      "═══════════════════════════════════════════\n" +
      "⚠️  اگر همه موارد رعایت شد، می‌توانید معامله کنید.\n" +
      "⛔  در غیر این صورت، معامله نکنید!";
   
   Comment(checklist);
   Alert("🔍 لطفاً چک‌لیست را بررسی کنید");
}

//+------------------------------------------------------------------+
//| تابع اجرای تحلیل                                               |
//+------------------------------------------------------------------+
void RunAnalysis()
{
   // ذخیره اطلاعات کنونی برای تحلیل
   string symbol = Symbol();
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   
   string data = StringFormat("%s,%.5f,%.5f,%s", 
                              symbol, bid, ask, 
                              TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS));
   
   int handle = FileOpen("analysis_request.txt", FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, data);
      FileClose(handle);
   }
   
   Alert("✅ درخواست تحلیل ارسال شد. نتایج در داشبورد نمایش داده می‌شود.");
}

//+------------------------------------------------------------------+
//| تابع قفل اضطراری                                                |
//+------------------------------------------------------------------+
void EmergencyLock()
{
   emergencyLocked = true;
   tradingAllowed = false;
   
   // بستن تمام پوزیشن‌ها
   int positions = PositionsTotal();
   int closedCount = 0;
   
   for(int i = positions - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket))
      {
         if(trade.PositionClose(ticket))
         {
            closedCount++;
         }
      }
   }
   
   Alert("🔴 قفل اضطراری فعال شد!");
   Alert(StringFormat("✅ %d پوزیشن بسته شدند.", closedCount));
   SendNotification("قفل اضطراری فعال شد - تمام معاملات بسته شدند");
   
   // مسدود کردن به مدت ۲۴ ساعت
   EventSetTimer(86400);
   
   Print("🚨 قفل اضطراری فعال شد. ", closedCount, " پوزیشن بسته شدند.");
}

//+------------------------------------------------------------------+
//| تابع بازنشانی سیستم                                             |
//+------------------------------------------------------------------+
void ResetSystem()
{
   emergencyLocked = false;
   tradingAllowed = true;
   
   // ریست آرایه‌های استاپ
   ArrayInitialize(originalSLs, 0);
   ArrayInitialize(slInitialized, false);
   ArrayInitialize(originalPrices, 0);
   
   // ریست تایمر
   EventSetTimer(1);
   
   Alert("✅ سیستم ریست شد.");
   Alert("🔓 معاملات مجدداً فعال گردید.");
   
   Print("🔄 سیستم ریست شد. معاملات فعال شدند.");
}

//+------------------------------------------------------------------+
//| تابع بارگذاری تنظیمات                                           |
//+------------------------------------------------------------------+
void LoadSettings()
{
   string filename = "settings.txt";
   if(FileIsExist(filename))
   {
      int handle = FileOpen(filename, FILE_READ|FILE_TXT|FILE_ANSI);
      if(handle != INVALID_HANDLE)
      {
         while(!FileIsEnding(handle))
         {
            string line = FileReadString(handle);
            string parts[];
            int count = StringSplit(line, '=', parts);
            
            if(count == 2)
            {
               string key = parts[0];
               string value = parts[1];
               
               if(key == "RiskPercent") 
                  currentRiskPercent = StringToDouble(value);
               else if(key == "DailyRiskLimit") 
                  currentDailyRiskLimit = StringToDouble(value);
               else if(key == "MaxPositions") 
                  currentMaxPositions = (int)StringToInteger(value);
            }
         }
         FileClose(handle);
         
         Print("⚙️ تنظیمات از فایل بارگذاری شد:");
         Print("   • ریسک هر معامله: ", currentRiskPercent, "%");
         Print("   • ریسک روزانه: ", currentDailyRiskLimit, "%");
         Print("   • حداکثر پوزیشن: ", currentMaxPositions);
      }
   }
   else
   {
      Print("⚠️ فایل تنظیمات یافت نشد. از تنظیمات پیش‌فرض استفاده می‌شود.");
   }
}

//+------------------------------------------------------------------+
//| تابع به‌روزرسانی آمار روزانه                                    |
//+------------------------------------------------------------------+
void UpdateDailyStats()
{
   datetime currentDay = GetStartOfDay(TimeCurrent());
   
   if(currentDay > lastResetTime)
   {
      // روز جدید - ریست آمار
      dailyProfit = 0;
      dailyLoss = 0;
      lastResetTime = currentDay;
      
      // باز کردن قفل‌ها در روز جدید
      if(!emergencyLocked)
      {
         tradingAllowed = true;
      }
      
      // ریست آرایه‌های استاپ
      ArrayInitialize(originalSLs, 0);
      ArrayInitialize(slInitialized, false);
      ArrayInitialize(originalPrices, 0);
      
      Print("📅 روز جدید: ", TimeToString(currentDay, TIME_DATE));
      Print("📊 آمار روزانه ریست شد.");
   }
}