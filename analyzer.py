#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحلیل‌گر بازار - نسخه کامل
"""

import pandas as pd
import numpy as np
from ta import trend, momentum, volatility, volume
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import talib
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """تحلیل‌گر کامل بازار"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.analysis_config = config.get('analysis', {})
        
        # Indicators to use
        self.trend_indicators = ['EMA', 'MACD', 'ADX', 'Ichimoku']
        self.momentum_indicators = ['RSI', 'Stochastic', 'WilliamsR', 'CCI']
        self.volatility_indicators = ['BollingerBands', 'ATR', 'KeltnerChannel']
        self.volume_indicators = ['OBV', 'VolumeSMA', 'MFI']
        
        logger.info("MarketAnalyzer initialized")
    
    def analyze_symbol(self, df: pd.DataFrame, symbol: str, timeframe: str = 'H1') -> Dict:
        """
        تحلیل جامع نماد
        
        Args:
            df: DataFrame قیمتی
            symbol: نام نماد
            timeframe: تایم‌فریم
        
        Returns:
            Dict: نتایج تحلیل
        """
        try:
            if df.empty or len(df) < 100:
                logger.warning(f"داده ناکافی برای {symbol} ({timeframe}): {len(df)} کندل")
                return self._get_empty_analysis(symbol, timeframe)
            
            logger.info(f"تحلیل {symbol} در تایم‌فریم {timeframe} ({len(df)} کندل)")
            
            # 1. محاسبه اندیکاتورها
            df_with_indicators = self._calculate_all_indicators(df.copy())
            
            # 2. تحلیل تکنیکال
            technical_analysis = self._technical_analysis(df_with_indicators)
            
            # 3. تحلیل قیمت
            price_analysis = self._price_analysis(df_with_indicators)
            
            # 4. تحلیل الگوها
            pattern_analysis = self._pattern_analysis(df_with_indicators)
            
            # 5. تحلیل زمانی
            time_analysis = self._time_analysis(df_with_indicators)
            
            # 6. شناسایی سطوح کلیدی
            key_levels = self._identify_key_levels(df_with_indicators)
            
            # 7. تولید سیگنال
            signals = self._generate_signals(
                technical_analysis, 
                price_analysis, 
                pattern_analysis, 
                key_levels
            )
            
            # 8. محاسبه امتیاز و اطمینان
            score, confidence = self._calculate_score_and_confidence(
                technical_analysis, 
                pattern_analysis, 
                signals
            )
            
            # 9. محاسبه نقاط ورود و خروج
            entry_exit_points = self._calculate_entry_exit_points(
                df_with_indicators, 
                signals, 
                key_levels
            )
            
            # 10. تحلیل ریسک
            risk_analysis = self._risk_analysis(df_with_indicators, signals)
            
            # نتایج نهایی
            result = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                'current_price': float(df_with_indicators['close'].iloc[-1]),
                'technical': technical_analysis,
                'price': price_analysis,
                'patterns': pattern_analysis,
                'time': time_analysis,
                'key_levels': key_levels,
                'signals': signals,
                'score': score,
                'confidence': confidence,
                'entry_exit': entry_exit_points,
                'risk': risk_analysis,
                'summary': self._generate_summary(signals, score, confidence),
                'recommendation': self._get_recommendation(signals, score, confidence)
            }
            
            logger.debug(f"تحلیل کامل برای {symbol}: {result['summary']}")
            
            return result
            
        except Exception as e:
            logger.error(f"خطا در تحلیل {symbol}: {e}", exc_info=True)
            return self._get_empty_analysis(symbol, timeframe)
    
    def _calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """محاسبه تمام اندیکاتورها"""
        try:
            # روند
            df['ema_9'] = trend.EMAIndicator(close=df['close'], window=9).ema_indicator()
            df['ema_20'] = trend.EMAIndicator(close=df['close'], window=20).ema_indicator()
            df['ema_50'] = trend.EMAIndicator(close=df['close'], window=50).ema_indicator()
            df['ema_100'] = trend.EMAIndicator(close=df['close'], window=100).ema_indicator()
            df['ema_200'] = trend.EMAIndicator(close=df['close'], window=200).ema_indicator()
            
            macd = trend.MACD(close=df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
            
            adx = trend.ADXIndicator(
                high=df['high'], 
                low=df['low'], 
                close=df['close'], 
                window=14
            )
            df['adx'] = adx.adx()
            df['adx_pos'] = adx.adx_pos()
            df['adx_neg'] = adx.adx_neg()
            
            # مومنتوم
            df['rsi'] = momentum.RSIIndicator(close=df['close'], window=14).rsi()
            
            stoch = momentum.StochasticOscillator(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                window=14,
                smooth_window=3
            )
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            df['williams_r'] = momentum.WilliamsRIndicator(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                lbp=14
            ).williams_r()
            
            df['cci'] = momentum.CCIIndicator(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                window=20
            ).cci()
            
            # نوسان
            bb = volatility.BollingerBands(
                close=df['close'],
                window=20,
                window_dev=2
            )
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_middle'] = bb.bollinger_mavg()
            df['bb_lower'] = bb.bollinger_lband()
            df['bb_width'] = bb.bollinger_wband()
            df['bb_pct'] = bb.bollinger_pband()
            
            df['atr'] = volatility.AverageTrueRange(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                window=14
            ).average_true_range()
            
            kc = volatility.KeltnerChannel(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                window=20
            )
            df['kc_upper'] = kc.keltner_channel_hband()
            df['kc_middle'] = kc.keltner_channel_mband()
            df['kc_lower'] = kc.keltner_channel_lband()
            
            # حجم
            if 'tick_volume' in df.columns:
                df['volume_sma'] = df['tick_volume'].rolling(window=20).mean()
                df['volume_ratio'] = df['tick_volume'] / df['volume_sma'].replace(0, 1)
                
                df['obv'] = volume.OnBalanceVolumeIndicator(
                    close=df['close'],
                    volume=df['tick_volume']
                ).on_balance_volume()
                
                df['mfi'] = volume.MFIIndicator(
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    volume=df['tick_volume'],
                    window=14
                ).money_flow_index()
            
            # ایچیموکو
            if len(df) > 52:
                ichimoku = trend.IchimokuIndicator(
                    high=df['high'],
                    low=df['low'],
                    window1=9,
                    window2=26,
                    window3=52
                )
                df['ichi_conversion'] = ichimoku.ichimoku_conversion_line()
                df['ichi_base'] = ichimoku.ichimoku_base_line()
                df['ichi_leading_a'] = ichimoku.ichimoku_a()
                df['ichi_leading_b'] = ichimoku.ichimoku_b()
                df['ichi_lagging'] = ichimoku.ichimoku_chikou_span()
            
            # پارابولیک SAR
            try:
                df['sar'] = talib.SAR(df['high'], df['low'], acceleration=0.02, maximum=0.2)
            except:
                pass
            
            # کندل‌شناسی
            df['body'] = abs(df['close'] - df['open'])
            df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
            df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
            df['body_ratio'] = df['body'] / (df['high'] - df['low']).replace(0, 0.0001)
            
            return df
            
        except Exception as e:
            logger.error(f"خطا در محاسبه اندیکاتورها: {e}")
            return df
    
    def _technical_analysis(self, df: pd.DataFrame) -> Dict:
        """تحلیل تکنیکال"""
        try:
            current_price = df['close'].iloc[-1]
            
            # تحلیل روند
            trend_analysis = self._analyze_trend(df)
            
            # تحلیل مومنتوم
            momentum_analysis = self._analyze_momentum(df)
            
            # تحلیل نوسان
            volatility_analysis = self._analyze_volatility(df)
            
            # تحلیل حجم
            volume_analysis = self._analyze_volume(df)
            
            # تحلیل ایچیموکو
            ichimoku_analysis = self._analyze_ichimoku(df) if 'ichi_conversion' in df.columns else {}
            
            return {
                'trend': trend_analysis,
                'momentum': momentum_analysis,
                'volatility': volatility_analysis,
                'volume': volume_analysis,
                'ichimoku': ichimoku_analysis,
                'overall_trend': self._determine_overall_trend(
                    trend_analysis, 
                    momentum_analysis, 
                    volatility_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل تکنیکال: {e}")
            return {}
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict:
        """تحلیل روند"""
        try:
            current_price = df['close'].iloc[-1]
            
            # EMA Alignment
            ema_values = {}
            for period in [9, 20, 50, 100, 200]:
                col = f'ema_{period}'
                if col in df.columns:
                    ema_values[period] = float(df[col].iloc[-1])
            
            # تعیین روند بر اساس EMA
            trend_direction = "NEUTRAL"
            trend_strength = 0
            
            if len(ema_values) >= 3:
                # بررسی ترتیب EMAها
                ema_list = sorted([(k, v) for k, v in ema_values.items()], key=lambda x: x[0])
                ema_prices = [v for _, v in ema_list]
                
                # صعودی قوی: قیمت > EMA9 > EMA20 > EMA50 > EMA100 > EMA200
                if all(current_price > ema_prices[i] > ema_prices[i+1] for i in range(len(ema_prices)-1)):
                    trend_direction = "STRONG_BULLISH"
                    trend_strength = 95
                # نزولی قوی: قیمت < EMA9 < EMA20 < EMA50 < EMA100 < EMA200
                elif all(current_price < ema_prices[i] < ema_prices[i+1] for i in range(len(ema_prices)-1)):
                    trend_direction = "STRONG_BEARISH"
                    trend_strength = 95
                # صعودی
                elif current_price > ema_values.get(20, 0) > ema_values.get(50, 0):
                    trend_direction = "BULLISH"
                    trend_strength = 70
                # نزولی
                elif current_price < ema_values.get(20, 0) < ema_values.get(50, 0):
                    trend_direction = "BEARISH"
                    trend_strength = 70
            
            # تحلیل MACD
            macd_signal = "NEUTRAL"
            if 'macd' in df.columns and 'macd_signal' in df.columns:
                macd_current = df['macd'].iloc[-1]
                macd_signal_current = df['macd_signal'].iloc[-1]
                macd_prev = df['macd'].iloc[-2] if len(df) > 1 else macd_current
                macd_signal_prev = df['macd_signal'].iloc[-2] if len(df) > 1 else macd_signal_current
                
                if macd_current > macd_signal_current and macd_prev <= macd_signal_prev:
                    macd_signal = "BULLISH_CROSS"
                elif macd_current < macd_signal_current and macd_prev >= macd_signal_prev:
                    macd_signal = "BEARISH_CROSS"
                elif macd_current > macd_signal_current:
                    macd_signal = "BULLISH"
                elif macd_current < macd_signal_current:
                    macd_signal = "BEARISH"
            
            # تحلیل ADX
            adx_strength = 0
            if 'adx' in df.columns:
                adx_value = df['adx'].iloc[-1]
                if adx_value > 25:
                    adx_strength = min(100, (adx_value - 25) * 2)
            
            return {
                'direction': trend_direction,
                'strength': int(trend_strength),
                'ema_alignment': ema_values,
                'macd': {
                    'value': float(df['macd'].iloc[-1]) if 'macd' in df.columns else 0,
                    'signal': float(df['macd_signal'].iloc[-1]) if 'macd_signal' in df.columns else 0,
                    'cross_signal': macd_signal
                },
                'adx': {
                    'value': float(df['adx'].iloc[-1]) if 'adx' in df.columns else 0,
                    'strength': int(adx_strength)
                }
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل روند: {e}")
            return {'direction': 'UNKNOWN', 'strength': 0}
    
    def _analyze_momentum(self, df: pd.DataFrame) -> Dict:
        """تحلیل مومنتوم"""
        try:
            momentum_indicators = {}
            
            # RSI
            if 'rsi' in df.columns:
                rsi_value = df['rsi'].iloc[-1]
                rsi_signal = "NEUTRAL"
                if rsi_value > 70:
                    rsi_signal = "OVERBOUGHT"
                elif rsi_value < 30:
                    rsi_signal = "OVERSOLD"
                elif rsi_value > 50:
                    rsi_signal = "BULLISH"
                elif rsi_value < 50:
                    rsi_signal = "BEARISH"
                
                momentum_indicators['rsi'] = {
                    'value': float(rsi_value),
                    'signal': rsi_signal,
                    'divergence': self._check_rsi_divergence(df)
                }
            
            # Stochastic
            if 'stoch_k' in df.columns and 'stoch_d' in df.columns:
                stoch_k = df['stoch_k'].iloc[-1]
                stoch_d = df['stoch_d'].iloc[-1]
                stoch_signal = "NEUTRAL"
                
                if stoch_k > 80 and stoch_d > 80:
                    stoch_signal = "OVERBOUGHT"
                elif stoch_k < 20 and stoch_d < 20:
                    stoch_signal = "OVERSOLD"
                elif stoch_k > stoch_d and df['stoch_k'].iloc[-2] <= df['stoch_d'].iloc[-2]:
                    stoch_signal = "BULLISH_CROSS"
                elif stoch_k < stoch_d and df['stoch_k'].iloc[-2] >= df['stoch_d'].iloc[-2]:
                    stoch_signal = "BEARISH_CROSS"
                
                momentum_indicators['stochastic'] = {
                    'k': float(stoch_k),
                    'd': float(stoch_d),
                    'signal': stoch_signal
                }
            
            # Williams %R
            if 'williams_r' in df.columns:
                will_r = df['williams_r'].iloc[-1]
                will_signal = "NEUTRAL"
                if will_r > -20:
                    will_signal = "OVERBOUGHT"
                elif will_r < -80:
                    will_signal = "OVERSOLD"
                
                momentum_indicators['williams_r'] = {
                    'value': float(will_r),
                    'signal': will_signal
                }
            
            # CCI
            if 'cci' in df.columns:
                cci_value = df['cci'].iloc[-1]
                cci_signal = "NEUTRAL"
                if cci_value > 100:
                    cci_signal = "OVERBOUGHT"
                elif cci_value < -100:
                    cci_signal = "OVERSOLD"
                
                momentum_indicators['cci'] = {
                    'value': float(cci_value),
                    'signal': cci_signal
                }
            
            # قدرت کلی مومنتوم
            overall_momentum = "NEUTRAL"
            momentum_score = 50
            
            if momentum_indicators:
                bull_count = 0
                total_count = 0
                
                for ind, values in momentum_indicators.items():
                    if 'signal' in values:
                        signal = values['signal']
                        if 'BULL' in signal:
                            bull_count += 1
                        elif 'BEAR' in signal:
                            bull_count -= 1
                        total_count += 1
                
                if total_count > 0:
                    momentum_score = 50 + (bull_count / total_count * 50)
                    momentum_score = max(0, min(100, momentum_score))
                    
                    if momentum_score > 60:
                        overall_momentum = "BULLISH"
                    elif momentum_score < 40:
                        overall_momentum = "BEARISH"
            
            return {
                'indicators': momentum_indicators,
                'overall': overall_momentum,
                'score': int(momentum_score)
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل مومنتوم: {e}")
            return {'overall': 'NEUTRAL', 'score': 50}
    
    def _check_rsi_divergence(self, df: pd.DataFrame, period: int = 14) -> str:
        """بررسی واگرایی RSI"""
        try:
            if len(df) < period * 2:
                return "NO_DATA"
            
            # قیمت‌ها
            prices = df['close'].values[-period*2:]
            rsi_values = df['rsi'].values[-period*2:] if 'rsi' in df.columns else None
            
            if rsi_values is None:
                return "NO_RSI_DATA"
            
            # یافتن سقف و کف
            price_peaks = self._find_peaks(prices)
            rsi_peaks = self._find_peaks(rsi_values)
            
            # بررسی واگرایی نزولی
            if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
                if (prices[price_peaks[-1]] > prices[price_peaks[-2]] and 
                    rsi_values[rsi_peaks[-1]] < rsi_values[rsi_peaks[-2]]):
                    return "BEARISH_DIVERGENCE"
            
            # بررسی واگرایی صعودی
            price_valleys = self._find_valleys(prices)
            rsi_valleys = self._find_valleys(rsi_values)
            
            if len(price_valleys) >= 2 and len(rsi_valleys) >= 2:
                if (prices[price_valleys[-1]] < prices[price_valleys[-2]] and 
                    rsi_values[rsi_valleys[-1]] > rsi_values[rsi_valleys[-2]]):
                    return "BULLISH_DIVERGENCE"
            
            return "NO_DIVERGENCE"
            
        except Exception as e:
            logger.error(f"خطا در بررسی واگرایی: {e}")
            return "ERROR"
    
    def _find_peaks(self, data: np.ndarray, lookaround: int = 3) -> List[int]:
        """یافتن سقف‌ها"""
        peaks = []
        for i in range(lookaround, len(data) - lookaround):
            if data[i] == max(data[i-lookaround:i+lookaround+1]):
                peaks.append(i)
        return peaks
    
    def _find_valleys(self, data: np.ndarray, lookaround: int = 3) -> List[int]:
        """یافتن کف‌ها"""
        valleys = []
        for i in range(lookaround, len(data) - lookaround):
            if data[i] == min(data[i-lookaround:i+lookaround+1]):
                valleys.append(i)
        return valleys
    
    def _analyze_volatility(self, df: pd.DataFrame) -> Dict:
        """تحلیل نوسان"""
        try:
            volatility_indicators = {}
            
            # باندهای بولینگر
            if 'bb_width' in df.columns:
                bb_width = df['bb_width'].iloc[-1]
                bb_position = "MIDDLE"
                current_price = df['close'].iloc[-1]
                
                if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
                    if current_price > df['bb_upper'].iloc[-1]:
                        bb_position = "ABOVE_UPPER"
                    elif current_price < df['bb_lower'].iloc[-1]:
                        bb_position = "BELOW_LOWER"
                    elif current_price > df['bb_middle'].iloc[-1]:
                        bb_position = "UPPER_HALF"
                    else:
                        bb_position = "LOWER_HALF"
                
                # Squeeze تشخیص
                squeeze = False
                if len(df) > 20:
                    bb_width_ma = df['bb_width'].rolling(20).mean().iloc[-1]
                    squeeze = bb_width < bb_width_ma * 0.7
                
                volatility_indicators['bollinger_bands'] = {
                    'width': float(bb_width),
                    'position': bb_position,
                    'squeeze': squeeze,
                    'percent': float(df['bb_pct'].iloc[-1]) if 'bb_pct' in df.columns else 0
                }
            
            # ATR
            if 'atr' in df.columns:
                atr_value = df['atr'].iloc[-1]
                atr_percent = (atr_value / df['close'].iloc[-1] * 100) if df['close'].iloc[-1] > 0 else 0
                
                volatility_level = "NORMAL"
                if atr_percent > 1.5:
                    volatility_level = "HIGH"
                elif atr_percent < 0.3:
                    volatility_level = "LOW"
                
                volatility_indicators['atr'] = {
                    'value': float(atr_value),
                    'percent': float(atr_percent),
                    'level': volatility_level
                }
            
            # کانال کلتنر
            if 'kc_upper' in df.columns and 'kc_lower' in df.columns:
                kc_width = df['kc_upper'].iloc[-1] - df['kc_lower'].iloc[-1]
                kc_width_percent = (kc_width / df['close'].iloc[-1] * 100) if df['close'].iloc[-1] > 0 else 0
                
                volatility_indicators['keltner_channel'] = {
                    'width': float(kc_width),
                    'width_percent': float(kc_width_percent)
                }
            
            # سطح کلی نوسان
            overall_volatility = "MEDIUM"
            volatility_score = 5.0
            
            if volatility_indicators:
                scores = []
                
                if 'atr' in volatility_indicators:
                    atr_percent = volatility_indicators['atr']['percent']
                    if atr_percent > 1.5:
                        scores.append(8)
                    elif atr_percent > 1.0:
                        scores.append(6)
                    elif atr_percent > 0.5:
                        scores.append(4)
                    else:
                        scores.append(2)
                
                if 'bollinger_bands' in volatility_indicators:
                    bb_width = volatility_indicators['bollinger_bands']['width']
                    if bb_width > 0.02:  # 2%
                        scores.append(8)
                    elif bb_width > 0.01:  # 1%
                        scores.append(6)
                    elif bb_width > 0.005:  # 0.5%
                        scores.append(4)
                    else:
                        scores.append(2)
                
                if scores:
                    volatility_score = sum(scores) / len(scores)
                    
                    if volatility_score >= 7:
                        overall_volatility = "HIGH"
                    elif volatility_score >= 4:
                        overall_volatility = "MEDIUM"
                    else:
                        overall_volatility = "LOW"
            
            return {
                'indicators': volatility_indicators,
                'overall': overall_volatility,
                'score': float(volatility_score)
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل نوسان: {e}")
            return {'overall': 'MEDIUM', 'score': 5.0}
    
    def _analyze_volume(self, df: pd.DataFrame) -> Dict:
        """تحلیل حجم"""
        try:
            volume_indicators = {}
            
            if 'tick_volume' in df.columns:
                current_volume = df['tick_volume'].iloc[-1]
                
                # حجم نسبی
                volume_sma = df['volume_sma'].iloc[-1] if 'volume_sma' in df.columns else current_volume
                volume_ratio = current_volume / volume_sma if volume_sma > 0 else 1
                
                volume_signal = "NORMAL"
                if volume_ratio > 3:
                    volume_signal = "EXTREME_HIGH"
                elif volume_ratio > 2:
                    volume_signal = "VERY_HIGH"
                elif volume_ratio > 1.5:
                    volume_signal = "HIGH"
                elif volume_ratio < 0.3:
                    volume_signal = "EXTREME_LOW"
                elif volume_ratio < 0.5:
                    volume_signal = "VERY_LOW"
                elif volume_ratio < 0.8:
                    volume_signal = "LOW"
                
                volume_indicators['volume'] = {
                    'current': float(current_volume),
                    'sma': float(volume_sma),
                    'ratio': float(volume_ratio),
                    'signal': volume_signal
                }
            
            # OBV
            if 'obv' in df.columns:
                obv_current = df['obv'].iloc[-1]
                obv_prev = df['obv'].iloc[-20] if len(df) > 20 else obv_current
                obv_change = ((obv_current - obv_prev) / abs(obv_prev) * 100) if obv_prev != 0 else 0
                
                obv_trend = "NEUTRAL"
                if obv_change > 20:
                    obv_trend = "STRONG_BULLISH"
                elif obv_change > 10:
                    obv_trend = "BULLISH"
                elif obv_change < -20:
                    obv_trend = "STRONG_BEARISH"
                elif obv_change < -10:
                    obv_trend = "BEARISH"
                
                volume_indicators['obv'] = {
                    'value': float(obv_current),
                    'change_percent': float(obv_change),
                    'trend': obv_trend
                }
            
            # MFI
            if 'mfi' in df.columns:
                mfi_value = df['mfi'].iloc[-1]
                mfi_signal = "NEUTRAL"
                if mfi_value > 80:
                    mfi_signal = "OVERBOUGHT"
                elif mfi_value < 20:
                    mfi_signal = "OVERSOLD"
                elif mfi_value > 50:
                    mfi_signal = "BULLISH"
                elif mfi_value < 50:
                    mfi_signal = "BEARISH"
                
                volume_indicators['mfi'] = {
                    'value': float(mfi_value),
                    'signal': mfi_signal
                }
            
            # تأیید کلی حجم
            volume_confirmation = "NEUTRAL"
            
            if volume_indicators:
                confirmations = []
                
                if 'volume' in volume_indicators:
                    vol_signal = volume_indicators['volume']['signal']
                    if vol_signal in ["HIGH", "VERY_HIGH", "EXTREME_HIGH"]:
                        confirmations.append(1)
                    elif vol_signal in ["LOW", "VERY_LOW", "EXTREME_LOW"]:
                        confirmations.append(-1)
                    else:
                        confirmations.append(0)
                
                if 'obv' in volume_indicators:
                    obv_trend = volume_indicators['obv']['trend']
                    if "BULLISH" in obv_trend:
                        confirmations.append(1)
                    elif "BEARISH" in obv_trend:
                        confirmations.append(-1)
                    else:
                        confirmations.append(0)
                
                if confirmations:
                    avg_confirmation = sum(confirmations) / len(confirmations)
                    if avg_confirmation > 0.3:
                        volume_confirmation = "BULLISH_CONFIRMATION"
                    elif avg_confirmation < -0.3:
                        volume_confirmation = "BEARISH_CONFIRMATION"
            
            return {
                'indicators': volume_indicators,
                'confirmation': volume_confirmation
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل حجم: {e}")
            return {'confirmation': 'NEUTRAL'}
    
    def _analyze_ichimoku(self, df: pd.DataFrame) -> Dict:
        """تحلیل ایچیموکو"""
        try:
            if 'ichi_conversion' not in df.columns:
                return {}
            
            current_price = df['close'].iloc[-1]
            conversion = df['ichi_conversion'].iloc[-1]
            base = df['ichi_base'].iloc[-1]
            leading_a = df['ichi_leading_a'].iloc[-26] if len(df) > 26 else 0
            leading_b = df['ichi_leading_b'].iloc[-26] if len(df) > 26 else 0
            lagging = df['ichi_lagging'].iloc[26] if len(df) > 26 else 0
            
            # سیگنال‌های ایچیموکو
            signals = []
            
            # تنکان سن × کیجون سن
            if conversion > base:
                signals.append("BULLISH_TK_CROSS")
            elif conversion < base:
                signals.append("BEARISH_TK_CROSS")
            
            # قیمت نسبت به ابر
            if leading_a > 0 and leading_b > 0:
                if current_price > max(leading_a, leading_b):
                    signals.append("ABOVE_CLOUD")
                elif current_price < min(leading_a, leading_b):
                    signals.append("BELOW_CLOUD")
                else:
                    signals.append("INSIDE_CLOUD")
            
            # رنگ ابر
            cloud_color = "NEUTRAL"
            if leading_a > leading_b:
                cloud_color = "GREEN"  # صعودی
            elif leading_a < leading_b:
                cloud_color = "RED"  # نزولی
            
            # چیکو اسپن
            chikou_signal = "NEUTRAL"
            if lagging > 0:
                if lagging > df['close'].iloc[26]:
                    chikou_signal = "BULLISH"
                elif lagging < df['close'].iloc[26]:
                    chikou_signal = "BEARISH"
            
            return {
                'tenkan_sen': float(conversion),
                'kijun_sen': float(base),
                'senkou_span_a': float(leading_a),
                'senkou_span_b': float(leading_b),
                'chikou_span': float(lagging),
                'cloud_color': cloud_color,
                'signals': signals,
                'chikou_signal': chikou_signal
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل ایچیموکو: {e}")
            return {}
    
    def _determine_overall_trend(self, trend_analysis: Dict, 
                                momentum_analysis: Dict, 
                                volatility_analysis: Dict) -> str:
        """تعیین روند کلی"""
        try:
            trend_score = 0
            momentum_score = momentum_analysis.get('score', 50)
            volatility_score = volatility_analysis.get('score', 5.0)
            
            # امتیاز روند
            trend_direction = trend_analysis.get('direction', 'NEUTRAL')
            if trend_direction == "STRONG_BULLISH":
                trend_score = 90
            elif trend_direction == "BULLISH":
                trend_score = 70
            elif trend_direction == "STRONG_BEARISH":
                trend_score = 10
            elif trend_direction == "BEARISH":
                trend_score = 30
            else:
                trend_score = 50
            
            # ترکیب امتیازها
            overall_score = (trend_score * 0.5 + momentum_score * 0.3 + 
                           (100 - volatility_score * 10) * 0.2)
            
            if overall_score >= 70:
                return "STRONG_BULLISH"
            elif overall_score >= 60:
                return "BULLISH"
            elif overall_score <= 30:
                return "STRONG_BEARISH"
            elif overall_score <= 40:
                return "BEARISH"
            else:
                return "NEUTRAL"
                
        except Exception as e:
            logger.error(f"خطا در تعیین روند کلی: {e}")
            return "NEUTRAL"
    
    def _price_analysis(self, df: pd.DataFrame) -> Dict:
        """تحلیل قیمت"""
        try:
            current_price = df['close'].iloc[-1]
            open_price = df['open'].iloc[-1]
            high_price = df['high'].iloc[-1]
            low_price = df['low'].iloc[-1]
            
            # حرکت روزانه
            daily_change = current_price - open_price
            daily_change_percent = (daily_change / open_price * 100) if open_price > 0 else 0
            
            # محدوده روز
            daily_range = high_price - low_price
            daily_range_percent = (daily_range / current_price * 100) if current_price > 0 else 0
            
            # موقعیت در محدوده روز
            position_in_range = ((current_price - low_price) / daily_range * 100) if daily_range > 0 else 50
            
            # کندل فعلی
            candle_body = abs(current_price - open_price)
            candle_range = high_price - low_price
            body_ratio = (candle_body / candle_range * 100) if candle_range > 0 else 0
            
            candle_type = "DOJI" if body_ratio < 10 else (
                "MARUBOZU" if body_ratio > 90 else "NORMAL"
            )
            
            # جهت کندل
            candle_direction = "BULLISH" if current_price > open_price else (
                "BEARISH" if current_price < open_price else "NEUTRAL"
            )
            
            return {
                'current': float(current_price),
                'open': float(open_price),
                'high': float(high_price),
                'low': float(low_price),
                'daily_change': float(daily_change),
                'daily_change_percent': float(daily_change_percent),
                'daily_range': float(daily_range),
                'daily_range_percent': float(daily_range_percent),
                'position_in_range': float(position_in_range),
                'candle': {
                    'type': candle_type,
                    'direction': candle_direction,
                    'body_ratio': float(body_ratio)
                }
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل قیمت: {e}")
            return {}
    
    def _pattern_analysis(self, df: pd.DataFrame) -> Dict:
        """تحلیل الگوها"""
        try:
            patterns = []
            
            # الگوهای کندل‌استیک
            candlestick_patterns = self._detect_candlestick_patterns(df)
            patterns.extend(candlestick_patterns)
            
            # الگوهای کلاسیک
            classic_patterns = self._detect_classic_patterns(df)
            patterns.extend(classic_patterns)
            
            # الگوهای هارمونیک (ساده‌شده)
            harmonic_patterns = self._detect_harmonic_patterns(df)
            patterns.extend(harmonic_patterns)
            
            # الگوهای فیبوناچی
            fibonacci_patterns = self._detect_fibonacci_patterns(df)
            patterns.extend(fibonacci_patterns)
            
            # قدرت الگوها
            pattern_strength = 0
            if patterns:
                strength_sum = sum(p.get('strength_score', 0) for p in patterns)
                pattern_strength = strength_sum / len(patterns)
            
            return {
                'patterns': patterns,
                'count': len(patterns),
                'strength': float(pattern_strength),
                'has_reversal': any(p.get('type') == 'REVERSAL' for p in patterns),
                'has_continuation': any(p.get('type') == 'CONTINUATION' for p in patterns)
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل الگوها: {e}")
            return {'patterns': [], 'count': 0, 'strength': 0}
    
    def _detect_candlestick_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """تشخیص الگوهای کندل‌استیک"""
        patterns = []
        
        try:
            if len(df) < 3:
                return patterns
            
            # آخرین 3 کندل
            last_3 = df.iloc[-3:]
            
            # Engulfing Pattern
            if len(last_3) >= 2:
                prev = last_3.iloc[-2]
                curr = last_3.iloc[-1]
                
                # Bullish Engulfing
                if (prev['close'] < prev['open'] and  # کندل قرمز قبلی
                    curr['close'] > curr['open'] and  # کندل سبز فعلی
                    curr['open'] < prev['close'] and  # باز شدن پایین‌تر از بسته شدن قبلی
                    curr['close'] > prev['open']):    # بسته شدن بالاتر از باز شدن قبلی
                    
                    patterns.append({
                        'name': 'BULLISH_ENGULFING',
                        'type': 'REVERSAL',
                        'direction': 'BULLISH',
                        'strength': 'STRONG',
                        'strength_score': 8,
                        'timeframe': 'SHORT',
                        'description': 'الگوی بازگشتی صعودی قوی'
                    })
                
                # Bearish Engulfing
                elif (prev['close'] > prev['open'] and
                      curr['close'] < curr['open'] and
                      curr['open'] > prev['close'] and
                      curr['close'] < prev['open']):
                    
                    patterns.append({
                        'name': 'BEARISH_ENGULFING',
                        'type': 'REVERSAL',
                        'direction': 'BEARISH',
                        'strength': 'STRONG',
                        'strength_score': 8,
                        'timeframe': 'SHORT',
                        'description': 'الگوی بازگشتی نزولی قوی'
                    })
            
            # Hammer / Hanging Man
            if len(df) >= 1:
                candle = df.iloc[-1]
                body_size = abs(candle['close'] - candle['open'])
                lower_shadow = min(candle['open'], candle['close']) - candle['low']
                upper_shadow = candle['high'] - max(candle['open'], candle['close'])
                
                # Hammer
                if (lower_shadow > body_size * 2 and
                    upper_shadow < body_size * 0.3 and
                    candle['close'] > candle['open']):
                    
                    patterns.append({
                        'name': 'HAMMER',
                        'type': 'REVERSAL',
                        'direction': 'BULLISH',
                        'strength': 'MEDIUM',
                        'strength_score': 6,
                        'timeframe': 'SHORT',
                        'description': 'الگوی چکش - بازگشت صعودی'
                    })
                
                # Hanging Man
                elif (lower_shadow > body_size * 2 and
                      upper_shadow < body_size * 0.3 and
                      candle['close'] < candle['open']):
                    
                    patterns.append({
                        'name': 'HANGING_MAN',
                        'type': 'REVERSAL',
                        'direction': 'BEARISH',
                        'strength': 'MEDIUM',
                        'strength_score': 6,
                        'timeframe': 'SHORT',
                        'description': 'الگوی مرد به دار آویخته - بازگشت نزولی'
                    })
            
            # Doji
            if len(df) >= 1:
                candle = df.iloc[-1]
                body_size = abs(candle['close'] - candle['open'])
                candle_range = candle['high'] - candle['low']
                
                if candle_range > 0 and body_size / candle_range < 0.1:
                    patterns.append({
                        'name': 'DOJI',
                        'type': 'INDECISION',
                        'direction': 'NEUTRAL',
                        'strength': 'WEAK',
                        'strength_score': 3,
                        'timeframe': 'SHORT',
                        'description': 'الگوی دوجی - بلاتکلیفی بازار'
                    })
            
            # Morning Star / Evening Star
            if len(df) >= 3:
                first = df.iloc[-3]
                second = df.iloc[-2]
                third = df.iloc[-1]
                
                # Morning Star
                if (first['close'] < first['open'] and  # کندل نزولی
                    abs(second['close'] - second['open']) < (first['high'] - first['low']) * 0.3 and  # کندل کوچک
                    third['close'] > third['open'] and  # کندل صعودی
                    third['close'] > first['close']):   # بسته شدن بالاتر از کندل اول
                    
                    patterns.append({
                        'name': 'MORNING_STAR',
                        'type': 'REVERSAL',
                        'direction': 'BULLISH',
                        'strength': 'STRONG',
                        'strength_score': 9,
                        'timeframe': 'MEDIUM',
                        'description': 'الگوی ستاره صبحگاهی - بازگشت صعودی'
                    })
                
                # Evening Star
                elif (first['close'] > first['open'] and
                      abs(second['close'] - second['open']) < (first['high'] - first['low']) * 0.3 and
                      third['close'] < third['open'] and
                      third['close'] < first['close']):
                    
                    patterns.append({
                        'name': 'EVENING_STAR',
                        'type': 'REVERSAL',
                        'direction': 'BEARISH',
                        'strength': 'STRONG',
                        'strength_score': 9,
                        'timeframe': 'MEDIUM',
                        'description': 'الگوی ستاره عصرگاهی - بازگشت نزولی'
                    })
            
        except Exception as e:
            logger.error(f"خطا در تشخیص الگوهای کندل‌استیک: {e}")
        
        return patterns
    
    def _detect_classic_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """تشخیص الگوهای کلاسیک"""
        patterns = []
        
        try:
            if len(df) < 20:
                return patterns
            
            # Head and Shoulders (ساده‌شده)
            patterns.extend(self._detect_head_shoulders(df))
            
            # Double Top/Bottom
            patterns.extend(self._detect_double_top_bottom(df))
            
            # Triangle Patterns
            patterns.extend(self._detect_triangle_patterns(df))
            
            # Flag and Pennant
            patterns.extend(self._detect_flag_pennant(df))
            
        except Exception as e:
            logger.error(f"خطا در تشخیص الگوهای کلاسیک: {e}")
        
        return patterns
    
    def _detect_head_shoulders(self, df: pd.DataFrame) -> List[Dict]:
        """تشخیص الگوی سر و شانه"""
        patterns = []
        
        try:
            # این یک پیاده‌سازی ساده است
            # در نسخه کامل از الگوریتم‌های پیچیده‌تر استفاده می‌شود
            
            # بررسی برای سر و شانه معکوس (Inverse Head and Shoulders)
            if len(df) >= 30:
                prices = df['close'].values[-30:]
                highs = df['high'].values[-30:]
                lows = df['low'].values[-30:]
                
                # یافتن Extremums
                # پیاده‌سازی کامل نیاز به منطق پیچیده‌تری دارد
            
        except Exception as e:
            logger.error(f"خطا در تشخیص الگوی سر و شانه: {e}")
        
        return patterns
    
    def _detect_double_top_bottom(self, df: pd.DataFrame) -> List[Dict]:
        """تشخیص الگوی دو قله/دو دره"""
        patterns = []
        
        try:
            if len(df) < 20:
                return patterns
            
            prices = df['close'].values[-20:]
            
            # یافتن قله‌ها
            peaks = []
            for i in range(1, len(prices) - 1):
                if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
                    peaks.append((i, prices[i]))
            
            # یافتن دره‌ها
            valleys = []
            for i in range(1, len(prices) - 1):
                if prices[i] < prices[i-1] and prices[i] < prices[i+1]:
                    valleys.append((i, prices[i]))
            
            # Double Top
            if len(peaks) >= 2:
                p1_idx, p1_price = peaks[-2]
                p2_idx, p2_price = peaks[-1]
                
                # فاصله مناسب بین دو قله و قیمت‌های مشابه
                if (5 <= abs(p2_idx - p1_idx) <= 15 and
                    abs(p2_price - p1_price) / p1_price < 0.02):  # حداکثر ۲٪ اختلاف
                    
                    # وجود دره بین دو قله
                    valley_between = False
                    for v_idx, v_price in valleys:
                        if p1_idx < v_idx < p2_idx:
                            valley_between = True
                            break
                    
                    if valley_between:
                        patterns.append({
                            'name': 'DOUBLE_TOP',
                            'type': 'REVERSAL',
                            'direction': 'BEARISH',
                            'strength': 'MEDIUM',
                            'strength_score': 7,
                            'timeframe': 'MEDIUM',
                            'description': 'الگوی دو قله - بازگشت نزولی'
                        })
            
            # Double Bottom
            if len(valleys) >= 2:
                v1_idx, v1_price = valleys[-2]
                v2_idx, v2_price = valleys[-1]
                
                if (5 <= abs(v2_idx - v1_idx) <= 15 and
                    abs(v2_price - v1_price) / v1_price < 0.02):
                    
                    # وجود قله بین دو دره
                    peak_between = False
                    for p_idx, p_price in peaks:
                        if v1_idx < p_idx < v2_idx:
                            peak_between = True
                            break
                    
                    if peak_between:
                        patterns.append({
                            'name': 'DOUBLE_BOTTOM',
                            'type': 'REVERSAL',
                            'direction': 'BULLISH',
                            'strength': 'MEDIUM',
                            'strength_score': 7,
                            'timeframe': 'MEDIUM',
                            'description': 'الگوی دو دره - بازگشت صعودی'
                        })
            
        except Exception as e:
            logger.error(f"خطا در تشخیص الگوی دو قله/دو دره: {e}")
        
        return patterns
    
    def _detect_triangle_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """تشخیص الگوهای مثلث"""
        patterns = []
        
        try:
            if len(df) < 15:
                return patterns
            
            # استفاده از آخرین 15 کندل
            recent_df = df.iloc[-15:]
            highs = recent_df['high'].values
            lows = recent_df['low'].values
            
            # خطوط روند
            from scipy import stats
            
            # خط روند برای سقف‌ها
            x_high = np.arange(len(highs))
            slope_high, _, _, _, _ = stats.linregress(x_high, highs)
            
            # خط روند برای کف‌ها
            x_low = np.arange(len(lows))
            slope_low, _, _, _, _ = stats.linregress(x_low, lows)
            
            # تشخیص نوع مثلث
            triangle_type = None
            
            if slope_high < 0 and slope_low > 0:
                triangle_type = 'SYMMETRICAL_TRIANGLE'
            elif slope_high < 0 and abs(slope_low) < 0.001:
                triangle_type = 'DESCENDING_TRIANGLE'
            elif abs(slope_high) < 0.001 and slope_low > 0:
                triangle_type = 'ASCENDING_TRIANGLE'
            
            if triangle_type:
                # بررسی همگرایی
                high_range = max(highs) - min(highs)
                low_range = max(lows) - min(lows)
                
                if high_range > 0 and low_range > 0:
                    volatility_ratio = min(high_range, low_range) / max(high_range, low_range)
                    
                    if volatility_ratio < 0.7:  # همگرایی قابل توجه
                        direction = 'BULLISH' if triangle_type == 'ASCENDING_TRIANGLE' else 'BEARISH' if triangle_type == 'DESCENDING_TRIANGLE' else 'NEUTRAL'
                        
                        patterns.append({
                            'name': triangle_type,
                            'type': 'CONTINUATION',
                            'direction': direction,
                            'strength': 'MEDIUM',
                            'strength_score': 6,
                            'timeframe': 'MEDIUM',
                            'description': f'الگوی مثلث {triangle_type.replace("_", " ").title()} - ادامه روند'
                        })
            
        except Exception as e:
            logger.error(f"خطا در تشخیص الگوهای مثلث: {e}")
        
        return patterns
    
    def _detect_flag_pennant(self, df: pd.DataFrame) -> List[Dict]:
        """تشخیص الگوی پرچم و پرچم سه‌گوش"""
        patterns = []
        
        try:
            if len(df) < 25:
                return patterns
            
            # این پیاده‌سازی ساده است
            # نسخه کامل نیاز به تحلیل عمیق‌تری دارد
            
        except Exception as e:
            logger.error(f"خطا در تشخیص الگوی پرچم: {e}")
        
        return patterns
    
    def _detect_harmonic_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """تشخیص الگوهای هارمونیک (ساده‌شده)"""
        patterns = []
        
        try:
            # پیاده‌سازی کامل الگوهای هارمونیک بسیار پیچیده است
            # این یک نسخه ساده‌شده است
            
        except Exception as e:
            logger.error(f"خطا در تشخیص الگوهای هارمونیک: {e}")
        
        return patterns
    
    def _detect_fibonacci_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """تشخیص الگوهای فیبوناچی"""
        patterns = []
        
        try:
            if len(df) < 30:
                return patterns
            
            # یافتن سوینگ‌ها
            # پیاده‌سازی کامل نیاز به منطق پیچیده دارد
            
        except Exception as e:
            logger.error(f"خطا در تشخیص الگوهای فیبوناچی: {e}")
        
        return patterns
    
    def _time_analysis(self, df: pd.DataFrame) -> Dict:
        """تحلیل زمانی"""
        try:
            time_data = {}
            
            # روز هفته
            if 'time' in df.index.name:
                last_time = df.index[-1]
                time_data['day_of_week'] = last_time.strftime('%A')
                time_data['hour'] = last_time.hour
                time_data['is_london_session'] = 8 <= last_time.hour <= 16
                time_data['is_newyork_session'] = 13 <= last_time.hour <= 21
                time_data['is_asian_session'] = 0 <= last_time.hour <= 8
            
            # تحلیل زمانی الگوها
            time_data['seasonal_tendency'] = self._check_seasonal_tendency()
            
            return time_data
            
        except Exception as e:
            logger.error(f"خطا در تحلیل زمانی: {e}")
            return {}
    
    def _check_seasonal_tendency(self) -> str:
        """بررسی تمایل فصلی"""
        # این یک نسخه ساده است
        # نسخه کامل از داده‌های تاریخی استفاده می‌کند
        return "NEUTRAL"
    
    def _identify_key_levels(self, df: pd.DataFrame) -> Dict:
        """شناسایی سطوح کلیدی"""
        try:
            key_levels = {}
            
            # حمایت و مقاومت
            support_levels = self._find_support_levels(df)
            resistance_levels = self._find_resistance_levels(df)
            
            key_levels['support'] = support_levels
            key_levels['resistance'] = resistance_levels
            
            # پیوت‌پوینت
            pivot_points = self._calculate_pivot_points(df)
            key_levels['pivot_points'] = pivot_points
            
            # فیبوناچی
            fibonacci_levels = self._calculate_fibonacci_levels(df)
            key_levels['fibonacci'] = fibonacci_levels
            
            # میانگین متحرک به عنوان سطوح داینامیک
            dynamic_levels = self._get_dynamic_levels(df)
            key_levels['dynamic'] = dynamic_levels
            
            # روانی بازار
            market_profile = self._analyze_market_profile(df)
            key_levels['market_profile'] = market_profile
            
            # شناسایی مهم‌ترین سطح
            current_price = df['close'].iloc[-1]
            key_levels['nearest_support'] = self._find_nearest_level(current_price, support_levels, below=True)
            key_levels['nearest_resistance'] = self._find_nearest_level(current_price, resistance_levels, above=True)
            
            # قدرت سطوح
            key_levels['level_strength'] = self._calculate_level_strength(df, support_levels, resistance_levels)
            
            return key_levels
            
        except Exception as e:
            logger.error(f"خطا در شناسایی سطوح کلیدی: {e}")
            return {}
    
    def _find_support_levels(self, df: pd.DataFrame, lookback: int = 100) -> List[float]:
        """یافتن سطوح حمایت"""
        try:
            if len(df) < lookback:
                lookback = len(df)
            
            recent_data = df.iloc[-lookback:]
            lows = recent_data['low'].values
            
            # استفاده از روش ساده: نقاطی که چند بار لمس شده‌اند
            from collections import Counter
            
            # گرد کردن قیمت‌ها
            rounded_lows = np.round(lows, 4)
            low_counts = Counter(rounded_lows)
            
            # سطوح با بیشترین تکرار
            common_lows = [price for price, count in low_counts.most_common(10) if count >= 3]
            
            # حذف سطوح خیلی نزدیک به هم
            filtered_lows = []
            for price in sorted(common_lows):
                if not filtered_lows or price > filtered_lows[-1] * 1.005:  # حداقل 0.5% فاصله
                    filtered_lows.append(float(price))
            
            return filtered_lows[:5]  # حداکثر 5 سطح
            
        except Exception as e:
            logger.error(f"خطا در یافتن سطوح حمایت: {e}")
            return []
    
    def _find_resistance_levels(self, df: pd.DataFrame, lookback: int = 100) -> List[float]:
        """یافتن سطوح مقاومت"""
        try:
            if len(df) < lookback:
                lookback = len(df)
            
            recent_data = df.iloc[-lookback:]
            highs = recent_data['high'].values
            
            from collections import Counter
            
            rounded_highs = np.round(highs, 4)
            high_counts = Counter(rounded_highs)
            
            common_highs = [price for price, count in high_counts.most_common(10) if count >= 3]
            
            filtered_highs = []
            for price in sorted(common_highs):
                if not filtered_highs or price > filtered_highs[-1] * 1.005:
                    filtered_highs.append(float(price))
            
            return filtered_highs[:5]
            
        except Exception as e:
            logger.error(f"خطا در یافتن سطوح مقاومت: {e}")
            return []
    
    def _calculate_pivot_points(self, df: pd.DataFrame) -> Dict:
        """محاسبه پیوت‌پوینت"""
        try:
            if len(df) < 1:
                return {}
            
            last_candle = df.iloc[-1]
            high = last_candle['high']
            low = last_candle['low']
            close = last_candle['close']
            
            # پیوت استاندارد
            pivot = (high + low + close) / 3
            r1 = 2 * pivot - low
            s1 = 2 * pivot - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)
            r3 = high + 2 * (pivot - low)
            s3 = low - 2 * (high - pivot)
            
            return {
                'pivot': float(pivot),
                'r1': float(r1),
                'r2': float(r2),
                'r3': float(r3),
                's1': float(s1),
                's2': float(s2),
                's3': float(s3)
            }
            
        except Exception as e:
            logger.error(f"خطا در محاسبه پیوت‌پوینت: {e}")
            return {}
    
    def _calculate_fibonacci_levels(self, df: pd.DataFrame, lookback: int = 50) -> Dict:
        """محاسبه سطوح فیبوناچی"""
        try:
            if len(df) < lookback:
                lookback = len(df)
            
            recent_data = df.iloc[-lookback:]
            recent_high = recent_data['high'].max()
            recent_low = recent_data['low'].min()
            price_range = recent_high - recent_low
            
            if price_range == 0:
                return {}
            
            fib_levels = {
                '0': float(recent_low),
                '0.236': float(recent_low + price_range * 0.236),
                '0.382': float(recent_low + price_range * 0.382),
                '0.5': float(recent_low + price_range * 0.5),
                '0.618': float(recent_low + price_range * 0.618),
                '0.786': float(recent_low + price_range * 0.786),
                '1': float(recent_high),
                '1.272': float(recent_low + price_range * 1.272),
                '1.618': float(recent_low + price_range * 1.618)
            }
            
            return fib_levels
            
        except Exception as e:
            logger.error(f"خطا در محاسبه سطوح فیبوناچی: {e}")
            return {}
    
    def _get_dynamic_levels(self, df: pd.DataFrame) -> Dict:
        """سطوح داینامیک (میانگین‌های متحرک)"""
        try:
            dynamic_levels = {}
            
            for period in [20, 50, 100, 200]:
                col = f'ema_{period}'
                if col in df.columns:
                    dynamic_levels[f'ema_{period}'] = float(df[col].iloc[-1])
            
            # باندهای بولینگر
            if 'bb_upper' in df.columns:
                dynamic_levels['bb_upper'] = float(df['bb_upper'].iloc[-1])
                dynamic_levels['bb_middle'] = float(df['bb_middle'].iloc[-1])
                dynamic_levels['bb_lower'] = float(df['bb_lower'].iloc[-1])
            
            return dynamic_levels
            
        except Exception as e:
            logger.error(f"خطا در محاسبه سطوح داینامیک: {e}")
            return {}
    
    def _analyze_market_profile(self, df: pd.DataFrame) -> Dict:
        """تحلیل پروفایل بازار (ساده‌شده)"""
        try:
            if len(df) < 20:
                return {}
            
            # توزیع قیمت در طول زمان
            recent_data = df.iloc[-20:]
            
            # ارزش معاملات (Volume Profile ساده)
            price_levels = np.linspace(recent_data['low'].min(), recent_data['high'].max(), 20)
            
            # این یک پیاده‌سازی ساده است
            # نسخه کامل Volume Profile پیچیده‌تر است
            
            return {
                'high_volume_nodes': [],
                'low_volume_nodes': [],
                'point_of_control': float(recent_data['close'].mean())
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل پروفایل بازار: {e}")
            return {}
    
    def _find_nearest_level(self, current_price: float, levels: List[float], 
                           above: bool = False, below: bool = False) -> Dict:
        """یافتن نزدیک‌ترین سطح"""
        try:
            if not levels:
                return {}
            
            if above:
                eligible = [l for l in levels if l > current_price]
                if not eligible:
                    return {}
                nearest = min(eligible, key=lambda x: abs(x - current_price))
            elif below:
                eligible = [l for l in levels if l < current_price]
                if not eligible:
                    return {}
                nearest = max(eligible, key=lambda x: abs(x - current_price))
            else:
                nearest = min(levels, key=lambda x: abs(x - current_price))
            
            distance = abs(nearest - current_price)
            distance_percent = (distance / current_price * 100) if current_price > 0 else 0
            
            return {
                'level': float(nearest),
                'distance': float(distance),
                'distance_percent': float(distance_percent),
                'is_close': distance_percent < 0.5  # کمتر از 0.5%
            }
            
        except Exception as e:
            logger.error(f"خطا در یافتن نزدیک‌ترین سطح: {e}")
            return {}
    
    def _calculate_level_strength(self, df: pd.DataFrame, 
                                 support_levels: List[float], 
                                 resistance_levels: List[float]) -> Dict:
        """محاسبه قدرت سطوح"""
        try:
            strength = {
                'support': {},
                'resistance': {}
            }
            
            # بررسی برخوردهای تاریخی
            for level in support_levels:
                touches = self._count_touches(df, level, 'support')
                strength['support'][str(level)] = {
                    'touches': touches,
                    'strength': min(10, touches * 2)  # امتیاز 0-10
                }
            
            for level in resistance_levels:
                touches = self._count_touches(df, level, 'resistance')
                strength['resistance'][str(level)] = {
                    'touches': touches,
                    'strength': min(10, touches * 2)
                }
            
            return strength
            
        except Exception as e:
            logger.error(f"خطا در محاسبه قدرت سطوح: {e}")
            return {}
    
    def _count_touches(self, df: pd.DataFrame, level: float, 
                      level_type: str = 'support', tolerance: float = 0.001) -> int:
        """شمردن تعداد برخوردها به یک سطح"""
        try:
            touches = 0
            tolerance_amount = level * tolerance
            
            for i in range(len(df)):
                if level_type == 'support':
                    # برخورد به حمایت: قیمت نزدیک به سطح از پایین
                    if abs(df['low'].iloc[i] - level) <= tolerance_amount:
                        touches += 1
                else:  # resistance
                    # برخورد به مقاومت: قیمت نزدیک به سطح از بالا
                    if abs(df['high'].iloc[i] - level) <= tolerance_amount:
                        touches += 1
            
            return touches
            
        except Exception as e:
            logger.error(f"خطا در شمردن برخوردها: {e}")
            return 0
    
    def _generate_signals(self, technical_analysis: Dict, 
                         price_analysis: Dict, 
                         pattern_analysis: Dict, 
                         key_levels: Dict) -> Dict:
        """تولید سیگنال‌ها"""
        try:
            signals = {
                'primary': 'HOLD',
                'secondary': 'HOLD',
                'entry_signal': 'NO_SIGNAL',
                'exit_signal': 'NO_SIGNAL',
                'strength': 0,
                'reasons': [],
                'risk_level': 'MEDIUM',
                'timeframe': 'MEDIUM_TERM',
                'confidence': 0
            }
            
            current_price = price_analysis.get('current', 0)
            overall_trend = technical_analysis.get('overall_trend', 'NEUTRAL')
            momentum_score = technical_analysis.get('momentum', {}).get('score', 50)
            trend_strength = technical_analysis.get('trend', {}).get('strength', 0)
            
            # جمع‌آوری دلایل
            reasons = []
            score = 50  # پایه
            
            # 1. روند (وزن 40%)
            if overall_trend == 'STRONG_BULLISH':
                score += 20
                reasons.append('روند صعودی قوی')
            elif overall_trend == 'BULLISH':
                score += 10
                reasons.append('روند صعودی')
            elif overall_trend == 'STRONG_BEARISH':
                score -= 20
                reasons.append('روند نزولی قوی')
            elif overall_trend == 'BEARISH':
                score -= 10
                reasons.append('روند نزولی')
            
            # 2. مومنتوم (وزن 25%)
            if momentum_score > 70:
                score += 12
                reasons.append('مومنتوم صعودی قوی')
            elif momentum_score > 60:
                score += 6
                reasons.append('مومنتوم صعودی')
            elif momentum_score < 30:
                score -= 12
                reasons.append('مومنتوم نزولی قوی')
            elif momentum_score < 40:
                score -= 6
                reasons.append('مومنتوم نزولی')
            
            # 3. الگوها (وزن 20%)
            pattern_score = pattern_analysis.get('strength', 0)
            if pattern_analysis.get('has_reversal', False):
                pattern_directions = [p.get('direction') for p in pattern_analysis.get('patterns', []) 
                                    if p.get('type') == 'REVERSAL']
                if 'BULLISH' in pattern_directions:
                    score += 8
                    reasons.append('الگوی بازگشتی صعودی')
                elif 'BEARISH' in pattern_directions:
                    score -= 8
                    reasons.append('الگوی بازگشتی نزولی')
            
            if pattern_analysis.get('has_continuation', False) and trend_strength > 50:
                score += 4
                reasons.append('الگوی ادامه‌دهنده')
            
            # 4. سطوح کلیدی (وزن 15%)
            nearest_support = key_levels.get('nearest_support', {})
            nearest_resistance = key_levels.get('nearest_resistance', {})
            
            if nearest_support.get('is_close', False):
                score += 6
                reasons.append('نزدیک به حمایت')
            
            if nearest_resistance.get('is_close', False):
                score -= 6
                reasons.append('نزدیک به مقاومت')
            
            # محدود کردن امتیاز
            score = max(0, min(100, score))
            
            # تعیین سیگنال اصلی
            if score >= 75:
                signals['primary'] = 'STRONG_BUY'
                signals['entry_signal'] = 'BUY'
                signals['strength'] = score
                signals['risk_level'] = 'LOW'
            elif score >= 65:
                signals['primary'] = 'BUY'
                signals['entry_signal'] = 'BUY'
                signals['strength'] = score
                signals['risk_level'] = 'MEDIUM'
            elif score <= 25:
                signals['primary'] = 'STRONG_SELL'
                signals['entry_signal'] = 'SELL'
                signals['strength'] = 100 - score
                signals['risk_level'] = 'LOW'
            elif score <= 35:
                signals['primary'] = 'SELL'
                signals['entry_signal'] = 'SELL'
                signals['strength'] = 100 - score
                signals['risk_level'] = 'MEDIUM'
            else:
                signals['primary'] = 'HOLD'
            
            # تعیین تایم‌فریم
            if trend_strength > 80:
                signals['timeframe'] = 'LONG_TERM'
            elif trend_strength > 50:
                signals['timeframe'] = 'MEDIUM_TERM'
            else:
                signals['timeframe'] = 'SHORT_TERM'
            
            # محاسبه اطمینان
            signals['confidence'] = self._calculate_confidence(
                score, 
                len(reasons), 
                trend_strength,
                pattern_analysis.get('count', 0)
            )
            
            signals['reasons'] = reasons
            
            return signals
            
        except Exception as e:
            logger.error(f"خطا در تولید سیگنال‌ها: {e}")
            return {
                'primary': 'HOLD',
                'strength': 0,
                'reasons': ['خطا در تحلیل'],
                'risk_level': 'HIGH',
                'confidence': 0
            }
    
    def _calculate_confidence(self, score: int, reason_count: int, 
                            trend_strength: int, pattern_count: int) -> int:
        """محاسبه اطمینان"""
        try:
            confidence = 50  # پایه
            
            # تأثیر امتیاز
            if score >= 70 or score <= 30:
                confidence += 20
            elif score >= 60 or score <= 40:
                confidence += 10
            
            # تأثیر تعداد دلایل
            if reason_count >= 3:
                confidence += 10
            
            # تأثیر قدرت روند
            if trend_strength >= 70:
                confidence += 10
            
            # تأثیر الگوها
            if pattern_count >= 2:
                confidence += 5
            
            # محدود کردن
            confidence = max(0, min(100, confidence))
            
            return confidence
            
        except Exception as e:
            logger.error(f"خطا در محاسبه اطمینان: {e}")
            return 50
    
    def _calculate_score_and_confidence(self, technical_analysis: Dict, 
                                      pattern_analysis: Dict, 
                                      signals: Dict) -> Tuple[int, int]:
        """محاسبه امتیاز و اطمینان نهایی"""
        try:
            score = signals.get('strength', 50)
            confidence = signals.get('confidence', 50)
            
            # تنظیم بر اساس جزئیات بیشتر
            trend_strength = technical_analysis.get('trend', {}).get('strength', 0)
            pattern_strength = pattern_analysis.get('strength', 0)
            
            # ترکیب نهایی
            final_score = int(score * 0.7 + trend_strength * 0.3)
            final_confidence = int(confidence * 0.6 + pattern_strength * 10 * 0.4)
            
            # محدود کردن
            final_score = max(0, min(100, final_score))
            final_confidence = max(0, min(100, final_confidence))
            
            return final_score, final_confidence
            
        except Exception as e:
            logger.error(f"خطا در محاسبه امتیاز نهایی: {e}")
            return 50, 50
    
    def _calculate_entry_exit_points(self, df: pd.DataFrame, 
                                    signals: Dict, 
                                    key_levels: Dict) -> Dict:
        """محاسبه نقاط ورود و خروج"""
        try:
            entry_exit = {
                'entry': None,
                'stop_loss': None,
                'take_profit_1': None,
                'take_profit_2': None,
                'risk_reward_ratio': None,
                'position_size_percent': None
            }
            
            current_price = df['close'].iloc[-1]
            signal = signals.get('primary', 'HOLD')
            
            if signal not in ['STRONG_BUY', 'BUY', 'STRONG_SELL', 'SELL']:
                return entry_exit
            
            # تعیین جهت
            is_buy = 'BUY' in signal
            
            # سطوح کلیدی
            support_levels = key_levels.get('support', [])
            resistance_levels = key_levels.get('resistance', [])
            pivot_points = key_levels.get('pivot_points', {})
            
            if is_buy:
                # نقاط ورود و خروج برای خرید
                entry_exit = self._calculate_buy_points(
                    current_price, support_levels, resistance_levels, pivot_points, df
                )
            else:
                # نقاط ورود و خروج برای فروش
                entry_exit = self._calculate_sell_points(
                    current_price, support_levels, resistance_levels, pivot_points, df
                )
            
            # محاسبه نسبت ریسک به ریوارد
            if (entry_exit['entry'] and entry_exit['stop_loss'] and 
                entry_exit['take_profit_1']):
                
                risk = abs(entry_exit['entry'] - entry_exit['stop_loss'])
                reward = abs(entry_exit['take_profit_1'] - entry_exit['entry'])
                
                if risk > 0:
                    entry_exit['risk_reward_ratio'] = round(reward / risk, 2)
            
            # پیشنهاد حجم پوزیشن
            if entry_exit['risk_reward_ratio']:
                if entry_exit['risk_reward_ratio'] >= 2:
                    entry_exit['position_size_percent'] = 2.0  # 2% ریسک
                elif entry_exit['risk_reward_ratio'] >= 1.5:
                    entry_exit['position_size_percent'] = 1.5  # 1.5% ریسک
                else:
                    entry_exit['position_size_percent'] = 1.0  # 1% ریسک
            
            return entry_exit
            
        except Exception as e:
            logger.error(f"خطا در محاسبه نقاط ورود و خروج: {e}")
            return {}
    
    def _calculate_buy_points(self, current_price: float, 
                             support_levels: List[float], 
                             resistance_levels: List[float], 
                             pivot_points: Dict, 
                             df: pd.DataFrame) -> Dict:
        """محاسبه نقاط برای خرید"""
        try:
            entry_exit = {}
            
            # نقطه ورود: نزدیک‌ترین حمایت یا کمی بالاتر
            if support_levels:
                nearest_support = max([s for s in support_levels if s < current_price])
                entry_price = nearest_support * 1.001  # 0.1% بالاتر از حمایت
            else:
                entry_price = current_price * 0.998  # 0.2% پایین‌تر از قیمت فعلی
            
            # استاپ‌لاس: زیر حمایت یا بر اساس ATR
            atr = df['atr'].iloc[-1] if 'atr' in df.columns else 0
            
            if support_levels:
                stop_loss = min(support_levels) * 0.995  # 0.5% زیر حمایت
            else:
                stop_loss = entry_price * 0.99  # 1% زیر نقطه ورود
            
            # استفاده از ATR اگر موجود باشد
            if atr > 0:
                stop_loss = max(stop_loss, entry_price - atr * 2)
            
            # تیک‌پروفیت اول: نزدیک‌ترین مقاومت
            if resistance_levels:
                nearest_resistance = min([r for r in resistance_levels if r > entry_price])
                take_profit_1 = nearest_resistance * 0.999  # 0.1% پایین‌تر از مقاومت
            else:
                # اگر مقاومتی نبود، بر اساس ریسک/ریوارد
                risk = entry_price - stop_loss
                take_profit_1 = entry_price + risk * 1.5
            
            # تیک‌پروفیت دوم: مقاومت بعدی یا ۲:۱ ریسک/ریوارد
            if len(resistance_levels) > 1:
                next_resistance = sorted([r for r in resistance_levels if r > take_profit_1])
                if next_resistance:
                    take_profit_2 = next_resistance[0] * 0.999
                else:
                    risk = entry_price - stop_loss
                    take_profit_2 = entry_price + risk * 2.5
            else:
                risk = entry_price - stop_loss
                take_profit_2 = entry_price + risk * 2.5
            
            entry_exit = {
                'entry': round(entry_price, 5),
                'stop_loss': round(stop_loss, 5),
                'take_profit_1': round(take_profit_1, 5),
                'take_profit_2': round(take_profit_2, 5)
            }
            
            return entry_exit
            
        except Exception as e:
            logger.error(f"خطا در محاسبه نقاط خرید: {e}")
            return {}
    
    def _calculate_sell_points(self, current_price: float, 
                              support_levels: List[float], 
                              resistance_levels: List[float], 
                              pivot_points: Dict, 
                              df: pd.DataFrame) -> Dict:
        """محاسبه نقاط برای فروش"""
        try:
            entry_exit = {}
            
            # نقطه ورود: نزدیک‌ترین مقاومت یا کمی پایین‌تر
            if resistance_levels:
                nearest_resistance = min([r for r in resistance_levels if r > current_price])
                entry_price = nearest_resistance * 0.999  # 0.1% پایین‌تر از مقاومت
            else:
                entry_price = current_price * 1.002  # 0.2% بالاتر از قیمت فعلی
            
            # استاپ‌لاس: بالای مقاومت یا بر اساس ATR
            atr = df['atr'].iloc[-1] if 'atr' in df.columns else 0
            
            if resistance_levels:
                stop_loss = max(resistance_levels) * 1.005  # 0.5% بالای مقاومت
            else:
                stop_loss = entry_price * 1.01  # 1% بالای نقطه ورود
            
            # استفاده از ATR اگر موجود باشد
            if atr > 0:
                stop_loss = min(stop_loss, entry_price + atr * 2)
            
            # تیک‌پروفیت اول: نزدیک‌ترین حمایت
            if support_levels:
                nearest_support = max([s for s in support_levels if s < entry_price])
                take_profit_1 = nearest_support * 1.001  # 0.1% بالاتر از حمایت
            else:
                # اگر حمایتی نبود، بر اساس ریسک/ریوارد
                risk = stop_loss - entry_price
                take_profit_1 = entry_price - risk * 1.5
            
            # تیک‌پروفیت دوم: حمایت بعدی یا ۲:۱ ریسک/ریوارد
            if len(support_levels) > 1:
                next_support = sorted([s for s in support_levels if s < take_profit_1], reverse=True)
                if next_support:
                    take_profit_2 = next_support[0] * 1.001
                else:
                    risk = stop_loss - entry_price
                    take_profit_2 = entry_price - risk * 2.5
            else:
                risk = stop_loss - entry_price
                take_profit_2 = entry_price - risk * 2.5
            
            entry_exit = {
                'entry': round(entry_price, 5),
                'stop_loss': round(stop_loss, 5),
                'take_profit_1': round(take_profit_1, 5),
                'take_profit_2': round(take_profit_2, 5)
            }
            
            return entry_exit
            
        except Exception as e:
            logger.error(f"خطا در محاسبه نقاط فروش: {e}")
            return {}
    
    def _risk_analysis(self, df: pd.DataFrame, signals: Dict) -> Dict:
        """تحلیل ریسک"""
        try:
            risk_score = 5.0  # 0-10
            
            # عوامل افزایش ریسک
            risk_factors = []
            
            # نوسان بالا
            if 'atr' in df.columns:
                atr_percent = (df['atr'].iloc[-1] / df['close'].iloc[-1] * 100)
                if atr_percent > 1.5:
                    risk_score += 2
                    risk_factors.append(f'نوسان بالا: {atr_percent:.2f}%')
            
            # روند ضعیف
            trend_strength = 50  # مقدار پیش‌فرض
            if 'adx' in df.columns:
                adx_value = df['adx'].iloc[-1]
                if adx_value < 20:
                    risk_score += 1
                    risk_factors.append('روند ضعیف')
            
            # نزدیکی به اخبار
            # در نسخه کامل از تقویم اقتصادی استفاده می‌شود
            
            # حجم کم
            if 'volume_ratio' in df.columns:
                volume_ratio = df['volume_ratio'].iloc[-1]
                if volume_ratio < 0.5:
                    risk_score += 1
                    risk_factors.append('حجم معاملات کم')
            
            # محدود کردن امتیاز
            risk_score = max(1, min(10, risk_score))
            
            # سطح ریسک
            risk_level = "LOW"
            if risk_score >= 8:
                risk_level = "VERY_HIGH"
            elif risk_score >= 7:
                risk_level = "HIGH"
            elif risk_score >= 5:
                risk_level = "MEDIUM"
            elif risk_score >= 3:
                risk_level = "LOW"
            else:
                risk_level = "VERY_LOW"
            
            # توصیه ریسک
            recommendation = ""
            if risk_level in ["VERY_HIGH", "HIGH"]:
                recommendation = "از معامله خودداری کنید یا حجم را کاهش دهید"
            elif risk_level == "MEDIUM":
                recommendation = "با احتیاط معامله کنید"
            else:
                recommendation = "شرایط مناسب برای معامله"
            
            return {
                'score': round(risk_score, 1),
                'level': risk_level,
                'factors': risk_factors,
                'recommendation': recommendation,
                'max_position_size_percent': self._calculate_max_position_size(risk_score)
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل ریسک: {e}")
            return {
                'score': 5.0,
                'level': 'MEDIUM',
                'factors': ['خطا در تحلیل ریسک'],
                'recommendation': 'با احتیاط اقدام کنید',
                'max_position_size_percent': 1.0
            }
    
    def _calculate_max_position_size(self, risk_score: float) -> float:
        """محاسبه حداکثر حجم پوزیشن بر اساس ریسک"""
        if risk_score >= 8:
            return 0.5  # 0.5% ریسک
        elif risk_score >= 7:
            return 1.0  # 1% ریسک
        elif risk_score >= 5:
            return 1.5  # 1.5% ریسک
        elif risk_score >= 3:
            return 2.0  # 2% ریسک
        else:
            return 2.5  # 2.5% ریسک
    
    def _generate_summary(self, signals: Dict, score: int, confidence: int) -> str:
        """تولید خلاصه تحلیل"""
        try:
            primary_signal = signals.get('primary', 'HOLD')
            strength = signals.get('strength', 0)
            risk_level = signals.get('risk_level', 'MEDIUM')
            
            if primary_signal == 'STRONG_BUY':
                return f"📈 سیگنال خرید قوی (امتیاز: {score}/100، اطمینان: {confidence}%، ریسک: {risk_level})"
            elif primary_signal == 'BUY':
                return f"📈 سیگنال خرید (امتیاز: {score}/100، اطمینان: {confidence}%، ریسک: {risk_level})"
            elif primary_signal == 'STRONG_SELL':
                return f"📉 سیگنال فروش قوی (امتیاز: {100-score}/100، اطمینان: {confidence}%، ریسک: {risk_level})"
            elif primary_signal == 'SELL':
                return f"📉 سیگنال فروش (امتیاز: {100-score}/100، اطمینان: {confidence}%، ریسک: {risk_level})"
            else:
                return f"⏸️  بدون سیگنال واضح (امتیاز: {score}/100، اطمینان: {confidence}%، ریسک: {risk_level})"
                
        except Exception as e:
            logger.error(f"خطا در تولید خلاصه: {e}")
            return "خطا در تولید خلاصه"
    
    def _get_recommendation(self, signals: Dict, score: int, confidence: int) -> Dict:
        """دریافت توصیه معاملاتی"""
        try:
            primary_signal = signals.get('primary', 'HOLD')
            
            if primary_signal in ['STRONG_BUY', 'BUY']:
                return {
                    'action': 'BUY',
                    'confidence': confidence,
                    'message': 'شرایط برای خرید مناسب است',
                    'risk_level': signals.get('risk_level', 'MEDIUM'),
                    'timeframe': signals.get('timeframe', 'MEDIUM_TERM')
                }
            elif primary_signal in ['STRONG_SELL', 'SELL']:
                return {
                    'action': 'SELL',
                    'confidence': confidence,
                    'message': 'شرایط برای فروش مناسب است',
                    'risk_level': signals.get('risk_level', 'MEDIUM'),
                    'timeframe': signals.get('timeframe', 'MEDIUM_TERM')
                }
            else:
                return {
                    'action': 'WAIT',
                    'confidence': confidence,
                    'message': 'منتظر فرصت بهتر باشید',
                    'risk_level': 'HIGH' if confidence < 30 else 'MEDIUM',
                    'timeframe': 'SHORT_TERM'
                }
                
        except Exception as e:
            logger.error(f"خطا در دریافت توصیه: {e}")
            return {
                'action': 'WAIT',
                'confidence': 0,
                'message': 'خطا در تحلیل',
                'risk_level': 'HIGH',
                'timeframe': 'UNKNOWN'
            }
    
    def _get_empty_analysis(self, symbol: str, timeframe: str) -> Dict:
        """تحلیل خالی برای مواقع خطا"""
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'current_price': 0,
            'technical': {'overall_trend': 'NEUTRAL'},
            'price': {},
            'patterns': {'patterns': [], 'count': 0, 'strength': 0},
            'time': {},
            'key_levels': {},
            'signals': {
                'primary': 'HOLD',
                'strength': 0,
                'reasons': ['خطا در تحلیل'],
                'risk_level': 'HIGH',
                'confidence': 0
            },
            'score': 0,
            'confidence': 0,
            'entry_exit': {},
            'risk': {'score': 10, 'level': 'VERY_HIGH'},
            'summary': 'خطا در تحلیل تکنیکال',
            'recommendation': {
                'action': 'WAIT',
                'confidence': 0,
                'message': 'خطا در تحلیل',
                'risk_level': 'HIGH',
                'timeframe': 'UNKNOWN'
            }
        }