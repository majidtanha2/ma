#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدیریت ریسک - نسخه کامل
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
import json
import hashlib

logger = logging.getLogger(__name__)

class RiskManager:
    """مدیریت ریسک پیشرفته"""
    
    def __init__(self):
        self.risk_history = []
        self.violations = []
        self.trade_journal = []
        
        # تنظیمات پیش‌فرض
        self.default_limits = {
            'max_daily_risk': 1.5,      # حداکثر ریسک روزانه (%)
            'max_trade_risk': 1.0,      # حداکثر ریسک هر معامله (%)
            'max_drawdown': 5.0,        # حداکثر دراودان (%)
            'max_positions': 3,         # حداکثر پوزیشن همزمان
            'daily_loss_limit': 2.0,    # حد ضرر روزانه (%)
            'max_leverage': 30,         # حداکثر لورج
            'min_risk_reward': 1.5,     # حداقل نسبت ریسک به ریوارد
            'max_consecutive_losses': 3, # حداکثر ضرر متوالی
            'correlation_limit': 0.7,   # حد همبستگی
            'sector_exposure_limit': 30, # حداکثر مواجهه با یک سکتور (%)
        }
        
        logger.info("Risk Manager initialized")
    
    def assess_trade_risk(self, analysis: Dict, risk_config: Dict) -> Dict:
        """
        ارزیابی ریسک یک معامله
        
        Args:
            analysis: نتایج تحلیل
            risk_config: تنظیمات ریسک
        
        Returns:
            Dict: ارزیابی ریسک
        """
        try:
            symbol = analysis.get('symbol', 'UNKNOWN')
            logger.info(f"Assessing trade risk for {symbol}")
            
            # 1. ارزیابی تکنیکال
            technical_risk = self._assess_technical_risk(analysis)
            
            # 2. ارزیابی قیمت
            price_risk = self._assess_price_risk(analysis)
            
            # 3. ارزیابی الگوها
            pattern_risk = self._assess_pattern_risk(analysis)
            
            # 4. ارزیابی سطوح
            level_risk = self._assess_level_risk(analysis)
            
            # 5. ارزیابی ریسک/ریوارد
            rr_risk = self._assess_risk_reward(analysis)
            
            # 6. ارزیابی حجم
            volume_risk = self._assess_volume_risk(analysis)
            
            # 7. ارزیابی نوسان
            volatility_risk = self._assess_volatility_risk(analysis)
            
            # 8. ترکیب امتیازها
            overall_risk = self._combine_risk_scores(
                technical_risk, price_risk, pattern_risk, 
                level_risk, rr_risk, volume_risk, volatility_risk
            )
            
            # 9. تولید سیگنال نهایی
            trade_signal, confidence = self._generate_trade_signal(
                overall_risk, analysis, risk_config
            )
            
            # 10. محاسبه اندازه پوزیشن
            position_size = self._calculate_position_size(
                overall_risk, analysis, risk_config
            )
            
            result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'technical_risk': technical_risk,
                'price_risk': price_risk,
                'pattern_risk': pattern_risk,
                'level_risk': level_risk,
                'rr_risk': rr_risk,
                'volume_risk': volume_risk,
                'volatility_risk': volatility_risk,
                'overall_risk': overall_risk,
                'trade_signal': trade_signal,
                'confidence': confidence,
                'position_size_percent': position_size,
                'risk_level': self._get_risk_level(overall_risk['score']),
                'recommendation': self._get_recommendation(overall_risk['score'], trade_signal),
                'warnings': overall_risk.get('warnings', []),
                'restrictions': self._get_trade_restrictions(overall_risk['score'])
            }
            
            # ذخیره در تاریخچه
            self.risk_history.append(result)
            
            logger.info(f"Risk assessment for {symbol}: {trade_signal} "
                       f"(Score: {overall_risk['score']:.1f}/10, "
                       f"Confidence: {confidence}%)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error assessing trade risk: {e}", exc_info=True)
            return self._get_empty_assessment()
    
    def _assess_technical_risk(self, analysis: Dict) -> Dict:
        """ارزیابی ریسک تکنیکال"""
        try:
            technical = analysis.get('technical', {})
            trend = technical.get('trend', {})
            momentum = technical.get('momentum', {})
            
            score = 5.0  # متوسط
            factors = []
            warnings = []
            
            # 1. قدرت روند
            trend_strength = trend.get('strength', 0)
            trend_direction = trend.get('direction', 'NEUTRAL')
            
            if trend_strength >= 80:
                score -= 1.5  # ریسک کمتر
                factors.append('روند قوی')
            elif trend_strength <= 20:
                score += 2.0  # ریسک بیشتر
                factors.append('روند ضعیف')
                warnings.append('روند بازار ضعیف است')
            
            # 2. همسویی اندیکاتورها
            alignment_score = self._check_indicator_alignment(technical)
            if alignment_score >= 80:
                score -= 1.0
                factors.append('همسویی اندیکاتورها')
            elif alignment_score <= 40:
                score += 1.5
                factors.append('عدم همسویی اندیکاتورها')
                warnings.append('اندیکاتورها همسو نیستند')
            
            # 3. سیگنال‌های متضاد
            conflicting_signals = self._check_conflicting_signals(technical)
            if conflicting_signals:
                score += len(conflicting_signals) * 0.5
                factors.append(f'{len(conflicting_signals)} سیگنال متضاد')
                warnings.extend(conflicting_signals)
            
            # 4. وضعیت مومنتوم
            momentum_score = momentum.get('score', 50)
            if momentum_score > 70:
                score -= 0.5
                factors.append('مومنتوم قوی')
            elif momentum_score < 30:
                score += 1.0
                factors.append('مومنتوم ضعیف')
                warnings.append('مومنتوم بازار ضعیف است')
            
            # محدود کردن امتیاز
            score = max(1, min(10, score))
            
            return {
                'score': round(score, 1),
                'factors': factors,
                'warnings': warnings,
                'trend_strength': trend_strength,
                'alignment_score': alignment_score,
                'momentum_score': momentum_score
            }
            
        except Exception as e:
            logger.error(f"Error in technical risk assessment: {e}")
            return {'score': 5.0, 'factors': ['خطا در تحلیل'], 'warnings': []}
    
    def _check_indicator_alignment(self, technical: Dict) -> float:
        """بررسی همسویی اندیکاتورها"""
        try:
            indicators = []
            
            # روند
            trend_direction = technical.get('trend', {}).get('direction', 'NEUTRAL')
            if trend_direction != 'NEUTRAL':
                indicators.append(1 if 'BULLISH' in trend_direction else -1)
            
            # MACD
            macd_signal = technical.get('trend', {}).get('macd', {}).get('cross_signal', 'NEUTRAL')
            if 'BULLISH' in macd_signal:
                indicators.append(1)
            elif 'BEARISH' in macd_signal:
                indicators.append(-1)
            
            # RSI
            momentum = technical.get('momentum', {})
            rsi_signal = momentum.get('indicators', {}).get('rsi', {}).get('signal', 'NEUTRAL')
            if rsi_signal == 'BULLISH' or rsi_signal == 'OVERSOLD':
                indicators.append(1)
            elif rsi_signal == 'BEARISH' or rsi_signal == 'OVERBOUGHT':
                indicators.append(-1)
            
            # Stochastic
            stoch_signal = momentum.get('indicators', {}).get('stochastic', {}).get('signal', 'NEUTRAL')
            if 'BULLISH' in stoch_signal:
                indicators.append(1)
            elif 'BEARISH' in stoch_signal:
                indicators.append(-1)
            
            if not indicators:
                return 50.0
            
            # محاسبه درصد همسویی
            bull_count = sum(1 for i in indicators if i > 0)
            bear_count = sum(1 for i in indicators if i < 0)
            total = len(indicators)
            
            if bull_count == total:
                return 100.0
            elif bear_count == total:
                return 0.0
            else:
                alignment = (max(bull_count, bear_count) / total) * 100
                return alignment
                
        except Exception as e:
            logger.error(f"Error checking indicator alignment: {e}")
            return 50.0
    
    def _check_conflicting_signals(self, technical: Dict) -> List[str]:
        """بررسی سیگنال‌های متضاد"""
        warnings = []
        
        try:
            trend_direction = technical.get('trend', {}).get('direction', 'NEUTRAL')
            momentum = technical.get('momentum', {})
            
            # بررسی تضاد بین روند و مومنتوم
            if 'BULLISH' in trend_direction:
                rsi_signal = momentum.get('indicators', {}).get('rsi', {}).get('signal', 'NEUTRAL')
                if rsi_signal == 'OVERBOUGHT':
                    warnings.append('تضاد: روند صعودی ولی RSI در منطقه اشباع خرید')
            
            elif 'BEARISH' in trend_direction:
                rsi_signal = momentum.get('indicators', {}).get('rsi', {}).get('signal', 'NEUTRAL')
                if rsi_signal == 'OVERSOLD':
                    warnings.append('تضاد: روند نزولی ولی RSI در منطقه اشباع فروش')
            
            # بررسی MACD divergence
            macd_divergence = momentum.get('indicators', {}).get('rsi', {}).get('divergence', 'NO_DIVERGENCE')
            if macd_divergence != 'NO_DIVERGENCE':
                if ('BULLISH' in trend_direction and 'BEARISH' in macd_divergence) or \
                   ('BEARISH' in trend_direction and 'BULLISH' in macd_divergence):
                    warnings.append(f'تضاد: واگرایی {macd_divergence} در جهت مخالف روند')
            
        except Exception as e:
            logger.error(f"Error checking conflicting signals: {e}")
        
        return warnings
    
    def _assess_price_risk(self, analysis: Dict) -> Dict:
        """ارزیابی ریسک قیمت"""
        try:
            price_data = analysis.get('price', {})
            current_price = price_data.get('current', 0)
            
            score = 5.0
            factors = []
            warnings = []
            
            if current_price <= 0:
                return {'score': 10.0, 'factors': ['قیمت نامعتبر'], 'warnings': ['قیمت صفر یا منفی']}
            
            # 1. تغییرات روزانه
            daily_change_percent = price_data.get('daily_change_percent', 0)
            if abs(daily_change_percent) > 3:
                score += 2.0
                factors.append(f'تغییر شدید روزانه: {daily_change_percent:.2f}%')
                warnings.append('تغییرات قیمتی شدید در یک روز')
            elif abs(daily_change_percent) > 1.5:
                score += 1.0
                factors.append(f'تغییر قابل توجه روزانه: {daily_change_percent:.2f}%')
            
            # 2. محدوده روز
            daily_range_percent = price_data.get('daily_range_percent', 0)
            if daily_range_percent > 2:
                score += 1.5
                factors.append(f'محدوده وسیع روزانه: {daily_range_percent:.2f}%')
            elif daily_range_percent > 1:
                score += 0.5
                factors.append(f'محدوده متوسط روزانه: {daily_range_percent:.2f}%')
            
            # 3. موقعیت در محدوده
            position_in_range = price_data.get('position_in_range', 50)
            if position_in_range > 80:
                score += 1.0
                factors.append('قیمت در سقف محدوده روزانه')
                warnings.append('قیمت نزدیک به سقف روزانه - احتمال مقاومت')
            elif position_in_range < 20:
                score += 1.0
                factors.append('قیمت در کف محدوده روزانه')
                warnings.append('قیمت نزدیک به کف روزانه - احتمال حمایت')
            
            # 4. نوع کندل
            candle_type = price_data.get('candle', {}).get('type', 'NORMAL')
            if candle_type == 'DOJI':
                score += 0.5
                factors.append('کندل دوجی - بلاتکلیفی')
            elif candle_type == 'MARUBOZU':
                score += 1.0
                factors.append('کندل ماروبوزو - قدرت خرید/فروش')
            
            # محدود کردن امتیاز
            score = max(1, min(10, score))
            
            return {
                'score': round(score, 1),
                'factors': factors,
                'warnings': warnings,
                'daily_change': daily_change_percent,
                'daily_range': daily_range_percent,
                'position_in_range': position_in_range,
                'candle_type': candle_type
            }
            
        except Exception as e:
            logger.error(f"Error in price risk assessment: {e}")
            return {'score': 5.0, 'factors': ['خطا در تحلیل'], 'warnings': []}
    
    def _assess_pattern_risk(self, analysis: Dict) -> Dict:
        """ارزیابی ریسک الگوها"""
        try:
            patterns_data = analysis.get('patterns', {})
            patterns = patterns_data.get('patterns', [])
            
            score = 5.0
            factors = []
            warnings = []
            
            if not patterns:
                factors.append('بدون الگوی مشخص')
                return {
                    'score': score,
                    'factors': factors,
                    'warnings': warnings,
                    'pattern_count': 0,
                    'has_reversal': False,
                    'has_continuation': False
                }
            
            pattern_count = len(patterns)
            has_reversal = patterns_data.get('has_reversal', False)
            has_continuation = patterns_data.get('has_continuation', False)
            pattern_strength = patterns_data.get('strength', 0)
            
            # 1. تعداد الگوها
            if pattern_count >= 3:
                score += 1.0
                factors.append(f'تعداد الگوها زیاد: {pattern_count}')
                warnings.append('الگوهای متعدد ممکن است سیگنال‌های متضاد ایجاد کنند')
            
            # 2. قدرت الگوها
            if pattern_strength >= 7:
                score -= 1.5
                factors.append('الگوهای قوی')
            elif pattern_strength <= 3:
                score += 1.5
                factors.append('الگوهای ضعیف')
                warnings.append('الگوهای شناسایی شده ضعیف هستند')
            
            # 3. نوع الگوها
            if has_reversal and has_continuation:
                score += 2.0
                factors.append('الگوهای بازگشتی و ادامه‌دهنده همزمان')
                warnings.append('تداخل الگوهای بازگشتی و ادامه‌دهنده')
            
            # 4. جهت‌گیری الگوها
            directions = [p.get('direction') for p in patterns if p.get('direction') != 'NEUTRAL']
            if directions:
                bull_patterns = sum(1 for d in directions if 'BULLISH' in d)
                bear_patterns = sum(1 for d in directions if 'BEARISH' in d)
                
                if bull_patterns > 0 and bear_patterns > 0:
                    score += 1.5
                    factors.append('الگوهای با جهت‌گیری متضاد')
                    warnings.append('الگوهای صعودی و نزولی همزمان وجود دارند')
            
            # 5. اعتبار الگوها
            valid_patterns = self._validate_patterns(patterns)
            if len(valid_patterns) < pattern_count:
                invalid_count = pattern_count - len(valid_patterns)
                score += invalid_count * 0.5
                factors.append(f'{invalid_count} الگوی نامعتبر')
            
            # محدود کردن امتیاز
            score = max(1, min(10, score))
            
            return {
                'score': round(score, 1),
                'factors': factors,
                'warnings': warnings,
                'pattern_count': pattern_count,
                'has_reversal': has_reversal,
                'has_continuation': has_continuation,
                'pattern_strength': pattern_strength,
                'valid_patterns': len(valid_patterns)
            }
            
        except Exception as e:
            logger.error(f"Error in pattern risk assessment: {e}")
            return {'score': 5.0, 'factors': ['خطا در تحلیل'], 'warnings': []}
    
    def _validate_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """اعتبارسنجی الگوها"""
        valid_patterns = []
        
        try:
            for pattern in patterns:
                # بررسی وجود فیلدهای ضروری
                required_fields = ['name', 'type', 'direction', 'strength']
                if all(field in pattern for field in required_fields):
                    # بررسی مقادیر معتبر
                    if pattern['strength'] in ['STRONG', 'MEDIUM', 'WEAK']:
                        valid_patterns.append(pattern)
        
        except Exception as e:
            logger.error(f"Error validating patterns: {e}")
        
        return valid_patterns
    
    def _assess_level_risk(self, analysis: Dict) -> Dict:
        """ارزیابی ریسک سطوح"""
        try:
            key_levels = analysis.get('key_levels', {})
            current_price = analysis.get('price', {}).get('current', 0)
            
            score = 5.0
            factors = []
            warnings = []
            
            if current_price <= 0:
                return {'score': 10.0, 'factors': ['قیمت نامعتبر'], 'warnings': []}
            
            # 1. نزدیکی به سطوح کلیدی
            nearest_support = key_levels.get('nearest_support', {})
            nearest_resistance = key_levels.get('nearest_resistance', {})
            
            support_distance = nearest_support.get('distance_percent', 100)
            resistance_distance = nearest_resistance.get('distance_percent', 100)
            
            # نزدیکی به حمایت
            if support_distance < 0.5:  # کمتر از 0.5%
                score -= 1.0
                factors.append('نزدیک به حمایت قوی')
            elif support_distance < 1.0:  # کمتر از 1%
                score -= 0.5
                factors.append('نزدیک به حمایت')
            
            # نزدیکی به مقاومت
            if resistance_distance < 0.5:
                score += 1.0
                factors.append('نزدیک به مقاومت قوی')
                warnings.append('قیمت نزدیک به مقاومت - احتمال بازگشت')
            elif resistance_distance < 1.0:
                score += 0.5
                factors.append('نزدیک به مقاومت')
            
            # 2. قدرت سطوح
            level_strength = key_levels.get('level_strength', {})
            
            support_strengths = level_strength.get('support', {}).values()
            resistance_strengths = level_strength.get('resistance', {}).values()
            
            avg_support_strength = np.mean([s.get('strength', 0) for s in support_strengths]) if support_strengths else 0
            avg_resistance_strength = np.mean([r.get('strength', 0) for r in resistance_strengths]) if resistance_strengths else 0
            
            if avg_support_strength >= 7:
                score -= 0.5
                factors.append('حمایت‌های قوی')
            if avg_resistance_strength >= 7:
                score += 0.5
                factors.append('مقاومت‌های قوی')
            
            # 3. شکست سطوح
            support_levels = key_levels.get('support', [])
            resistance_levels = key_levels.get('resistance', [])
            
            # بررسی شکست حمایت
            if support_levels and current_price < min(support_levels):
                score += 2.0
                factors.append('شکست حمایت')
                warnings.append('شکست سطح حمایت - احتمال ادامه نزول')
            
            # بررسی شکست مقاومت
            if resistance_levels and current_price > max(resistance_levels):
                score -= 2.0
                factors.append('شکست مقاومت')
                warnings.append('شکست سطح مقاومت - احتمال ادامه صعود')
            
            # 4. فشردگی قیمت (Price Squeeze)
            if len(support_levels) >= 2 and len(resistance_levels) >= 2:
                price_range = max(resistance_levels) - min(support_levels)
                price_range_percent = (price_range / current_price) * 100
                
                if price_range_percent < 2:  # محدوده قیمتی فشرده
                    score += 1.0
                    factors.append('فشردگی قیمت')
                    warnings.append('فشردگی قیمت - احتمال حرکت شدید')
            
            # محدود کردن امتیاز
            score = max(1, min(10, score))
            
            return {
                'score': round(score, 1),
                'factors': factors,
                'warnings': warnings,
                'support_distance': support_distance,
                'resistance_distance': resistance_distance,
                'avg_support_strength': round(avg_support_strength, 1),
                'avg_resistance_strength': round(avg_resistance_strength, 1),
                'price_range_percent': price_range_percent if 'price_range_percent' in locals() else 0
            }
            
        except Exception as e:
            logger.error(f"Error in level risk assessment: {e}")
            return {'score': 5.0, 'factors': ['خطا در تحلیل'], 'warnings': []}
    
    def _assess_risk_reward(self, analysis: Dict) -> Dict:
        """ارزیابی نسبت ریسک به ریوارد"""
        try:
            entry_exit = analysis.get('entry_exit', {})
            rr_ratio = entry_exit.get('risk_reward_ratio', 0)
            
            score = 5.0
            factors = []
            warnings = []
            
            # 1. نسبت ریسک به ریوارد
            if rr_ratio <= 0:
                score = 10.0
                factors.append('نسبت R/R نامعتبر')
                warnings.append('نسبت ریسک به ریوارد محاسبه نشده')
            elif rr_ratio >= 3:
                score -= 2.0
                factors.append(f'نسبت R/R عالی: {rr_ratio:.2f}')
            elif rr_ratio >= 2:
                score -= 1.5
                factors.append(f'نسبت R/R خوب: {rr_ratio:.2f}')
            elif rr_ratio >= 1.5:
                score -= 1.0
                factors.append(f'نسبت R/R قابل قبول: {rr_ratio:.2f}')
            elif rr_ratio >= 1:
                score += 0.5
                factors.append(f'نسبت R/R ضعیف: {rr_ratio:.2f}')
                warnings.append('نسبت ریسک به ریوارد ضعیف')
            else:
                score += 2.0
                factors.append(f'نسبت R/R بسیار ضعیف: {rr_ratio:.2f}')
                warnings.append('نسبت ریسک به ریوارد بسیار ضعیف - معامله توصیه نمی‌شود')
            
            # 2. اندازه استاپ نسبت به ATR
            atr = analysis.get('technical', {}).get('volatility', {}).get('indicators', {}).get('atr', {}).get('value', 0)
            stop_loss = entry_exit.get('stop_loss', 0)
            entry = entry_exit.get('entry', 0)
            
            if atr > 0 and entry > 0 and stop_loss > 0:
                stop_distance = abs(entry - stop_loss)
                atr_multiple = stop_distance / atr
                
                if atr_multiple < 1:
                    score += 1.5
                    factors.append(f'استاپ بسیار کوچک: {atr_multiple:.1f}xATR')
                    warnings.append('استاپ‌لاس بسیار نزدیک - احتمال hit شدن بالا')
                elif atr_multiple > 3:
                    score += 1.0
                    factors.append(f'استاپ بسیار بزرگ: {atr_multiple:.1f}xATR')
                    warnings.append('استاپ‌لاس بسیار دور - ریسک زیاد')
                elif 1.5 <= atr_multiple <= 2.5:
                    score -= 0.5
                    factors.append(f'استاپ ایده‌آل: {atr_multiple:.1f}xATR')
            
            # 3. فاصله تارگت‌ها
            tp1 = entry_exit.get('take_profit_1', 0)
            tp2 = entry_exit.get('take_profit_2', 0)
            
            if tp1 > 0 and tp2 > 0 and entry > 0:
                tp_distance = abs(tp2 - tp1)
                tp_distance_percent = (tp_distance / entry) * 100
                
                if tp_distance_percent > 5:
                    score += 0.5
                    factors.append(f'فاصله زیاد بین تارگت‌ها: {tp_distance_percent:.1f}%')
            
            # محدود کردن امتیاز
            score = max(1, min(10, score))
            
            return {
                'score': round(score, 1),
                'factors': factors,
                'warnings': warnings,
                'rr_ratio': rr_ratio,
                'atr_multiple': atr_multiple if 'atr_multiple' in locals() else 0,
                'tp_distance_percent': tp_distance_percent if 'tp_distance_percent' in locals() else 0
            }
            
        except Exception as e:
            logger.error(f"Error in risk/reward assessment: {e}")
            return {'score': 5.0, 'factors': ['خطا در تحلیل'], 'warnings': []}
    
    def _assess_volume_risk(self, analysis: Dict) -> Dict:
        """ارزیابی ریسک حجم"""
        try:
            technical = analysis.get('technical', {})
            volume_data = technical.get('volume', {})
            volume_indicators = volume_data.get('indicators', {})
            
            score = 5.0
            factors = []
            warnings = []
            
            # 1. حجم معاملات
            volume_info = volume_indicators.get('volume', {})
            volume_ratio = volume_info.get('ratio', 1)
            
            if volume_ratio > 3:
                score -= 1.0
                factors.append(f'حجم بسیار بالا: {volume_ratio:.1f}x')
            elif volume_ratio > 2:
                score -= 0.5
                factors.append(f'حجم بالا: {volume_ratio:.1f}x')
            elif volume_ratio < 0.3:
                score += 2.0
                factors.append(f'حجم بسیار پایین: {volume_ratio:.1f}x')
                warnings.append('حجم معاملات بسیار پایین - عدم تایید حرکت')
            elif volume_ratio < 0.5:
                score += 1.0
                factors.append(f'حجم پایین: {volume_ratio:.1f}x')
                warnings.append('حجم معاملات پایین')
            
            # 2. تایید حجم (OBV)
            obv_info = volume_indicators.get('obv', {})
            obv_trend = obv_info.get('trend', 'NEUTRAL')
            
            if 'BULLISH' in obv_trend:
                score -= 0.5
                factors.append('تایید حجم صعودی')
            elif 'BEARISH' in obv_trend:
                score += 0.5
                factors.append('تایید حجم نزولی')
            
            # 3. شاخص جریان مالی (MFI)
            mfi_info = volume_indicators.get('mfi', {})
            mfi_value = mfi_info.get('value', 50)
            mfi_signal = mfi_info.get('signal', 'NEUTRAL')
            
            if mfi_signal == 'OVERBOUGHT':
                score += 1.0
                factors.append('MFI در منطقه اشباع خرید')
                warnings.append('اشباع خرید در شاخص جریان مالی')
            elif mfi_signal == 'OVERSOLD':
                score -= 1.0
                factors.append('MFI در منطقه اشباع فروش')
            
            # 4. واگرایی حجم-قیمت
            volume_confirmation = volume_data.get('confirmation', 'NEUTRAL')
            
            if volume_confirmation == 'BEARISH_CONFIRMATION':
                score += 1.0
                factors.append('تایید حجم نزولی')
            elif volume_confirmation == 'BULLISH_CONFIRMATION':
                score -= 1.0
                factors.append('تایید حجم صعودی')
            
            # محدود کردن امتیاز
            score = max(1, min(10, score))
            
            return {
                'score': round(score, 1),
                'factors': factors,
                'warnings': warnings,
                'volume_ratio': volume_ratio,
                'obv_trend': obv_trend,
                'mfi_value': mfi_value,
                'mfi_signal': mfi_signal,
                'volume_confirmation': volume_confirmation
            }
            
        except Exception as e:
            logger.error(f"Error in volume risk assessment: {e}")
            return {'score': 5.0, 'factors': ['خطا در تحلیل'], 'warnings': []}
    
    def _assess_volatility_risk(self, analysis: Dict) -> Dict:
        """ارزیابی ریسک نوسان"""
        try:
            technical = analysis.get('technical', {})
            volatility_data = technical.get('volatility', {})
            volatility_indicators = volatility_data.get('indicators', {})
            
            score = 5.0
            factors = []
            warnings = []
            
            # 1. سطح کلی نوسان
            overall_volatility = volatility_data.get('overall', 'MEDIUM')
            volatility_score = volatility_data.get('score', 5.0)
            
            if overall_volatility == 'HIGH':
                score += 2.0
                factors.append('نوسان بالا')
                warnings.append('نوسان بازار بالا - ریسک افزایش یافته')
            elif overall_volatility == 'LOW':
                score -= 1.0
                factors.append('نوسان پایین')
            
            # 2. ATR
            atr_info = volatility_indicators.get('atr', {})
            atr_percent = atr_info.get('percent', 0)
            
            if atr_percent > 2:
                score += 2.0
                factors.append(f'ATR بسیار بالا: {atr_percent:.2f}%')
                warnings.append('نوسان روزانه بسیار بالا')
            elif atr_percent > 1.5:
                score += 1.0
                factors.append(f'ATR بالا: {atr_percent:.2f}%')
            elif atr_percent < 0.3:
                score -= 0.5
                factors.append(f'ATR پایین: {atr_percent:.2f}%')
            
            # 3. باندهای بولینگر
            bb_info = volatility_indicators.get('bollinger_bands', {})
            bb_width = bb_info.get('width', 0)
            bb_position = bb_info.get('position', 'MIDDLE')
            bb_squeeze = bb_info.get('squeeze', False)
            
            if bb_squeeze:
                score += 1.5
                factors.append('فشردگی باندهای بولینگر')
                warnings.append('فشردگی باندهای بولینگر - احتمال حرکت شدید')
            
            if bb_position == 'ABOVE_UPPER':
                score += 1.0
                factors.append('قیمت خارج از باند بالا')
                warnings.append('قیمت خارج از باند بولینگر بالا - احتمال بازگشت')
            elif bb_position == 'BELOW_LOWER':
                score -= 1.0
                factors.append('قیمت خارج از باند پایین')
            
            # 4. کانال کلتنر
            kc_info = volatility_indicators.get('keltner_channel', {})
            kc_width_percent = kc_info.get('width_percent', 0)
            
            if kc_width_percent > 3:
                score += 1.0
                factors.append(f'کانال کلتنر وسیع: {kc_width_percent:.1f}%')
            
            # 5. نسبت نوسان تاریخی
            historical_volatility = self._calculate_historical_volatility(analysis)
            if historical_volatility > 0:
                current_vs_historical = (volatility_score * 10) / historical_volatility
                
                if current_vs_historical > 1.5:
                    score += 1.0
                    factors.append('نوسان فعلی بیشتر از میانگین تاریخی')
                    warnings.append('نوسان فعلی بیشتر از حد معمول است')
                elif current_vs_historical < 0.7:
                    score -= 0.5
                    factors.append('نوسان فعلی کمتر از میانگین تاریخی')
            
            # محدود کردن امتیاز
            score = max(1, min(10, score))
            
            return {
                'score': round(score, 1),
                'factors': factors,
                'warnings': warnings,
                'overall_volatility': overall_volatility,
                'volatility_score': volatility_score,
                'atr_percent': atr_percent,
                'bb_width': bb_width,
                'bb_position': bb_position,
                'bb_squeeze': bb_squeeze,
                'kc_width_percent': kc_width_percent,
                'historical_volatility_ratio': current_vs_historical if 'current_vs_historical' in locals() else 1.0
            }
            
        except Exception as e:
            logger.error(f"Error in volatility risk assessment: {e}")
            return {'score': 5.0, 'factors': ['خطا در تحلیل'], 'warnings': []}
    
    def _calculate_historical_volatility(self, analysis: Dict, period: int = 20) -> float:
        """محاسبه نوسان تاریخی"""
        # این تابع ساده است. در نسخه کامل از داده‌های تاریخی واقعی استفاده می‌شود
        return 5.0  # مقدار پیش‌فرض
    
    def _combine_risk_scores(self, technical_risk: Dict, price_risk: Dict, 
                           pattern_risk: Dict, level_risk: Dict, 
                           rr_risk: Dict, volume_risk: Dict, 
                           volatility_risk: Dict) -> Dict:
        """ترکیب امتیازهای ریسک"""
        try:
            scores = [
                technical_risk.get('score', 5.0),
                price_risk.get('score', 5.0),
                pattern_risk.get('score', 5.0),
                level_risk.get('score', 5.0),
                rr_risk.get('score', 5.0),
                volume_risk.get('score', 5.0),
                volatility_risk.get('score', 5.0)
            ]
            
            # وزن‌های مختلف برای هر بخش
            weights = [0.20, 0.15, 0.10, 0.15, 0.20, 0.10, 0.10]
            
            # محاسبه میانگین وزنی
            weighted_sum = sum(s * w for s, w in zip(scores, weights))
            overall_score = weighted_sum
            
            # جمع‌آوری تمام هشدارها
            all_warnings = []
            all_warnings.extend(technical_risk.get('warnings', []))
            all_warnings.extend(price_risk.get('warnings', []))
            all_warnings.extend(pattern_risk.get('warnings', []))
            all_warnings.extend(level_risk.get('warnings', []))
            all_warnings.extend(rr_risk.get('warnings', []))
            all_warnings.extend(volume_risk.get('warnings', []))
            all_warnings.extend(volatility_risk.get('warnings', []))
            
            # جمع‌آوری تمام فاکتورها
            all_factors = []
            all_factors.extend(technical_risk.get('factors', []))
            all_factors.extend(price_risk.get('factors', []))
            all_factors.extend(pattern_risk.get('factors', []))
            all_factors.extend(level_risk.get('factors', []))
            all_factors.extend(rr_risk.get('factors', []))
            all_factors.extend(volume_risk.get('factors', []))
            all_factors.extend(volatility_risk.get('factors', []))
            
            # حذف موارد تکراری
            all_warnings = list(dict.fromkeys(all_warnings))
            all_factors = list(dict.fromkeys(all_factors))
            
            return {
                'score': round(overall_score, 1),
                'technical_score': technical_risk.get('score', 5.0),
                'price_score': price_risk.get('score', 5.0),
                'pattern_score': pattern_risk.get('score', 5.0),
                'level_score': level_risk.get('score', 5.0),
                'rr_score': rr_risk.get('score', 5.0),
                'volume_score': volume_risk.get('score', 5.0),
                'volatility_score': volatility_risk.get('score', 5.0),
                'warnings': all_warnings,
                'factors': all_factors,
                'weighted_average': True
            }
            
        except Exception as e:
            logger.error(f"Error combining risk scores: {e}")
            return {'score': 5.0, 'warnings': ['خطا در ترکیب امتیازها'], 'factors': []}
    
    def _generate_trade_signal(self, overall_risk: Dict, analysis: Dict, 
                              risk_config: Dict) -> Tuple[str, int]:
        """تولید سیگنال معاملاتی"""
        try:
            score = overall_risk.get('score', 5.0)
            signals = analysis.get('signals', {})
            primary_signal = signals.get('primary', 'HOLD')
            signal_strength = signals.get('strength', 50)
            confidence = signals.get('confidence', 50)
            
            # تنظیمات ریسک
            max_score_for_trade = risk_config.get('max_risk_score', 6.0)
            min_confidence = risk_config.get('min_confidence', 60)
            
            # تصمیم‌گیری
            if score > max_score_for_trade:
                # ریسک بسیار بالا
                return 'NO_TRADE', 0
            
            if confidence < min_confidence:
                # اطمینان کم
                return 'NO_TRADE', 0
            
            # بررسی هشدارهای مهم
            warnings = overall_risk.get('warnings', [])
            critical_warnings = [w for w in warnings if any(keyword in w for keyword in 
                                                           ['تضاد', 'شکست', 'اشباع', 'شدید', 'بسیار'])]
            
            if len(critical_warnings) >= 2:
                return 'NO_TRADE', 0
            
            # تصمیم بر اساس سیگنال اصلی
            if primary_signal in ['STRONG_BUY', 'BUY'] and score <= max_score_for_trade:
                if primary_signal == 'STRONG_BUY':
                    return 'BUY', min(95, confidence + 10)
                else:
                    return 'BUY', confidence
            
            elif primary_signal in ['STRONG_SELL', 'SELL'] and score <= max_score_for_trade:
                if primary_signal == 'STRONG_SELL':
                    return 'SELL', min(95, confidence + 10)
                else:
                    return 'SELL', confidence
            
            else:
                return 'HOLD', confidence
                
        except Exception as e:
            logger.error(f"Error generating trade signal: {e}")
            return 'HOLD', 0
    
    def _calculate_position_size(self, overall_risk: Dict, analysis: Dict, 
                                risk_config: Dict) -> float:
        """محاسبه اندازه پوزیشن"""
        try:
            score = overall_risk.get('score', 5.0)
            max_trade_risk = risk_config.get('max_trade_risk', 1.0)
            
            # تنظیم اندازه پوزیشن بر اساس ریسک
            if score <= 3.0:  # ریسک بسیار پایین
                position_size = max_trade_risk * 1.5  # 50% بیشتر
            elif score <= 4.0:  # ریسک پایین
                position_size = max_trade_risk * 1.2  # 20% بیشتر
            elif score <= 5.0:  # ریسک متوسط
                position_size = max_trade_risk
            elif score <= 6.0:  # ریسک بالا
                position_size = max_trade_risk * 0.7  # 30% کمتر
            elif score <= 7.0:  # ریسک بسیار بالا
                position_size = max_trade_risk * 0.5  # 50% کمتر
            else:  # ریسک بحرانی
                position_size = max_trade_risk * 0.3  # 70% کمتر
            
            # محدود کردن
            position_size = max(0.1, min(5.0, position_size))  # بین 0.1% تا 5%
            
            return round(position_size, 2)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return risk_config.get('max_trade_risk', 1.0)
    
    def _get_risk_level(self, score: float) -> str:
        """دریافت سطح ریسک"""
        if score <= 3.0:
            return "VERY_LOW"
        elif score <= 4.0:
            return "LOW"
        elif score <= 5.0:
            return "MEDIUM"
        elif score <= 6.0:
            return "HIGH"
        elif score <= 7.0:
            return "VERY_HIGH"
        else:
            return "EXTREME"
    
    def _get_recommendation(self, score: float, signal: str) -> str:
        """دریافت توصیه"""
        if signal == 'NO_TRADE':
            return "از معامله خودداری کنید"
        
        risk_level = self._get_risk_level(score)
        
        recommendations = {
            "VERY_LOW": "شرایط ایده‌آل برای معامله",
            "LOW": "شرایط خوب برای معامله",
            "MEDIUM": "با احتیاط معامله کنید",
            "HIGH": "فقط برای معامله‌گران با تجربه",
            "VERY_HIGH": "معامله با ریسک بسیار بالا",
            "EXTREME": "به شدت از معامله خودداری کنید"
        }
        
        return recommendations.get(risk_level, "با احتیاط اقدام کنید")
    
    def _get_trade_restrictions(self, score: float) -> Dict:
        """دریافت محدودیت‌های معامله"""
        restrictions = {
            'max_position_size_percent': 2.0,
            'max_leverage': 30,
            'require_stop_loss': True,
            'require_take_profit': True,
            'max_duration_days': 7,
            'allow_hedging': False,
            'require_trailing_stop': False
        }
        
        if score >= 7.0:
            restrictions.update({
                'max_position_size_percent': 0.5,
                'max_leverage': 10,
                'require_trailing_stop': True,
                'max_duration_days': 3
            })
        elif score >= 6.0:
            restrictions.update({
                'max_position_size_percent': 1.0,
                'max_leverage': 20,
                'max_duration_days': 5
            })
        elif score <= 3.0:
            restrictions.update({
                'max_position_size_percent': 3.0,
                'max_leverage': 50,
                'allow_hedging': True
            })
        
        return restrictions
    
    def check_portfolio_risk(self, positions: List[Dict], 
                            account_balance: float) -> Dict:
        """بررسی ریسک پرتفوی"""
        try:
            if not positions:
                return {
                    'total_risk': 0,
                    'diversification_score': 100,
                    'correlation_risk': 0,
                    'sector_exposure': {},
                    'recommendations': []
                }
            
            # محاسبه ریسک کل
            total_exposure = sum(p.get('exposure', 0) for p in positions)
            total_risk = (total_exposure / account_balance * 100) if account_balance > 0 else 0
            
            # تحلیل تنوع
            symbols = [p.get('symbol', '') for p in positions]
            unique_symbols = set(symbols)
            diversification_score = (len(unique_symbols) / len(symbols)) * 100 if symbols else 0
            
            # تحلیل همبستگی (ساده‌شده)
            correlation_risk = self._calculate_correlation_risk(positions)
            
            # تحلیل مواجهه سکتوری
            sector_exposure = self._calculate_sector_exposure(positions)
            
            # تولید توصیه‌ها
            recommendations = []
            
            if total_risk > 10:
                recommendations.append(f"ریسک پرتفوی بالا: {total_risk:.1f}% - کاهش حجم پیشنهاد می‌شود")
            
            if diversification_score < 50:
                recommendations.append(f"تنوع کم: {diversification_score:.1f}% - اضافه کردن نمادهای مختلف")
            
            if correlation_risk > 0.7:
                recommendations.append(f"همبستگی بالا: {correlation_risk:.2f} - پرتفوی متنوع‌تر")
            
            return {
                'total_risk': round(total_risk, 2),
                'diversification_score': round(diversification_score, 1),
                'correlation_risk': round(correlation_risk, 2),
                'sector_exposure': sector_exposure,
                'recommendations': recommendations,
                'position_count': len(positions),
                'unique_symbols': len(unique_symbols)
            }
            
        except Exception as e:
            logger.error(f"Error checking portfolio risk: {e}")
            return {}
    
    def _calculate_correlation_risk(self, positions: List[Dict]) -> float:
        """محاسبه ریسک همبستگی"""
        # این یک پیاده‌سازی ساده است
        # در نسخه کامل از ماتریس همبستگی واقعی استفاده می‌شود
        return 0.5  # مقدار پیش‌فرض
    
    def _calculate_sector_exposure(self, positions: List[Dict]) -> Dict:
        """محاسبه مواجهه سکتوری"""
        # این یک پیاده‌سازی ساده است
        sectors = {}
        
        for position in positions:
            symbol = position.get('symbol', '')
            exposure = position.get('exposure', 0)
            
            # تشخیص سکتور بر اساس نماد
            if any(curr in symbol for curr in ['USD', 'EUR', 'GBP', 'JPY']):
                sector = 'FOREX_MAJORS'
            elif 'XAU' in symbol or 'XAG' in symbol:
                sector = 'PRECIOUS_METALS'
            elif any(idx in symbol for idx in ['US30', 'SPX', 'NAS']):
                sector = 'INDICES'
            else:
                sector = 'OTHER'
            
            sectors[sector] = sectors.get(sector, 0) + exposure
        
        return sectors
    
    def monitor_account_risk(self, account_info: Dict, 
                            daily_stats: Dict) -> Dict:
        """نظارت بر ریسک حساب"""
        try:
            balance = account_info.get('balance', 0)
            equity = account_info.get('equity', 0)
            margin = account_info.get('margin', 0)
            free_margin = account_info.get('free_margin', 0)
            
            # محاسبه دراودان
            drawdown = ((balance - equity) / balance * 100) if balance > 0 else 0
            
            # سطح مارجین
            margin_level = (equity / margin * 100) if margin > 0 else 0
            
            # ریسک روزانه
            daily_pnl = daily_stats.get('daily_profit', 0)
            daily_risk = (abs(daily_pnl) / balance * 100) if daily_pnl < 0 and balance > 0 else 0
            
            # هشدارها
            warnings = []
            
            if drawdown > 5:
                warnings.append(f"دراودان بالا: {drawdown:.2f}%")
            
            if margin_level < 100:
                warnings.append(f"سطح مارجین پایین: {margin_level:.2f}%")
            
            if daily_risk > 2:
                warnings.append(f"ریسک روزانه بالا: {daily_risk:.2f}%")
            
            if free_margin < balance * 0.1:
                warnings.append(f"مارجین آزاد کم: ${free_margin:.2f}")
            
            return {
                'drawdown': round(drawdown, 2),
                'margin_level': round(margin_level, 2),
                'daily_risk': round(daily_risk, 2),
                'free_margin_ratio': round(free_margin / balance * 100, 2) if balance > 0 else 0,
                'warnings': warnings,
                'is_risk_acceptable': len(warnings) < 2
            }
            
        except Exception as e:
            logger.error(f"Error monitoring account risk: {e}")
            return {}
    
    def log_violation(self, violation_type: str, details: str, 
                     severity: str = 'MEDIUM') -> None:
        """ثبت تخلف"""
        violation = {
            'id': hashlib.md5(f"{violation_type}{details}{datetime.now()}".encode()).hexdigest()[:8],
            'type': violation_type,
            'details': details,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'resolved': False
        }
        
        self.violations.append(violation)
        logger.warning(f"Violation logged: {violation_type} - {details}")
        
        # ذخیره در فایل
        try:
            with open('risk_violations.json', 'a', encoding='utf-8') as f:
                f.write(json.dumps(violation, ensure_ascii=False) + '\n')
        except:
            pass
    
    def log_trade(self, trade_data: Dict) -> None:
        """ثبت معامله در ژورنال"""
        try:
            journal_entry = {
                'trade_id': hashlib.md5(str(trade_data).encode()).hexdigest()[:12],
                'timestamp': datetime.now().isoformat(),
                'data': trade_data,
                'risk_assessment': self._assess_trade_log_risk(trade_data)
            }
            
            self.trade_journal.append(journal_entry)
            
            # ذخیره در فایل
            with open('trade_journal.json', 'a', encoding='utf-8') as f:
                f.write(json.dumps(journal_entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            logger.error(f"Error logging trade: {e}")
    
    def _assess_trade_log_risk(self, trade_data: Dict) -> Dict:
        """ارزیابی ریسک ثبت معامله"""
        # ارزیابی پس از معامله
        return {
            'entry_timing_score': 7,
            'exit_timing_score': 7,
            'risk_management_score': 8,
            'overall_score': 7.5
        }
    
    def generate_risk_report(self, period: str = 'daily') -> Dict:
        """تولید گزارش ریسک"""
        try:
            now = datetime.now()
            
            if period == 'daily':
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == 'weekly':
                start_time = now - timedelta(days=7)
            elif period == 'monthly':
                start_time = now - timedelta(days=30)
            else:
                start_time = now - timedelta(days=1)
            
            # فیلتر تاریخچه
            period_history = [h for h in self.risk_history 
                            if datetime.fromisoformat(h['timestamp']) >= start_time]
            
            if not period_history:
                return {'error': 'No data for the specified period'}
            
            # آمارها
            total_assessments = len(period_history)
            average_risk_score = np.mean([h['overall_risk']['score'] for h in period_history])
            buy_signals = sum(1 for h in period_history if h['trade_signal'] == 'BUY')
            sell_signals = sum(1 for h in period_history if h['trade_signal'] == 'SELL')
            no_trade_signals = sum(1 for h in period_history if h['trade_signal'] == 'NO_TRADE')
            
            # توزیع سطح ریسک
            risk_levels = {}
            for h in period_history:
                level = h.get('risk_level', 'UNKNOWN')
                risk_levels[level] = risk_levels.get(level, 0) + 1
            
            # هشدارهای رایج
            common_warnings = {}
            for h in period_history:
                warnings = h['overall_risk'].get('warnings', [])
                for warning in warnings:
                    common_warnings[warning] = common_warnings.get(warning, 0) + 1
            
            # مرتب‌سازی هشدارها
            sorted_warnings = sorted(common_warnings.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # تخلفات
            period_violations = [v for v in self.violations 
                               if datetime.fromisoformat(v['timestamp']) >= start_time]
            
            return {
                'period': period,
                'start_date': start_time.isoformat(),
                'end_date': now.isoformat(),
                'total_assessments': total_assessments,
                'average_risk_score': round(average_risk_score, 2),
                'signal_distribution': {
                    'BUY': buy_signals,
                    'SELL': sell_signals,
                    'NO_TRADE': no_trade_signals
                },
                'risk_level_distribution': risk_levels,
                'common_warnings': dict(sorted_warnings),
                'violations_count': len(period_violations),
                'unresolved_violations': sum(1 for v in period_violations if not v['resolved']),
                'trades_logged': len([t for t in self.trade_journal 
                                     if datetime.fromisoformat(t['timestamp']) >= start_time])
            }
            
        except Exception as e:
            logger.error(f"Error generating risk report: {e}")
            return {'error': str(e)}
    
    def _get_empty_assessment(self) -> Dict:
        """ارزیابی خالی برای مواقع خطا"""
        return {
            'symbol': 'UNKNOWN',
            'timestamp': datetime.now().isoformat(),
            'technical_risk': {'score': 5.0, 'factors': [], 'warnings': []},
            'price_risk': {'score': 5.0, 'factors': [], 'warnings': []},
            'pattern_risk': {'score': 5.0, 'factors': [], 'warnings': []},
            'level_risk': {'score': 5.0, 'factors': [], 'warnings': []},
            'rr_risk': {'score': 5.0, 'factors': [], 'warnings': []},
            'volume_risk': {'score': 5.0, 'factors': [], 'warnings': []},
            'volatility_risk': {'score': 5.0, 'factors': [], 'warnings': []},
            'overall_risk': {'score': 5.0, 'warnings': ['خطا در ارزیابی ریسک'], 'factors': []},
            'trade_signal': 'HOLD',
            'confidence': 0,
            'position_size_percent': 0.5,
            'risk_level': 'HIGH',
            'recommendation': 'خطا در تحلیل - از معامله خودداری کنید',
            'warnings': ['خطا در ارزیابی ریسک'],
            'restrictions': {
                'max_position_size_percent': 0.5,
                'max_leverage': 10,
                'require_stop_loss': True,
                'require_take_profit': True,
                'max_duration_days': 1,
                'allow_hedging': False,
                'require_trailing_stop': True
            }
        }