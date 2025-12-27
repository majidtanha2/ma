#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trader's Guardian System - Main Backend
Version: 2.0 - Complete Version
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import yaml
from typing import Dict, List, Optional, Tuple
import asyncio
import threading
from queue import Queue
import glob

# تنظیمات مسیر
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Import modules
try:
    from analyzer import MarketAnalyzer
    from risk_manager import RiskManager
    from dashboard.data_provider import DataProvider
    from mt5_connector import MT5Connector
except ImportError:
    # اگر ماژول‌ها وجود ندارند، تعریف می‌کنیم
    print("Creating missing modules...")
    
    # ایجاد ماژول‌های حداقلی
    class MarketAnalyzer:
        def __init__(self, config):
            self.config = config
        
        def analyze_symbol(self, symbol, df, timeframe='H1'):
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                'current_price': df['close'].iloc[-1] if not df.empty else 0,
                'signal': 'HOLD',
                'confidence': 50
            }
    
    class RiskManager:
        def __init__(self):
            pass
        
        def assess_trade_risk(self, analysis, risk_config):
            return {
                'risk_score': 5.0,
                'trade_signal': 'HOLD',
                'confidence': 50,
                'recommendation': 'WAIT'
            }
    
    class DataProvider:
        def __init__(self):
            pass
        
        def get_symbol_data(self, symbol, timeframes):
            return pd.DataFrame()
    
    class MT5Connector:
        def __init__(self, config):
            self.config = config
            self.connected = False

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, 'logs', 'system.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TraderGuardianBackend:
    """کلاس اصلی سیستم بک‌اند - نسخه کامل"""
    
    def __init__(self, config_file='config/settings.yaml'):
        """مقداردهی اولیه سیستم کامل"""
        self.base_dir = BASE_DIR
        self.config = self.load_config(config_file)
        self.setup_directories()
        
        # Initialize modules
        self.analyzer = MarketAnalyzer(self.config)
        self.risk_manager = RiskManager()
        self.data_provider = DataProvider()
        self.mt5_connector = MT5Connector(self.config)
        
        # System state
        self.running = False
        self.mt5_connected = False
        self.emergency_mode = False
        self.daily_stats = {
            'profit': 0,
            'loss': 0,
            'trades': 0,
            'violations': 0
        }
        
        # Queues for communication
        self.signal_queue = Queue()
        self.alert_queue = Queue()
        
        # Threads
        self.monitor_thread = None
        self.analysis_thread = None
        
        logger.info("Trader's Guardian System - Complete Version Initialized")
    
    def setup_directories(self):
        """ایجاد تمام دایرکتوری‌های لازم"""
        directories = [
            'logs',
            'data',
            'data/signals',
            'data/analysis',
            'data/stats',
            'shared_files',
            'shared_files/signals',
            'shared_files/violations',
            'dashboard/assets',
            'config'
        ]
        
        for dir_path in directories:
            full_path = os.path.join(self.base_dir, dir_path)
            os.makedirs(full_path, exist_ok=True)
            logger.debug(f"Directory created/verified: {full_path}")
    
    def load_config(self, config_file):
        """بارگذاری تنظیمات از فایل YAML"""
        config_path = os.path.join(self.base_dir, config_file)
        
        default_config = {
            'mt5': {
                'path': 'C:/Program Files/MetaTrader 5/terminal64.exe',
                'login': 12345678,
                'password': 'password',
                'server': 'MetaQuotes-Demo',
                'timeout': 60000,
                'portable_mode': False
            },
            'risk': {
                'max_daily_risk': 1.5,
                'max_trade_risk': 1.0,
                'max_drawdown': 5.0,
                'max_positions': 3,
                'daily_loss_limit': 2.0
            },
            'trading': {
                'symbols': ['EURUSD', 'GBPUSD', 'XAUUSD', 'USDJPY'],
                'timeframes': ['M15', 'H1', 'H4', 'D1'],
                'trading_hours_start': 10,
                'trading_hours_end': 18,
                'weekend_trading': False
            },
            'analysis': {
                'indicators': ['RSI', 'MACD', 'EMA', 'BollingerBands', 'ATR'],
                'patterns': True,
                'volume_analysis': True,
                'sentiment_analysis': False
            },
            'system': {
                'monitoring_interval': 5,
                'analysis_interval': 300,
                'dashboard_port': 8501,
                'dashboard_host': 'localhost',
                'auto_start': True,
                'emergency_phone': '',
                'email_alerts': ''
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                
                # Merge with default
                merged_config = self.merge_dicts(default_config, user_config)
                logger.info(f"Configuration loaded from {config_file}")
                return merged_config
            else:
                # Save default config
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
                logger.info(f"Default configuration saved to {config_file}")
                return default_config
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return default_config
    
    def merge_dicts(self, dict1, dict2):
        """ادغام عمقی دو دیکشنری"""
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    def connect_to_mt5(self):
        """اتصال کامل به MetaTrader 5"""
        try:
            mt5_config = self.config['mt5']
            
            logger.info(f"Connecting to MT5 with login: {mt5_config['login']}")
            logger.info(f"MT5 Path: {mt5_config['path']}")
            logger.info(f"Server: {mt5_config['server']}")
            
            # Close any existing connection
            if mt5.initialize():
                mt5.shutdown()
                time.sleep(1)
            
            # Initialize with full parameters
            if not mt5.initialize(
                path=mt5_config['path'],
                login=mt5_config['login'],
                password=mt5_config['password'],
                server=mt5_config['server'],
                timeout=mt5_config['timeout'],
                portable=mt5_config.get('portable_mode', False)
            ):
                error = mt5.last_error()
                logger.error(f"MT5 initialization failed. Error code: {error}")
                
                # Try alternative connection method
                logger.info("Trying alternative connection method...")
                if not mt5.initialize():
                    logger.error("All connection attempts failed")
                    return False
            
            # Verify connection
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to retrieve account information")
                return False
            
            self.mt5_connected = True
            
            # Log connection details
            logger.info("✅ Successfully connected to MetaTrader 5")
            logger.info(f"   Account: {account_info.login}")
            logger.info(f"   Name: {account_info.name}")
            logger.info(f"   Server: {account_info.server}")
            logger.info(f"   Balance: ${account_info.balance:.2f}")
            logger.info(f"   Equity: ${account_info.equity:.2f}")
            logger.info(f"   Currency: {account_info.currency}")
            logger.info(f"   Leverage: 1:{account_info.leverage}")
            logger.info(f"   Trade Allowed: {account_info.trade_allowed}")
            
            # Verify symbols
            symbols = self.config['trading']['symbols']
            for symbol in symbols:
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info:
                    logger.info(f"   Symbol {symbol}: Available")
                else:
                    logger.warning(f"   Symbol {symbol}: Not available")
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to MT5: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def start_monitoring(self):
        """شروع نظارت بر حساب و معاملات"""
        logger.info("Starting account monitoring...")
        self.running = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        # Start analysis thread
        self.analysis_thread = threading.Thread(target=self.analysis_loop, daemon=True)
        self.analysis_thread.start()
        
        # Start dashboard if enabled
        if self.config['system'].get('dashboard_enabled', True):
            dashboard_thread = threading.Thread(target=self.start_dashboard, daemon=True)
            dashboard_thread.start()
        
        logger.info("All system threads started")
    
    def monitoring_loop(self):
        """حلقه نظارت مداوم"""
        monitoring_interval = self.config['system']['monitoring_interval']
        
        while self.running:
            try:
                if not self.mt5_connected:
                    if not self.connect_to_mt5():
                        time.sleep(30)
                        continue
                
                # 1. Check account status
                self.check_account_status()
                
                # 2. Monitor open positions
                self.monitor_positions()
                
                # 3. Check for violations
                self.check_violations()
                
                # 4. Communicate with MT5 EA
                self.communicate_with_ea()
                
                # 5. Update daily stats
                self.update_daily_stats()
                
                # 6. Process alerts
                self.process_alerts()
                
                time.sleep(monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)
    
    def analysis_loop(self):
        """حلقه تحلیل بازار"""
        analysis_interval = self.config['system']['analysis_interval']
        
        while self.running:
            try:
                if not self.mt5_connected:
                    time.sleep(60)
                    continue
                
                logger.info("Starting market analysis cycle...")
                
                symbols = self.config['trading']['symbols']
                timeframes = self.config['trading']['timeframes']
                
                for symbol in symbols:
                    for timeframe in timeframes:
                        try:
                            # Get market data
                            data = self.get_market_data(symbol, timeframe)
                            if data is None or data.empty:
                                continue
                            
                            # Analyze
                            analysis = self.analyzer.analyze_symbol(data, symbol, timeframe)
                            
                            # Risk assessment
                            risk_assessment = self.risk_manager.assess_trade_risk(
                                analysis, 
                                self.config['risk']
                            )
                            
                            # Save analysis
                            self.save_analysis(symbol, timeframe, analysis, risk_assessment)
                            
                            # Generate signal if conditions met
                            if risk_assessment.get('trade_signal') in ['BUY', 'SELL']:
                                confidence = risk_assessment.get('confidence', 0)
                                if confidence >= 70:  # Minimum confidence threshold
                                    self.generate_signal(symbol, analysis, risk_assessment)
                            
                        except Exception as e:
                            logger.error(f"Error analyzing {symbol} {timeframe}: {e}")
                
                logger.info(f"Analysis cycle completed. Next in {analysis_interval} seconds")
                time.sleep(analysis_interval)
                
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                time.sleep(60)
    
    def get_market_data(self, symbol, timeframe, bars=500):
        """دریافت داده‌های بازار از MT5"""
        try:
            # Convert timeframe string to MT5 constant
            tf_mapping = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1,
                'W1': mt5.TIMEFRAME_W1,
                'MN1': mt5.TIMEFRAME_MN1
            }
            
            tf_code = tf_mapping.get(timeframe.upper())
            if tf_code is None:
                logger.error(f"Invalid timeframe: {timeframe}")
                return None
            
            # Get rates
            rates = mt5.copy_rates_from_pos(symbol, tf_code, 0, bars)
            if rates is None or len(rates) == 0:
                logger.warning(f"No data for {symbol} on {timeframe}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Rename columns
            df.columns = ['open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def check_account_status(self):
        """بررسی وضعیت حساب"""
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return
            
            # Check margin level
            margin_level = account_info.margin_level
            if margin_level < 100:
                self.alert_queue.put({
                    'type': 'MARGIN_WARNING',
                    'message': f"Margin level critical: {margin_level:.2f}%",
                    'priority': 'HIGH'
                })
            
            # Check free margin
            free_margin = account_info.margin_free
            balance = account_info.balance
            
            if balance > 0 and free_margin / balance < 0.1:
                self.alert_queue.put({
                    'type': 'FREE_MARGIN_WARNING',
                    'message': f"Free margin low: ${free_margin:.2f}",
                    'priority': 'MEDIUM'
                })
            
        except Exception as e:
            logger.error(f"Error checking account status: {e}")
    
    def monitor_positions(self):
        """نظارت بر پوزیشن‌های باز"""
        try:
            positions = mt5.positions_get()
            if positions is None:
                return
            
            max_positions = self.config['risk']['max_positions']
            if len(positions) > max_positions:
                self.alert_queue.put({
                    'type': 'MAX_POSITIONS_VIOLATION',
                    'message': f"Max positions exceeded: {len(positions)}/{max_positions}",
                    'priority': 'HIGH'
                })
            
            # Monitor each position
            for position in positions:
                self.monitor_single_position(position)
                
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
    
    def monitor_single_position(self, position):
        """نظارت بر یک پوزیشن خاص"""
        try:
            ticket = position.ticket
            symbol = position.symbol
            profit = position.profit
            sl = position.sl
            tp = position.tp
            current_price = position.price_current
            
            # Check stop loss distance
            if sl > 0:
                if position.type == mt5.POSITION_TYPE_BUY:
                    distance = (current_price - sl) / current_price * 100
                    if distance < 0.5:  # Less than 0.5%
                        self.alert_queue.put({
                            'type': 'SL_WARNING',
                            'message': f"Position {ticket} ({symbol}) close to SL: {distance:.2f}%",
                            'priority': 'MEDIUM'
                        })
                else:  # SELL
                    distance = (sl - current_price) / current_price * 100
                    if distance < 0.5:
                        self.alert_queue.put({
                            'type': 'SL_WARNING',
                            'message': f"Position {ticket} ({symbol}) close to SL: {distance:.2f}%",
                            'priority': 'MEDIUM'
                        })
            
            # Check profit/loss
            balance = mt5.account_info().balance
            if balance > 0:
                profit_percent = (profit / balance) * 100
                
                if profit_percent < -2:  # More than 2% loss
                    self.alert_queue.put({
                        'type': 'LARGE_LOSS',
                        'message': f"Position {ticket} losing {profit_percent:.2f}% of balance",
                        'priority': 'HIGH'
                    })
                elif profit_percent > 5:  # More than 5% profit
                    self.alert_queue.put({
                        'type': 'PROFIT_WARNING',
                        'message': f"Position {ticket} has {profit_percent:.2f}% profit. Consider taking profit.",
                        'priority': 'LOW'
                    })
                    
        except Exception as e:
            logger.error(f"Error monitoring position: {e}")
    
    def check_violations(self):
        """بررسی تخلفات از فایل‌های مشترک"""
        try:
            violations_dir = os.path.join(self.base_dir, 'shared_files', 'violations')
            os.makedirs(violations_dir, exist_ok=True)
            
            # Check for violation files
            pattern = os.path.join(violations_dir, 'violation_*.txt')
            for file_path in glob.glob(pattern):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse violation
                    lines = content.strip().split('\n')
                    if len(lines) >= 2:
                        violation_type = lines[0]
                        details = lines[1] if len(lines) > 1 else ""
                        
                        self.alert_queue.put({
                            'type': 'EA_VIOLATION',
                            'message': f"Violation from EA: {violation_type} - {details}",
                            'priority': 'HIGH'
                        })
                        
                        # Log to system
                        logger.warning(f"Violation detected from EA: {violation_type}")
                        self.daily_stats['violations'] += 1
                    
                    # Archive file
                    archive_path = file_path.replace('.txt', f'_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
                    os.rename(file_path, archive_path)
                    
                except Exception as e:
                    logger.error(f"Error processing violation file {file_path}: {e}")
            
        except Exception as e:
            logger.error(f"Error checking violations: {e}")
    
    def communicate_with_ea(self):
        """ارتباط با اکسپرت متاتریدر"""
        try:
            # Read signals from EA
            self.read_ea_signals()
            
            # Write signals to EA
            self.write_signals_to_ea()
            
            # Process analysis requests
            self.process_analysis_requests()
            
        except Exception as e:
            logger.error(f"Error communicating with EA: {e}")
    
    def read_ea_signals(self):
        """خواندن سیگنال‌های ارسالی از اکسپرت"""
        signal_file = os.path.join(self.base_dir, 'shared_files', 'ea_signals.txt')
        
        if os.path.exists(signal_file):
            try:
                with open(signal_file, 'r', encoding='utf-8') as f:
                    signal_data = f.read().strip()
                
                if signal_data:
                    # Parse signal
                    parts = signal_data.split('|')
                    if len(parts) >= 5:
                        signal = {
                            'action': parts[0],
                            'symbol': parts[1],
                            'price': float(parts[2]),
                            'sl': float(parts[3]),
                            'tp': float(parts[4]),
                            'lot': float(parts[5]) if len(parts) > 5 else 0.01,
                            'source': 'EA',
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        self.signal_queue.put(signal)
                        logger.info(f"Signal received from EA: {signal['action']} {signal['symbol']}")
                
                # Clear file
                open(signal_file, 'w').close()
                
            except Exception as e:
                logger.error(f"Error reading EA signals: {e}")
    
    def write_signals_to_ea(self):
        """نوشتن سیگنال‌ها برای اکسپرت"""
        # Check if there are signals to send
        if not self.signal_queue.empty():
            try:
                signal = self.signal_queue.get_nowait()
                
                # Format signal for EA
                signal_str = f"{signal['action']}|{signal['symbol']}|{signal.get('price', 0)}|{signal.get('sl', 0)}|{signal.get('tp', 0)}|{signal.get('lot', 0.01)}"
                
                # Write to shared file
                shared_file = os.path.join(self.base_dir, 'shared_files', 'shared_signals.txt')
                with open(shared_file, 'w', encoding='utf-8') as f:
                    f.write(signal_str)
                
                logger.info(f"Signal sent to EA: {signal['action']} {signal['symbol']}")
                
            except Exception as e:
                logger.error(f"Error writing signal to EA: {e}")
    
    def process_analysis_requests(self):
        """پردازش درخواست‌های تحلیل از اکسپرت"""
        request_file = os.path.join(self.base_dir, 'shared_files', 'analysis_request.txt')
        
        if os.path.exists(request_file):
            try:
                with open(request_file, 'r', encoding='utf-8') as f:
                    request_data = f.read().strip()
                
                if request_data:
                    # Parse request
                    parts = request_data.split(',')
                    if len(parts) >= 3:
                        symbol = parts[0]
                        bid = float(parts[1])
                        ask = float(parts[2])
                        
                        # Perform quick analysis
                        analysis = self.quick_analysis(symbol, bid, ask)
                        
                        # Save analysis result
                        result_file = os.path.join(self.base_dir, 'shared_files', 'analysis_result.txt')
                        with open(result_file, 'w', encoding='utf-8') as f:
                            f.write(json.dumps(analysis, ensure_ascii=False))
                        
                        logger.info(f"Analysis completed for {symbol}")
                
                # Clear request file
                open(request_file, 'w').close()
                
            except Exception as e:
                logger.error(f"Error processing analysis request: {e}")
    
    def quick_analysis(self, symbol, bid, ask):
        """تحلیل سریع برای درخواست‌های اکسپرت"""
        try:
            # Get recent data
            data = self.get_market_data(symbol, 'M15', bars=100)
            
            if data is None or data.empty:
                return {'error': 'No data available'}
            
            # Simple analysis
            current_price = (bid + ask) / 2
            ma_20 = data['close'].rolling(20).mean().iloc[-1]
            ma_50 = data['close'].rolling(50).mean().iloc[-1]
            
            trend = 'BULLISH' if current_price > ma_20 > ma_50 else 'BEARISH' if current_price < ma_20 < ma_50 else 'NEUTRAL'
            
            rsi = self.calculate_rsi(data['close'], period=14)
            rsi_value = rsi.iloc[-1] if not rsi.empty else 50
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'bid': bid,
                'ask': ask,
                'trend': trend,
                'ma_20': ma_20,
                'ma_50': ma_50,
                'rsi': rsi_value,
                'timestamp': datetime.now().isoformat(),
                'recommendation': 'BUY' if rsi_value < 30 and trend == 'BULLISH' else 'SELL' if rsi_value > 70 and trend == 'BEARISH' else 'HOLD'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_rsi(self, prices, period=14):
        """محاسبه RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def update_daily_stats(self):
        """به‌روزرسانی آمار روزانه"""
        try:
            # Calculate daily profit/loss
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            if not self.mt5_connected:
                return
            
            deals = mt5.history_deals_get(today, datetime.now())
            if deals:
                daily_profit = sum(deal.profit for deal in deals)
                daily_trades = len(deals)
                
                self.daily_stats = {
                    'profit': daily_profit,
                    'loss': abs(daily_profit) if daily_profit < 0 else 0,
                    'trades': daily_trades,
                    'violations': self.daily_stats['violations']
                }
                
                # Check daily risk limit
                max_daily_risk = self.config['risk']['max_daily_risk']
                balance = mt5.account_info().balance
                
                if balance > 0 and daily_profit < 0:
                    risk_percent = (abs(daily_profit) / balance) * 100
                    
                    if risk_percent >= max_daily_risk * 0.8:
                        self.alert_queue.put({
                            'type': 'DAILY_RISK_WARNING',
                            'message': f"Daily risk approaching limit: {risk_percent:.2f}%",
                            'priority': 'MEDIUM'
                        })
                    
                    if risk_percent >= max_daily_risk:
                        self.alert_queue.put({
                            'type': 'DAILY_RISK_LIMIT',
                            'message': f"Daily risk limit reached: {risk_percent:.2f}%",
                            'priority': 'HIGH'
                        })
                        self.activate_emergency_mode('DAILY_RISK_LIMIT_REACHED')
            
            # Save stats to file
            stats_file = os.path.join(self.base_dir, 'data', 'stats', f"daily_stats_{datetime.now().strftime('%Y%m%d')}.json")
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.daily_stats, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error updating daily stats: {e}")
    
    def process_alerts(self):
        """پردازش هشدارها"""
        try:
            while not self.alert_queue.empty():
                alert = self.alert_queue.get_nowait()
                
                # Log alert
                logger.warning(f"ALERT [{alert['priority']}]: {alert['type']} - {alert['message']}")
                
                # Save to alert log
                alert_log = os.path.join(self.base_dir, 'logs', 'alerts.log')
                with open(alert_log, 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now()}] [{alert['priority']}] {alert['type']}: {alert['message']}\n")
                
                # Send email/sms if configured
                if alert['priority'] == 'HIGH':
                    self.send_high_priority_alert(alert)
                
        except Exception as e:
            logger.error(f"Error processing alerts: {e}")
    
    def send_high_priority_alert(self, alert):
        """ارسال هشدار با اولویت بالا"""
        try:
            # Here you can implement email, SMS, or other notifications
            # For now, just log to a separate file
            emergency_log = os.path.join(self.base_dir, 'logs', 'emergency_alerts.log')
            with open(emergency_log, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] EMERGENCY: {alert['type']} - {alert['message']}\n")
            
            # Also create a visible notification file for EA
            notification_file = os.path.join(self.base_dir, 'shared_files', 'emergency_notification.txt')
            with open(notification_file, 'w', encoding='utf-8') as f:
                f.write(f"EMERGENCY|{alert['type']}|{alert['message']}")
            
        except Exception as e:
            logger.error(f"Error sending high priority alert: {e}")
    
    def save_analysis(self, symbol, timeframe, analysis, risk_assessment):
        """ذخیره تحلیل"""
        try:
            analysis_data = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis,
                'risk_assessment': risk_assessment,
                'system_state': {
                    'mt5_connected': self.mt5_connected,
                    'emergency_mode': self.emergency_mode,
                    'daily_stats': self.daily_stats
                }
            }
            
            # Save to file
            filename = f"analysis_{symbol}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.base_dir, 'data', 'analysis', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Analysis saved: {filename}")
            
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
    
    def generate_signal(self, symbol, analysis, risk_assessment):
        """تولید سیگنال معاملاتی"""
        try:
            if self.emergency_mode:
                logger.warning(f"Cannot generate signal in emergency mode: {symbol}")
                return
            
            if not self.mt5_connected:
                logger.warning(f"Cannot generate signal, MT5 not connected: {symbol}")
                return
            
            # Get account info for lot calculation
            account_info = mt5.account_info()
            balance = account_info.balance
            
            # Calculate position size based on risk
            max_trade_risk = self.config['risk']['max_trade_risk']
            risk_amount = balance * (max_trade_risk / 100)
            
            # Get current price
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.error(f"Cannot get symbol info: {symbol}")
                return
            
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"Cannot get tick data: {symbol}")
                return
            
            # Calculate stop loss and take profit from analysis
            entry_price = tick.ask if risk_assessment['trade_signal'] == 'BUY' else tick.bid
            stop_loss = analysis.get('stop_loss', 0)
            take_profit = analysis.get('take_profit', 0)
            
            # Calculate lot size
            if stop_loss > 0 and entry_price > 0:
                # Simplified lot calculation
                # In reality, you need to consider pip value, etc.
                lot_size = self.calculate_lot_size(symbol, entry_price, stop_loss, risk_amount)
            else:
                # Default lot size
                lot_size = 0.01
            
            # Create signal
            signal = {
                'action': risk_assessment['trade_signal'],
                'symbol': symbol,
                'price': entry_price,
                'sl': stop_loss,
                'tp': take_profit,
                'lot': lot_size,
                'confidence': risk_assessment.get('confidence', 0),
                'risk_percent': max_trade_risk,
                'risk_amount': risk_amount,
                'source': 'SYSTEM',
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to queue
            self.signal_queue.put(signal)
            
            # Also save to file
            signal_file = os.path.join(self.base_dir, 'data', 'signals', f"signal_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(signal_file, 'w', encoding='utf-8') as f:
                json.dump(signal, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Signal generated: {signal['action']} {symbol} {lot_size}L")
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
    
    def calculate_lot_size(self, symbol, entry_price, stop_loss, risk_amount):
        """محاسبه حجم معامله"""
        try:
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return 0.01
            
            # Calculate stop distance in points
            point = symbol_info.point
            stop_distance = abs(entry_price - stop_loss)
            stop_distance_points = stop_distance / point
            
            # Get tick value (simplified)
            # In reality, you need to consider currency conversion
            tick_value = 10  # $10 per lot for EURUSD
            
            # Calculate lot size
            if stop_distance_points > 0 and tick_value > 0:
                lot_size = risk_amount / (stop_distance_points * tick_value)
            else:
                lot_size = 0.01
            
            # Apply limits
            lot_size = max(lot_size, symbol_info.volume_min)
            lot_size = min(lot_size, symbol_info.volume_max)
            
            # Round to step
            volume_step = symbol_info.volume_step
            if volume_step > 0:
                lot_size = round(lot_size / volume_step) * volume_step
            
            return round(lot_size, 2)
            
        except Exception as e:
            logger.error(f"Error calculating lot size: {e}")
            return 0.01
    
    def activate_emergency_mode(self, reason):
        """فعال‌سازی حالت اضطراری"""
        if not self.emergency_mode:
            self.emergency_mode = True
            
            logger.critical(f"⚠️⚠️⚠️ EMERGENCY MODE ACTIVATED: {reason} ⚠️⚠️⚠️")
            
            # Send immediate alerts
            self.alert_queue.put({
                'type': 'EMERGENCY_MODE_ACTIVATED',
                'message': f"Emergency mode activated: {reason}",
                'priority': 'CRITICAL'
            })
            
            # Create emergency lock file
            lock_file = os.path.join(self.base_dir, 'shared_files', 'emergency_lock.txt')
            with open(lock_file, 'w', encoding='utf-8') as f:
                f.write(f"EMERGENCY_LOCK|{datetime.now().isoformat()}|{reason}")
            
            # Try to close all positions
            self.close_all_positions()
    
    def close_all_positions(self):
        """بستن تمام پوزیشن‌ها"""
        try:
            if not self.mt5_connected:
                return
            
            positions = mt5.positions_get()
            if not positions:
                return
            
            logger.warning(f"Closing all positions ({len(positions)} positions)")
            
            for position in positions:
                try:
                    # Prepare close request
                    close_request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": position.symbol,
                        "volume": position.volume,
                        "type": mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                        "position": position.ticket,
                        "price": mt5.symbol_info_tick(position.symbol).bid if position.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask,
                        "deviation": 20,
                        "magic": 999999,  # Emergency magic number
                        "comment": "EMERGENCY_CLOSE",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    
                    # Send order
                    result = mt5.order_send(close_request)
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        logger.info(f"Emergency close: Position {position.ticket} closed")
                    else:
                        logger.error(f"Failed to close position {position.ticket}: {result.comment}")
                        
                except Exception as e:
                    logger.error(f"Error closing position {position.ticket}: {e}")
            
        except Exception as e:
            logger.error(f"Error in close_all_positions: {e}")
    
    def start_dashboard(self):
        """راه‌اندازی داشبورد"""
        try:
            import subprocess
            import sys
            
            dashboard_path = os.path.join(self.base_dir, 'dashboard', 'app.py')
            
            if os.path.exists(dashboard_path):
                logger.info(f"Starting dashboard on port {self.config['system']['dashboard_port']}")
                
                # Run Streamlit dashboard
                cmd = [sys.executable, "-m", "streamlit", "run", dashboard_path, 
                      "--server.port", str(self.config['system']['dashboard_port']),
                      "--server.headless", "true",
                      "--browser.serverAddress", self.config['system']['dashboard_host']]
                
                subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
            else:
                logger.warning(f"Dashboard file not found: {dashboard_path}")
                
        except Exception as e:
            logger.error(f"Error starting dashboard: {e}")
    
    def shutdown(self):
        """خاموش کردن سیستم"""
        logger.info("Shutting down Trader's Guardian System...")
        
        self.running = False
        
        # Wait for threads
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)
        
        # Disconnect from MT5
        if self.mt5_connected:
            mt5.shutdown()
            logger.info("Disconnected from MT5")
        
        # Save final state
        self.save_system_state()
        
        logger.info("System shutdown complete")
    
    def save_system_state(self):
        """ذخیره وضعیت سیستم"""
        try:
            state = {
                'timestamp': datetime.now().isoformat(),
                'mt5_connected': self.mt5_connected,
                'emergency_mode': self.emergency_mode,
                'daily_stats': self.daily_stats,
                'running': self.running,
                'config': self.config
            }
            
            state_file = os.path.join(self.base_dir, 'data', 'system_state.json')
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving system state: {e}")

def main():
    """تابع اصلی اجرای سیستم"""
    print("\n" + "="*80)
    print("🛡️  TRADER'S GUARDIAN SYSTEM - COMPLETE VERSION")
    print("="*80)
    
    # Create system instance
    system = TraderGuardianBackend()
    
    try:
        # Connect to MT5
        print("\n🔗 Connecting to MetaTrader 5...")
        if not system.connect_to_mt5():
            print("❌ Failed to connect to MT5. Please check your configuration.")
            print("\nCheck the following:")
            print("1. Is MT5 installed and running?")
            print("2. Are the login credentials correct in config/settings.yaml?")
            print("3. Is the server name correct?")
            return
        
        # Start monitoring
        print("\n🚀 Starting system monitoring...")
        system.start_monitoring()
        
        # Keep main thread alive
        print("\n✅ System is now running!")
        print("Press Ctrl+C to stop\n")
        
        while system.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Shutdown requested by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        system.shutdown()
        print("\n👋 System terminated")

if __name__ == "__main__":
    main()