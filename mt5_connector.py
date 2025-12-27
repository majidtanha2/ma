#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اتصال کامل به MetaTrader 5
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
import json
import os
import threading
from queue import Queue

logger = logging.getLogger(__name__)

class MT5Connector:
    """مدیریت کامل ارتباط با MT5"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.mt5_config = config.get('mt5', {})
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.connection_lock = threading.Lock()
        
        # صف‌ها برای ارتباط ناهمزمان
        self.command_queue = Queue()
        self.response_queue = Queue()
        
        # وضعیت نمادها
        self.symbols_info = {}
        self.last_symbols_update = None
        
        # کش برای داده‌ها
        self.data_cache = {}
        self.cache_timeout = 60  # ثانیه
        
        logger.info("MT5Connector initialized")
    
    def connect(self, retry: bool = True) -> bool:
        """اتصال به MT5"""
        with self.connection_lock:
            if self.connected:
                return True
            
            try:
                logger.info("Connecting to MetaTrader 5...")
                
                # تنظیمات اتصال
                mt5_path = self.mt5_config.get('path', '')
                login = self.mt5_config.get('login')
                password = self.mt5_config.get('password')
                server = self.mt5_config.get('server')
                timeout = self.mt5_config.get('timeout', 10000)
                portable = self.mt5_config.get('portable_mode', False)
                
                # قطع اتصال قبلی اگر وجود دارد
                if mt5.initialize():
                    mt5.shutdown()
                    time.sleep(1)
                
                # اتصال جدید
                initialized = mt5.initialize(
                    path=mt5_path,
                    login=login,
                    password=password,
                    server=server,
                    timeout=timeout,
                    portable=portable
                )
                
                if not initialized:
                    error = mt5.last_error()
                    logger.error(f"MT5 initialization failed. Error: {error}")
                    
                    if retry and self.reconnect_attempts < self.max_reconnect_attempts:
                        self.reconnect_attempts += 1
                        logger.info(f"Retrying connection ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
                        time.sleep(2)
                        return self.connect(retry=True)
                    
                    return False
                
                # تأیید اتصال
                account_info = mt5.account_info()
                if account_info is None:
                    logger.error("Failed to get account info after connection")
                    mt5.shutdown()
                    return False
                
                self.connected = True
                self.reconnect_attempts = 0
                
                # بارگذاری اطلاعات نمادها
                self._load_symbols_info()
                
                # شروع thread مدیریت دستورات
                self._start_command_processor()
                
                logger.info(f"✅ Successfully connected to MT5 (Account: {account_info.login})")
                logger.info(f"   Balance: ${account_info.balance:.2f}")
                logger.info(f"   Server: {account_info.server}")
                logger.info(f"   Leverage: 1:{account_info.leverage}")
                
                return True
                
            except Exception as e:
                logger.error(f"Error connecting to MT5: {e}")
                return False
    
    def _load_symbols_info(self):
        """بارگذاری اطلاعات نمادها"""
        try:
            symbols = self.config.get('trading', {}).get('symbols', [])
            
            for symbol in symbols:
                info = mt5.symbol_info(symbol)
                if info:
                    self.symbols_info[symbol] = {
                        'name': symbol,
                        'digits': info.digits,
                        'point': info.point,
                        'trade_mode': info.trade_mode,
                        'swap_mode': info.swap_mode,
                        'margin_initial': info.margin_initial,
                        'margin_maintenance': info.margin_maintenance,
                        'volume_min': info.volume_min,
                        'volume_max': info.volume_max,
                        'volume_step': info.volume_step,
                        'volume_limit': info.volume_limit,
                        'trade_tick_size': info.trade_tick_size,
                        'trade_tick_value': info.trade_tick_value,
                        'trade_tick_value_profit': info.trade_tick_value_profit,
                        'trade_tick_value_loss': info.trade_tick_value_loss,
                        'trade_calc_mode': info.trade_calc_mode,
                        'trade_mode': info.trade_mode,
                        'swap_long': info.swap_long,
                        'swap_short': info.swap_short,
                        'spread': info.spread,
                        'spread_float': info.spread_float,
                        'start_time': info.start_time,
                        'time': info.time,
                        'expiration_time': info.expiration_time,
                        'trade_stops_level': info.trade_stops_level,
                        'trade_freeze_level': info.trade_freeze_level,
                        'trade_exemode': info.trade_exemode,
                        'currency_base': info.currency_base,
                        'currency_profit': info.currency_profit,
                        'currency_margin': info.currency_margin,
                        'description': info.description
                    }
            
            self.last_symbols_update = datetime.now()
            logger.info(f"Loaded info for {len(self.symbols_info)} symbols")
            
        except Exception as e:
            logger.error(f"Error loading symbols info: {e}")
    
    def _start_command_processor(self):
        """شروع پردازش دستورات"""
        def processor():
            while self.connected:
                try:
                    if not self.command_queue.empty():
                        command = self.command_queue.get_nowait()
                        result = self._process_command(command)
                        self.response_queue.put(result)
                    time.sleep(0.1)
                except Exception as e:
                    logger.error(f"Error in command processor: {e}")
                    time.sleep(1)
        
        thread = threading.Thread(target=processor, daemon=True)
        thread.start()
        logger.info("Command processor started")
    
    def _process_command(self, command: Dict) -> Dict:
        """پردازش دستور"""
        try:
            cmd_type = command.get('type')
            data = command.get('data', {})
            
            if cmd_type == 'GET_DATA':
                return self._command_get_data(data)
            elif cmd_type == 'PLACE_ORDER':
                return self._command_place_order(data)
            elif cmd_type == 'MODIFY_ORDER':
                return self._command_modify_order(data)
            elif cmd_type == 'CLOSE_ORDER':
                return self._command_close_order(data)
            elif cmd_type == 'GET_ACCOUNT_INFO':
                return self._command_get_account_info()
            elif cmd_type == 'GET_POSITIONS':
                return self._command_get_positions()
            elif cmd_type == 'GET_ORDERS':
                return self._command_get_orders()
            else:
                return {'success': False, 'error': f'Unknown command type: {cmd_type}'}
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {'success': False, 'error': str(e)}
    
    def disconnect(self):
        """قطع ارتباط"""
        with self.connection_lock:
            if self.connected:
                self.connected = False
                time.sleep(0.5)  # زمان برای توقف threadها
                mt5.shutdown()
                logger.info("Disconnected from MT5")
    
    def get_account_info(self) -> Dict:
        """دریافت اطلاعات حساب"""
        try:
            if not self.connected:
                if not self.connect():
                    return {}
            
            info = mt5.account_info()
            if info is None:
                return {}
            
            return {
                'login': info.login,
                'name': info.name,
                'server': info.server,
                'currency': info.currency,
                'company': info.company,
                'balance': info.balance,
                'equity': info.equity,
                'margin': info.margin,
                'free_margin': info.margin_free,
                'margin_level': info.margin_level,
                'margin_so_call': info.margin_so_call,
                'margin_so_so': info.margin_so_so,
                'margin_initial': info.margin_initial,
                'margin_maintenance': info.margin_maintenance,
                'assets': info.assets,
                'liabilities': info.liabilities,
                'blocked_commission': info.commission_blocked,
                'free_commission': info.commission_free,
                'leverage': info.leverage,
                'trade_allowed': info.trade_allowed,
                'trade_expert': info.trade_expert,
                'limit_orders': info.limit_orders,
                'credit': info.credit
            }
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    def get_market_data(self, symbol: str, timeframe: str = 'H1', 
                       bars: int = 100, from_date: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """دریافت داده‌های بازار"""
        try:
            if not self.connected:
                if not self.connect():
                    return None
            
            # بررسی کش
            cache_key = f"{symbol}_{timeframe}_{bars}"
            if cache_key in self.data_cache:
                cached_data, cache_time = self.data_cache[cache_key]
                if (datetime.now() - cache_time).seconds < self.cache_timeout:
                    return cached_data.copy()
            
            # تبدیل تایم‌فریم
            tf_map = {
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
            
            tf_code = tf_map.get(timeframe.upper())
            if tf_code is None:
                logger.error(f"Invalid timeframe: {timeframe}")
                return None
            
            # دریافت داده‌ها
            if from_date:
                rates = mt5.copy_rates_from(symbol, tf_code, from_date, bars)
            else:
                rates = mt5.copy_rates_from_pos(symbol, tf_code, 0, bars)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No data for {symbol} on {timeframe}")
                return None
            
            # تبدیل به DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # نام‌گذاری ستون‌ها
            df.columns = ['open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
            
            # ذخیره در کش
            self.data_cache[cache_key] = (df.copy(), datetime.now())
            
            logger.debug(f"Retrieved {len(df)} bars for {symbol} {timeframe}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """دریافت قیمت لحظه‌ای"""
        try:
            if not self.connected:
                if not self.connect():
                    return None
            
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.warning(f"No tick data for {symbol}")
                return None
            
            # اطلاعات نماد
            symbol_info = mt5.symbol_info(symbol)
            
            return {
                'symbol': symbol,
                'time': datetime.fromtimestamp(tick.time),
                'bid': tick.bid,
                'ask': tick.ask,
                'last': tick.last,
                'volume': tick.volume,
                'spread': tick.ask - tick.bid,
                'spread_pips': (tick.ask - tick.bid) * (10 ** symbol_info.digits) if symbol_info else 0,
                'high': tick.high if hasattr(tick, 'high') else tick.bid,
                'low': tick.low if hasattr(tick, 'low') else tick.ask
            }
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def get_open_positions(self) -> List[Dict]:
        """دریافت پوزیشن‌های باز"""
        try:
            if not self.connected:
                if not self.connect():
                    return []
            
            positions = mt5.positions_get()
            if positions is None:
                return []
            
            positions_list = []
            for pos in positions:
                positions_list.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                    'volume': pos.volume,
                    'open_price': pos.price_open,
                    'current_price': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'swap': pos.swap,
                    'commission': pos.commission,
                    'open_time': datetime.fromtimestamp(pos.time),
                    'magic': pos.magic,
                    'comment': pos.comment,
                    'identifier': pos.identifier
                })
            
            return positions_list
            
        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return []
    
    def get_pending_orders(self) -> List[Dict]:
        """دریافت دستورات معلق"""
        try:
            if not self.connected:
                if not self.connect():
                    return []
            
            orders = mt5.orders_get()
            if orders is None:
                return []
            
            orders_list = []
            for order in orders:
                orders_list.append({
                    'ticket': order.ticket,
                    'symbol': order.symbol,
                    'type': self._get_order_type_name(order.type),
                    'volume': order.volume_current,
                    'price_open': order.price_open,
                    'sl': order.sl,
                    'tp': order.tp,
                    'price_current': order.price_current,
                    'price_stoplimit': order.price_stoplimit,
                    'time_setup': datetime.fromtimestamp(order.time_setup),
                    'time_expiration': datetime.fromtimestamp(order.time_expiration) if order.time_expiration > 0 else None,
                    'magic': order.magic,
                    'comment': order.comment
                })
            
            return orders_list
            
        except Exception as e:
            logger.error(f"Error getting pending orders: {e}")
            return []
    
    def _get_order_type_name(self, order_type: int) -> str:
        """تبدیل نوع دستور به رشته"""
        type_map = {
            mt5.ORDER_TYPE_BUY: 'BUY',
            mt5.ORDER_TYPE_SELL: 'SELL',
            mt5.ORDER_TYPE_BUY_LIMIT: 'BUY_LIMIT',
            mt5.ORDER_TYPE_SELL_LIMIT: 'SELL_LIMIT',
            mt5.ORDER_TYPE_BUY_STOP: 'BUY_STOP',
            mt5.ORDER_TYPE_SELL_STOP: 'SELL_STOP',
            mt5.ORDER_TYPE_BUY_STOP_LIMIT: 'BUY_STOP_LIMIT',
            mt5.ORDER_TYPE_SELL_STOP_LIMIT: 'SELL_STOP_LIMIT',
            mt5.ORDER_TYPE_CLOSE_BY: 'CLOSE_BY'
        }
        return type_map.get(order_type, f'UNKNOWN_{order_type}')
    
    def place_order(self, order_params: Dict) -> Dict:
        """ثبت دستور معاملاتی"""
        try:
            if not self.connected:
                if not self.connect():
                    return {'success': False, 'error': 'Not connected to MT5'}
            
            # اعتبارسنجی پارامترها
            validation_result = self._validate_order_params(order_params)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            symbol = order_params['symbol']
            order_type = order_params['type']  # 'BUY', 'SELL', 'BUY_LIMIT', etc.
            volume = order_params['volume']
            price = order_params.get('price', 0)
            sl = order_params.get('sl', 0)
            tp = order_params.get('tp', 0)
            deviation = order_params.get('deviation', 10)
            magic = order_params.get('magic', 0)
            comment = order_params.get('comment', '')
            
            # دریافت قیمت فعلی
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {'success': False, 'error': f'No tick data for {symbol}'}
            
            # تنظیم درخواست
            request = {}
            
            if order_type in ['BUY', 'SELL']:
                # معامله فوری
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": volume,
                    "type": mt5.ORDER_TYPE_BUY if order_type == 'BUY' else mt5.ORDER_TYPE_SELL,
                    "price": tick.ask if order_type == 'BUY' else tick.bid,
                    "sl": sl,
                    "tp": tp,
                    "deviation": deviation,
                    "magic": magic,
                    "comment": comment,
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                # اگر قیمت مشخص شده باشد
                if price > 0:
                    request["price"] = price
                    
            elif order_type in ['BUY_LIMIT', 'SELL_LIMIT', 'BUY_STOP', 'SELL_STOP']:
                # دستور معلق
                type_map = {
                    'BUY_LIMIT': mt5.ORDER_TYPE_BUY_LIMIT,
                    'SELL_LIMIT': mt5.ORDER_TYPE_SELL_LIMIT,
                    'BUY_STOP': mt5.ORDER_TYPE_BUY_STOP,
                    'SELL_STOP': mt5.ORDER_TYPE_SELL_STOP
                }
                
                request = {
                    "action": mt5.TRADE_ACTION_PENDING,
                    "symbol": symbol,
                    "volume": volume,
                    "type": type_map[order_type],
                    "price": price,
                    "sl": sl,
                    "tp": tp,
                    "deviation": deviation,
                    "magic": magic,
                    "comment": comment,
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
            
            else:
                return {'success': False, 'error': f'Invalid order type: {order_type}'}
            
            # ارسال درخواست
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"✅ Order executed: {order_type} {symbol} {volume}L")
                
                return {
                    'success': True,
                    'order_id': result.order,
                    'deal_id': result.deal,
                    'volume': result.volume,
                    'price': result.price,
                    'bid': result.bid,
                    'ask': result.ask,
                    'comment': result.comment,
                    'request_id': result.request_id,
                    'retcode': result.retcode
                }
            else:
                logger.error(f"❌ Order failed: {result.comment}")
                
                return {
                    'success': False,
                    'retcode': result.retcode,
                    'comment': result.comment,
                    'error': self._get_error_description(result.retcode)
                }
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {'success': False, 'error': str(e)}
    
    def _validate_order_params(self, params: Dict) -> Dict:
        """اعتبارسنجی پارامترهای دستور"""
        try:
            required_fields = ['symbol', 'type', 'volume']
            missing_fields = [field for field in required_fields if field not in params]
            
            if missing_fields:
                return {'valid': False, 'error': f'Missing required fields: {missing_fields}'}
            
            symbol = params['symbol']
            order_type = params['type']
            volume = params['volume']
            
            # بررسی وجود نماد
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return {'valid': False, 'error': f'Symbol {symbol} not found'}
            
            # بررسی حجم
            if volume < symbol_info.volume_min:
                return {'valid': False, 'error': f'Volume too small. Minimum: {symbol_info.volume_min}'}
            
            if volume > symbol_info.volume_max:
                return {'valid': False, 'error': f'Volume too large. Maximum: {symbol_info.volume_max}'}
            
            # بررسی نوع دستور
            valid_types = ['BUY', 'SELL', 'BUY_LIMIT', 'SELL_LIMIT', 'BUY_STOP', 'SELL_STOP']
            if order_type not in valid_types:
                return {'valid': False, 'error': f'Invalid order type. Valid types: {valid_types}'}
            
            # برای دستورات معلق، بررسی قیمت
            if order_type in ['BUY_LIMIT', 'SELL_LIMIT', 'BUY_STOP', 'SELL_STOP']:
                if 'price' not in params or params['price'] <= 0:
                    return {'valid': False, 'error': 'Price is required for pending orders'}
            
            return {'valid': True, 'error': ''}
            
        except Exception as e:
            return {'valid': False, 'error': f'Validation error: {e}'}
    
    def modify_order(self, ticket: int, sl: float = 0, tp: float = 0, 
                    price: float = 0) -> Dict:
        """ویرایش دستور"""
        try:
            if not self.connected:
                if not self.connect():
                    return {'success': False, 'error': 'Not connected to MT5'}
            
            # پیدا کردن دستور
            positions = mt5.positions_get(ticket=ticket)
            orders = mt5.orders_get(ticket=ticket)
            
            if not positions and not orders:
                return {'success': False, 'error': f'Order/position {ticket} not found'}
            
            # تنظیم درخواست ویرایش
            request = {
                "action": mt5.TRADE_ACTION_SLTP if positions else mt5.TRADE_ACTION_MODIFY,
                "position" if positions else "order": ticket,
                "sl": sl,
                "tp": tp,
            }
            
            if price > 0 and not positions:
                request["price"] = price
            
            # ارسال درخواست
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"✅ Order {ticket} modified successfully")
                
                return {
                    'success': True,
                    'order_id': result.order,
                    'price': result.price,
                    'sl': sl,
                    'tp': tp,
                    'retcode': result.retcode
                }
            else:
                logger.error(f"❌ Failed to modify order {ticket}: {result.comment}")
                
                return {
                    'success': False,
                    'retcode': result.retcode,
                    'comment': result.comment,
                    'error': self._get_error_description(result.retcode)
                }
                
        except Exception as e:
            logger.error(f"Error modifying order: {e}")
            return {'success': False, 'error': str(e)}
    
    def close_position(self, ticket: int, volume: float = 0, 
                      deviation: int = 10) -> Dict:
        """بستن پوزیشن"""
        try:
            if not self.connected:
                if not self.connect():
                    return {'success': False, 'error': 'Not connected to MT5'}
            
            # پیدا کردن پوزیشن
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                return {'success': False, 'error': f'Position {ticket} not found'}
            
            position = positions[0]
            symbol = position.symbol
            
            # اگر حجم مشخص نشده باشد، کل حجم بسته می‌شود
            if volume <= 0:
                volume = position.volume
            
            # دریافت قیمت فعلی
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {'success': False, 'error': f'No tick data for {symbol}'}
            
            # تنظیم درخواست بستن
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "position": ticket,
                "price": tick.bid if position.type == mt5.POSITION_TYPE_BUY else tick.ask,
                "deviation": deviation,
                "magic": position.magic,
                "comment": "Closed by system",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # ارسال درخواست
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"✅ Position {ticket} closed successfully")
                
                return {
                    'success': True,
                    'order_id': result.order,
                    'deal_id': result.deal,
                    'volume': result.volume,
                    'price': result.price,
                    'profit': position.profit,
                    'retcode': result.retcode
                }
            else:
                logger.error(f"❌ Failed to close position {ticket}: {result.comment}")
                
                return {
                    'success': False,
                    'retcode': result.retcode,
                    'comment': result.comment,
                    'error': self._get_error_description(result.retcode)
                }
                
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {'success': False, 'error': str(e)}
    
    def close_all_positions(self, symbol: str = None) -> Dict:
        """بستن تمام پوزیشن‌ها"""
        try:
            if not self.connected:
                if not self.connect():
                    return {'success': False, 'error': 'Not connected to MT5'}
            
            # دریافت پوزیشن‌ها
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            if not positions:
                return {'success': True, 'closed_count': 0, 'total_profit': 0}
            
            closed_count = 0
            total_profit = 0
            errors = []
            
            # بستن هر پوزیشن
            for position in positions:
                result = self.close_position(position.ticket)
                
                if result['success']:
                    closed_count += 1
                    total_profit += position.profit
                else:
                    errors.append(f"Position {position.ticket}: {result.get('error', 'Unknown error')}")
            
            logger.info(f"Closed {closed_count} positions. Total profit: ${total_profit:.2f}")
            
            return {
                'success': closed_count == len(positions),
                'closed_count': closed_count,
                'total_positions': len(positions),
                'total_profit': total_profit,
                'errors': errors if errors else None
            }
            
        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_daily_stats(self, date: datetime = None) -> Dict:
        """دریافت آمار روزانه"""
        try:
            if not self.connected:
                if not self.connect():
                    return {}
            
            if date is None:
                date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # دریافت معاملات روز
            deals = mt5.history_deals_get(date, date + timedelta(days=1))
            
            total_profit = 0
            total_volume = 0
            win_count = 0
            loss_count = 0
            trades = []
            
            if deals:
                for deal in deals:
                    total_profit += deal.profit
                    total_volume += deal.volume
                    
                    if deal.profit > 0:
                        win_count += 1
                    elif deal.profit < 0:
                        loss_count += 1
                    
                    trades.append({
                        'ticket': deal.ticket,
                        'order': deal.order,
                        'symbol': deal.symbol,
                        'type': 'BUY' if deal.type == mt5.DEAL_TYPE_BUY else 'SELL',
                        'volume': deal.volume,
                        'price': deal.price,
                        'profit': deal.profit,
                        'commission': deal.commission,
                        'swap': deal.swap,
                        'time': datetime.fromtimestamp(deal.time),
                        'magic': deal.magic,
                        'comment': deal.comment
                    })
            
            # محاسبه نسبت برد
            total_trades = win_count + loss_count
            win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'date': date.strftime('%Y-%m-%d'),
                'total_profit': total_profit,
                'total_volume': total_volume,
                'win_count': win_count,
                'loss_count': loss_count,
                'total_trades': total_trades,
                'win_rate': round(win_rate, 2),
                'trades': trades
            }
            
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return {}
    
    def calculate_lot_size(self, symbol: str, risk_percent: float, 
                          entry_price: float, stop_loss: float, 
                          account_balance: float = None) -> float:
        """محاسبه حجم بر اساس ریسک"""
        try:
            if not self.connected:
                if not self.connect():
                    return 0.01
            
            # اطلاعات حساب
            if account_balance is None:
                account_info = mt5.account_info()
                if account_info:
                    account_balance = account_info.balance
                else:
                    account_balance = 1000  # مقدار پیش‌فرض
            
            # اطلاعات نماد
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return 0.01
            
            # محاسبه مقدار ریسک
            risk_amount = account_balance * (risk_percent / 100)
            
            # محاسبه فاصله استاپ در پیپ
            point = symbol_info.point
            stop_distance = abs(entry_price - stop_loss)
            stop_distance_points = stop_distance / point
            
            # ارزش هر پیپ
            pip_value = self._calculate_pip_value(symbol, symbol_info)
            
            if pip_value <= 0 or stop_distance_points <= 0:
                return 0.01
            
            # محاسبه حجم
            lot_size = risk_amount / (stop_distance_points * pip_value)
            
            # اعمال محدودیت‌ها
            lot_size = max(lot_size, symbol_info.volume_min)
            lot_size = min(lot_size, symbol_info.volume_max)
            
            # گرد کردن به step
            if symbol_info.volume_step > 0:
                lot_size = round(lot_size / symbol_info.volume_step) * symbol_info.volume_step
            
            lot_size = round(lot_size, 2)
            
            logger.debug(f"Calculated lot size for {symbol}: {lot_size}L "
                        f"(Risk: {risk_percent}%, Distance: {stop_distance_points:.1f} points)")
            
            return lot_size
            
        except Exception as e:
            logger.error(f"Error calculating lot size: {e}")
            return 0.01
    
    def _calculate_pip_value(self, symbol: str, symbol_info) -> float:
        """محاسبه ارزش هر پیپ"""
        try:
            # برای جفت‌های فارکس
            if symbol_info.currency_profit == "USD":
                return 10  # $10 per lot for USD-based pairs
            elif symbol_info.currency_profit == "JPY":
                return 9.5  # ¥9.5 per lot, approximately $0.085
            else:
                # محاسبه تقریبی
                return 10  # مقدار پیش‌فرض
                
        except:
            return 10  # مقدار پیش‌فرض
    
    def _get_error_description(self, retcode: int) -> str:
        """دریافت توضیح خطا"""
        error_descriptions = {
            10004: "Requote",
            10006: "Request rejected",
            10007: "Request canceled by trader",
            10008: "Order placed",
            10009: "Request completed",
            10010: "Only part of the request was completed",
            10011: "Request processing error",
            10012: "Request canceled by timeout",
            10013: "Invalid request",
            10014: "Invalid volume in the request",
            10015: "Invalid price in the request",
            10016: "Invalid stops in the request",
            10017: "Trade is disabled",
            10018: "Market is closed",
            10019: "There is not enough money to complete the request",
            10020: "Prices changed",
            10021: "There are no quotes to process the request",
            10022: "Invalid order expiration date in the request",
            10023: "Order state changed",
            10024: "Too frequent requests",
            10025: "No changes in request",
            10026: "Autotrading disabled by server",
            10027: "Autotrading disabled by client terminal",
            10028: "Request locked for processing",
            10029: "Order or position frozen"
        }
        
        return error_descriptions.get(retcode, f"Unknown error code: {retcode}")
    
    def _command_get_data(self, data: Dict) -> Dict:
        """دستور دریافت داده"""
        symbol = data.get('symbol')
        timeframe = data.get('timeframe', 'H1')
        bars = data.get('bars', 100)
        
        df = self.get_market_data(symbol, timeframe, bars)
        
        if df is not None:
            return {
                'success': True,
                'data': df.to_dict('records'),
                'columns': list(df.columns),
                'index': df.index.tolist()
            }
        else:
            return {'success': False, 'error': f'Failed to get data for {symbol}'}
    
    def _command_place_order(self, data: Dict) -> Dict:
        """دستور ثبت معامله"""
        return self.place_order(data)
    
    def _command_modify_order(self, data: Dict) -> Dict:
        """دستور ویرایش معامله"""
        ticket = data.get('ticket')
        sl = data.get('sl', 0)
        tp = data.get('tp', 0)
        price = data.get('price', 0)
        
        return self.modify_order(ticket, sl, tp, price)
    
    def _command_close_order(self, data: Dict) -> Dict:
        """دستور بستن معامله"""
        ticket = data.get('ticket')
        volume = data.get('volume', 0)
        
        return self.close_position(ticket, volume)
    
    def _command_get_account_info(self) -> Dict:
        """دستور دریافت اطلاعات حساب"""
        info = self.get_account_info()
        return {'success': True, 'data': info}
    
    def _command_get_positions(self) -> Dict:
        """دستور دریافت پوزیشن‌ها"""
        positions = self.get_open_positions()
        return {'success': True, 'data': positions}
    
    def _command_get_orders(self) -> Dict:
        """دستور دریافت دستورات معلق"""
        orders = self.get_pending_orders()
        return {'success': True, 'data': orders}
    
    def send_command(self, command_type: str, data: Dict = None, 
                    timeout: float = 10.0) -> Dict:
        """ارسال دستور ناهمزمان"""
        try:
            command = {
                'type': command_type,
                'data': data or {},
                'timestamp': datetime.now().isoformat(),
                'id': hash(f"{command_type}{datetime.now()}{data}")
            }
            
            self.command_queue.put(command)
            
            # انتظار برای پاسخ
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not self.response_queue.empty():
                    response = self.response_queue.get_nowait()
                    if response.get('id') == command['id']:
                        return response
                time.sleep(0.1)
            
            return {'success': False, 'error': 'Timeout waiting for response'}
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return {'success': False, 'error': str(e)}
    
    def emergency_close_all(self) -> Dict:
        """بستن اضطراری تمام معاملات"""
        try:
            logger.warning("⚠️ Emergency close all positions initiated!")
            
            result = self.close_all_positions()
            
            if result['success']:
                logger.info(f"✅ Emergency close completed: {result['closed_count']} positions closed")
            else:
                logger.error(f"❌ Emergency close failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in emergency close: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_symbols_info(self) -> Dict:
        """دریافت اطلاعات تمام نمادها"""
        if not self.symbols_info or (datetime.now() - self.last_symbols_update).seconds > 300:
            self._load_symbols_info()
        
        return self.symbols_info
    
    def check_connection(self) -> bool:
        """بررسی وضعیت اتصال"""
        try:
            if not self.connected:
                return False
            
            # تست ساده اتصال
            account_info = mt5.account_info()
            return account_info is not None
            
        except:
            return False
    
    def reconnect(self) -> bool:
        """اتصال مجدد"""
        logger.info("Attempting to reconnect to MT5...")
        self.disconnect()
        time.sleep(2)
        return self.connect()