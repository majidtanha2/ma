"""
================================================================================
🔥 دشبورد فوق پیشرفته بورس ایران - نسخه نهایی کامل با رفع مشکلات
================================================================================
✅ قابلیت‌ها:
   - لاگین مستقیم در مرورگر داخلی (رفع مشکل ورود)
   - تنظیمات پیشرفته فونت و جداول
   - نمایش صحیح داده‌های بازار
   - اتصال آنلاین به ایزی‌تریدر
   - آماده برای انتشار روی اینترنت
   - تحلیل پایه سهام با ۶ معیار اصلی
   - تحلیل پیشرفته ۷ روشی (حباب، ارزش ذاتی، تابلوخوانی، ریسک، عملکرد، تکنیکال)
   - تحلیل پورتفو با محاسبه صحیح سود/زیان
   - خروجی Excel با همه تحلیلها
================================================================================
"""

import os
import sys
import time
import json
import math
import uuid
import pickle
import threading
import webbrowser
import traceback
import warnings
import hashlib
import secrets
import tempfile
import shutil
import re
import io
import zipfile
from datetime import datetime, timedelta
from collections import defaultdict
from urllib.parse import urlparse, urljoin
import socket

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request, send_file, render_template_string, session, make_response, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots

warnings.filterwarnings('ignore')

# ============================================================================
# بخش ۱: تنظیمات اولیه و ثابت‌ها
# ============================================================================

VERSION = "3.2.0"
APP_NAME = "دشبورد فوق پیشرفته بورس ایران"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DOWNLOADS_DIR = os.path.join(DATA_DIR, 'downloads')
UPLOADS_DIR = os.path.join(DATA_DIR, 'uploads')
CACHE_DIR = os.path.join(DATA_DIR, 'cache')
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')
FONT_SETTINGS_FILE = os.path.join(DATA_DIR, 'font_settings.json')
COOKIES_FILE = os.path.join(DATA_DIR, 'cookies.json')
DEBUG_LOG_FILE = os.path.join(DATA_DIR, 'debug.log')

for dir_path in [DATA_DIR, DOWNLOADS_DIR, UPLOADS_DIR, CACHE_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# دریافت IP واقعی سرور برای انتشار روی اینترنت
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()
PORT = 8002

# ============================================================================
# بخش ۲: تابع Debug برای عیب‌یابی
# ============================================================================

def debug_log(message, level="INFO"):
    """ثبت لاگ برای عیب‌یابی"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] [{level}] {message}\n"
    
    print(log_line.strip())
    
    try:
        with open(DEBUG_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_line)
    except:
        pass

# ============================================================================
# بخش ۳: تلاش برای import سلنیوم (اختیاری)
# ============================================================================

SELENIUM_AVAILABLE = False
WEBDRIVER_MANAGER_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    SELENIUM_AVAILABLE = True
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        WEBDRIVER_MANAGER_AVAILABLE = True
    except:
        pass
except ImportError:
    debug_log("سلنیوم نصب نیست - برخی قابلیت‌ها محدود است", "WARNING")

# ============================================================================
# بخش ۴: تنظیمات پیش‌فرض (کاملترین تنظیمات ممکن)
# ============================================================================

DEFAULT_SETTINGS = {
    'weights': {
        'eps_weight': 0.40,
        'pb_weight': 0.25,
        'eps_growth_weight': 0.15,
        'pe_weight': 0.10,
        'rsi_weight': 0.05,
        'volume_weight': 0.05
    },
    'eps_thresholds': {
        'excellent': 2000,
        'very_good': 1000,
        'good': 500,
        'average': 200,
        'below_average': 100,
        'low': 50,
        'scores': {
            'excellent': 100,
            'very_good': 90,
            'good': 80,
            'average': 70,
            'below_average': 60,
            'low': 50,
            'positive': 40,
            'default': 30
        }
    },
    'pb_thresholds': {
        'excellent': 0.8,
        'very_good': 1.2,
        'good': 1.5,
        'average': 2.0,
        'scores': {
            'excellent': 100,
            'very_good': 80,
            'good': 60,
            'average': 40,
            'poor': 20
        }
    },
    'eps_growth_thresholds': {
        'excellent': 50,
        'very_good': 30,
        'good': 10,
        'average': 0,
        'poor': -10,
        'scores': {
            'excellent': 100,
            'very_good': 80,
            'good': 60,
            'average': 40,
            'poor': 20,
            'very_poor': 0
        }
    },
    'pe_thresholds': {
        'excellent': 8,
        'very_good': 12,
        'good': 20,
        'scores': {
            'excellent': 100,
            'very_good': 80,
            'good': 60,
            'poor': 30
        }
    },
    'rsi_thresholds': {
        'oversold_extreme': 20,
        'oversold': 30,
        'overbought': 70,
        'overbought_extreme': 60,
        'scores': {
            'oversold_extreme': 100,
            'oversold': 80,
            'neutral_low': 60,
            'neutral_high': 40,
            'overbought': 20
        }
    },
    'volume_thresholds': {
        'excellent': 10000000,
        'very_good': 5000000,
        'good': 1000000,
        'average': 500000,
        'scores': {
            'excellent': 100,
            'very_good': 80,
            'good': 60,
            'average': 40
        }
    },
    'filters': {
        'min_volume': 100000,
        'max_pb': 2.5,
        'min_eps': 50,
        'max_pe': 30,
        'rsi_min': 20,
        'rsi_max': 80,
        'max_1month_return': 50,
        'min_price': 1000,
        'max_price': 500000
    },
    'disqualifiers': {
        'max_pb_disqualify': 3.0,
        'min_eps_disqualify': 0,
        'max_rsi_disqualify': 85,
        'max_1month_return_disqualify': 60
    },
    'validation': {
        'min_final_score': 50,
        'max_pb_final': 2.0,
        'max_pe_final': 25,
        'max_rsi_final': 65,
        'max_stocks_final': 10
    },
    'status_thresholds': {
        'excellent': 85,
        'very_good': 75,
        'good': 65,
        'average': 55,
        'acceptable': 50
    },
    'bubble': {
        'pe_high': 25,
        'pe_medium_high': 18,
        'pe_medium': 12,
        'pe_low': 8,
        'pb_very_high': 5,
        'pb_high': 3,
        'pb_medium': 2,
        'pb_low': 1,
        'return_1m_very_high': 30,
        'return_1m_high': 20,
        'return_1m_medium': 10,
        'return_3m_very_high': 80,
        'return_3m_high': 50,
        'return_3m_medium': 30,
        'volume_ratio_very_high': 3,
        'volume_ratio_high': 2,
        'volume_ratio_medium': 1.5,
        'weights': {
            'pe': 0.3,
            'pb': 0.3,
            'growth': 0.25,
            'volume': 0.15
        }
    },
    'intrinsic_value': {
        'pe_multiplier': 8,
        'pb_multiplier': 1.5,
        'graham_base': 8.5,
        'graham_growth': 2,
        'dividend_payout': 0.3,
        'discount_rate': 0.15,
        'thresholds': {
            'strong_buy': 0.5,
            'buy': 0.7,
            'cautious_buy': 0.9,
            'hold': 1.1,
            'cautious_sell': 1.3,
            'sell': 1.5
        },
        'scores': {
            'strong_buy': 100,
            'buy': 90,
            'cautious_buy': 75,
            'hold': 60,
            'cautious_sell': 40,
            'sell': 25,
            'strong_sell': 10
        }
    },
    'tape_reading': {
        'demand_supply_max': 3,
        'price_power_min': -10,
        'price_power_max': 10,
        'avg_trade_divisor': 50000000,
        'avg_trade_max': 5,
        'power_index_thresholds': {
            'very_bullish': 5,
            'bullish': 2,
            'bearish': -2,
            'very_bearish': -5
        },
        'base_score': 50,
        'score_multiplier': 2.5
    },
    'risk': {
        'beta_thresholds': {
            'very_high': 1.5,
            'high': 1.2,
            'medium': 0.8,
            'low': 0.5
        },
        'volume_thresholds': {
            'very_low': 100000,
            'low': 500000,
            'medium': 1000000,
            'high': 5000000
        },
        'volatility_thresholds': {
            'very_high': 100,
            'high': 50,
            'medium': 20
        },
        'weights': {
            'beta': 0.2,
            'liquidity': 0.2,
            'volatility': 0.15,
            'rsi': 0.15,
            'pb': 0.15,
            'eps': 0.15
        }
    },
    'performance': {
        'cagr_weights': {
            '1m': 0.1,
            '3m': 0.2,
            '6m': 0.3,
            '1y': 0.3,
            'consistency': 0.1
        },
        'cagr_multipliers': {
            '1m': 50,
            '3m': 40,
            '6m': 30,
            '1y': 20
        },
        'cagr_limits': {
            'min': -10,
            'max': 20
        },
        'base_score': 50,
        'score_multiplier': 2.5
    },
    'technical': {
        'rsi_thresholds': {
            'oversold_extreme': 20,
            'oversold': 30,
            'overbought': 70,
            'overbought_extreme': 60
        },
        'mfi_thresholds': {
            'oversold_extreme': 20,
            'oversold': 30,
            'overbought': 80,
            'overbought_extreme': 70
        },
        'scores': {
            'strong_buy': 2,
            'buy': 1,
            'neutral': 0,
            'sell': -1,
            'strong_sell': -2
        },
        'ma_scores': {
            'very_bullish': 3,
            'bullish': 2,
            'mildly_bullish': 1,
            'very_bearish': -3,
            'bearish': -2,
            'mildly_bearish': -1
        },
        'position_scores': {
            'excellent': 2,
            'good': 1,
            'neutral': 0,
            'poor': -1
        },
        'base_score': 50,
        'score_multiplier': 5
    },
    'portfolio': {
        'alert_thresholds': {
            'profit_high': 25,
            'profit_medium': 15,
            'loss_high': -15,
            'loss_medium': -10,
            'loss_low': -8,
            'loss_very_low': -3
        },
        'rsi_thresholds': {
            'high': 70,
            'low': 30
        },
        'pb_thresholds': {
            'high': 2.5,
            'low': 0.8
        },
        'status_thresholds': {
            'excellent': 20,
            'very_good': 15,
            'good': 10,
            'average': 5,
            'poor': 0,
            'very_poor': -10
        },
        'diversity_scores': {
            10: 100,
            7: 80,
            5: 60,
            3: 40,
            'default': 20
        }
    }
}

# ============================================================================
# بخش ۵: تنظیمات پیش‌فرض فونت و جداول
# ============================================================================

DEFAULT_FONT_SETTINGS = {
    'general': {
        'font_family': 'Tahoma, Arial, sans-serif',
        'base_font_size': 14,
        'base_text_color': '#ffffff',
        'base_background_color': '#0a0a0a',
        'card_background_color': '#1a1a1a',
        'card_header_color': '#00bcd4',
        'card_header_background': '#2d2d2d'
    },
    'tables': {
        'header_font_size': 14,
        'header_font_color': '#00bcd4',
        'header_background': '#1e1e1e',
        'row_font_size': 13,
        'row_font_color': '#000000',
        'row_background_even': '#f5f5f5',
        'row_background_odd': '#ffffff',
        'border_color': '#dddddd'
    },
    'charts': {
        'title_font_size': 16,
        'title_font_color': '#ffffff',
        'axis_font_size': 12,
        'axis_font_color': '#ffffff',
        'legend_font_size': 11,
        'legend_font_color': '#ffffff',
        'grid_color': '#333333',
        'paper_background': 'rgba(0,0,0,0)',
        'plot_background': 'rgba(0,0,0,0)'
    },
    'alerts': {
        'card_title_font_size': 16,
        'card_title_font_color': '#ffffff',
        'card_text_font_size': 14,
        'card_text_font_color': '#ffffff',
        'success_color': '#4caf50',
        'info_color': '#2196f3',
        'warning_color': '#ff9800',
        'danger_color': '#f44336',
        'secondary_color': '#9e9e9e'
    },
    'stats': {
        'value_font_size': 32,
        'value_font_color': '#00bcd4',
        'label_font_size': 16,
        'label_font_color': '#ffffff'
    }
}

# ============================================================================
# بخش ۶: کلاس مدیریت تنظیمات فونت (رفع مشکل اعمال تنظیمات)
# ============================================================================

class FontSettingsManager:
    """مدیریت تنظیمات فونت و ظاهر - با قابلیت اعمال لحظه‌ای"""
    
    def __init__(self):
        self.settings_file = FONT_SETTINGS_FILE
        self.settings = self.load()
        self.css_cache = None
        self.last_modified = None
    
    def load(self):
        """بارگذاری تنظیمات فونت"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        settings = json.loads(content)
                        
                        # اطمینان از وجود تمام کلیدها
                        settings = self.ensure_all_keys(settings)
                        
                        debug_log(f"تنظیمات فونت بارگذاری شد: {os.path.getmtime(self.settings_file)}")
                        return settings
            except Exception as e:
                debug_log(f"خطا در بارگذاری تنظیمات فونت: {e}", "ERROR")
        
        debug_log("استفاده از تنظیمات پیش‌فرض فونت")
        return DEFAULT_FONT_SETTINGS.copy()
    
    def ensure_all_keys(self, settings):
        """اطمینان از وجود تمام کلیدهای مورد نیاز"""
        # اگر کلیدی وجود نداشت، از پیش‌فرض استفاده کن
        default = DEFAULT_FONT_SETTINGS.copy()
        
        for section, values in default.items():
            if section not in settings:
                settings[section] = values
            else:
                for key, val in values.items():
                    if key not in settings[section]:
                        settings[section][key] = val
        
        return settings
    
    def save(self):
        """ذخیره تنظیمات فونت"""
        try:
            # ذخیره با فرمت زیبا
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            
            # پاک کردن کش CSS - این خیلی مهمه!
            self.css_cache = None
            self.last_modified = datetime.now().timestamp()
            
            debug_log(f"تنظیمات فونت ذخیره شد: {self.settings_file}")
            return True
        except Exception as e:
            debug_log(f"خطا در ذخیره تنظیمات فونت: {e}", "ERROR")
            return False
    
    def reset(self):
        """بازنشانی به پیش‌فرض"""
        self.settings = DEFAULT_FONT_SETTINGS.copy()
        self.save()
        debug_log("تنظیمات فونت بازنشانی شد")
    
    def generate_css(self):
        """تولید CSS پویا از تنظیمات با اولویت بالا"""
        
        # بررسی تغییرات فایل - اگر فایل تغییر کرده بود، کش رو پاک کن
        if os.path.exists(self.settings_file):
            file_mtime = os.path.getmtime(self.settings_file)
            if self.last_modified and file_mtime > self.last_modified:
                self.css_cache = None
                self.last_modified = file_mtime
                debug_log("فایل تنظیمات فونت تغییر کرده، کش CSS پاک شد")
        
        # اگر کش وجود داره، همون رو برگردون
        if self.css_cache:
            return self.css_cache
        
        s = self.settings
        
        # CSS بسیار قوی با انتخابگرهای دقیق و !important
        css = f"""
        <style data-font="dynamic" data-version="{datetime.now().timestamp()}">
            /* ============================================== */
            /* تنظیمات پویای فونت - بروزرسانی: {datetime.now().isoformat()} */
            /* ============================================== */
            
            /* اعمال به body و تمام المان‌ها */
            html, body, div, span, applet, object, iframe,
            h1, h2, h3, h4, h5, h6, p, blockquote, pre,
            a, abbr, acronym, address, big, cite, code,
            del, dfn, em, img, ins, kbd, q, s, samp,
            small, strike, strong, sub, sup, tt, var,
            b, u, i, center,
            dl, dt, dd, ol, ul, li,
            fieldset, form, label, legend,
            table, caption, tbody, tfoot, thead, tr, th, td,
            article, aside, canvas, details, embed, 
            figure, figcaption, footer, header, hgroup, 
            menu, nav, output, ruby, section, summary,
            time, mark, audio, video {{
                font-family: {s['general']['font_family']} !important;
            }}
            
            body {{
                font-size: {s['general']['base_font_size']}px !important;
                color: {s['general']['base_text_color']} !important;
                background-color: {s['general']['base_background_color']} !important;
            }}
            
            .card {{
                background: {s['general']['card_background_color']} !important;
                border-color: {s['tables']['border_color']} !important;
            }}
            
            .card-header {{
                color: {s['general']['card_header_color']} !important;
                background: {s['general']['card_header_background']} !important;
                border-bottom-color: {s['tables']['border_color']} !important;
            }}
            
            .card-header, .card-header * {{
                color: {s['general']['card_header_color']} !important;
            }}
            
            .card-body, .card-body * {{
                color: {s['general']['base_text_color']} !important;
            }}
            
            /* ========== جداول - با بیشترین اولویت ========== */
            
            /* تمام جداول */
            table, .table, .table-responsive table {{
                color: {s['tables']['row_font_color']} !important;
                background-color: transparent !important;
                border-color: {s['tables']['border_color']} !important;
            }}
            
            /* هدر جدول */
            table thead, .table thead,
            table thead tr, .table thead tr,
            table thead th, .table thead th {{
                font-size: {s['tables']['header_font_size']}px !important;
                color: {s['tables']['header_font_color']} !important;
                background: {s['tables']['header_background']} !important;
                border-bottom-color: {s['tables']['border_color']} !important;
                border-bottom-width: 2px !important;
                border-bottom-style: solid !important;
            }}
            
            /* بدنه جدول - ردیف‌ها */
            table tbody, .table tbody,
            table tbody tr, .table tbody tr {{
                background-color: transparent !important;
            }}
            
            /* سلول‌های بدنه */
            table tbody td, .table tbody td {{
                font-size: {s['tables']['row_font_size']}px !important;
                color: {s['tables']['row_font_color']} !important;
                border-color: {s['tables']['border_color']} !important;
                border-width: 1px !important;
                border-style: solid !important;
                padding: 8px !important;
            }}
            
            /* ردیف‌های زوج */
            table tbody tr:nth-of-type(even),
            .table tbody tr:nth-of-type(even),
            .table-striped tbody tr:nth-of-type(even) {{
                background-color: {s['tables']['row_background_even']} !important;
            }}
            
            /* ردیف‌های فرد */
            table tbody tr:nth-of-type(odd),
            .table tbody tr:nth-of-type(odd),
            .table-striped tbody tr:nth-of-type(odd) {{
                background-color: {s['tables']['row_background_odd']} !important;
            }}
            
            /* hover روی ردیف‌ها */
            table tbody tr:hover,
            .table tbody tr:hover {{
                background-color: {s['general']['card_header_background']} !important;
            }}
            
            /* سلول‌های hover */
            table tbody tr:hover td,
            .table tbody tr:hover td {{
                color: {s['tables']['row_font_color']} !important;
            }}
            
            /* ========== کارت‌های آمار ========== */
            .stat-label {{
                font-size: {s['stats']['label_font_size']}px !important;
                color: {s['stats']['label_font_color']} !important;
            }}
            
            .stat-value {{
                font-size: {s['stats']['value_font_size']}px !important;
                color: {s['stats']['value_font_color']} !important;
            }}
            
            /* ========== هشدارها ========== */
            .alert-card h6 {{
                font-size: {s['alerts']['card_title_font_size']}px !important;
                color: {s['alerts']['card_title_font_color']} !important;
            }}
            
            .alert-card, .alert-card * {{
                font-size: {s['alerts']['card_text_font_size']}px !important;
                color: {s['alerts']['card_text_font_color']} !important;
            }}
            
            .badge-success {{
                background: {s['alerts']['success_color']} !important;
                color: #ffffff !important;
            }}
            
            .badge-info {{
                background: {s['alerts']['info_color']} !important;
                color: #ffffff !important;
            }}
            
            .badge-warning {{
                background: {s['alerts']['warning_color']} !important;
                color: #ffffff !important;
            }}
            
            .badge-danger {{
                background: {s['alerts']['danger_color']} !important;
                color: #ffffff !important;
            }}
            
            .badge-secondary {{
                background: {s['alerts']['secondary_color']} !important;
                color: #ffffff !important;
            }}
            
            /* رنگ‌های متن */
            .profit-text {{
                color: {s['alerts']['success_color']} !important;
            }}
            
            .loss-text {{
                color: {s['alerts']['danger_color']} !important;
            }}
            
            .text-info {{
                color: {s['alerts']['info_color']} !important;
            }}
            
            .text-warning {{
                color: {s['alerts']['warning_color']} !important;
            }}
            
            .text-muted {{
                color: {s['alerts']['secondary_color']} !important;
            }}
            
            /* ========== المان‌های دیگر ========== */
            .section-title {{
                color: {s['general']['card_header_color']} !important;
                font-size: 18px !important;
                border-right-color: {s['general']['card_header_color']} !important;
            }}
            
            h1, h2, h3, h4, h5, h6 {{
                color: {s['general']['base_text_color']} !important;
            }}
            
            .form-label {{
                color: {s['general']['card_header_color']} !important;
            }}
            
            .nav-tabs .nav-link.active {{
                color: {s['general']['card_header_color']} !important;
                border-bottom-color: {s['general']['card_header_color']} !important;
            }}
            
            /* نمودارها */
            .plotly-graph-div .main-svg {{
                background: transparent !important;
            }}
            
            .plotly-graph-div .bg {{
                fill: transparent !important;
            }}
            
            /* تنظیمات اضافی برای اطمینان از اعمال */
            input, select, textarea, button {{
                font-family: inherit !important;
            }}
            
            /* اولویت بیشتر برای bootstrap */
            .table, .table-bordered, .table-striped,
            .table-hover, .table-sm, .table-dark {{
                color: {s['tables']['row_font_color']} !important;
            }}
            
            /* بازنویسی مستقیم bootstrap */
            .table thead th,
            .table tbody td,
            .table tbody th {{
                color: inherit !important;
            }}
        </style>
        """
        
        self.css_cache = css
        debug_log(f"CSS جدید تولید شد با رنگ متن: {s['tables']['row_font_color']}")
        return css

font_settings = FontSettingsManager()

# ============================================================================
# بخش ۷: کلاس مدیریت تنظیمات اصلی
# ============================================================================

class SettingsManager:
    """مدیریت تنظیمات پویا - با قابلیت ادغام عمیق"""
    
    def __init__(self):
        self.settings_file = SETTINGS_FILE
        self.settings = self.load()
    
    def load(self):
        """بارگذاری تنظیمات از فایل"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                debug_log(f"تنظیمات اصلی بارگذاری شد")
                return self.merge_deep(DEFAULT_SETTINGS.copy(), user_settings)
            except Exception as e:
                debug_log(f"خطا در بارگذاری تنظیمات: {e}", "ERROR")
                return DEFAULT_SETTINGS.copy()
        return DEFAULT_SETTINGS.copy()
    
    def merge_deep(self, default, user):
        """ادغام عمیق دو دیکشنری"""
        merged = default.copy()
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self.merge_deep(merged[key], value)
            else:
                merged[key] = value
        return merged
    
    def save(self):
        """ذخیره تنظیمات در فایل"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            debug_log("تنظیمات اصلی ذخیره شد")
            return True
        except Exception as e:
            debug_log(f"خطا در ذخیره تنظیمات: {e}", "ERROR")
            return False
    
    def reset(self):
        """بازنشانی به تنظیمات پیش‌فرض"""
        self.settings = DEFAULT_SETTINGS.copy()
        self.save()
        debug_log("تنظیمات اصلی بازنشانی شد")

settings = SettingsManager()

# ============================================================================
# بخش ۸: کلاس اتصال آنلاین به ایزی‌تریدر (کامل و بدون خلاصه‌سازی)
# ============================================================================

import requests
import time
import os
import sys
import re
import pickle
import threading
import tempfile
import subprocess
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import pandas as pd
import tkinter as tk
from tkinter import messagebox

# بررسی وجود selenium و webdriver_manager
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except:
    WEBDRIVER_MANAGER_AVAILABLE = False

SELENIUM_AVAILABLE = True

class EasyTraderOnline:
    """اتصال مستقیم آنلاین به ایزی‌تریدر - با قابلیت دانلود اتوماتیک"""
    
    def __init__(self, logger=None):
        self.session = requests.Session() if 'requests' in sys.modules else None
        self.base_url = "https://d.easytrader.ir"
        self.driver = None
        self.selenium_available = SELENIUM_AVAILABLE
        self.webdriver_manager_available = WEBDRIVER_MANAGER_AVAILABLE
        self.is_logged_in = False
        self.login_lock = threading.Lock()
        self.chrome_version = self.get_chrome_version()
        self.user_data_dir = tempfile.mkdtemp(prefix="chrome_profile_")
        self.logger = logger
        self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "easytrader_downloads")
        
        # متغیرهای وضعیت
        self.status = {'status': 'disconnected', 'message': 'قطع', 'timestamp': datetime.now().isoformat()}
        self.cookies = {}
        self.auth_token = None
        self.market_data = None
        self.portfolio_data = None
        self.last_download_time = None
        
        # تنظیمات دانلود اتوماتیک
        self.auto_download_enabled = False
        self.auto_download_interval = 300
        self.auto_download_thread = None
        self.auto_download_market = True
        self.auto_download_portfolio = True
        
        # ایجاد پوشه دانلود
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
    
    def log(self, message, level="INFO"):
        """ثبت لاگ با استفاده از logger"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        
        if self.logger:
            self.logger.log(message, level)
        else:
            print(log_message)
    
    def update_status(self, status, message):
        """بروزرسانی وضعیت"""
        self.status = {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.log(message, "INFO")
    
    def get_chrome_version(self):
        """دریافت نسخه کروم نصب شده"""
        try:
            if sys.platform == "win32":
                import winreg
                
                registry_paths = [
                    r"Software\Google\Chrome\BLBeacon",
                    r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
                    r"Software\Wow6432Node\Google\Chrome\BLBeacon"
                ]
                
                for path in registry_paths:
                    try:
                        if "App Paths" in path:
                            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                            chrome_path, _ = winreg.QueryValueEx(key, "")
                            winreg.CloseKey(key)
                            
                            result = subprocess.run([chrome_path, '--version'], 
                                                  capture_output=True, text=True, 
                                                  creationflags=subprocess.CREATE_NO_WINDOW)
                            if result.stdout:
                                version_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                                if version_match:
                                    return version_match.group(1)
                        else:
                            try:
                                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path)
                                version, _ = winreg.QueryValueEx(key, "version")
                                winreg.CloseKey(key)
                                return version
                            except:
                                try:
                                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                                    version, _ = winreg.QueryValueEx(key, "version")
                                    winreg.CloseKey(key)
                                    return version
                                except:
                                    continue
                    except:
                        continue
            
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                os.path.expanduser("~") + "\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    try:
                        result = subprocess.run([path, '--version'], 
                                              capture_output=True, text=True,
                                              creationflags=subprocess.CREATE_NO_WINDOW)
                        if result.stdout:
                            version_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                            if version_match:
                                return version_match.group(1)
                    except Exception as e:
                        self.log(f"خطا در دریافت نسخه کروم از {path}: {e}", "WARNING")
                        continue
            
            return "120.0.0.0"
        except Exception as e:
            self.log(f"خطا در دریافت نسخه کروم: {e}", "WARNING")
            return "120.0.0.0"
    
    def get_2fa_code_from_user(self):
        """دریافت کد 2FA از کاربر با رابط بهتر"""
        try:
            dialog = tk.Toplevel()
            dialog.title("کد احراز هویت دو مرحله‌ای")
            dialog.geometry("400x200")
            dialog.resizable(False, False)
            dialog.configure(bg='#f0f0f0')
            dialog.attributes('-topmost', True)
            
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'{width}x{height}+{x}+{y}')
            
            help_text = """لطفاً کد 6 رقمی را از برنامه Google Authenticator وارد کنید.
            
اگر 2FA فعال نیست، می‌توانید این پنجره را ببندید."""
            
            label = tk.Label(dialog, text=help_text, font=('Tahoma', 11), 
                           bg='#f0f0f0', justify=tk.LEFT, wraplength=350)
            label.pack(pady=20)
            
            input_frame = tk.Frame(dialog, bg='#f0f0f0')
            input_frame.pack(pady=10)
            
            tk.Label(input_frame, text="کد 6 رقمی:", font=('Tahoma', 11), 
                   bg='#f0f0f0').pack(side=tk.LEFT, padx=5)
            
            code_var = tk.StringVar()
            code_entry = tk.Entry(input_frame, textvariable=code_var, 
                                font=('Tahoma', 12), width=10, justify='center')
            code_entry.pack(side=tk.LEFT, padx=5)
            
            result = {"code": None}
            
            def submit():
                code = code_var.get().strip()
                if code and len(code) == 6 and code.isdigit():
                    result["code"] = code
                    dialog.destroy()
                else:
                    messagebox.showerror("خطا", "لطفاً کد 6 رقمی معتبر وارد کنید")
            
            def cancel():
                result["code"] = None
                dialog.destroy()
            
            button_frame = tk.Frame(dialog, bg='#f0f0f0')
            button_frame.pack(pady=20)
            
            submit_btn = tk.Button(button_frame, text="تأیید", font=('Tahoma', 11),
                                 bg='#27ae60', fg='white', width=10, command=submit)
            submit_btn.pack(side=tk.LEFT, padx=10)
            
            cancel_btn = tk.Button(button_frame, text="انصراف", font=('Tahoma', 11),
                                 bg='#e74c3c', fg='white', width=10, command=cancel)
            cancel_btn.pack(side=tk.LEFT, padx=10)
            
            code_entry.focus_set()
            
            dialog.bind('<Return>', lambda e: submit())
            dialog.bind('<Escape>', lambda e: cancel())
            
            dialog.transient()
            dialog.grab_set()
            dialog.wait_window()
            
            return result["code"]
            
        except Exception as e:
            self.log(f"خطا در دریافت کد 2FA: {e}", "ERROR")
            return None
    
    def save_session_cookies(self):
        """ذخیره کوکی‌های session در فایل"""
        if self.driver:
            try:
                cookies = self.driver.get_cookies()
                with open('easytrader_cookies.pkl', 'wb') as f:
                    pickle.dump(cookies, f)
                self.log("کوکی‌ها در فایل ذخیره شدند", "INFO")
                return True
            except Exception as e:
                self.log(f"خطا در ذخیره کوکی‌ها: {e}", "ERROR")
                return False
        return False
    
    def load_session_cookies(self):
        """بارگذاری کوکی‌های session از فایل"""
        try:
            if not os.path.exists('easytrader_cookies.pkl'):
                return False
                
            with open('easytrader_cookies.pkl', 'rb') as f:
                cookies = pickle.load(f)
            
            if self.driver:
                self.driver.delete_all_cookies()
                
                for cookie in cookies:
                    try:
                        if 'expiry' in cookie:
                            cookie['expiry'] = int(cookie['expiry'])
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        self.log(f"خطا در اضافه کردن کوکی {cookie.get('name')}: {e}", "WARNING")
                
                self.log(f"{len(cookies)} کوکی از فایل بارگذاری شدند", "INFO")
                return True
            return False
            
        except Exception as e:
            self.log(f"خطا در بارگذاری کوکی‌ها: {e}", "WARNING")
            return False
    
    def check_cookies_valid(self):
        """بررسی معتبر بودن کوکی‌های ذخیره شده"""
        try:
            if os.path.exists('easytrader_cookies.pkl'):
                file_time = os.path.getmtime('easytrader_cookies.pkl')
                if time.time() - file_time > 43200:
                    self.log("کوکی‌های ذخیره شده منقضی شده‌اند (بیش از 12 ساعت)", "WARNING")
                    return False
                return True
            return False
        except:
            return False
    
    def setup_driver_simple(self):
        """راه‌اندازی ساده درایور بدون پیچیدگی"""
        try:
            self.log("راه‌اندازی درایور با تنظیمات ساده...", "INFO")
            
            # اول سعی می‌کنیم از undetected-chromedriver استفاده کنیم
            try:
                self.log("تلاش با undetected-chromedriver...", "INFO")
                import undetected_chromedriver as uc
                
                options = uc.ChromeOptions()
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--start-maximized")
                options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                options.add_argument("--disable-notifications")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-popup-blocking")
                
                if not os.path.exists(self.download_dir):
                    os.makedirs(self.download_dir)
                
                prefs = {
                    "download.default_directory": self.download_dir,
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "plugins.always_open_pdf_externally": True,
                    "safebrowsing.enabled": False,
                    "credentials_enable_service": False,
                    "profile.password_manager_enabled": False,
                }
                options.add_experimental_option("prefs", prefs)
                
                self.driver = uc.Chrome(
                    options=options,
                    use_subprocess=True,
                    version_main=int(self.chrome_version.split('.')[0]) if '.' in self.chrome_version else 120
                )
                
                self.log("درایور با undetected-chromedriver راه‌اندازی شد", "INFO")
                return self.driver
                
            except Exception as e:
                self.log(f"خطا در undetected-chromedriver: {e}", "WARNING")
            
            # روش دوم: استفاده از selenium ساده
            self.log("تلاش با selenium ساده...", "INFO")
            chrome_options = Options()
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            if not os.path.exists(self.download_dir):
                os.makedirs(self.download_dir)
            
            prefs = {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True,
                "safebrowsing.enabled": False,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                os.path.expanduser("~") + "\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_options.binary_location = path
                    self.log(f"کروم یافت شد: {path}", "INFO")
                    break
            
            if self.webdriver_manager_available:
                try:
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.log("درایور با webdriver-manager راه‌اندازی شد", "INFO")
                except Exception as e:
                    self.log(f"خطا در webdriver-manager: {e}", "WARNING")
                    try:
                        self.driver = webdriver.Chrome(options=chrome_options)
                        self.log("درایور با کروم سیستم راه‌اندازی شد", "INFO")
                    except Exception as e2:
                        self.log(f"خطا در راه‌اندازی درایور: {e2}", "ERROR")
                        return None
            else:
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    self.log("درایور با کروم سیستم راه‌اندازی شد", "INFO")
                except Exception as e:
                    self.log(f"خطا در راه‌اندازی درایور: {e}", "ERROR")
                    return None
            
            return self.driver
            
        except Exception as e:
            self.log(f"خطا در راه‌اندازی درایور: {e}", "ERROR")
            return None
    
    def setup_driver(self):
        """تنظیم درایور کروم"""
        if not self.selenium_available:
            self.log("Selenium در دسترس نیست", "ERROR")
            return None
        
        try:
            self.log(f"نسخه کروم سیستم: {self.chrome_version}", "INFO")
            driver = self.setup_driver_simple()
            if driver:
                return driver
            
            response = messagebox.askyesno("خطا در Chrome", 
                "ChromeDriver با مشکل مواجه شده. آیا می‌خواهید از Microsoft Edge استفاده کنید؟")
            
            if response:
                try:
                    from msedge.selenium_tools import Edge, EdgeOptions
                    
                    edge_options = EdgeOptions()
                    edge_options.use_chromium = True
                    edge_options.add_argument("--no-sandbox")
                    edge_options.add_argument("--disable-dev-shm-usage")
                    edge_options.add_argument("--window-size=1920,1080")
                    edge_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                    
                    self.driver = Edge(options=edge_options)
                    self.log("درایور Edge راه‌اندازی شد", "INFO")
                    return self.driver
                except ImportError:
                    messagebox.showinfo("نصب نیاز است", 
                        "لطفاً نصب کنید: pip install msedge-selenium-tools")
                except Exception as e:
                    self.log(f"خطا در راه‌اندازی Edge: {e}", "WARNING")
            
            return None
            
        except Exception as e:
            self.log(f"خطا در راه‌اندازی درایور: {e}", "ERROR")
            return None
    
    def wait_for_element(self, by, value, timeout=30):
        """منتظر ماندن برای وجود عنصر"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            self.log(f"عنصر پیدا نشد: {by}={value}", "WARNING")
            return None
    
    def wait_for_element_clickable(self, by, value, timeout=30):
        """منتظر ماندن برای قابل کلیک بودن عنصر"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except Exception as e:
            self.log(f"عنصر قابل کلیک نیست: {by}={value}", "WARNING")
            return None
    
    def find_element_by_multiple(self, selectors):
        """یافتن عنصر با چندین سلکتور مختلف"""
        for selector_type, selector_value in selectors:
            try:
                if selector_type == "id":
                    element = self.driver.find_element(By.ID, selector_value)
                elif selector_type == "name":
                    element = self.driver.find_element(By.NAME, selector_value)
                elif selector_type == "xpath":
                    element = self.driver.find_element(By.XPATH, selector_value)
                elif selector_type == "css":
                    element = self.driver.find_element(By.CSS_SELECTOR, selector_value)
                elif selector_type == "class":
                    element = self.driver.find_element(By.CLASS_NAME, selector_value)
                else:
                    continue
                    
                if element:
                    self.log(f"عنصر با {selector_type}={selector_value} یافت شد", "INFO")
                    return element
            except:
                continue
        return None
    
    def check_login_success(self):
        """بررسی موفقیت‌آمیز بودن لاگین با دقت بیشتر"""
        try:
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            
            success_indicators = [
                'dashboard', 'داشبورد', 'portfolio', 'پورتفو', 
                'حساب کاربری', 'account', 'سبد دارایی', 'منوی کاربری',
                'خروج از حساب', 'logout', 'sign out'
            ]
            
            failure_indicators = [
                'invalid', 'نامعتبر', 'خطا در ورود', 'نام کاربری یا رمز عبور اشتباه',
                'ورود ناموفق', 'login failed', 'error', 'خطا'
            ]
            
            for indicator in success_indicators:
                if indicator in page_source:
                    self.log(f"نشانه لاگین موفق یافت شد: {indicator}", "INFO")
                    return True
            
            for indicator in failure_indicators:
                if indicator in page_source:
                    self.log(f"نشانه لاگین ناموفق یافت شد: {indicator}", "WARNING")
                    return False
            
            if 'login' in current_url or 'ورود' in page_source:
                return False
            
            if current_url == 'https://d.easytrader.ir/' or current_url == 'https://d.easytrader.ir':
                if 'ورود' not in page_source and 'login' not in page_source:
                    return True
            
            return False
            
        except Exception as e:
            self.log(f"خطا در بررسی لاگین: {e}", "WARNING")
            return False
    
    def login_with_selenium(self, username, password):
        """ورود به ایزی تریدر با سلنیوم - نسخه بهبود یافته"""
        with self.login_lock:
            if not self.selenium_available:
                self.log("Selenium در دسترس نیست", "ERROR")
                return False
            
            try:
                if not self.driver:
                    self.driver = self.setup_driver()
                    if not self.driver:
                        return False
                
                self.log("تست اتصال به اینترنت...", "INFO")
                try:
                    self.driver.get("https://www.google.com")
                    time.sleep(2)
                    self.log("اتصال اینترنت OK", "INFO")
                except Exception as e:
                    self.log(f"مشکل در اتصال اینترنت: {e}", "WARNING")
                
                self.log("در حال بارگذاری صفحه لاگین...", "INFO")
                
                login_urls = [
                    "https://d.easytrader.ir/account/login",
                    "https://d.easytrader.ir/login",
                    "https://d.easytrader.ir/signin",
                    "https://d.easytrader.ir/"
                ]
                
                loaded = False
                for url in login_urls:
                    try:
                        self.log(f"تلاش با URL: {url}", "INFO")
                        self.driver.get(url)
                        time.sleep(5)
                        
                        page_html = self.driver.page_source.lower()
                        if 'ورود' in page_html or 'login' in page_html or 'username' in page_html or 'password' in page_html:
                            self.log(f"صفحه لاگین بارگذاری شد: {url}", "INFO")
                            loaded = True
                            break
                    except:
                        continue
                
                if not loaded:
                    self.log("نتوانستیم صفحه لاگین را بارگذاری کنیم", "ERROR")
                    return False
                
                if self.check_cookies_valid():
                    self.log("تلاش بارگذاری کوکی‌های ذخیره شده...", "INFO")
                    self.load_session_cookies()
                    self.driver.refresh()
                    time.sleep(5)
                    
                    if self.check_login_success():
                        self.log("ورود با کوکی‌های ذخیره شده موفق بود", "INFO")
                        self.is_logged_in = True
                        return True
                
                self.log("جستجوی فیلد نام کاربری...", "INFO")
                username_selectors = [
                    ("name", "username"),
                    ("name", "email"),
                    ("id", "username"),
                    ("id", "email"),
                    ("xpath", "//input[@type='text']"),
                    ("xpath", "//input[@type='email']"),
                    ("xpath", "//input[contains(@placeholder, 'نام کاربری')]"),
                    ("xpath", "//input[contains(@placeholder, 'ایمیل')]"),
                    ("xpath", "//input[contains(@id, 'username')]"),
                    ("xpath", "//input[contains(@id, 'email')]")
                ]
                
                username_field = self.find_element_by_multiple(username_selectors)
                if not username_field:
                    try:
                        screenshot_path = "login_page_debug.png"
                        self.driver.save_screenshot(screenshot_path)
                        self.log(f"اسکرین‌شات برای دیباگ ذخیره شد: {screenshot_path}", "INFO")
                    except:
                        pass
                    self.log("فیلد نام کاربری پیدا نشد", "ERROR")
                    return False
                
                username_field.clear()
                username_field.send_keys(username)
                self.log("نام کاربری وارد شد", "INFO")
                time.sleep(1)
                
                self.log("جستجوی فیلد رمز عبور...", "INFO")
                password_selectors = [
                    ("name", "password"),
                    ("id", "password"),
                    ("xpath", "//input[@type='password']"),
                    ("xpath", "//input[contains(@placeholder, 'رمز عبور')]"),
                    ("xpath", "//input[contains(@id, 'password')]")
                ]
                
                password_field = self.find_element_by_multiple(password_selectors)
                if not password_field:
                    self.log("فیلد رمز عبور پیدا نشد", "ERROR")
                    return False
                
                password_field.clear()
                password_field.send_keys(password)
                self.log("رمز عبور وارد شد", "INFO")
                time.sleep(1)
                
                self.log("جستجوی دکمه ورود...", "INFO")
                login_button_selectors = [
                    ("xpath", "//button[@type='submit']"),
                    ("xpath", "//input[@type='submit']"),
                    ("xpath", "//button[contains(text(), 'ورود')]"),
                    ("xpath", "//button[contains(text(), 'Login')]"),
                    ("css", "button[type='submit']"),
                    ("xpath", "//button[contains(@class, 'btn-login')]"),
                    ("xpath", "//button[contains(@class, 'btn-primary') and contains(text(), 'ورود')]")
                ]
                
                login_button = self.find_element_by_multiple(login_button_selectors)
                if not login_button:
                    self.log("دکمه ورود پیدا نشد", "ERROR")
                    return False
                
                self.log("کلیک روی دکمه ورود...", "INFO")
                try:
                    login_button.click()
                except:
                    self.driver.execute_script("arguments[0].click();", login_button)
                
                self.log("منتظر نتیجه لاگین...", "INFO")
                time.sleep(10)
                
                page_html = self.driver.page_source.lower()
                if 'کد امنیتی' in page_html or 'captcha' in page_html or 'کد تأیید' in page_html:
                    self.log("نیاز به کد امنیتی/CAPTCHA", "WARNING")
                    captcha_code = self.get_2fa_code_from_user()
                    if captcha_code:
                        captcha_selectors = [
                            ("name", "captcha"),
                            ("id", "captcha"),
                            ("xpath", "//input[@type='text' and contains(@placeholder, 'کد')]"),
                            ("xpath", "//input[contains(@placeholder, 'کد امنیتی')]")
                        ]
                        
                        captcha_field = self.find_element_by_multiple(captcha_selectors)
                        if captcha_field:
                            captcha_field.clear()
                            captcha_field.send_keys(captcha_code)
                            time.sleep(1)
                            
                            submit_selectors = [
                                ("xpath", "//button[@type='submit']"),
                                ("xpath", "//button[contains(text(), 'تأیید')]"),
                                ("xpath", "//button[contains(text(), 'Verify')]")
                            ]
                            
                            submit_button = self.find_element_by_multiple(submit_selectors)
                            if submit_button:
                                submit_button.click()
                                time.sleep(5)
                
                if self.check_login_success():
                    self.log("ورود موفقیت‌آمیز", "INFO")
                    self.is_logged_in = True
                    self.save_session_cookies()
                    return True
                else:
                    self.log("ورود ناموفق", "ERROR")
                    page_html = self.driver.page_source
                    if 'نام کاربری یا رمز عبور اشتباه' in page_html:
                        self.log("نام کاربری یا رمز عبور اشتباه است", "ERROR")
                    elif 'حساب کاربری قفل شده' in page_html:
                        self.log("حساب کاربری قفل شده است", "ERROR")
                    elif 'کد امنیتی' in page_html:
                        self.log("نیاز به کد امنیتی/CAPTCHA", "ERROR")
                    return False
                
            except Exception as e:
                self.log(f"خطا در ورود: {e}", "ERROR")
                return False
    
    def extract_table_manually(self, table_element):
        """استخراج دستی داده‌ها از جدول"""
        try:
            data = []
            rows = table_element.find_elements(By.TAG_NAME, "tr")
            
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    cells = row.find_elements(By.TAG_NAME, "th")
                
                row_data = [cell.text.strip() for cell in cells if cell.text.strip()]
                if row_data:
                    data.append(row_data)
            
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0] if len(data[0]) == len(data[1]) else None)
                return df
            
            return None
            
        except Exception as e:
            self.log(f"خطا در استخراج دستی جدول: {e}", "ERROR")
            return None
    
    def extract_data_directly(self):
        """استخراج مستقیم داده‌ها از صفحه"""
        try:
            self.log("تلاش برای استخراج مستقیم داده‌ها از صفحه...", "INFO")
            time.sleep(8)
            
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            
            if not tables:
                tables = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'table')]")
            
            if tables:
                self.log(f"{len(tables)} جدول/دیو با کلاس table یافت شد", "INFO")
                
                max_rows = 0
                best_table = None
                
                for i, table in enumerate(tables):
                    try:
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        if len(rows) > max_rows and len(rows) > 5:
                            max_rows = len(rows)
                            best_table = table
                    except:
                        continue
                
                if best_table:
                    self.log(f"جدول با بیشترین سطرها یافت شد: {max_rows} سطر", "INFO")
                    html_content = best_table.get_attribute('outerHTML')
                    
                    try:
                        df_list = pd.read_html(html_content)
                    except Exception as e:
                        self.log(f"خطا در خواندن جدول با pandas: {e}", "WARNING")
                        df = self.extract_table_manually(best_table)
                        if df is not None and not df.empty:
                            return df
                        else:
                            return None
                    
                    if df_list:
                        df = df_list[0]
                        self.log(f"داده‌ها از جدول استخراج شد: {df.shape}", "INFO")
                        
                        self.log("ستون‌های استخراج شده:", "INFO")
                        for col in df.columns:
                            self.log(f"  {col}", "INFO")
                        
                        return df
            
            self.log("جستجوی داده‌ها در المان‌های صفحه...", "INFO")
            data_elements = self.driver.find_elements(By.XPATH, "//td | //th | //div[contains(@class, 'cell')]")
            
            if data_elements and len(data_elements) > 20:
                data = []
                current_row = []
                
                for elem in data_elements:
                    text = elem.text.strip()
                    if text:
                        current_row.append(text)
                        
                        if len(current_row) > 10:
                            data.append(current_row)
                            current_row = []
                
                if len(data) > 2:
                    df = pd.DataFrame(data)
                    self.log(f"داده‌ها به صورت دستی استخراج شد: {df.shape}", "INFO")
                    return df
            
            self.log("نتوانستیم داده‌ها را از صفحه استخراج کنیم", "WARNING")
            return None
            
        except Exception as e:
            self.log(f"خطا در استخراج مستقیم داده‌ها: {e}", "ERROR")
            return None
    
    def download_market_data(self):
        """دانلود داده‌های بازار از ایزی تریدر - نسخه بهبود یافته"""
        if not self.selenium_available or not self.driver:
            self.log("درایور سلنیوم آماده نیست", "ERROR")
            return None
        
        if not self.is_logged_in:
            self.log("ابتدا باید وارد شوید", "ERROR")
            return None
        
        try:
            self.log("در حال رفتن به صفحه ایزی فیلتر...", "INFO")
            
            market_url = "https://d.easytrader.ir/easy-filter"
            
            self.driver.get(market_url)
            time.sleep(10)
            
            self.log("منتظر لود شدن کامل صفحه ایزی فیلتر...", "INFO")
            time.sleep(15)
            
            page_source = self.driver.page_source
            
            self.log("جستجو برای لینک‌ها و دکمه‌های دانلود...", "INFO")
            
            try:
                menu_items = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'dropdown')] | //div[contains(@class, 'dropdown')]")
                for item in menu_items:
                    try:
                        item_text = item.text.lower()
                        if 'خروجی' in item_text or 'export' in item_text or 'excel' in item_text:
                            self.log(f"عنصر منو یافت شد: {item_text}", "INFO")
                            item.click()
                            time.sleep(2)
                            
                            dropdown_items = self.driver.find_elements(By.XPATH, "//a[contains(., 'Excel')] | //button[contains(., 'Excel')]")
                            for dropdown_item in dropdown_items:
                                if dropdown_item.is_displayed():
                                    self.log("کلیک روی گزینه اکسل در منو", "INFO")
                                    dropdown_item.click()
                                    time.sleep(10)
                                    break
                            break
                    except:
                        continue
            except Exception as e:
                self.log(f"خطا در جستجوی منوها: {e}", "WARNING")
            
            files_before = set(os.listdir(self.download_dir))
            
            try:
                self.log("تلاش با کلیدهای ترکیبی Ctrl+S...", "INFO")
                actions = ActionChains(self.driver)
                actions.key_down(Keys.CONTROL).send_keys('s').key_up(Keys.CONTROL).perform()
                time.sleep(5)
            except:
                pass
            
            time.sleep(15)
            files_after = set(os.listdir(self.download_dir))
            new_files = files_after - files_before
            
            excel_files = []
            for f in new_files:
                if f.lower().endswith('.xlsx') or f.lower().endswith('.xls'):
                    file_path = os.path.join(self.download_dir, f)
                    excel_files.append((file_path, os.path.getctime(file_path)))
                    self.log(f"فایل اکسل جدید یافت شد: {f}", "INFO")
            
            if not excel_files:
                self.log("جستجوی فایل‌های اخیر...", "INFO")
                all_excel_files = []
                for f in os.listdir(self.download_dir):
                    if f.lower().endswith('.xlsx') or f.lower().endswith('.xls'):
                        file_path = os.path.join(self.download_dir, f)
                        file_time = os.path.getctime(file_path)
                        if file_time > time.time() - 600:
                            all_excel_files.append((file_path, file_time))
                
                if all_excel_files:
                    all_excel_files.sort(key=lambda x: x[1], reverse=True)
                    excel_files = [all_excel_files[0]]
                    self.log(f"آخرین فایل اکسل یافت شد: {os.path.basename(excel_files[0][0])}", "INFO")
            
            if excel_files:
                latest_file = max(excel_files, key=lambda x: x[1])[0]
                self.log(f"فایل دانلود شده: {latest_file}", "INFO")
                
                try:
                    df = pd.read_excel(latest_file)
                    self.log(f"فایل خوانده شد. {len(df)} ردیف، {len(df.columns)} ستون", "INFO")
                    
                    self.log("ستون‌های فایل:", "INFO")
                    for i, col in enumerate(df.columns):
                        self.log(f"  {i+1}. {col}", "INFO")
                    
                    df.columns = [f'ستون_{i+1}' if 'Unnamed' in str(col) else col for i, col in enumerate(df.columns)]
                    
                    self.market_data = df
                    self.last_download_time = datetime.now()
                    return df
                except Exception as e:
                    self.log(f"خطا در خواندن فایل: {e}", "ERROR")
                    return self.extract_data_directly()
            else:
                self.log("هیچ فایل اکسلی یافت نشد - تلاش برای استخراج مستقیم", "WARNING")
                return self.extract_data_directly()
                
        except Exception as e:
            self.log(f"خطا در دانلود داده بازار: {e}", "ERROR")
            return None
    
    def download_portfolio_data(self):
        """دانلود داده‌های پورتفو از ایزی تریدر"""
        if not self.selenium_available or not self.driver:
            self.log("درایور سلنیوم آماده نیست", "ERROR")
            return None
        
        if not self.is_logged_in:
            self.log("ابتدا باید وارد شوید", "ERROR")
            return None
        
        try:
            self.log("در حال رفتن به صفحه پورتفو...", "INFO")
            
            portfolio_url = "https://d.easytrader.ir/portfolio"
            
            self.driver.get(portfolio_url)
            time.sleep(10)
            
            self.log("منتظر لود شدن کامل صفحه پورتفو...", "INFO")
            time.sleep(10)
            
            files_before = set(os.listdir(self.download_dir))
            
            self.log("جستجوی دکمه خروجی اکسل...", "INFO")
            
            download_selectors = [
                ("xpath", "//button[contains(., 'خروجی اکسل')]"),
                ("xpath", "//button[contains(., 'Excel')]"),
                ("xpath", "//button[contains(., 'اکسل')]"),
                ("xpath", "//a[contains(., 'خروجی اکسل')]"),
                ("xpath", "//a[contains(., 'Excel')]"),
                ("xpath", "//a[contains(., 'اکسل')]"),
                ("xpath", "//*[contains(text(), 'خروجی') and contains(text(), 'اکسل')]"),
                ("xpath", "//button[contains(@class, 'btn')]"),
                ("xpath", "//a[contains(@class, 'btn')]")
            ]
            
            download_button = None
            for selector_type, selector_value in download_selectors:
                try:
                    if selector_type == "xpath":
                        elements = self.driver.find_elements(By.XPATH, selector_value)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                element_text = element.text.strip()
                                if element_text and ('اکسل' in element_text or 'Excel' in element_text or 'خروجی' in element_text):
                                    self.log(f"دکمه با XPath '{selector_value}' یافت شد: {element_text}", "INFO")
                                    download_button = element
                                    break
                    if download_button:
                        break
                except Exception as e:
                    continue
            
            if not download_button:
                self.log("جستجوی گسترده برای دکمه‌ها...", "INFO")
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for button in all_buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.strip()
                            if button_text and ('اکسل' in button_text or 'Excel' in button_text):
                                self.log(f"دکمه یافت شد: {button_text}", "INFO")
                                download_button = button
                                break
                    except:
                        continue
            
            if download_button:
                self.log(f"دکمه دانلود پورتفو یافت شد: {download_button.text}", "INFO")
                
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", download_button)
                except Exception as e:
                    self.log(f"خطا در کلیک: {e}", "WARNING")
                    try:
                        download_button.click()
                    except:
                        pass
                
                self.log("منتظر اتمام دانلود پورتفو...", "INFO")
                time.sleep(15)
                
                files_after = set(os.listdir(self.download_dir))
                new_files = files_after - files_before
                
                excel_files = []
                for f in new_files:
                    if f.lower().endswith('.xlsx') or f.lower().endswith('.xls'):
                        file_path = os.path.join(self.download_dir, f)
                        excel_files.append((file_path, os.path.getctime(file_path)))
                        self.log(f"فایل پورتفو یافت شد: {f}", "INFO")
                
                if not excel_files:
                    for f in os.listdir(self.download_dir):
                        if f.lower().endswith('.xlsx') or f.lower().endswith('.xls'):
                            file_path = os.path.join(self.download_dir, f)
                            if os.path.getctime(file_path) > time.time() - 300:
                                excel_files.append((file_path, os.path.getctime(file_path)))
                
                if excel_files:
                    latest_file = max(excel_files, key=lambda x: x[1])[0]
                    self.log(f"فایل پورتفو دانلود شده: {latest_file}", "INFO")
                    
                    try:
                        df = pd.read_excel(latest_file)
                        self.log(f"فایل پورتفو خوانده شد. {len(df)} ردیف", "INFO")
                        
                        self.log("ستون‌های فایل پورتفو:", "INFO")
                        for i, col in enumerate(df.columns):
                            self.log(f"  {i+1}. {col}", "INFO")
                        
                        self.portfolio_data = df
                        self.last_download_time = datetime.now()
                        return df
                    except Exception as e:
                        self.log(f"خطا در خواندن فایل پورتفو: {e}", "ERROR")
                        return None
                else:
                    self.log("هیچ فایل پورتفوی جدیدی یافت نشد", "WARNING")
                    return None
            else:
                self.log("دکمه دانلود پورتفو پیدا نشد", "WARNING")
                return None
            
        except Exception as e:
            self.log(f"خطا در دانلود پورتفو: {e}", "ERROR")
            return None
    
    def detect_field_names(self, df):
        """تشخیص خودکار نام فیلدها"""
        if df is None or df.empty:
            return {}
        
        field_map = {}
        
        patterns = {
            'symbol': ['نماد', 'symbol', 'name', 'نام', 'سهام', 'شرکت'],
            'quantity': ['تعداد', 'quantity', 'qty', 'مقدار', 'حجم'],
            'buy_price': ['قیمت خرید', 'buy_price', 'avg_price', 'میانگین خرید', 'خرید', 'قیمت میانگین'],
            'current_price': ['قیمت آخر', 'آخرین قیمت', 'current_price', 'price', 'قیمت پایانی', 'قیمت روز'],
            'current_value': ['ارزش', 'value', 'current_value', 'ارزش روز', 'ارش'],
            'profit': ['سود', 'زیان', 'profit', 'loss', 'pnl', 'سود/زیان', 'سود و زیان'],
            'eps': ['eps', 'سود هر سهم', 'سود'],
            'pe': ['p/e', 'pe', 'نسبت p/e'],
            'pb': ['p/b', 'pb', 'نسبت p/b'],
            'rsi': ['rsi', 'شاخص rsi'],
            'volume': ['حجم', 'volume', 'حجم معاملات'],
            'return_1m': ['بازدهی1ماه', 'return_1m', 'بازدهی ماه', 'بازدهی یک ماه'],
            'return_3m': ['بازدهی3ماه', 'return_3m', 'بازدهی 3ماه', 'بازدهی سه ماه'],
            'return_6m': ['بازدهی6ماه', 'return_6m', 'بازدهی 6ماه', 'بازدهی شش ماه'],
            'return_1y': ['بازدهی1سال', 'return_1y', 'بازدهی سال', 'بازدهی یک سال']
        }
        
        for field, pattern_list in patterns.items():
            for col in df.columns:
                col_str = str(col).strip().lower()
                for pattern in pattern_list:
                    if pattern.lower() in col_str:
                        field_map[field] = col
                        self.log(f"فیلد {field} -> ستون {col}", "INFO")
                        break
                if field in field_map:
                    break
        
        return field_map
    
    def get_status(self):
        """دریافت وضعیت فعلی اتصال"""
        status_text = "قطع"
        if self.is_logged_in:
            status_text = "متصل"
        
        return {
            'status': 'connected' if self.is_logged_in else 'disconnected',
            'message': status_text,
            'timestamp': datetime.now().isoformat(),
            'last_download': self.last_download_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_download_time else None
        }
    
    def start_auto_download(self, interval_minutes=5, download_market=True, download_portfolio=True):
        """شروع دانلود اتوماتیک در بازه‌های زمانی مشخص"""
        if not self.is_logged_in:
            self.log("برای شروع دانلود اتوماتیک ابتدا وارد شوید", "ERROR")
            return False
        
        self.auto_download_enabled = True
        self.auto_download_interval = interval_minutes * 60
        self.auto_download_market = download_market
        self.auto_download_portfolio = download_portfolio
        
        if self.auto_download_thread is None or not self.auto_download_thread.is_alive():
            self.auto_download_thread = threading.Thread(target=self._auto_download_loop, daemon=True)
            self.auto_download_thread.start()
            self.log(f"✅ دانلود اتوماتیک با فاصله {interval_minutes} دقیقه شروع شد", "INFO")
            return True
        
        return False
    
    def stop_auto_download(self):
        """توقف دانلود اتوماتیک"""
        self.auto_download_enabled = False
        self.log("⏹️ دانلود اتوماتیک متوقف شد", "INFO")
        return True
    
    def _auto_download_loop(self):
        """حلقه دانلود اتوماتیک"""
        while self.auto_download_enabled:
            try:
                current_time = datetime.now()
                
                if (self.last_download_time is None or 
                    (current_time - self.last_download_time).total_seconds() >= self.auto_download_interval):
                    
                    self.log("🔄 شروع دانلود اتوماتیک...", "INFO")
                    
                    if self.auto_download_market:
                        market_data = self.download_market_data()
                        if market_data is not None:
                            self.log(f"✅ داده بازار در {current_time.strftime('%H:%M:%S')} دانلود شد", "INFO")
                    
                    if self.auto_download_portfolio:
                        portfolio_data = self.download_portfolio_data()
                        if portfolio_data is not None:
                            self.log(f"✅ داده پورتفو در {current_time.strftime('%H:%M:%S')} دانلود شد", "INFO")
                    
                    self.last_download_time = current_time
                
                for _ in range(self.auto_download_interval):
                    if not self.auto_download_enabled:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.log(f"❌ خطا در دانلود اتوماتیک: {e}", "ERROR")
                time.sleep(60)
    
    def logout(self):
        """خروج از حساب"""
        self.stop_auto_download()
        
        if self.driver:
            try:
                self.driver.quit()
                self.log("مرورگر بسته شد", "INFO")
            except:
                pass
            self.driver = None
        
        self.is_logged_in = False
        self.update_status('disconnected', 'قطع شد')
        
        return True
    
    def close(self):
        """بستن کامل اتصال"""
        self.logout()
        
        try:
            import shutil
            if os.path.exists(self.user_data_dir):
                shutil.rmtree(self.user_data_dir, ignore_errors=True)
        except:
            pass

# ایجاد نمونه برای استفاده در برنامه اصلی
online = EasyTraderOnline()
# ============================================================================
# بخش ۹: ایجاد نمونه‌های اصلی
# ============================================================================

online = EasyTraderOnline()

# ============================================================================
# بخش ۱۰: کلاس مدیریت داده‌ها
# ============================================================================

class DataManager:
    """مدیریت داده‌ها با قابلیت کش"""
    
    def __init__(self):
        self.market_data = None
        self.portfolio_data = None
        self.analysis_basic = None
        self.analysis_advanced = None
        self.last_update = None
        self.session_id = str(uuid.uuid4())[:8]
        self.field_names = {}
        self.load_cached()
    
    def load_cached(self):
        """بارگذاری داده‌های کش شده"""
        cache_file = os.path.join(CACHE_DIR, f'data_{self.session_id}.pkl')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                    self.market_data = data.get('market')
                    self.portfolio_data = data.get('portfolio')
                    self.analysis_basic = data.get('basic')
                    self.analysis_advanced = data.get('advanced')
                    self.field_names = data.get('fields', {})
                    self.last_update = data.get('last_update')
                debug_log(f"داده‌های کش شده بارگذاری شد: {cache_file}")
            except Exception as e:
                debug_log(f"خطا در بارگذاری کش: {e}", "ERROR")
    
    def save_cache(self):
        """ذخیره در کش"""
        cache_file = os.path.join(CACHE_DIR, f'data_{self.session_id}.pkl')
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'market': self.market_data,
                    'portfolio': self.portfolio_data,
                    'basic': self.analysis_basic,
                    'advanced': self.analysis_advanced,
                    'fields': self.field_names,
                    'last_update': self.last_update
                }, f)
            debug_log(f"داده‌ها در کش ذخیره شد: {cache_file}")
        except Exception as e:
            debug_log(f"خطا در ذخیره کش: {e}", "ERROR")
    
    def set_market_data(self, df):
        """تنظیم داده‌های بازار"""
        self.market_data = df
        if df is not None:
            self.field_names['market'] = online.detect_field_names(df)
        self.last_update = datetime.now().isoformat()
        self.save_cache()
        debug_log(f"✅ داده بازار تنظیم شد: {len(df) if df is not None else 0} ردیف")
    
    def set_portfolio_data(self, df):
        """تنظیم داده‌های پورتفو"""
        self.portfolio_data = df
        if df is not None:
            self.field_names['portfolio'] = online.detect_field_names(df)
        self.last_update = datetime.now().isoformat()
        self.save_cache()
        debug_log(f"✅ داده پورتفو تنظیم شد: {len(df) if df is not None else 0} ردیف")
    
    def set_analysis_basic(self, df):
        """تنظیم تحلیل پایه"""
        self.analysis_basic = df
        self.save_cache()
    
    def set_analysis_advanced(self, df):
        """تنظیم تحلیل پیشرفته"""
        self.analysis_advanced = df
        self.save_cache()
    
    def clear(self):
        """پاک کردن همه داده‌ها"""
        self.market_data = None
        self.portfolio_data = None
        self.analysis_basic = None
        self.analysis_advanced = None
        self.field_names = {}
        self.last_update = None
        self.save_cache()
        debug_log("همه داده‌ها پاک شدند")
    
    def get_stats(self):
        """دریافت آمار"""
        return {
            'market': len(self.market_data) if self.market_data is not None else 0,
            'portfolio': len(self.portfolio_data) if self.portfolio_data is not None else 0,
            'basic': len(self.analysis_basic) if self.analysis_basic is not None else 0,
            'advanced': len(self.analysis_advanced) if self.analysis_advanced is not None else 0,
            'last_update': self.last_update
        }

data = DataManager()

# ============================================================================
# بخش ۱۱: توابع کمکی
# ============================================================================

def find_column(df, patterns, default=None):
    """پیدا کردن ستون براساس الگو"""
    if df is None:
        return default
    for col in df.columns:
        col_str = str(col).strip()
        col_lower = col_str.lower()
        for pattern in patterns:
            if pattern.lower() in col_lower:
                return col
    return default

def safe_float(value, default=0):
    """تبدیل امن به عدد"""
    try:
        return float(value) if pd.notna(value) else default
    except:
        return default

def safe_int(value, default=0):
    """تبدیل امن به عدد صحیح"""
    try:
        return int(float(value)) if pd.notna(value) else default
    except:
        return default

def format_number(num):
    """فرمت اعداد"""
    if num >= 1e9:
        return f"{num/1e9:.2f}B"
    elif num >= 1e6:
        return f"{num/1e6:.2f}M"
    elif num >= 1e3:
        return f"{num/1e3:.2f}K"
    else:
        return f"{num:.0f}"

# ============================================================================
# بخش ۱۲: توابع تحلیل پایه
# ============================================================================

def calculate_basic_score(row):
    """محاسبه امتیاز پایه سهم"""
    s = settings.settings
    weights = s['weights']
    score = 0
    
    # EPS
    eps = None
    for col in ['EPS', 'eps', 'سود هر سهم']:
        if col in row and pd.notna(row[col]):
            eps = safe_float(row[col])
            break
    
    eps_s = s['eps_thresholds']
    if eps is not None:
        if eps > eps_s['excellent']:
            score += eps_s['scores']['excellent'] * weights['eps_weight']
        elif eps > eps_s['very_good']:
            score += eps_s['scores']['very_good'] * weights['eps_weight']
        elif eps > eps_s['good']:
            score += eps_s['scores']['good'] * weights['eps_weight']
        elif eps > eps_s['average']:
            score += eps_s['scores']['average'] * weights['eps_weight']
        elif eps > eps_s['below_average']:
            score += eps_s['scores']['below_average'] * weights['eps_weight']
        elif eps > eps_s['low']:
            score += eps_s['scores']['low'] * weights['eps_weight']
        elif eps > 0:
            score += eps_s['scores']['positive'] * weights['eps_weight']
    else:
        score += eps_s['scores']['default'] * weights['eps_weight']
    
    # P/B
    pb = None
    for col in ['P/B', 'pb', 'PB', 'نسبت P/B']:
        if col in row and pd.notna(row[col]):
            pb = safe_float(row[col])
            break
    
    pb_s = s['pb_thresholds']
    if pb is not None and pb > 0:
        if pb <= pb_s['excellent']:
            score += pb_s['scores']['excellent'] * weights['pb_weight']
        elif pb <= pb_s['very_good']:
            score += pb_s['scores']['very_good'] * weights['pb_weight']
        elif pb <= pb_s['good']:
            score += pb_s['scores']['good'] * weights['pb_weight']
        elif pb <= pb_s['average']:
            score += pb_s['scores']['average'] * weights['pb_weight']
        else:
            score += pb_s['scores']['poor'] * weights['pb_weight']
    
    # رشد EPS
    growth = None
    for col in ['رشد EPS', 'eps_growth', 'EPS Growth']:
        if col in row and pd.notna(row[col]):
            growth = safe_float(row[col])
            break
    
    g_s = s['eps_growth_thresholds']
    if growth is not None:
        if growth > g_s['excellent']:
            score += g_s['scores']['excellent'] * weights['eps_growth_weight']
        elif growth > g_s['very_good']:
            score += g_s['scores']['very_good'] * weights['eps_growth_weight']
        elif growth > g_s['good']:
            score += g_s['scores']['good'] * weights['eps_growth_weight']
        elif growth > g_s['average']:
            score += g_s['scores']['average'] * weights['eps_growth_weight']
        elif growth > g_s['poor']:
            score += g_s['scores']['poor'] * weights['eps_growth_weight']
        else:
            score += g_s['scores']['very_poor'] * weights['eps_growth_weight']
    
    # P/E
    pe = None
    for col in ['P/E', 'pe', 'PE', 'نسبت P/E']:
        if col in row and pd.notna(row[col]):
            pe = safe_float(row[col])
            break
    
    pe_s = s['pe_thresholds']
    if pe is not None and pe > 0:
        if pe <= pe_s['excellent']:
            score += pe_s['scores']['excellent'] * weights['pe_weight']
        elif pe <= pe_s['very_good']:
            score += pe_s['scores']['very_good'] * weights['pe_weight']
        elif pe <= pe_s['good']:
            score += pe_s['scores']['good'] * weights['pe_weight']
        else:
            score += pe_s['scores']['poor'] * weights['pe_weight']
    
    # RSI
    rsi = None
    for col in ['RSI', 'rsi', 'شاخص RSI']:
        if col in row and pd.notna(row[col]):
            rsi = safe_float(row[col])
            break
    
    rsi_s = s['rsi_thresholds']
    if rsi is not None:
        if rsi < rsi_s['oversold_extreme']:
            score += rsi_s['scores']['oversold_extreme'] * weights['rsi_weight']
        elif rsi < rsi_s['oversold']:
            score += rsi_s['scores']['oversold'] * weights['rsi_weight']
        elif rsi < rsi_s['overbought_extreme']:
            score += rsi_s['scores']['neutral_low'] * weights['rsi_weight']
        elif rsi < rsi_s['overbought']:
            score += rsi_s['scores']['neutral_high'] * weights['rsi_weight']
        else:
            score += rsi_s['scores']['overbought'] * weights['rsi_weight']
    
    # حجم
    volume = None
    for col in ['حجم', 'volume', 'حجم معاملات']:
        if col in row and pd.notna(row[col]):
            volume = safe_float(row[col])
            break
    
    vol_s = s['volume_thresholds']
    if volume is not None:
        if volume > vol_s['excellent']:
            score += vol_s['scores']['excellent'] * weights['volume_weight']
        elif volume > vol_s['very_good']:
            score += vol_s['scores']['very_good'] * weights['volume_weight']
        elif volume > vol_s['good']:
            score += vol_s['scores']['good'] * weights['volume_weight']
        elif volume > vol_s['average']:
            score += vol_s['scores']['average'] * weights['volume_weight']
    
    return max(0, min(100, round(score, 2)))

def get_status_text(score):
    """دریافت متن وضعیت"""
    thresholds = settings.settings['status_thresholds']
    
    if score >= thresholds['excellent']:
        return "🌟🌟 عالی", "success"
    elif score >= thresholds['very_good']:
        return "⭐️⭐️ خیلی خوب", "info"
    elif score >= thresholds['good']:
        return "⭐️ خوب", "warning"
    elif score >= thresholds['average']:
        return "⚠️ متوسط", "warning"
    elif score >= thresholds['acceptable']:
        return "📊 قابل قبول", "secondary"
    else:
        return "❌ ضعیف", "danger"

def get_key_points(row):
    """استخراج نکات کلیدی"""
    points = []
    
    try:
        # EPS
        for col in ['EPS', 'eps']:
            if col in row and pd.notna(row[col]):
                eps = safe_float(row[col])
                if eps > 2000:
                    points.append("EPS عالی")
                elif eps > 1000:
                    points.append("EPS خیلی خوب")
                elif eps > 500:
                    points.append("EPS خوب")
                elif eps > 200:
                    points.append("EPS مناسب")
                break
        
        # P/B
        for col in ['P/B', 'pb']:
            if col in row and pd.notna(row[col]):
                pb = safe_float(row[col])
                if 0 < pb < 0.8:
                    points.append("ارزش ذاتی بالا")
                elif pb < 1.2:
                    points.append("P/B منطقی")
                break
        
        # P/E
        for col in ['P/E', 'pe']:
            if col in row and pd.notna(row[col]):
                pe = safe_float(row[col])
                if pe < 5:
                    points.append("P/E بسیار جذاب")
                elif pe < 8:
                    points.append("P/E جذاب")
                elif pe < 12:
                    points.append("P/E مناسب")
                break
        
        # RSI
        for col in ['RSI', 'rsi']:
            if col in row and pd.notna(row[col]):
                rsi = safe_float(row[col])
                if rsi < 20:
                    points.append("اشباع فروش شدید")
                elif rsi < 30:
                    points.append("اشباع فروش")
                elif rsi > 80:
                    points.append("اشباع خرید شدید")
                elif rsi > 70:
                    points.append("اشباع خرید")
                break
        
        # حجم
        for col in ['حجم', 'volume']:
            if col in row and pd.notna(row[col]):
                volume = safe_float(row[col])
                if volume > 10000000:
                    points.append("نقدشوندگی عالی")
                elif volume > 5000000:
                    points.append("نقدشوندگی خوب")
                elif volume > 1000000:
                    points.append("نقدشوندگی مناسب")
                break
    
    except:
        pass
    
    return "، ".join(points[:5]) if points else "بدون نکته خاص"

def apply_filters(df):
    """اعمال فیلترها"""
    filters = settings.settings['filters']
    filtered = df.copy()
    
    try:
        # EPS
        eps_col = find_column(df, ['eps', 'سود'])
        if eps_col:
            filtered[eps_col] = pd.to_numeric(filtered[eps_col], errors='coerce')
            filtered = filtered[filtered[eps_col] > 0]
            filtered = filtered[filtered[eps_col] >= filters['min_eps']]
        
        # P/B
        pb_col = find_column(df, ['p/b', 'pb', 'نسبت p/b'])
        if pb_col:
            filtered[pb_col] = pd.to_numeric(filtered[pb_col], errors='coerce')
            filtered = filtered[(filtered[pb_col] > 0) & (filtered[pb_col] <= filters['max_pb'])]
        
        # P/E
        pe_col = find_column(df, ['p/e', 'pe', 'نسبت p/e'])
        if pe_col:
            filtered[pe_col] = pd.to_numeric(filtered[pe_col], errors='coerce')
            filtered = filtered[(filtered[pe_col] > 0) & (filtered[pe_col] <= filters['max_pe'])]
        
        # حجم
        vol_col = find_column(df, ['حجم', 'volume'])
        if vol_col:
            filtered[vol_col] = pd.to_numeric(filtered[vol_col], errors='coerce')
            filtered = filtered[filtered[vol_col] >= filters['min_volume']]
        
        # RSI
        rsi_col = find_column(df, ['rsi'])
        if rsi_col:
            filtered[rsi_col] = pd.to_numeric(filtered[rsi_col], errors='coerce')
            filtered = filtered[
                (filtered[rsi_col] >= filters['rsi_min']) & 
                (filtered[rsi_col] <= filters['rsi_max'])
            ]
        
        # بازدهی ۱ماه
        ret_col = find_column(df, ['بازدهی', 'return'])
        if ret_col:
            filtered[ret_col] = pd.to_numeric(filtered[ret_col], errors='coerce')
            filtered = filtered[filtered[ret_col] <= filters['max_1month_return']]
        
        # قیمت
        price_col = find_column(df, ['قیمت', 'price', 'آخرین قیمت'])
        if price_col:
            filtered[price_col] = pd.to_numeric(filtered[price_col], errors='coerce')
            filtered = filtered[
                (filtered[price_col] >= filters['min_price']) & 
                (filtered[price_col] <= filters['max_price'])
            ]
        
        # حذف تکراری
        symbol_col = find_column(df, ['نماد', 'symbol'])
        if symbol_col:
            filtered = filtered.drop_duplicates(subset=[symbol_col])
            filtered = filtered.dropna(subset=[symbol_col])
    
    except Exception as e:
        debug_log(f"خطا در فیلتر: {e}", "ERROR")
    
    return filtered

def analyze_basic_stocks(df, budget=100000000, top_n=15):
    """تحلیل پایه سهام"""
    try:
        filtered = apply_filters(df)
        
        if len(filtered) == 0:
            return None
        
        filtered['امتیاز'] = filtered.apply(lambda r: calculate_basic_score(r), axis=1)
        filtered = filtered.sort_values('امتیاز', ascending=False)
        
        top_stocks = filtered.head(min(top_n, len(filtered))).copy()
        
        validation = settings.settings['validation']
        qualified = top_stocks[top_stocks['امتیاز'] >= validation['min_final_score']]
        
        if len(qualified) == 0:
            return None
        
        if budget > 0:
            total_score = qualified['امتیاز'].sum()
            
            if total_score > 0:
                qualified['سهم بودجه'] = (qualified['امتیاز'] / total_score) * budget
                
                price_col = find_column(qualified, ['قیمت', 'price', 'آخرین قیمت'])
                if price_col:
                    qualified['تعداد سهم'] = (qualified['سهم بودجه'] / qualified[price_col]).astype(int)
                    qualified['تعداد سهم'] = qualified['تعداد سهم'].apply(lambda x: max(x, 1))
                    qualified['ارزش خرید'] = qualified['تعداد سهم'] * qualified[price_col]
        
        # اضافه کردن ستون‌های اضافی
        qualified['وضعیت'] = qualified['امتیاز'].apply(lambda x: get_status_text(x)[0])
        qualified['نکات'] = qualified.apply(lambda r: get_key_points(r), axis=1)
        
        # انتخاب ستون‌های مناسب
        symbol_col = find_column(qualified, ['نماد', 'symbol'])
        price_col = find_column(qualified, ['قیمت', 'price', 'آخرین قیمت'])
        eps_col = find_column(qualified, ['eps', 'سود'])
        pe_col = find_column(qualified, ['p/e', 'pe'])
        pb_col = find_column(qualified, ['p/b', 'pb'])
        rsi_col = find_column(qualified, ['rsi'])
        ret_col = find_column(qualified, ['بازدهی', 'return'])
        
        result_cols = {
            'نماد': symbol_col,
            'قیمت': price_col,
            'EPS': eps_col,
            'P/E': pe_col,
            'P/B': pb_col,
            'RSI': rsi_col,
            'بازدهی_1ماه': ret_col,
            'امتیاز': 'امتیاز',
            'وضعیت': 'وضعیت',
            'نکات': 'نکات'
        }
        
        result = pd.DataFrame()
        for new_name, col_name in result_cols.items():
            if col_name and col_name in qualified.columns:
                result[new_name] = qualified[col_name]
        
        return result
        
    except Exception as e:
        debug_log(f"خطا در تحلیل پایه: {e}", "ERROR")
        traceback.print_exc()
        return None

# ============================================================================
# بخش ۱۳: توابع تحلیل پیشرفته (۷ روش)
# ============================================================================

def analyze_bubble(row):
    """تحلیل حباب"""
    result = {
        'امتیاز': 50,
        'سطح_خطر': 'متوسط',
        'هشدارها': []
    }
    
    try:
        pe = None
        for col in ['P/E', 'pe']:
            if col in row and pd.notna(row[col]):
                pe = safe_float(row[col])
                break
        
        pb = None
        for col in ['P/B', 'pb']:
            if col in row and pd.notna(row[col]):
                pb = safe_float(row[col])
                break
        
        ret_1m = None
        for col in ['بازدهی1ماه', 'return_1m', 'بازدهی ماه']:
            if col in row and pd.notna(row[col]):
                ret_1m = safe_float(row[col])
                break
        
        ret_3m = None
        for col in ['بازدهی3ماه', 'return_3m', 'بازدهی 3ماه']:
            if col in row and pd.notna(row[col]):
                ret_3m = safe_float(row[col])
                break
        
        volume = None
        for col in ['حجم', 'volume']:
            if col in row and pd.notna(row[col]):
                volume = safe_float(row[col])
                break
        
        b = settings.settings['bubble']
        
        pe_score = 0
        if pe is not None and pe > 0:
            if pe > b['pe_high']:
                pe_score = 10
                result['هشدارها'].append("P/E بسیار بالا")
            else:
                pe_score = max(0, 10 - pe / 3)
        
        pb_score = 0
        if pb is not None and pb > 0:
            if pb > b['pb_very_high']:
                pb_score = 10
                result['هشدارها'].append("P/B بسیار بالا")
            elif pb > b['pb_high']:
                pb_score = 7
            elif pb > b['pb_medium']:
                pb_score = 4
            elif pb > b['pb_low']:
                pb_score = 2
            else:
                pb_score = 1
        
        growth_score = 0
        if ret_1m is not None:
            if ret_1m > b['return_1m_very_high']:
                growth_score += 5
                result['هشدارها'].append("رشد بیش از 30% در یک ماه")
            elif ret_1m > b['return_1m_high']:
                growth_score += 3
            elif ret_1m > b['return_1m_medium']:
                growth_score += 1
        
        if ret_3m is not None:
            if ret_3m > b['return_3m_very_high']:
                growth_score += 5
                result['هشدارها'].append("رشد بیش از 80% در سه ماه")
            elif ret_3m > b['return_3m_high']:
                growth_score += 3
            elif ret_3m > b['return_3m_medium']:
                growth_score += 1
        
        volume_score = 0
        if volume is not None and volume > 0:
            avg_vol = volume  # فرض
            if volume / avg_vol > b['volume_ratio_very_high']:
                volume_score = 5
                result['هشدارها'].append("حجم معاملات 3 برابر میانگین")
            elif volume / avg_vol > b['volume_ratio_high']:
                volume_score = 3
            elif volume / avg_vol > b['volume_ratio_medium']:
                volume_score = 1
        
        bubble_score = pe_score * 0.3 + pb_score * 0.3 + growth_score * 0.25 + volume_score * 0.15
        final_score = max(0, 100 - bubble_score * 10)
        
        result['امتیاز'] = round(final_score, 2)
        
        if bubble_score < 3:
            result['سطح_خطر'] = 'پایین'
        elif bubble_score < 5:
            result['سطح_خطر'] = 'متوسط'
        elif bubble_score < 7:
            result['سطح_خطر'] = 'بالا'
        else:
            result['سطح_خطر'] = 'بسیار بالا'
    
    except:
        pass
    
    return result

def analyze_intrinsic_value(row):
    """تحلیل ارزش ذاتی"""
    result = {
        'امتیاز': 50,
        'نسبت_قیمت_به_ارزش': 1.0,
        'توصیه': 'نگهداری'
    }
    
    try:
        eps = None
        for col in ['EPS', 'eps']:
            if col in row and pd.notna(row[col]):
                eps = safe_float(row[col])
                break
        
        price = None
        for col in ['قیمت', 'price', 'آخرین قیمت']:
            if col in row and pd.notna(row[col]):
                price = safe_float(row[col])
                break
        
        pb = None
        for col in ['P/B', 'pb']:
            if col in row and pd.notna(row[col]):
                pb = safe_float(row[col])
                break
        
        if eps is None or eps <= 0 or price is None:
            return result
        
        iv = settings.settings['intrinsic_value']
        
        pe_value = eps * iv['pe_multiplier']
        
        pb_value = 0
        if pb is not None and pb > 0:
            pb_value = price / pb * iv['pb_multiplier']
        
        graham_value = eps * (iv['graham_base'] + iv['graham_growth'] * 5)
        
        ddm_value = eps * iv['dividend_payout'] / iv['discount_rate']
        
        values = [v for v in [pe_value, pb_value, graham_value, ddm_value] if v > 0]
        if values:
            avg_intrinsic = sum(values) / len(values)
        else:
            avg_intrinsic = price * 0.8
        
        ratio = price / avg_intrinsic if avg_intrinsic > 0 else 1
        result['نسبت_قیمت_به_ارزش'] = round(ratio, 2)
        
        thresholds = iv['thresholds']
        scores = iv.get('scores', {
            'strong_buy': 100,
            'buy': 90,
            'cautious_buy': 75,
            'hold': 60,
            'cautious_sell': 40,
            'sell': 25,
            'strong_sell': 10
        })
        
        if ratio < thresholds['strong_buy']:
            result['توصیه'] = 'خرید قوی'
            result['امتیاز'] = scores['strong_buy']
        elif ratio < thresholds['buy']:
            result['توصیه'] = 'خرید'
            result['امتیاز'] = scores['buy']
        elif ratio < thresholds['cautious_buy']:
            result['توصیه'] = 'خرید محتاطانه'
            result['امتیاز'] = scores['cautious_buy']
        elif ratio < thresholds['hold']:
            result['توصیه'] = 'نگهداری'
            result['امتیاز'] = scores['hold']
        elif ratio < thresholds['cautious_sell']:
            result['توصیه'] = 'فروش محتاطانه'
            result['امتیاز'] = scores['cautious_sell']
        elif ratio < thresholds['sell']:
            result['توصیه'] = 'فروش'
            result['امتیاز'] = scores['sell']
        else:
            result['توصیه'] = 'فروش قوی'
            result['امتیاز'] = scores['strong_sell']
    
    except:
        pass
    
    return result

def analyze_tape_reading(row):
    """تحلیل تابلوخوانی"""
    result = {
        'امتیاز': 50,
        'روند': 'خنثی',
        'قدرت': 0
    }
    
    try:
        buy_real = None
        for col in ['خرید حقیقی', 'buy_real']:
            if col in row and pd.notna(row[col]):
                buy_real = safe_float(row[col])
                break
        
        sell_real = None
        for col in ['فروش حقیقی', 'sell_real']:
            if col in row and pd.notna(row[col]):
                sell_real = safe_float(row[col])
                break
        
        if buy_real is None:
            buy_real = 50
        if sell_real is None:
            sell_real = 50
        
        net = buy_real - sell_real
        
        volume = None
        for col in ['حجم', 'volume']:
            if col in row and pd.notna(row[col]):
                volume = safe_float(row[col])
                break
        
        value = None
        for col in ['ارزش', 'value']:
            if col in row and pd.notna(row[col]):
                value = safe_float(row[col])
                break
        
        t = settings.settings['tape_reading']
        
        power = net / 10 + (volume / 1e6 if volume else 0) / 10
        power = max(-10, min(10, power))
        
        result['قدرت'] = round(power, 2)
        result['امتیاز'] = round(t['base_score'] + power * t['score_multiplier'], 2)
        result['امتیاز'] = max(0, min(100, result['امتیاز']))
        
        if power > t['power_index_thresholds']['very_bullish']:
            result['روند'] = 'صعودی قوی'
        elif power > t['power_index_thresholds']['bullish']:
            result['روند'] = 'صعودی'
        elif power > t['power_index_thresholds']['bearish']:
            result['روند'] = 'خنثی'
        elif power > t['power_index_thresholds']['very_bearish']:
            result['روند'] = 'نزولی'
        else:
            result['روند'] = 'نزولی قوی'
    
    except:
        pass
    
    return result

def analyze_risk(row):
    """تحلیل ریسک"""
    result = {
        'امتیاز': 50,
        'سطح_ریسک': 'متوسط',
        'عوامل': []
    }
    
    try:
        beta = None
        for col in ['بتا', 'beta']:
            if col in row and pd.notna(row[col]):
                beta = safe_float(row[col])
                break
        
        volume = None
        for col in ['حجم', 'volume']:
            if col in row and pd.notna(row[col]):
                volume = safe_float(row[col])
                break
        
        rsi = None
        for col in ['RSI', 'rsi']:
            if col in row and pd.notna(row[col]):
                rsi = safe_float(row[col])
                break
        
        pb = None
        for col in ['P/B', 'pb']:
            if col in row and pd.notna(row[col]):
                pb = safe_float(row[col])
                break
        
        eps = None
        for col in ['EPS', 'eps']:
            if col in row and pd.notna(row[col]):
                eps = safe_float(row[col])
                break
        
        r = settings.settings['risk']
        
        beta_risk = 0
        if beta is not None:
            if beta > r['beta_thresholds']['very_high']:
                beta_risk = 10
                result['عوامل'].append("ریسک سیستماتیک بالا")
            elif beta > r['beta_thresholds']['high']:
                beta_risk = 7
            elif beta > r['beta_thresholds']['medium']:
                beta_risk = 4
            elif beta > r['beta_thresholds']['low']:
                beta_risk = 2
            else:
                beta_risk = 1
        
        liq_risk = 0
        if volume is not None:
            if volume < r['volume_thresholds']['very_low']:
                liq_risk = 10
                result['عوامل'].append("نقدشوندگی بسیار پایین")
            elif volume < r['volume_thresholds']['low']:
                liq_risk = 7
            elif volume < r['volume_thresholds']['medium']:
                liq_risk = 4
            elif volume < r['volume_thresholds']['high']:
                liq_risk = 2
            else:
                liq_risk = 1
        
        rsi_risk = 0
        if rsi is not None:
            if rsi > 80 or rsi < 20:
                rsi_risk = 8
            elif rsi > 70 or rsi < 30:
                rsi_risk = 5
            elif rsi > 60 or rsi < 40:
                rsi_risk = 3
            else:
                rsi_risk = 1
        
        pb_risk = 0
        if pb is not None:
            if pb > 5:
                pb_risk = 10
                result['عوامل'].append("ارزش‌گذاری بسیار گران")
            elif pb > 3:
                pb_risk = 7
            elif pb > 2:
                pb_risk = 4
            else:
                pb_risk = 1
        
        eps_risk = 0
        if eps is not None:
            if eps <= 0:
                eps_risk = 10
                result['عوامل'].append("سودآوری منفی")
            elif eps < 100:
                eps_risk = 5
                result['عوامل'].append("سودآوری پایین")
            else:
                eps_risk = 1
        
        total_risk = (beta_risk + liq_risk + rsi_risk + pb_risk + eps_risk) / 5
        result['امتیاز'] = round(100 - total_risk * 8, 2)
        result['امتیاز'] = max(0, min(100, result['امتیاز']))
        
        if total_risk < 3:
            result['سطح_ریسک'] = 'پایین'
        elif total_risk < 5:
            result['سطح_ریسک'] = 'متوسط'
        elif total_risk < 7:
            result['سطح_ریسک'] = 'بالا'
        else:
            result['سطح_ریسک'] = 'بسیار بالا'
    
    except:
        pass
    
    return result

def analyze_performance(row):
    """تحلیل عملکرد"""
    result = {
        'امتیاز': 50,
        'روند': 'خنثی'
    }
    
    try:
        ret_1m = None
        for col in ['بازدهی1ماه', 'return_1m']:
            if col in row and pd.notna(row[col]):
                ret_1m = safe_float(row[col])
                break
        
        ret_3m = None
        for col in ['بازدهی3ماه', 'return_3m']:
            if col in row and pd.notna(row[col]):
                ret_3m = safe_float(row[col])
                break
        
        ret_6m = None
        for col in ['بازدهی6ماه', 'return_6m']:
            if col in row and pd.notna(row[col]):
                ret_6m = safe_float(row[col])
                break
        
        ret_1y = None
        for col in ['بازدهی1سال', 'return_1y']:
            if col in row and pd.notna(row[col]):
                ret_1y = safe_float(row[col])
                break
        
        if ret_1m is None:
            ret_1m = 0
        if ret_3m is None:
            ret_3m = 0
        if ret_6m is None:
            ret_6m = 0
        if ret_1y is None:
            ret_1y = 0
        
        perf_score = (ret_1m * 0.3 + ret_3m * 0.3 + ret_6m * 0.2 + ret_1y * 0.2)
        perf_score = max(-20, min(20, perf_score))
        
        p = settings.settings['performance']
        result['امتیاز'] = round(p['base_score'] + perf_score * p['score_multiplier'], 2)
        result['امتیاز'] = max(0, min(100, result['امتیاز']))
        
        if perf_score > 10:
            result['روند'] = 'صعودی قوی'
        elif perf_score > 5:
            result['روند'] = 'صعودی'
        elif perf_score > -5:
            result['روند'] = 'خنثی'
        elif perf_score > -10:
            result['روند'] = 'نزولی'
        else:
            result['روند'] = 'نزولی قوی'
    
    except:
        pass
    
    return result

def analyze_technical(row):
    """تحلیل تکنیکال"""
    result = {
        'امتیاز': 50,
        'سیگنال': 'خنثی'
    }
    
    try:
        rsi = None
        for col in ['RSI', 'rsi']:
            if col in row and pd.notna(row[col]):
                rsi = safe_float(row[col])
                break
        
        if rsi is None:
            rsi = 50
        
        t = settings.settings['technical']
        
        if rsi < t['rsi_thresholds']['oversold']:
            result['سیگنال'] = 'خرید'
            rsi_score = 100
        elif rsi > t['rsi_thresholds']['overbought']:
            result['سیگنال'] = 'فروش'
            rsi_score = 0
        else:
            result['سیگنال'] = 'خنثی'
            rsi_score = 50
        
        result['امتیاز'] = round(t['base_score'] + (rsi_score - 50) * t['score_multiplier'] / 10, 2)
        result['امتیاز'] = max(0, min(100, result['امتیاز']))
    
    except:
        pass
    
    return result

def analyze_advanced_stocks(df):
    """تحلیل پیشرفته با ۷ روش"""
    try:
        filtered = apply_filters(df)
        
        if len(filtered) == 0:
            return None
        
        results = []
        
        for idx, row in filtered.iterrows():
            try:
                symbol = None
                for col in ['نماد', 'symbol']:
                    if col in row:
                        symbol = row[col]
                        break
                if symbol is None:
                    symbol = f"سهم_{idx}"
                
                bubble = analyze_bubble(row)
                intrinsic = analyze_intrinsic_value(row)
                tape = analyze_tape_reading(row)
                risk = analyze_risk(row)
                perf = analyze_performance(row)
                tech = analyze_technical(row)
                
                # امتیاز ترکیبی
                composite = (
                    bubble['امتیاز'] * 0.15 +
                    intrinsic['امتیاز'] * 0.20 +
                    tape['امتیاز'] * 0.15 +
                    risk['امتیاز'] * 0.15 +
                    perf['امتیاز'] * 0.15 +
                    tech['امتیاز'] * 0.20
                )
                
                status, _ = get_status_text(composite)
                
                result = {
                    'نماد': symbol,
                    'امتیاز_نهایی': round(composite, 2),
                    'وضعیت': status,
                    'امتیاز_حباب': bubble['امتیاز'],
                    'امتیاز_ارزش_ذاتی': intrinsic['امتیاز'],
                    'امتیاز_تابلوخوانی': tape['امتیاز'],
                    'امتیاز_ریسک': risk['امتیاز'],
                    'امتیاز_عملکرد': perf['امتیاز'],
                    'امتیاز_تکنیکال': tech['امتیاز'],
                }
                
                # اضافه کردن داده‌های پایه
                price_col = find_column(filtered, ['قیمت', 'price', 'آخرین قیمت'])
                if price_col and price_col in row:
                    result['قیمت'] = safe_float(row[price_col])
                
                eps_col = find_column(filtered, ['eps', 'سود'])
                if eps_col and eps_col in row:
                    result['EPS'] = safe_float(row[eps_col])
                
                pe_col = find_column(filtered, ['p/e', 'pe'])
                if pe_col and pe_col in row:
                    result['P/E'] = safe_float(row[pe_col])
                
                pb_col = find_column(filtered, ['p/b', 'pb'])
                if pb_col and pb_col in row:
                    result['P/B'] = safe_float(row[pb_col])
                
                results.append(result)
                
            except Exception as e:
                continue
        
        if results:
            result_df = pd.DataFrame(results)
            result_df = result_df.sort_values('امتیاز_نهایی', ascending=False).reset_index(drop=True)
            return result_df
        else:
            return None
            
    except Exception as e:
        debug_log(f"خطا در تحلیل پیشرفته: {e}", "ERROR")
        traceback.print_exc()
        return None

# ============================================================================
# بخش ۱۴: تحلیل پورتفو
# ============================================================================

def analyze_portfolio(portfolio_df, market_df=None):
    """تحلیل پورتفو با محاسبه صحیح سود/زیان بر اساس میانگین وزنی قیمت خرید"""
    if portfolio_df is None or portfolio_df.empty:
        return {
            'portfolio_value': 0,
            'total_profit_loss': 0,
            'profit_loss_percent': 0,
            'sell_alerts': [],
            'buy_recommendations': [],
            'good_performers': [],
            'poor_performers': [],
            'stock_details': {},
            'sold_stocks': [],
            'diversification_score': 0,
            'portfolio_risk_level': 'نامشخص',
            'profit_count': 0,
            'loss_count': 0
        }
    
    p = settings.settings['portfolio']
    
    analysis = {
        'portfolio_value': 0,
        'total_profit_loss': 0,
        'profit_loss_percent': 0,
        'sell_alerts': [],
        'buy_recommendations': [],
        'good_performers': [],
        'poor_performers': [],
        'stock_details': {},
        'sold_stocks': [],
        'diversification_score': 0,
        'portfolio_risk_level': 'نامشخص',
        'profit_count': 0,
        'loss_count': 0
    }
    
    try:
        df = portfolio_df.copy()
        
        # شناسایی ستون‌ها با الگوهای مختلف
        symbol_col = find_column(df, ['نماد', 'symbol', 'نام سهام', 'name'])
        quantity_col = find_column(df, ['تعداد', 'quantity', 'مقدار', 'qty'])
        buy_price_col = find_column(df, ['قیمت خرید', 'buy_price', 'avg_price', 'میانگین خرید', 'قیمت خرید میانگین'])
        current_price_col = find_column(df, ['قیمت آخر', 'آخرین قیمت', 'current_price', 'price', 'قیمت پایانی', 'قیمت روز'])
        current_value_col = find_column(df, ['ارزش', 'value', 'current_value', 'ارزش روز', 'ارش'])
        profit_col = find_column(df, ['سود', 'زیان', 'profit', 'loss', 'pnl', 'سود/زیان', 'سود و زیان'])
        
        debug_log(f"ستون‌های شناسایی شده: نماد={symbol_col}, تعداد={quantity_col}, قیمت خرید={buy_price_col}")
        
        if not symbol_col:
            debug_log("⚠️ ستون نماد پیدا نشد!")
            return analysis
        
        total_value = 0
        total_cost = 0
        profit_count = 0
        loss_count = 0
        
        # گروه‌بندی بر اساس نماد برای محاسبه میانگین وزنی
        if symbol_col in df.columns:
            symbol_groups = df.groupby(symbol_col)
        else:
            debug_log("⚠️ خطا در گروه‌بندی")
            return analysis
        
        for symbol, group in symbol_groups:
            try:
                symbol = str(symbol)
                
                # محاسبه میانگین وزنی قیمت خرید
                total_quantity = 0
                total_buy_value = 0
                total_current_value = 0
                total_profit = 0
                
                for idx, row in group.iterrows():
                    quantity = safe_float(row[quantity_col]) if quantity_col else 0
                    buy_price = safe_float(row[buy_price_col]) if buy_price_col else 0
                    current_price = safe_float(row[current_price_col]) if current_price_col else 0
                    current_value = safe_float(row[current_value_col]) if current_value_col else 0
                    profit = safe_float(row[profit_col]) if profit_col else 0
                    
                    if quantity < 0:  # سهام فروخته شده
                        sold_item = {
                            'symbol': symbol,
                            'quantity': int(abs(quantity)),
                            'avg_buy_price': round(buy_price, 0),
                            'sell_price': round(current_price, 0),
                            'profit_loss': round(profit, 0),
                            'profit_loss_percent': round((profit / (abs(quantity) * buy_price)) * 100 if buy_price > 0 else 0, 2)
                        }
                        analysis['sold_stocks'].append(sold_item)
                        analysis['total_profit_loss'] += profit
                        
                        if profit > 0:
                            profit_count += 1
                        elif profit < 0:
                            loss_count += 1
                    else:
                        if current_value == 0 and quantity > 0 and current_price > 0:
                            current_value = quantity * current_price
                        
                        total_quantity += quantity
                        total_buy_value += quantity * buy_price
                        total_current_value += current_value
                        total_profit += profit
                
                if total_quantity > 0 and total_buy_value > 0:
                    avg_buy_price = total_buy_value / total_quantity
                    current_price_avg = total_current_value / total_quantity if total_current_value > 0 and total_quantity > 0 else 0
                    
                    total_value += total_current_value
                    total_cost += total_buy_value
                    
                    profit_loss = total_current_value - total_buy_value
                    profit_loss_percent = (profit_loss / total_buy_value) * 100 if total_buy_value > 0 else 0
                    
                    analysis['total_profit_loss'] += profit_loss
                    
                    if profit_loss > 0:
                        profit_count += 1
                    elif profit_loss < 0:
                        loss_count += 1
                    
                    # دریافت RSI از بازار
                    rsi = None
                    if market_df is not None:
                        m_symbol_col = find_column(market_df, ['نماد', 'symbol'])
                        if m_symbol_col:
                            market_row = market_df[market_df[m_symbol_col].astype(str) == symbol]
                            if not market_row.empty:
                                rsi_col = find_column(market_df, ['rsi'])
                                if rsi_col:
                                    rsi = safe_float(market_row.iloc[0][rsi_col])
                    
                    # پیشنهادات
                    recommendations = []
                    if profit_loss_percent >= p['alert_thresholds']['profit_high']:
                        recommendations.append(f"⚠️ فروش {profit_loss_percent:.1f}%")
                    elif profit_loss_percent <= p['alert_thresholds']['loss_high']:
                        recommendations.append(f"🔴 خروج {profit_loss_percent:.1f}%")
                    elif profit_loss_percent >= p['alert_thresholds']['profit_medium']:
                        recommendations.append(f"💰 کسب سود")
                    elif profit_loss_percent <= p['alert_thresholds']['loss_medium']:
                        recommendations.append(f"📉 زیان موقت")
                    else:
                        recommendations.append(f"💼 نگهداری")
                    
                    if rsi and rsi >= p['rsi_thresholds']['high']:
                        recommendations.append(f"📊 RSI بالا")
                    elif rsi and rsi <= p['rsi_thresholds']['low']:
                        recommendations.append(f"🟢 RSI پایین")
                    
                    recommendation = ' | '.join(recommendations[:3])
                    
                    # وضعیت
                    if profit_loss_percent >= p['status_thresholds']['excellent']:
                        status = "🌟🌟 عالی"
                    elif profit_loss_percent >= p['status_thresholds']['very_good']:
                        status = "⭐️⭐️ خوب"
                    elif profit_loss_percent >= p['status_thresholds']['good']:
                        status = "⭐️ خوب"
                    elif profit_loss_percent >= p['status_thresholds']['average']:
                        status = "📊 متوسط"
                    elif profit_loss_percent >= p['status_thresholds']['poor']:
                        status = "⚠️ ضعیف"
                    else:
                        status = "❌ بحرانی"
                    
                    stock_detail = {
                        'symbol': symbol,
                        'quantity': int(total_quantity),
                        'avg_buy_price': round(avg_buy_price, 0),
                        'current_price': round(current_price_avg, 0),
                        'current_value': round(total_current_value, 0),
                        'profit_loss': round(profit_loss, 0),
                        'profit_loss_percent': round(profit_loss_percent, 2),
                        'status': status,
                        'recommendation': recommendation,
                        'weight': 0,
                        'rsi': round(rsi, 1) if rsi else None
                    }
                    
                    if 'فروش' in recommendation or 'خروج' in recommendation:
                        analysis['sell_alerts'].append(f"{symbol}: {recommendation}")
                    if 'خرید' in recommendation or '🟢' in recommendation:
                        analysis['buy_recommendations'].append(f"{symbol}: {recommendation}")
                    if profit_loss_percent >= 15:
                        analysis['good_performers'].append(f"{symbol}: {profit_loss_percent:.1f}%")
                    elif profit_loss_percent <= -10:
                        analysis['poor_performers'].append(f"{symbol}: {profit_loss_percent:.1f}%")
                    
                    analysis['stock_details'][symbol] = stock_detail
                    
            except Exception as e:
                debug_log(f"خطا در پردازش نماد {symbol}: {e}", "ERROR")
                continue
        
        analysis['portfolio_value'] = total_value
        analysis['profit_count'] = profit_count
        analysis['loss_count'] = loss_count
        
        if total_cost > 0:
            analysis['profit_loss_percent'] = (analysis['total_profit_loss'] / total_cost) * 100
        
        # محاسبه وزن هر سهم
        for symbol, detail in analysis['stock_details'].items():
            if total_value > 0:
                detail['weight'] = (detail['current_value'] / total_value) * 100
        
        # امتیاز تنوع
        num_stocks = len(analysis['stock_details'])
        diversity = p['diversity_scores']
        
        if num_stocks >= 10:
            analysis['diversification_score'] = diversity[10]
        elif num_stocks >= 7:
            analysis['diversification_score'] = diversity[7]
        elif num_stocks >= 5:
            analysis['diversification_score'] = diversity[5]
        elif num_stocks >= 3:
            analysis['diversification_score'] = diversity[3]
        else:
            analysis['diversification_score'] = diversity['default']
        
        # سطح ریسک پورتفو
        if num_stocks >= 8:
            analysis['portfolio_risk_level'] = '🟢 پایین'
        elif num_stocks >= 5:
            analysis['portfolio_risk_level'] = '🟠 متوسط'
        else:
            analysis['portfolio_risk_level'] = '🔴 بالا'
        
        debug_log(f"✅ تحلیل پورتفو: ارزش کل {total_value:,.0f} ریال، سود/زیان {analysis['profit_loss_percent']:.2f}%")
        
    except Exception as e:
        debug_log(f"خطا در تحلیل پورتفو: {e}", "ERROR")
        traceback.print_exc()
    
    return analysis

# ============================================================================
# بخش ۱۵: توابع ایجاد نمودار با رعایت تنظیمات فونت
# ============================================================================

def get_font_style():
    """دریافت استایل فونت از تنظیمات"""
    fs = font_settings.settings
    
    return {
        'font_family': fs['general']['font_family'],
        'title_font_size': fs['charts']['title_font_size'],
        'title_font_color': fs['charts']['title_font_color'],
        'axis_font_size': fs['charts']['axis_font_size'],
        'axis_font_color': fs['charts']['axis_font_color'],
        'legend_font_size': fs['charts']['legend_font_size'],
        'legend_font_color': fs['charts']['legend_font_color'],
        'paper_bgcolor': fs['charts']['paper_background'],
        'plot_bgcolor': fs['charts']['plot_background'],
        'grid_color': fs['charts']['grid_color']
    }

def create_basic_charts(df):
    """ایجاد نمودارهای تحلیل پایه"""
    if df is None or df.empty:
        return None
    
    font = get_font_style()
    
    fig = go.Figure()
    
    top_10 = df.head(10)
    symbols = top_10['نماد'].tolist() if 'نماد' in top_10.columns else list(range(len(top_10)))
    scores = top_10['امتیاز'].tolist() if 'امتیاز' in top_10.columns else []
    
    colors = []
    for s in scores:
        if s >= 85:
            colors.append('#4caf50')
        elif s >= 75:
            colors.append('#2196f3')
        elif s >= 65:
            colors.append('#ff9800')
        elif s >= 55:
            colors.append('#9c27b0')
        else:
            colors.append('#f44336')
    
    fig.add_trace(go.Bar(
        x=symbols,
        y=scores,
        marker_color=colors,
        text=[f"{s:.1f}" for s in scores],
        textposition='outside',
        textfont=dict(size=11, color='white')
    ))
    
    fig.update_layout(
        title=dict(
            text="امتیاز ۱۰ سهم برتر",
            font=dict(size=font['title_font_size'], color=font['title_font_color'], family=font['font_family'])
        ),
        template="plotly_dark",
        height=400,
        xaxis=dict(
            title=dict(text="نماد", font=dict(size=font['axis_font_size'], color=font['axis_font_color'])),
            tickfont=dict(size=font['axis_font_size'], color=font['axis_font_color']),
            tickangle=45
        ),
        yaxis=dict(
            title=dict(text="امتیاز", font=dict(size=font['axis_font_size'], color=font['axis_font_color'])),
            tickfont=dict(size=font['axis_font_size'], color=font['axis_font_color']),
            gridcolor=font['grid_color']
        ),
        paper_bgcolor=font['paper_bgcolor'],
        plot_bgcolor=font['plot_bgcolor'],
        font=dict(family=font['font_family'])
    )
    
    return fig

def create_advanced_charts(df):
    """ایجاد نمودارهای تحلیل پیشرفته"""
    if df is None or df.empty:
        return None, None
    
    font = get_font_style()
    
    # نمودار امتیاز نهایی
    fig_final = go.Figure()
    
    top_10 = df.head(10)
    symbols = top_10['نماد'].tolist()
    scores = top_10['امتیاز_نهایی'].tolist()
    
    colors = []
    for s in scores:
        if s >= 85:
            colors.append('#4caf50')
        elif s >= 75:
            colors.append('#2196f3')
        elif s >= 65:
            colors.append('#ff9800')
        else:
            colors.append('#f44336')
    
    fig_final.add_trace(go.Bar(
        x=symbols,
        y=scores,
        marker_color=colors,
        text=[f"{s:.1f}" for s in scores],
        textposition='outside',
        textfont=dict(size=11, color='white')
    ))
    
    fig_final.update_layout(
        title=dict(
            text="امتیاز نهایی سهام (۱۰ سهم برتر)",
            font=dict(size=font['title_font_size'], color=font['title_font_color'], family=font['font_family'])
        ),
        template="plotly_dark",
        height=400,
        xaxis=dict(
            title=dict(text="نماد", font=dict(size=font['axis_font_size'], color=font['axis_font_color'])),
            tickfont=dict(size=font['axis_font_size'], color=font['axis_font_color']),
            tickangle=45,
            gridcolor=font['grid_color']
        ),
        yaxis=dict(
            title=dict(text="امتیاز", font=dict(size=font['axis_font_size'], color=font['axis_font_color'])),
            tickfont=dict(size=font['axis_font_size'], color=font['axis_font_color']),
            gridcolor=font['grid_color']
        ),
        paper_bgcolor=font['paper_bgcolor'],
        plot_bgcolor=font['plot_bgcolor'],
        font=dict(family=font['font_family'])
    )
    
    # نمودار شش‌گانه
    fig_six = make_subplots(
        rows=2, cols=3,
        subplot_titles=('حباب', 'ارزش ذاتی', 'تابلوخوانی', 'ریسک', 'عملکرد', 'تکنیکال')
    )
    
    metrics = [
        ('امتیاز_حباب', (1,1)),
        ('امتیاز_ارزش_ذاتی', (1,2)),
        ('امتیاز_تابلوخوانی', (1,3)),
        ('امتیاز_ریسک', (2,1)),
        ('امتیاز_عملکرد', (2,2)),
        ('امتیاز_تکنیکال', (2,3))
    ]
    
    top_15 = df.head(15)
    symbols_15 = top_15['نماد'].tolist()
    
    colors_list = ['#f44336', '#4caf50', '#ff9800', '#2196f3', '#9c27b0', '#00bcd4']
    
    for (metric, pos), color in zip(metrics, colors_list):
        if metric in top_15.columns:
            values = top_15[metric].tolist()
            fig_six.add_trace(
                go.Bar(
                    x=symbols_15,
                    y=values,
                    marker_color=color,
                    text=[f"{v:.1f}" for v in values],
                    textposition='outside',
                    textfont=dict(size=9, color='white')
                ),
                row=pos[0], col=pos[1]
            )
    
    fig_six.update_layout(
        template="plotly_dark",
        height=600,
        showlegend=False,
        paper_bgcolor=font['paper_bgcolor'],
        plot_bgcolor=font['plot_bgcolor'],
        font=dict(family=font['font_family']),
        title_font=dict(size=font['title_font_size'], color=font['title_font_color'])
    )
    
    # تنظیم محورها
    for i in range(1, 7):
        fig_six.layout.annotations[i-1].font.color = font['title_font_color']
        fig_six.layout.annotations[i-1].font.size = font['title_font_size'] - 2
    
    fig_six.update_xaxes(tickangle=45, tickfont=dict(size=font['axis_font_size'], color=font['axis_font_color']))
    fig_six.update_yaxes(tickfont=dict(size=font['axis_font_size'], color=font['axis_font_color']))
    
    return fig_final, fig_six

def create_portfolio_charts(analysis):
    """ایجاد نمودارهای پورتفو"""
    if not analysis or not analysis.get('stock_details'):
        return None, None, None
    
    font = get_font_style()
    
    stocks = list(analysis['stock_details'].values())
    df = pd.DataFrame(stocks)
    
    if df.empty:
        return None, None, None
    
    # نمودار دایره‌ای
    fig_pie = go.Figure(data=[go.Pie(
        labels=df['symbol'],
        values=df['current_value'],
        hole=0.4,
        textinfo='label+percent',
        marker=dict(colors=px.colors.qualitative.Set3),
        textfont=dict(size=12, color='white')
    )])
    fig_pie.update_layout(
        title=dict(
            text="توزیع پورتفو",
            font=dict(size=font['title_font_size'], color=font['title_font_color'], family=font['font_family'])
        ),
        template="plotly_dark",
        height=350,
        paper_bgcolor=font['paper_bgcolor'],
        plot_bgcolor=font['plot_bgcolor'],
        showlegend=False,
        font=dict(family=font['font_family'])
    )
    
    # نمودار سود/زیان
    fig_profit = go.Figure()
    colors = ['#4caf50' if p >= 0 else '#f44336' for p in df['profit_loss_percent']]
    fig_profit.add_trace(go.Bar(
        x=df['symbol'],
        y=df['profit_loss_percent'],
        marker_color=colors,
        text=df['profit_loss_percent'].round(1).astype(str) + '%',
        textposition='outside',
        textfont=dict(size=11, color='white')
    ))
    fig_profit.update_layout(
        title=dict(
            text="سود/زیان هر سهم",
            font=dict(size=font['title_font_size'], color=font['title_font_color'], family=font['font_family'])
        ),
        xaxis=dict(
            title=dict(text="نماد", font=dict(size=font['axis_font_size'], color=font['axis_font_color'])),
            tickfont=dict(size=font['axis_font_size'], color=font['axis_font_color']),
            tickangle=45,
            gridcolor=font['grid_color']
        ),
        yaxis=dict(
            title=dict(text="درصد", font=dict(size=font['axis_font_size'], color=font['axis_font_color'])),
            tickfont=dict(size=font['axis_font_size'], color=font['axis_font_color']),
            gridcolor=font['grid_color']
        ),
        template="plotly_dark",
        height=350,
        paper_bgcolor=font['paper_bgcolor'],
        plot_bgcolor=font['plot_bgcolor'],
        font=dict(family=font['font_family'])
    )
    fig_profit.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
    
    # نمودار وزن
    fig_weight = go.Figure(data=[go.Bar(
        x=df['symbol'],
        y=df['weight'],
        marker_color='#00bcd4',
        text=df['weight'].round(1).astype(str) + '%',
        textposition='outside',
        textfont=dict(size=11, color='white')
    )])
    fig_weight.update_layout(
        title=dict(
            text="وزن هر سهم",
            font=dict(size=font['title_font_size'], color=font['title_font_color'], family=font['font_family'])
        ),
        xaxis=dict(
            title=dict(text="نماد", font=dict(size=font['axis_font_size'], color=font['axis_font_color'])),
            tickfont=dict(size=font['axis_font_size'], color=font['axis_font_color']),
            tickangle=45,
            gridcolor=font['grid_color']
        ),
        yaxis=dict(
            title=dict(text="درصد", font=dict(size=font['axis_font_size'], color=font['axis_font_color'])),
            tickfont=dict(size=font['axis_font_size'], color=font['axis_font_color']),
            gridcolor=font['grid_color']
        ),
        template="plotly_dark",
        height=350,
        paper_bgcolor=font['paper_bgcolor'],
        plot_bgcolor=font['plot_bgcolor'],
        font=dict(family=font['font_family'])
    )
    
    return fig_pie, fig_profit, fig_weight

# ============================================================================
# بخش ۱۶: راه‌اندازی Flask
# ============================================================================

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# ============================================================================
# بخش ۱۷: API‌ها
# ============================================================================

@app.route('/health')
def health():
    """بررسی سلامت"""
    return jsonify({
        'status': 'ok',
        'version': VERSION,
        'name': APP_NAME,
        'selenium': SELENIUM_AVAILABLE,
        'data': data.get_stats(),
        'online': online.get_status(),
        'server_ip': LOCAL_IP,
        'server_port': PORT,
        'debug_log': os.path.exists(DEBUG_LOG_FILE)
    })

@app.route('/upload/market', methods=['POST'])
def upload_market():
    """آپلود داده بازار"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'فایلی ارسال نشده'}), 400
        
        file = request.files['file']
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"market_{timestamp}_{file.filename}"
        filepath = os.path.join(UPLOADS_DIR, filename)
        file.save(filepath)
        
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath, encoding='utf-8-sig')
        else:
            df = pd.read_excel(filepath)
        
        data.set_market_data(df)
        
        return jsonify({
            'success': True,
            'rows': len(df),
            'columns': list(df.columns),
            'message': f'✅ {len(df)} ردیف آپلود شد'
        })
        
    except Exception as e:
        debug_log(f"خطا در آپلود بازار: {e}", "ERROR")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/upload/portfolio', methods=['POST'])
def upload_portfolio():
    """آپلود داده پورتفو"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'فایلی ارسال نشده'}), 400
        
        file = request.files['file']
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"portfolio_{timestamp}_{file.filename}"
        filepath = os.path.join(UPLOADS_DIR, filename)
        file.save(filepath)
        
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath, encoding='utf-8-sig')
        else:
            df = pd.read_excel(filepath)
        
        data.set_portfolio_data(df)
        
        return jsonify({
            'success': True,
            'rows': len(df),
            'columns': list(df.columns),
            'message': f'✅ {len(df)} ردیف آپلود شد'
        })
        
    except Exception as e:
        debug_log(f"خطا در آپلود پورتفو: {e}", "ERROR")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/online/login', methods=['POST'])
def online_login():
    """ورود آنلاین به ایزی‌تریدر"""
    try:
        req = request.json
        username = req.get('username')
        password = req.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'نام کاربری و رمز عبور الزامی است'}), 400
        
        def login_thread():
            success = online.login(username, password)
            if success:
                # پس از ورود موفق، داده‌ها را دریافت کن
                time.sleep(2)
                market_df = online.fetch_market_data()
                if market_df is not None:
                    data.set_market_data(market_df)
                portfolio_df = online.fetch_portfolio_data()
                if portfolio_df is not None:
                    data.set_portfolio_data(portfolio_df)
        
        threading.Thread(target=login_thread, daemon=True).start()
        
        return jsonify({'success': True, 'message': 'در حال ورود...'})
        
    except Exception as e:
        debug_log(f"خطا در لاگین: {e}", "ERROR")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/online/status')
def online_status():
    """وضعیت اتصال آنلاین"""
    return jsonify(online.get_status())

@app.route('/online/fetch/market', methods=['POST'])
def online_fetch_market():
    """دریافت داده بازار به صورت آنلاین"""
    if not online.logged_in:
        return jsonify({'success': False, 'message': 'ابتدا وارد شوید'}), 400
    
    def fetch_thread():
        df = online.fetch_market_data()
        if df is not None:
            data.set_market_data(df)
    
    threading.Thread(target=fetch_thread, daemon=True).start()
    
    return jsonify({'success': True, 'message': 'دریافت داده‌های بازار شروع شد'})

@app.route('/online/fetch/portfolio', methods=['POST'])
def online_fetch_portfolio():
    """دریافت داده پورتفو به صورت آنلاین"""
    if not online.logged_in:
        return jsonify({'success': False, 'message': 'ابتدا وارد شوید'}), 400
    
    def fetch_thread():
        df = online.fetch_portfolio_data()
        if df is not None:
            data.set_portfolio_data(df)
    
    threading.Thread(target=fetch_thread, daemon=True).start()
    
    return jsonify({'success': True, 'message': 'دریافت داده‌های پورتفو شروع شد'})

@app.route('/online/logout', methods=['POST'])
def online_logout():
    """خروج از حساب آنلاین"""
    online.logout()
    return jsonify({'success': True})

@app.route('/analyze/basic', methods=['POST'])
def analyze_basic():
    """تحلیل پایه"""
    try:
        req = request.json or {}
        budget = float(req.get('budget', 100000000))
        top_n = int(req.get('top_n', 15))
        
        if data.market_data is None:
            return jsonify({'success': False, 'message': 'داده بازار موجود نیست'}), 400
        
        results = analyze_basic_stocks(data.market_data, budget, top_n)
        
        if results is not None:
            data.set_analysis_basic(results)
            
            # تبدیل به json
            results_json = results.to_dict('records')
            for r in results_json:
                for k, v in r.items():
                    if isinstance(v, (np.integer, np.floating)):
                        r[k] = float(v) if isinstance(v, np.floating) else int(v)
            
            return jsonify({
                'success': True,
                'results': results_json,
                'count': len(results_json)
            })
        else:
            return jsonify({'success': False, 'message': 'هیچ سهم واجد شرایطی یافت نشد'}), 400
            
    except Exception as e:
        debug_log(f"خطا در تحلیل پایه: {e}", "ERROR")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/analyze/advanced', methods=['POST'])
def analyze_advanced():
    """تحلیل پیشرفته"""
    try:
        if data.market_data is None:
            return jsonify({'success': False, 'message': 'داده بازار موجود نیست'}), 400
        
        results = analyze_advanced_stocks(data.market_data)
        
        if results is not None:
            data.set_analysis_advanced(results)
            
            results_json = results.to_dict('records')
            for r in results_json:
                for k, v in r.items():
                    if isinstance(v, (np.integer, np.floating)):
                        r[k] = float(v) if isinstance(v, np.floating) else int(v)
            
            return jsonify({
                'success': True,
                'results': results_json,
                'count': len(results_json)
            })
        else:
            return jsonify({'success': False, 'message': 'تحلیل با خطا مواجه شد'}), 400
            
    except Exception as e:
        debug_log(f"خطا در تحلیل پیشرفته: {e}", "ERROR")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/analyze/portfolio', methods=['POST'])
def analyze_portfolio_api():
    """تحلیل پورتفو"""
    try:
        if data.portfolio_data is None:
            return jsonify({'success': False, 'message': 'داده پورتفو موجود نیست'}), 400
        
        analysis = analyze_portfolio(data.portfolio_data, data.market_data)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        debug_log(f"خطا در تحلیل پورتفو: {e}", "ERROR")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/data/market')
def get_market_data():
    """دریافت داده بازار (با صفحه‌بندی)"""
    if data.market_data is None:
        return jsonify({'success': False, 'message': 'داده‌ای وجود ندارد'})
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))
    
    df = data.market_data.copy()
    
    # جستجو
    search = request.args.get('search', '')
    if search:
        mask = pd.Series([False] * len(df))
        for col in df.columns:
            try:
                mask |= df[col].astype(str).str.contains(search, case=False, na=False)
            except:
                pass
        df = df[mask]
    
    # مرتب‌سازی
    sort_by = request.args.get('sort_by')
    sort_order = request.args.get('sort_order', 'asc')
    if sort_by and sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=(sort_order == 'asc'))
    
    total = len(df)
    start = (page - 1) * per_page
    end = start + per_page
    
    page_data = df.iloc[start:end].to_dict('records')
    
    # تبدیل مقادیر
    for row in page_data:
        for k, v in row.items():
            if isinstance(v, (np.integer, np.floating)):
                row[k] = float(v) if isinstance(v, np.floating) else int(v)
    
    return jsonify({
        'success': True,
        'data': page_data,
        'columns': list(df.columns),
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })

@app.route('/data/portfolio')
def get_portfolio_data():
    """دریافت داده پورتفو"""
    if data.portfolio_data is None:
        return jsonify({'success': False, 'message': 'داده‌ای وجود ندارد'})
    
    df = data.portfolio_data.copy()
    
    page_data = df.head(500).to_dict('records')
    for row in page_data:
        for k, v in row.items():
            if isinstance(v, (np.integer, np.floating)):
                row[k] = float(v) if isinstance(v, np.floating) else int(v)
    
    return jsonify({
        'success': True,
        'data': page_data,
        'columns': list(df.columns),
        'total': len(df)
    })

@app.route('/charts/basic')
def get_basic_charts():
    """دریافت نمودارهای پایه"""
    if data.analysis_basic is None:
        return jsonify({'success': False, 'message': 'تحلیلی وجود ندارد'})
    
    fig = create_basic_charts(data.analysis_basic)
    if fig:
        return jsonify({'success': True, 'chart': fig.to_json()})
    return jsonify({'success': False})

@app.route('/charts/advanced')
def get_advanced_charts():
    """دریافت نمودارهای پیشرفته"""
    if data.analysis_advanced is None:
        return jsonify({'success': False, 'message': 'تحلیلی وجود ندارد'})
    
    fig1, fig2 = create_advanced_charts(data.analysis_advanced)
    if fig1:
        return jsonify({
            'success': True,
            'chart_final': fig1.to_json(),
            'chart_six': fig2.to_json() if fig2 else None
        })
    return jsonify({'success': False})

@app.route('/charts/portfolio')
def get_portfolio_charts():
    """دریافت نمودارهای پورتفو"""
    if data.portfolio_data is None:
        return jsonify({'success': False, 'message': 'داده‌ای وجود ندارد'})
    
    analysis = analyze_portfolio(data.portfolio_data, data.market_data)
    fig1, fig2, fig3 = create_portfolio_charts(analysis)
    
    charts = {}
    if fig1:
        charts['pie'] = fig1.to_json()
    if fig2:
        charts['profit'] = fig2.to_json()
    if fig3:
        charts['weight'] = fig3.to_json()
    
    return jsonify({'success': True, 'charts': charts})

@app.route('/export')
def export_data():
    """خروجی Excel"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if data.market_data is not None:
            data.market_data.to_excel(writer, sheet_name='داده بازار', index=False)
        if data.portfolio_data is not None:
            data.portfolio_data.to_excel(writer, sheet_name='پورتفو', index=False)
        if data.analysis_basic is not None:
            data.analysis_basic.to_excel(writer, sheet_name='تحلیل پایه', index=False)
        if data.analysis_advanced is not None:
            data.analysis_advanced.to_excel(writer, sheet_name='تحلیل پیشرفته', index=False)
        
        # تحلیل پورتفو
        if data.portfolio_data is not None:
            analysis = analyze_portfolio(data.portfolio_data, data.market_data)
            if analysis:
                df_summary = pd.DataFrame([{
                    'موارد': 'ارزش کل',
                    'مقدار': analysis['portfolio_value']
                }, {
                    'موارد': 'سود/زیان کل',
                    'مقدار': analysis['total_profit_loss']
                }, {
                    'موارد': 'درصد سود/زیان',
                    'مقدار': analysis['profit_loss_percent']
                }, {
                    'موارد': 'تعداد سهام',
                    'مقدار': len(analysis['stock_details'])
                }, {
                    'موارد': 'سهام سودده',
                    'مقدار': analysis['profit_count']
                }, {
                    'موارد': 'سهام زیانده',
                    'مقدار': analysis['loss_count']
                }, {
                    'موارد': 'امتیاز تنوع',
                    'مقدار': analysis['diversification_score']
                }])
                df_summary.to_excel(writer, sheet_name='خلاصه پورتفو', index=False)
                
                if analysis['stock_details']:
                    df_details = pd.DataFrame(analysis['stock_details'].values())
                    df_details.to_excel(writer, sheet_name='جزئیات پورتفو', index=False)
                
                if analysis['sold_stocks']:
                    df_sold = pd.DataFrame(analysis['sold_stocks'])
                    df_sold.to_excel(writer, sheet_name='سهام فروخته شده', index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )

@app.route('/settings', methods=['GET'])
def get_settings():
    """دریافت تنظیمات اصلی"""
    return jsonify(settings.settings)

@app.route('/settings', methods=['POST'])
def save_settings():
    """ذخیره تنظیمات اصلی"""
    try:
        new_settings = request.json
        settings.settings = settings.merge_deep(DEFAULT_SETTINGS.copy(), new_settings)
        settings.save()
        return jsonify({'success': True})
    except Exception as e:
        debug_log(f"خطا در ذخیره تنظیمات: {e}", "ERROR")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/settings/reset', methods=['POST'])
def reset_settings():
    """بازنشانی تنظیمات اصلی"""
    settings.reset()
    return jsonify({'success': True})

@app.route('/font-settings', methods=['GET'])
def get_font_settings():
    """دریافت تنظیمات فونت"""
    return jsonify(font_settings.settings)

@app.route('/font-settings', methods=['POST'])
def save_font_settings():
    """ذخیره تنظیمات فونت"""
    try:
        new_settings = request.json
        font_settings.settings = new_settings
        font_settings.save()
        return jsonify({'success': True})
    except Exception as e:
        debug_log(f"خطا در ذخیره تنظیمات فونت: {e}", "ERROR")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/font-settings/reset', methods=['POST'])
def reset_font_settings():
    """بازنشانی تنظیمات فونت"""
    font_settings.reset()
    return jsonify({'success': True})

@app.route('/font-settings/css')
def get_font_css():
    """دریافت CSS پویای فونت"""
    return font_settings.generate_css()

@app.route('/debug/log')
def get_debug_log():
    """دریافت لاگ دیباگ"""
    if os.path.exists(DEBUG_LOG_FILE):
        with open(DEBUG_LOG_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    return "لاگ وجود ندارد"

@app.route('/debug/clear', methods=['POST'])
def clear_debug_log():
    """پاک کردن لاگ دیباگ"""
    try:
        with open(DEBUG_LOG_FILE, 'w', encoding='utf-8') as f:
            f.write("")
        return jsonify({'success': True})
    except:
        return jsonify({'success': False})

@app.route('/settings/page')
def settings_page():
    """صفحه تنظیمات اصلی"""
    try:
        css = font_settings.generate_css()
        return render_template_string(SETTINGS_HTML_TEMPLATE, settings=settings.settings, font_css=css)
    except Exception as e:
        debug_log(f"خطا در نمایش صفحه تنظیمات: {e}", "ERROR")
        return f"خطا در بارگذاری صفحه تنظیمات: {str(e)}", 500

@app.route('/font-settings/page')
def font_settings_page():
    """صفحه تنظیمات فونت"""
    try:
        css = font_settings.generate_css()
        return render_template_string(FONT_SETTINGS_HTML_TEMPLATE, font_settings=font_settings.settings, font_css=css)
    except Exception as e:
        debug_log(f"خطا در نمایش صفحه تنظیمات فونت: {e}", "ERROR")
        return f"خطا در بارگذاری صفحه تنظیمات فونت: {str(e)}", 500

@app.route('/')
@app.route('/dashboard')
def index():
    """صفحه اصلی"""
    try:
        css = font_settings.generate_css()
        return render_template_string(
            MAIN_HTML_TEMPLATE,
            version=VERSION,
            selenium_available=SELENIUM_AVAILABLE,
            stats=data.get_stats(),
            server_ip=LOCAL_IP,
            server_port=PORT,
            font_css=css
        )
    except Exception as e:
        debug_log(f"خطا در نمایش صفحه اصلی: {e}", "ERROR")
        return f"خطا در بارگذاری صفحه اصلی: {str(e)}", 500

# ============================================================================
# بخش ۱۸: قالب HTML تنظیمات فونت
# ============================================================================

FONT_SETTINGS_HTML_TEMPLATE = """
<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>تنظیمات فونت و جداول</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    {{ font_css|safe }}
    <style>
        body { 
            font-family: Tahoma, Arial; 
            background: #0a0a0a; 
            color: #ffffff; 
            padding: 20px; 
        }
        .card { 
            background: #1a1a1a; 
            border: 1px solid #333; 
            border-radius: 12px; 
            margin-bottom: 20px; 
        }
        .card-header { 
            background: #2d2d2d; 
            color: #00bcd4; 
            font-weight: bold; 
            padding: 15px 20px; 
            border-bottom: 1px solid #404040; 
            cursor: pointer; 
        }
        .card-header:hover { 
            background: #3d3d3d; 
        }
        .card-body { 
            padding: 20px; 
        }
        .form-label { 
            color: #00bcd4; 
            margin-bottom: 5px; 
            font-weight: bold;
        }
        .form-control, .form-select { 
            background: #2d2d2d; 
            border: 1px solid #404040; 
            color: #ffffff; 
            padding: 8px 12px; 
            border-radius: 6px; 
        }
        .form-control:focus { 
            border-color: #00bcd4; 
            box-shadow: 0 0 0 0.2rem rgba(0,188,212,0.25); 
        }
        .btn-primary { 
            background: #00bcd4; 
            border: none; 
            padding: 10px 25px; 
            margin: 5px; 
            color: #ffffff;
            font-weight: bold;
        }
        .btn-success { 
            background: #4caf50; 
            border: none; 
            padding: 10px 25px; 
            margin: 5px; 
            color: #ffffff;
            font-weight: bold;
        }
        .btn-danger { 
            background: #f44336; 
            border: none; 
            padding: 10px 25px; 
            margin: 5px; 
            color: #ffffff;
            font-weight: bold;
        }
        .btn-info { 
            background: #2196f3; 
            border: none; 
            padding: 10px 25px; 
            margin: 5px; 
            color: #ffffff;
            font-weight: bold;
        }
        .toolbar { 
            background: #1a1a1a; 
            padding: 15px 20px; 
            border-radius: 12px; 
            margin-bottom: 20px; 
            border: 1px solid #333; 
        }
        .nav-tabs { 
            border-bottom: 2px solid #333; 
            margin-bottom: 20px; 
            flex-wrap: wrap; 
        }
        .nav-tabs .nav-link { 
            color: #888; 
            border: none; 
            padding: 12px 20px; 
        }
        .nav-tabs .nav-link:hover { 
            color: #00bcd4; 
        }
        .nav-tabs .nav-link.active { 
            color: #00bcd4; 
            border-bottom: 3px solid #00bcd4; 
            background: transparent; 
        }
        .color-preview {
            width: 30px;
            height: 30px;
            border-radius: 4px;
            display: inline-block;
            margin-left: 10px;
            border: 1px solid #404040;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1 class="text-center mb-4" style="color: #00bcd4;">🎨 تنظیمات فونت و جداول</h1>
        
        <div class="toolbar">
            <div class="row">
                <div class="col-12 text-center">
                    <button class="btn btn-success" onclick="saveFontSettings()"><i class="bi bi-save"></i> ذخیره</button>
                    <button class="btn btn-danger" onclick="resetFontSettings()"><i class="bi bi-arrow-counterclockwise"></i> بازنشانی</button>
                    <button class="btn btn-info" onclick="window.location.href='/'"><i class="bi bi-house"></i> بازگشت</button>
                </div>
            </div>
        </div>
        
        <ul class="nav nav-tabs" id="settingsTabs">
            <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#general">عمومی</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tables">جداول</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#charts">نمودارها</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#alerts">هشدارها</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#stats">آمار</button></li>
        </ul>
        
        <div class="tab-content">
            <!-- عمومی -->
            <div class="tab-pane active" id="general">
                <div class="card">
                    <div class="card-header"><i class="bi bi-gear"></i> تنظیمات عمومی</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">فونت پیش‌فرض</label>
                                <input type="text" class="form-control" id="general_font_family" value="{{ font_settings['general']['font_family'] }}">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">اندازه فونت پایه</label>
                                <input type="number" class="form-control" id="general_base_font_size" value="{{ font_settings['general']['base_font_size'] }}">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">رنگ متن پایه</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="general_base_text_color" value="{{ font_settings['general']['base_text_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['general']['base_text_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">رنگ پس‌زمینه پایه</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="general_base_background_color" value="{{ font_settings['general']['base_background_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['general']['base_background_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">رنگ پس‌زمینه کارت</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="general_card_background_color" value="{{ font_settings['general']['card_background_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['general']['card_background_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">رنگ هدر کارت</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="general_card_header_color" value="{{ font_settings['general']['card_header_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['general']['card_header_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">رنگ پس‌زمینه هدر کارت</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="general_card_header_background" value="{{ font_settings['general']['card_header_background'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['general']['card_header_background'] }}"></span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- جداول -->
            <div class="tab-pane" id="tables">
                <div class="card">
                    <div class="card-header"><i class="bi bi-table"></i> تنظیمات جداول</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4 mb-3">
                                <label class="form-label">اندازه فونت هدر جدول</label>
                                <input type="number" class="form-control" id="tables_header_font_size" value="{{ font_settings['tables']['header_font_size'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ فونت هدر جدول</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="tables_header_font_color" value="{{ font_settings['tables']['header_font_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['tables']['header_font_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ پس‌زمینه هدر جدول</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="tables_header_background" value="{{ font_settings['tables']['header_background'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['tables']['header_background'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">اندازه فونت ردیف‌ها</label>
                                <input type="number" class="form-control" id="tables_row_font_size" value="{{ font_settings['tables']['row_font_size'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ فونت ردیف‌ها</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="tables_row_font_color" value="{{ font_settings['tables']['row_font_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['tables']['row_font_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ پس‌زمینه ردیف‌های زوج</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="tables_row_background_even" value="{{ font_settings['tables']['row_background_even'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['tables']['row_background_even'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ پس‌زمینه ردیف‌های فرد</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="tables_row_background_odd" value="{{ font_settings['tables']['row_background_odd'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['tables']['row_background_odd'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ حاشیه‌ها</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="tables_border_color" value="{{ font_settings['tables']['border_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['tables']['border_color'] }}"></span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- نمودارها -->
            <div class="tab-pane" id="charts">
                <div class="card">
                    <div class="card-header"><i class="bi bi-pie-chart"></i> تنظیمات نمودارها</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4 mb-3">
                                <label class="form-label">اندازه فونت عنوان</label>
                                <input type="number" class="form-control" id="charts_title_font_size" value="{{ font_settings['charts']['title_font_size'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ فونت عنوان</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="charts_title_font_color" value="{{ font_settings['charts']['title_font_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['charts']['title_font_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">اندازه فونت محورها</label>
                                <input type="number" class="form-control" id="charts_axis_font_size" value="{{ font_settings['charts']['axis_font_size'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ فونت محورها</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="charts_axis_font_color" value="{{ font_settings['charts']['axis_font_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['charts']['axis_font_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">اندازه فونت راهنما</label>
                                <input type="number" class="form-control" id="charts_legend_font_size" value="{{ font_settings['charts']['legend_font_size'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ فونت راهنما</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="charts_legend_font_color" value="{{ font_settings['charts']['legend_font_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['charts']['legend_font_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ خطوط شبکه</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="charts_grid_color" value="{{ font_settings['charts']['grid_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['charts']['grid_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ پس‌زمینه کاغذ</label>
                                <input type="text" class="form-control" id="charts_paper_background" value="{{ font_settings['charts']['paper_background'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ پس‌زمینه نمودار</label>
                                <input type="text" class="form-control" id="charts_plot_background" value="{{ font_settings['charts']['plot_background'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- هشدارها -->
            <div class="tab-pane" id="alerts">
                <div class="card">
                    <div class="card-header"><i class="bi bi-exclamation-triangle"></i> تنظیمات هشدارها</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4 mb-3">
                                <label class="form-label">اندازه فونت عنوان کارت</label>
                                <input type="number" class="form-control" id="alerts_card_title_font_size" value="{{ font_settings['alerts']['card_title_font_size'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ فونت عنوان کارت</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="alerts_card_title_font_color" value="{{ font_settings['alerts']['card_title_font_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['alerts']['card_title_font_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">اندازه فونت متن کارت</label>
                                <input type="number" class="form-control" id="alerts_card_text_font_size" value="{{ font_settings['alerts']['card_text_font_size'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ فونت متن کارت</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="alerts_card_text_font_color" value="{{ font_settings['alerts']['card_text_font_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['alerts']['card_text_font_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ موفقیت</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="alerts_success_color" value="{{ font_settings['alerts']['success_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['alerts']['success_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ اطلاعات</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="alerts_info_color" value="{{ font_settings['alerts']['info_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['alerts']['info_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ هشدار</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="alerts_warning_color" value="{{ font_settings['alerts']['warning_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['alerts']['warning_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ خطر</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="alerts_danger_color" value="{{ font_settings['alerts']['danger_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['alerts']['danger_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ ثانویه</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="alerts_secondary_color" value="{{ font_settings['alerts']['secondary_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['alerts']['secondary_color'] }}"></span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- آمار -->
            <div class="tab-pane" id="stats">
                <div class="card">
                    <div class="card-header"><i class="bi bi-bar-chart"></i> تنظیمات کارت‌های آمار</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4 mb-3">
                                <label class="form-label">اندازه فونت مقدار</label>
                                <input type="number" class="form-control" id="stats_value_font_size" value="{{ font_settings['stats']['value_font_size'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ فونت مقدار</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="stats_value_font_color" value="{{ font_settings['stats']['value_font_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['stats']['value_font_color'] }}"></span>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">اندازه فونت برچسب</label>
                                <input type="number" class="form-control" id="stats_label_font_size" value="{{ font_settings['stats']['label_font_size'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">رنگ فونت برچسب</label>
                                <div class="d-flex align-items-center">
                                    <input type="color" class="form-control form-control-color" id="stats_label_font_color" value="{{ font_settings['stats']['label_font_color'] }}">
                                    <span class="color-preview" style="background-color: {{ font_settings['stats']['label_font_color'] }}"></span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // جمع‌آوری تنظیمات فونت
        function collectFontSettings() {
            return {
                general: {
                    font_family: document.getElementById('general_font_family').value,
                    base_font_size: parseInt(document.getElementById('general_base_font_size').value),
                    base_text_color: document.getElementById('general_base_text_color').value,
                    base_background_color: document.getElementById('general_base_background_color').value,
                    card_background_color: document.getElementById('general_card_background_color').value,
                    card_header_color: document.getElementById('general_card_header_color').value,
                    card_header_background: document.getElementById('general_card_header_background').value
                },
                tables: {
                    header_font_size: parseInt(document.getElementById('tables_header_font_size').value),
                    header_font_color: document.getElementById('tables_header_font_color').value,
                    header_background: document.getElementById('tables_header_background').value,
                    row_font_size: parseInt(document.getElementById('tables_row_font_size').value),
                    row_font_color: document.getElementById('tables_row_font_color').value,
                    row_background_even: document.getElementById('tables_row_background_even').value,
                    row_background_odd: document.getElementById('tables_row_background_odd').value,
                    border_color: document.getElementById('tables_border_color').value
                },
                charts: {
                    title_font_size: parseInt(document.getElementById('charts_title_font_size').value),
                    title_font_color: document.getElementById('charts_title_font_color').value,
                    axis_font_size: parseInt(document.getElementById('charts_axis_font_size').value),
                    axis_font_color: document.getElementById('charts_axis_font_color').value,
                    legend_font_size: parseInt(document.getElementById('charts_legend_font_size').value),
                    legend_font_color: document.getElementById('charts_legend_font_color').value,
                    grid_color: document.getElementById('charts_grid_color').value,
                    paper_background: document.getElementById('charts_paper_background').value,
                    plot_background: document.getElementById('charts_plot_background').value
                },
                alerts: {
                    card_title_font_size: parseInt(document.getElementById('alerts_card_title_font_size').value),
                    card_title_font_color: document.getElementById('alerts_card_title_font_color').value,
                    card_text_font_size: parseInt(document.getElementById('alerts_card_text_font_size').value),
                    card_text_font_color: document.getElementById('alerts_card_text_font_color').value,
                    success_color: document.getElementById('alerts_success_color').value,
                    info_color: document.getElementById('alerts_info_color').value,
                    warning_color: document.getElementById('alerts_warning_color').value,
                    danger_color: document.getElementById('alerts_danger_color').value,
                    secondary_color: document.getElementById('alerts_secondary_color').value
                },
                stats: {
                    value_font_size: parseInt(document.getElementById('stats_value_font_size').value),
                    value_font_color: document.getElementById('stats_value_font_color').value,
                    label_font_size: parseInt(document.getElementById('stats_label_font_size').value),
                    label_font_color: document.getElementById('stats_label_font_color').value
                }
            };
        }
        
        // ذخیره تنظیمات فونت
        function saveFontSettings() {
            const settings = collectFontSettings();
            
            fetch('/font-settings', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(settings)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('✅ تنظیمات فونت با موفقیت ذخیره شد');
                    
                    // بروزرسانی CSS
                    fetch('/font-settings/css')
                    .then(r => r.text())
                    .then(css => {
                        let styleTag = document.querySelector('style[data-font="dynamic"]');
                        if (!styleTag) {
                            styleTag = document.createElement('style');
                            styleTag.setAttribute('data-font', 'dynamic');
                            document.head.appendChild(styleTag);
                        }
                        styleTag.innerHTML = css;
                    });
                } else {
                    alert('❌ خطا در ذخیره تنظیمات');
                }
            })
            .catch(error => {
                alert('❌ خطا در ارتباط با سرور');
            });
        }
        
        // بازنشانی به پیش‌فرض
        function resetFontSettings() {
            if (confirm('آیا از بازنشانی به تنظیمات پیش‌فرض اطمینان دارید؟')) {
                fetch('/font-settings/reset', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    }
                });
            }
        }
        
        // به‌روزرسانی پیش‌نمایش رنگ
        document.querySelectorAll('input[type=color]').forEach(input => {
            input.addEventListener('input', function() {
                const preview = this.nextElementSibling;
                if (preview && preview.classList.contains('color-preview')) {
                    preview.style.backgroundColor = this.value;
                }
            });
        });
    </script>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ============================================================================
# بخش ۱۹: قالب HTML تنظیمات اصلی
# ============================================================================

SETTINGS_HTML_TEMPLATE = """
<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>تنظیمات پیشرفته بورس</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    {{ font_css|safe }}
    <style>
        body { 
            font-family: Tahoma, Arial; 
            background: #0a0a0a; 
            color: #ffffff; 
            padding: 20px; 
        }
        .card { 
            background: #1a1a1a; 
            border: 1px solid #333; 
            border-radius: 12px; 
            margin-bottom: 20px; 
        }
        .card-header { 
            background: #2d2d2d; 
            color: #00bcd4; 
            font-weight: bold; 
            padding: 15px 20px; 
            border-bottom: 1px solid #404040; 
            cursor: pointer; 
        }
        .card-header:hover { 
            background: #3d3d3d; 
        }
        .card-body { 
            padding: 20px; 
        }
        .form-label { 
            color: #00bcd4; 
            margin-bottom: 5px; 
            font-weight: bold;
        }
        .form-control, .form-select { 
            background: #2d2d2d; 
            border: 1px solid #404040; 
            color: #ffffff; 
            padding: 8px 12px; 
            border-radius: 6px; 
        }
        .form-control:focus { 
            border-color: #00bcd4; 
            box-shadow: 0 0 0 0.2rem rgba(0,188,212,0.25); 
        }
        .btn-primary { 
            background: #00bcd4; 
            border: none; 
            padding: 10px 25px; 
            margin: 5px; 
            color: #ffffff;
            font-weight: bold;
        }
        .btn-success { 
            background: #4caf50; 
            border: none; 
            padding: 10px 25px; 
            margin: 5px; 
            color: #ffffff;
            font-weight: bold;
        }
        .btn-danger { 
            background: #f44336; 
            border: none; 
            padding: 10px 25px; 
            margin: 5px; 
            color: #ffffff;
            font-weight: bold;
        }
        .btn-info { 
            background: #2196f3; 
            border: none; 
            padding: 10px 25px; 
            margin: 5px; 
            color: #ffffff;
            font-weight: bold;
        }
        .section-title { 
            color: #00bcd4; 
            font-size: 18px; 
            margin: 20px 0 10px; 
            font-weight: bold;
        }
        .range-value { 
            display: inline-block; 
            margin-left: 10px; 
            color: #00bcd4; 
            font-weight: bold; 
        }
        .toolbar { 
            background: #1a1a1a; 
            padding: 15px 20px; 
            border-radius: 12px; 
            margin-bottom: 20px; 
            border: 1px solid #333; 
        }
        .alert-info { 
            background: #1e3a4a; 
            color: #00bcd4; 
            border: 1px solid #005662; 
        }
        .nav-tabs { 
            border-bottom: 2px solid #333; 
            margin-bottom: 20px; 
            flex-wrap: wrap; 
        }
        .nav-tabs .nav-link { 
            color: #888; 
            border: none; 
            padding: 12px 20px; 
        }
        .nav-tabs .nav-link:hover { 
            color: #00bcd4; 
        }
        .nav-tabs .nav-link.active { 
            color: #00bcd4; 
            border-bottom: 3px solid #00bcd4; 
            background: transparent; 
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1 class="text-center mb-4" style="color: #00bcd4;">⚙️ تنظیمات پیشرفته بورس</h1>
        
        <div class="toolbar">
            <div class="row">
                <div class="col-12 text-center">
                    <button class="btn btn-success" onclick="saveSettings()"><i class="bi bi-save"></i> ذخیره</button>
                    <button class="btn btn-danger" onclick="resetSettings()"><i class="bi bi-arrow-counterclockwise"></i> بازنشانی</button>
                    <a href="/font-settings/page" class="btn btn-info" target="_blank"><i class="bi bi-palette"></i> تنظیمات فونت</a>
                    <button class="btn btn-primary" onclick="window.location.href='/'"><i class="bi bi-house"></i> بازگشت</button>
                </div>
            </div>
        </div>
        
        <ul class="nav nav-tabs" id="settingsTabs">
            <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#weights">وزن‌ها</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#eps">EPS</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#pb">P/B</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#pe">P/E</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#rsi">RSI</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#volume">حجم</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#filters">فیلترها</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#disqualifiers">رد صلاحیت</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#validation">اعتبارسنجی</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#status">وضعیت</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#bubble">حباب</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#intrinsic">ارزش ذاتی</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tape">تابلوخوانی</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#risk">ریسک</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#performance">عملکرد</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#technical">تکنیکال</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#portfolio">پورتفو</button></li>
        </ul>
        
        <div class="tab-content">
            <!-- وزن‌ها -->
            <div class="tab-pane active" id="weights">
                <div class="card">
                    <div class="card-header"><i class="bi bi-sliders"></i> وزن‌های معیارها</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">وزن EPS (سودآوری)</label>
                                <input type="range" class="form-range" id="weights_eps_weight" min="0" max="1" step="0.05" value="{{ settings['weights']['eps_weight'] }}">
                                <span class="range-value" id="weights_eps_weight_val">{{ settings['weights']['eps_weight'] }}</span>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">وزن P/B (ارزش ذاتی)</label>
                                <input type="range" class="form-range" id="weights_pb_weight" min="0" max="1" step="0.05" value="{{ settings['weights']['pb_weight'] }}">
                                <span class="range-value" id="weights_pb_weight_val">{{ settings['weights']['pb_weight'] }}</span>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">وزن رشد EPS</label>
                                <input type="range" class="form-range" id="weights_eps_growth_weight" min="0" max="1" step="0.05" value="{{ settings['weights']['eps_growth_weight'] }}">
                                <span class="range-value" id="weights_eps_growth_weight_val">{{ settings['weights']['eps_growth_weight'] }}</span>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">وزن P/E</label>
                                <input type="range" class="form-range" id="weights_pe_weight" min="0" max="1" step="0.05" value="{{ settings['weights']['pe_weight'] }}">
                                <span class="range-value" id="weights_pe_weight_val">{{ settings['weights']['pe_weight'] }}</span>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">وزن RSI</label>
                                <input type="range" class="form-range" id="weights_rsi_weight" min="0" max="1" step="0.05" value="{{ settings['weights']['rsi_weight'] }}">
                                <span class="range-value" id="weights_rsi_weight_val">{{ settings['weights']['rsi_weight'] }}</span>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">وزن حجم معاملات</label>
                                <input type="range" class="form-range" id="weights_volume_weight" min="0" max="1" step="0.05" value="{{ settings['weights']['volume_weight'] }}">
                                <span class="range-value" id="weights_volume_weight_val">{{ settings['weights']['volume_weight'] }}</span>
                            </div>
                        </div>
                        <div class="alert alert-info">
                            مجموع وزن‌ها باید برابر 1 باشد. مجموع فعلی: <span id="total_weights">0</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- EPS -->
            <div class="tab-pane" id="eps">
                <div class="card">
                    <div class="card-header"><i class="bi bi-bar-chart"></i> آستانه‌های EPS</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4 mb-3">
                                <label class="form-label">EPS عالی (> این مقدار)</label>
                                <input type="number" class="form-control" id="eps_thresholds_excellent" value="{{ settings['eps_thresholds']['excellent'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">EPS خیلی خوب (> این مقدار)</label>
                                <input type="number" class="form-control" id="eps_thresholds_very_good" value="{{ settings['eps_thresholds']['very_good'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">EPS خوب (> این مقدار)</label>
                                <input type="number" class="form-control" id="eps_thresholds_good" value="{{ settings['eps_thresholds']['good'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">EPS متوسط (> این مقدار)</label>
                                <input type="number" class="form-control" id="eps_thresholds_average" value="{{ settings['eps_thresholds']['average'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">EPS پایین (> این مقدار)</label>
                                <input type="number" class="form-control" id="eps_thresholds_below_average" value="{{ settings['eps_thresholds']['below_average'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">EPS خیلی پایین (> این مقدار)</label>
                                <input type="number" class="form-control" id="eps_thresholds_low" value="{{ settings['eps_thresholds']['low'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">امتیازات EPS</h6>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز عالی</label>
                                <input type="number" class="form-control" id="eps_scores_excellent" value="{{ settings['eps_thresholds']['scores']['excellent'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز خیلی خوب</label>
                                <input type="number" class="form-control" id="eps_scores_very_good" value="{{ settings['eps_thresholds']['scores']['very_good'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز خوب</label>
                                <input type="number" class="form-control" id="eps_scores_good" value="{{ settings['eps_thresholds']['scores']['good'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز متوسط</label>
                                <input type="number" class="form-control" id="eps_scores_average" value="{{ settings['eps_thresholds']['scores']['average'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز پایین</label>
                                <input type="number" class="form-control" id="eps_scores_below_average" value="{{ settings['eps_thresholds']['scores']['below_average'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز خیلی پایین</label>
                                <input type="number" class="form-control" id="eps_scores_low" value="{{ settings['eps_thresholds']['scores']['low'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز مثبت</label>
                                <input type="number" class="form-control" id="eps_scores_positive" value="{{ settings['eps_thresholds']['scores']['positive'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز پیش‌فرض</label>
                                <input type="number" class="form-control" id="eps_scores_default" value="{{ settings['eps_thresholds']['scores']['default'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- P/B -->
            <div class="tab-pane" id="pb">
                <div class="card">
                    <div class="card-header"><i class="bi bi-graph-up"></i> آستانه‌های P/B</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">P/B عالی (≤ این مقدار)</label>
                                <input type="number" class="form-control" id="pb_thresholds_excellent" step="0.1" value="{{ settings['pb_thresholds']['excellent'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">P/B خیلی خوب (≤ این مقدار)</label>
                                <input type="number" class="form-control" id="pb_thresholds_very_good" step="0.1" value="{{ settings['pb_thresholds']['very_good'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">P/B خوب (≤ این مقدار)</label>
                                <input type="number" class="form-control" id="pb_thresholds_good" step="0.1" value="{{ settings['pb_thresholds']['good'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">P/B متوسط (≤ این مقدار)</label>
                                <input type="number" class="form-control" id="pb_thresholds_average" step="0.1" value="{{ settings['pb_thresholds']['average'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">امتیازات P/B</h6>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز عالی</label>
                                <input type="number" class="form-control" id="pb_scores_excellent" value="{{ settings['pb_thresholds']['scores']['excellent'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز خیلی خوب</label>
                                <input type="number" class="form-control" id="pb_scores_very_good" value="{{ settings['pb_thresholds']['scores']['very_good'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز خوب</label>
                                <input type="number" class="form-control" id="pb_scores_good" value="{{ settings['pb_thresholds']['scores']['good'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز متوسط</label>
                                <input type="number" class="form-control" id="pb_scores_average" value="{{ settings['pb_thresholds']['scores']['average'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز ضعیف</label>
                                <input type="number" class="form-control" id="pb_scores_poor" value="{{ settings['pb_thresholds']['scores']['poor'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- P/E -->
            <div class="tab-pane" id="pe">
                <div class="card">
                    <div class="card-header"><i class="bi bi-graph-down"></i> آستانه‌های P/E</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4 mb-3">
                                <label class="form-label">P/E عالی (≤ این مقدار)</label>
                                <input type="number" class="form-control" id="pe_thresholds_excellent" step="0.1" value="{{ settings['pe_thresholds']['excellent'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">P/E خیلی خوب (≤ این مقدار)</label>
                                <input type="number" class="form-control" id="pe_thresholds_very_good" step="0.1" value="{{ settings['pe_thresholds']['very_good'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">P/E خوب (≤ این مقدار)</label>
                                <input type="number" class="form-control" id="pe_thresholds_good" step="0.1" value="{{ settings['pe_thresholds']['good'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">امتیازات P/E</h6>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز عالی</label>
                                <input type="number" class="form-control" id="pe_scores_excellent" value="{{ settings['pe_thresholds']['scores']['excellent'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز خیلی خوب</label>
                                <input type="number" class="form-control" id="pe_scores_very_good" value="{{ settings['pe_thresholds']['scores']['very_good'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز خوب</label>
                                <input type="number" class="form-control" id="pe_scores_good" value="{{ settings['pe_thresholds']['scores']['good'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز ضعیف</label>
                                <input type="number" class="form-control" id="pe_scores_poor" value="{{ settings['pe_thresholds']['scores']['poor'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- RSI -->
            <div class="tab-pane" id="rsi">
                <div class="card">
                    <div class="card-header"><i class="bi bi-activity"></i> آستانه‌های RSI</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">اشباع فروش شدید (< این مقدار)</label>
                                <input type="number" class="form-control" id="rsi_oversold_extreme" value="{{ settings['rsi_thresholds']['oversold_extreme'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">اشباع فروش (< این مقدار)</label>
                                <input type="number" class="form-control" id="rsi_oversold" value="{{ settings['rsi_thresholds']['oversold'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">اشباع خرید (≥ این مقدار)</label>
                                <input type="number" class="form-control" id="rsi_overbought" value="{{ settings['rsi_thresholds']['overbought'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">نزدیک اشباع خرید (≥ این مقدار)</label>
                                <input type="number" class="form-control" id="rsi_overbought_extreme" value="{{ settings['rsi_thresholds']['overbought_extreme'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">امتیازات RSI</h6>
                        <div class="row">
                            <div class="col-md-2 mb-3">
                                <label class="form-label">اشباع فروش شدید</label>
                                <input type="number" class="form-control" id="rsi_scores_oversold_extreme" value="{{ settings['rsi_thresholds']['scores']['oversold_extreme'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">اشباع فروش</label>
                                <input type="number" class="form-control" id="rsi_scores_oversold" value="{{ settings['rsi_thresholds']['scores']['oversold'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">خنثی پایین</label>
                                <input type="number" class="form-control" id="rsi_scores_neutral_low" value="{{ settings['rsi_thresholds']['scores']['neutral_low'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">خنثی بالا</label>
                                <input type="number" class="form-control" id="rsi_scores_neutral_high" value="{{ settings['rsi_thresholds']['scores']['neutral_high'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">اشباع خرید</label>
                                <input type="number" class="form-control" id="rsi_scores_overbought" value="{{ settings['rsi_thresholds']['scores']['overbought'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- حجم -->
            <div class="tab-pane" id="volume">
                <div class="card">
                    <div class="card-header"><i class="bi bi-bar-chart"></i> آستانه‌های حجم</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">حجم عالی (> این مقدار)</label>
                                <input type="number" class="form-control" id="volume_excellent" value="{{ settings['volume_thresholds']['excellent'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">حجم خیلی خوب (> این مقدار)</label>
                                <input type="number" class="form-control" id="volume_very_good" value="{{ settings['volume_thresholds']['very_good'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">حجم خوب (> این مقدار)</label>
                                <input type="number" class="form-control" id="volume_good" value="{{ settings['volume_thresholds']['good'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">حجم متوسط (> این مقدار)</label>
                                <input type="number" class="form-control" id="volume_average" value="{{ settings['volume_thresholds']['average'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">امتیازات حجم</h6>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز عالی</label>
                                <input type="number" class="form-control" id="volume_scores_excellent" value="{{ settings['volume_thresholds']['scores']['excellent'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز خیلی خوب</label>
                                <input type="number" class="form-control" id="volume_scores_very_good" value="{{ settings['volume_thresholds']['scores']['very_good'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز خوب</label>
                                <input type="number" class="form-control" id="volume_scores_good" value="{{ settings['volume_thresholds']['scores']['good'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز متوسط</label>
                                <input type="number" class="form-control" id="volume_scores_average" value="{{ settings['volume_thresholds']['scores']['average'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- فیلترها -->
            <div class="tab-pane" id="filters">
                <div class="card">
                    <div class="card-header"><i class="bi bi-funnel"></i> فیلترهای ورودی</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4 mb-3">
                                <label class="form-label">حداقل حجم معاملات</label>
                                <input type="number" class="form-control" id="filters_min_volume" value="{{ settings['filters']['min_volume'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">حداکثر P/B</label>
                                <input type="number" class="form-control" id="filters_max_pb" step="0.1" value="{{ settings['filters']['max_pb'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">حداقل EPS</label>
                                <input type="number" class="form-control" id="filters_min_eps" value="{{ settings['filters']['min_eps'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">حداکثر P/E</label>
                                <input type="number" class="form-control" id="filters_max_pe" step="0.1" value="{{ settings['filters']['max_pe'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">حداقل RSI</label>
                                <input type="number" class="form-control" id="filters_rsi_min" value="{{ settings['filters']['rsi_min'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">حداکثر RSI</label>
                                <input type="number" class="form-control" id="filters_rsi_max" value="{{ settings['filters']['rsi_max'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">حداکثر بازدهی ۱ماه</label>
                                <input type="number" class="form-control" id="filters_max_return" value="{{ settings['filters']['max_1month_return'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">حداقل قیمت</label>
                                <input type="number" class="form-control" id="filters_min_price" value="{{ settings['filters']['min_price'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">حداکثر قیمت</label>
                                <input type="number" class="form-control" id="filters_max_price" value="{{ settings['filters']['max_price'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- رد صلاحیت -->
            <div class="tab-pane" id="disqualifiers">
                <div class="card">
                    <div class="card-header"><i class="bi bi-exclamation-triangle"></i> معیارهای رد صلاحیت</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">حداکثر P/B برای رد</label>
                                <input type="number" class="form-control" id="disqualifiers_max_pb" step="0.1" value="{{ settings['disqualifiers']['max_pb_disqualify'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">حداقل EPS برای رد</label>
                                <input type="number" class="form-control" id="disqualifiers_min_eps" value="{{ settings['disqualifiers']['min_eps_disqualify'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">حداکثر RSI برای رد</label>
                                <input type="number" class="form-control" id="disqualifiers_max_rsi" value="{{ settings['disqualifiers']['max_rsi_disqualify'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">حداکثر بازدهی برای رد</label>
                                <input type="number" class="form-control" id="disqualifiers_max_return" value="{{ settings['disqualifiers']['max_1month_return_disqualify'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- اعتبارسنجی نهایی -->
            <div class="tab-pane" id="validation">
                <div class="card">
                    <div class="card-header"><i class="bi bi-check-circle"></i> معیارهای اعتبارسنجی نهایی</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">حداقل امتیاز نهایی</label>
                                <input type="number" class="form-control" id="validation_min_score" value="{{ settings['validation']['min_final_score'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">حداکثر P/B نهایی</label>
                                <input type="number" class="form-control" id="validation_max_pb" step="0.1" value="{{ settings['validation']['max_pb_final'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">حداکثر P/E نهایی</label>
                                <input type="number" class="form-control" id="validation_max_pe" step="0.1" value="{{ settings['validation']['max_pe_final'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">حداکثر RSI نهایی</label>
                                <input type="number" class="form-control" id="validation_max_rsi" value="{{ settings['validation']['max_rsi_final'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">حداکثر سهام نهایی</label>
                                <input type="number" class="form-control" id="validation_max_stocks" value="{{ settings['validation']['max_stocks_final'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- وضعیت -->
            <div class="tab-pane" id="status">
                <div class="card">
                    <div class="card-header"><i class="bi bi-flag"></i> آستانه‌های وضعیت</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-2 mb-3">
                                <label class="form-label">عالی (≥ این مقدار)</label>
                                <input type="number" class="form-control" id="status_excellent" value="{{ settings['status_thresholds']['excellent'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">خیلی خوب (≥ این مقدار)</label>
                                <input type="number" class="form-control" id="status_very_good" value="{{ settings['status_thresholds']['very_good'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">خوب (≥ این مقدار)</label>
                                <input type="number" class="form-control" id="status_good" value="{{ settings['status_thresholds']['good'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">متوسط (≥ این مقدار)</label>
                                <input type="number" class="form-control" id="status_average" value="{{ settings['status_thresholds']['average'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">قابل قبول (≥ این مقدار)</label>
                                <input type="number" class="form-control" id="status_acceptable" value="{{ settings['status_thresholds']['acceptable'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- حباب -->
            <div class="tab-pane" id="bubble">
                <div class="card">
                    <div class="card-header"><i class="bi bi-balloon"></i> تنظیمات تحلیل حباب</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">P/E بالا</label>
                                <input type="number" class="form-control" id="bubble_pe_high" value="{{ settings['bubble']['pe_high'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">P/B بسیار بالا</label>
                                <input type="number" class="form-control" id="bubble_pb_very_high" step="0.1" value="{{ settings['bubble']['pb_very_high'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">بازدهی ماهانه بسیار بالا</label>
                                <input type="number" class="form-control" id="bubble_return_1m" value="{{ settings['bubble']['return_1m_very_high'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">بازدهی سه ماهه بسیار بالا</label>
                                <input type="number" class="form-control" id="bubble_return_3m" value="{{ settings['bubble']['return_3m_very_high'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">نسبت حجم بسیار بالا</label>
                                <input type="number" class="form-control" id="bubble_volume_ratio" step="0.1" value="{{ settings['bubble']['volume_ratio_very_high'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">وزن‌های تحلیل حباب</h6>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">وزن P/E</label>
                                <input type="number" class="form-control" id="bubble_weights_pe" step="0.1" value="{{ settings['bubble']['weights']['pe'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">وزن P/B</label>
                                <input type="number" class="form-control" id="bubble_weights_pb" step="0.1" value="{{ settings['bubble']['weights']['pb'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">وزن رشد</label>
                                <input type="number" class="form-control" id="bubble_weights_growth" step="0.1" value="{{ settings['bubble']['weights']['growth'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">وزن حجم</label>
                                <input type="number" class="form-control" id="bubble_weights_volume" step="0.1" value="{{ settings['bubble']['weights']['volume'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- ارزش ذاتی -->
            <div class="tab-pane" id="intrinsic">
                <div class="card">
                    <div class="card-header"><i class="bi bi-calculator"></i> تنظیمات ارزش ذاتی</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">ضریب P/E</label>
                                <input type="number" class="form-control" id="intrinsic_pe_multiplier" step="0.1" value="{{ settings['intrinsic_value']['pe_multiplier'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">ضریب P/B</label>
                                <input type="number" class="form-control" id="intrinsic_pb_multiplier" step="0.1" value="{{ settings['intrinsic_value']['pb_multiplier'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">پایه گراهام</label>
                                <input type="number" class="form-control" id="intrinsic_graham_base" step="0.1" value="{{ settings['intrinsic_value']['graham_base'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">رشد گراهام</label>
                                <input type="number" class="form-control" id="intrinsic_graham_growth" step="0.1" value="{{ settings['intrinsic_value']['graham_growth'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">نسبت تقسیم سود</label>
                                <input type="number" class="form-control" id="intrinsic_dividend_payout" step="0.1" value="{{ settings['intrinsic_value']['dividend_payout'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">نرخ تنزیل</label>
                                <input type="number" class="form-control" id="intrinsic_discount_rate" step="0.01" value="{{ settings['intrinsic_value']['discount_rate'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">آستانه‌های خرید/فروش</h6>
                        <div class="row">
                            <div class="col-md-2 mb-3">
                                <label class="form-label">خرید قوی</label>
                                <input type="number" class="form-control" id="intrinsic_thresholds_strong_buy" step="0.1" value="{{ settings['intrinsic_value']['thresholds']['strong_buy'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">خرید</label>
                                <input type="number" class="form-control" id="intrinsic_thresholds_buy" step="0.1" value="{{ settings['intrinsic_value']['thresholds']['buy'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">خرید محتاطانه</label>
                                <input type="number" class="form-control" id="intrinsic_thresholds_cautious_buy" step="0.1" value="{{ settings['intrinsic_value']['thresholds']['cautious_buy'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">نگهداری</label>
                                <input type="number" class="form-control" id="intrinsic_thresholds_hold" step="0.1" value="{{ settings['intrinsic_value']['thresholds']['hold'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">فروش محتاطانه</label>
                                <input type="number" class="form-control" id="intrinsic_thresholds_cautious_sell" step="0.1" value="{{ settings['intrinsic_value']['thresholds']['cautious_sell'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">فروش</label>
                                <input type="number" class="form-control" id="intrinsic_thresholds_sell" step="0.1" value="{{ settings['intrinsic_value']['thresholds']['sell'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">امتیازات ارزش ذاتی</h6>
                        <div class="row">
                            <div class="col-md-2 mb-3">
                                <label class="form-label">خرید قوی</label>
                                <input type="number" class="form-control" id="intrinsic_scores_strong_buy" value="{{ settings['intrinsic_value']['scores']['strong_buy'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">خرید</label>
                                <input type="number" class="form-control" id="intrinsic_scores_buy" value="{{ settings['intrinsic_value']['scores']['buy'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">خرید محتاطانه</label>
                                <input type="number" class="form-control" id="intrinsic_scores_cautious_buy" value="{{ settings['intrinsic_value']['scores']['cautious_buy'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">نگهداری</label>
                                <input type="number" class="form-control" id="intrinsic_scores_hold" value="{{ settings['intrinsic_value']['scores']['hold'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">فروش محتاطانه</label>
                                <input type="number" class="form-control" id="intrinsic_scores_cautious_sell" value="{{ settings['intrinsic_value']['scores']['cautious_sell'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">فروش</label>
                                <input type="number" class="form-control" id="intrinsic_scores_sell" value="{{ settings['intrinsic_value']['scores']['sell'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">فروش قوی</label>
                                <input type="number" class="form-control" id="intrinsic_scores_strong_sell" value="{{ settings['intrinsic_value']['scores']['strong_sell'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- تابلوخوانی -->
            <div class="tab-pane" id="tape">
                <div class="card">
                    <div class="card-header"><i class="bi bi-graph-up-arrow"></i> تنظیمات تابلوخوانی</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">حداکثر نسبت تقاضا به عرضه</label>
                                <input type="number" class="form-control" id="tape_demand_supply_max" step="0.1" value="{{ settings['tape_reading']['demand_supply_max'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">امتیاز پایه</label>
                                <input type="number" class="form-control" id="tape_base_score" value="{{ settings['tape_reading']['base_score'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">ضریب امتیاز</label>
                                <input type="number" class="form-control" id="tape_score_multiplier" step="0.1" value="{{ settings['tape_reading']['score_multiplier'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">آستانه‌های شاخص قدرت</h6>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">صعودی قوی (> این مقدار)</label>
                                <input type="number" class="form-control" id="tape_power_very_bullish" step="0.1" value="{{ settings['tape_reading']['power_index_thresholds']['very_bullish'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">صعودی (> این مقدار)</label>
                                <input type="number" class="form-control" id="tape_power_bullish" step="0.1" value="{{ settings['tape_reading']['power_index_thresholds']['bullish'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">نزولی (< این مقدار)</label>
                                <input type="number" class="form-control" id="tape_power_bearish" step="0.1" value="{{ settings['tape_reading']['power_index_thresholds']['bearish'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">نزولی قوی (< این مقدار)</label>
                                <input type="number" class="form-control" id="tape_power_very_bearish" step="0.1" value="{{ settings['tape_reading']['power_index_thresholds']['very_bearish'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- ریسک -->
            <div class="tab-pane" id="risk">
                <div class="card">
                    <div class="card-header"><i class="bi bi-shield"></i> تنظیمات ریسک</div>
                    <div class="card-body">
                        <h6 class="section-title">آستانه‌های بتا</h6>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">بسیار بالا (> این مقدار)</label>
                                <input type="number" class="form-control" id="risk_beta_very_high" step="0.1" value="{{ settings['risk']['beta_thresholds']['very_high'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">بالا (> این مقدار)</label>
                                <input type="number" class="form-control" id="risk_beta_high" step="0.1" value="{{ settings['risk']['beta_thresholds']['high'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">متوسط (> این مقدار)</label>
                                <input type="number" class="form-control" id="risk_beta_medium" step="0.1" value="{{ settings['risk']['beta_thresholds']['medium'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">پایین (< این مقدار)</label>
                                <input type="number" class="form-control" id="risk_beta_low" step="0.1" value="{{ settings['risk']['beta_thresholds']['low'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">آستانه‌های حجم</h6>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">بسیار پایین (< این مقدار)</label>
                                <input type="number" class="form-control" id="risk_volume_very_low" value="{{ settings['risk']['volume_thresholds']['very_low'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">پایین (< این مقدار)</label>
                                <input type="number" class="form-control" id="risk_volume_low" value="{{ settings['risk']['volume_thresholds']['low'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">متوسط (< این مقدار)</label>
                                <input type="number" class="form-control" id="risk_volume_medium" value="{{ settings['risk']['volume_thresholds']['medium'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">بالا (≥ این مقدار)</label>
                                <input type="number" class="form-control" id="risk_volume_high" value="{{ settings['risk']['volume_thresholds']['high'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">آستانه‌های نوسان</h6>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">بسیار بالا (> این مقدار)</label>
                                <input type="number" class="form-control" id="risk_volatility_very_high" value="{{ settings['risk']['volatility_thresholds']['very_high'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">بالا (> این مقدار)</label>
                                <input type="number" class="form-control" id="risk_volatility_high" value="{{ settings['risk']['volatility_thresholds']['high'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">متوسط (> این مقدار)</label>
                                <input type="number" class="form-control" id="risk_volatility_medium" value="{{ settings['risk']['volatility_thresholds']['medium'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">وزن‌های ریسک</h6>
                        <div class="row">
                            <div class="col-md-2 mb-3">
                                <label class="form-label">بتا</label>
                                <input type="number" class="form-control" id="risk_weights_beta" step="0.1" value="{{ settings['risk']['weights']['beta'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">نقدشوندگی</label>
                                <input type="number" class="form-control" id="risk_weights_liquidity" step="0.1" value="{{ settings['risk']['weights']['liquidity'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">نوسان</label>
                                <input type="number" class="form-control" id="risk_weights_volatility" step="0.1" value="{{ settings['risk']['weights']['volatility'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">RSI</label>
                                <input type="number" class="form-control" id="risk_weights_rsi" step="0.1" value="{{ settings['risk']['weights']['rsi'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">P/B</label>
                                <input type="number" class="form-control" id="risk_weights_pb" step="0.1" value="{{ settings['risk']['weights']['pb'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">EPS</label>
                                <input type="number" class="form-control" id="risk_weights_eps" step="0.1" value="{{ settings['risk']['weights']['eps'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- عملکرد -->
            <div class="tab-pane" id="performance">
                <div class="card">
                    <div class="card-header"><i class="bi bi-graph-up"></i> تنظیمات تحلیل عملکرد</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4 mb-3">
                                <label class="form-label">امتیاز پایه</label>
                                <input type="number" class="form-control" id="performance_base_score" value="{{ settings['performance']['base_score'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">ضریب امتیاز</label>
                                <input type="number" class="form-control" id="performance_score_multiplier" step="0.1" value="{{ settings['performance']['score_multiplier'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">وزن‌های CAGR</h6>
                        <div class="row">
                            <div class="col-md-2 mb-3">
                                <label class="form-label">۱ ماه</label>
                                <input type="number" class="form-control" id="performance_cagr_weights_1m" step="0.1" value="{{ settings['performance']['cagr_weights']['1m'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">۳ ماه</label>
                                <input type="number" class="form-control" id="performance_cagr_weights_3m" step="0.1" value="{{ settings['performance']['cagr_weights']['3m'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">۶ ماه</label>
                                <input type="number" class="form-control" id="performance_cagr_weights_6m" step="0.1" value="{{ settings['performance']['cagr_weights']['6m'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">۱ سال</label>
                                <input type="number" class="form-control" id="performance_cagr_weights_1y" step="0.1" value="{{ settings['performance']['cagr_weights']['1y'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">ثبات</label>
                                <input type="number" class="form-control" id="performance_cagr_weights_consistency" step="0.1" value="{{ settings['performance']['cagr_weights']['consistency'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- تکنیکال -->
            <div class="tab-pane" id="technical">
                <div class="card">
                    <div class="card-header"><i class="bi bi-activity"></i> تنظیمات تحلیل تکنیکال</div>
                    <div class="card-body">
                        <h6 class="section-title">آستانه‌های RSI</h6>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">اشباع فروش شدید</label>
                                <input type="number" class="form-control" id="technical_rsi_oversold_extreme" value="{{ settings['technical']['rsi_thresholds']['oversold_extreme'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">اشباع فروش</label>
                                <input type="number" class="form-control" id="technical_rsi_oversold" value="{{ settings['technical']['rsi_thresholds']['oversold'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">اشباع خرید</label>
                                <input type="number" class="form-control" id="technical_rsi_overbought" value="{{ settings['technical']['rsi_thresholds']['overbought'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">نزدیک اشباع خرید</label>
                                <input type="number" class="form-control" id="technical_rsi_overbought_extreme" value="{{ settings['technical']['rsi_thresholds']['overbought_extreme'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">آستانه‌های MFI</h6>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">اشباع فروش شدید</label>
                                <input type="number" class="form-control" id="technical_mfi_oversold_extreme" value="{{ settings['technical']['mfi_thresholds']['oversold_extreme'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">اشباع فروش</label>
                                <input type="number" class="form-control" id="technical_mfi_oversold" value="{{ settings['technical']['mfi_thresholds']['oversold'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">اشباع خرید</label>
                                <input type="number" class="form-control" id="technical_mfi_overbought" value="{{ settings['technical']['mfi_thresholds']['overbought'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">نزدیک اشباع خرید</label>
                                <input type="number" class="form-control" id="technical_mfi_overbought_extreme" value="{{ settings['technical']['mfi_thresholds']['overbought_extreme'] }}">
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-4 mb-3">
                                <label class="form-label">امتیاز پایه</label>
                                <input type="number" class="form-control" id="technical_base_score" value="{{ settings['technical']['base_score'] }}">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">ضریب امتیاز</label>
                                <input type="number" class="form-control" id="technical_score_multiplier" step="0.1" value="{{ settings['technical']['score_multiplier'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- پورتفو -->
            <div class="tab-pane" id="portfolio">
                <div class="card">
                    <div class="card-header"><i class="bi bi-briefcase"></i> تنظیمات پورتفو</div>
                    <div class="card-body">
                        <h6 class="section-title">آستانه‌های هشدار</h6>
                        <div class="row">
                            <div class="col-md-2 mb-3">
                                <label class="form-label">سود بالا (%)</label>
                                <input type="number" class="form-control" id="portfolio_alert_profit_high" value="{{ settings['portfolio']['alert_thresholds']['profit_high'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">سود متوسط (%)</label>
                                <input type="number" class="form-control" id="portfolio_alert_profit_medium" value="{{ settings['portfolio']['alert_thresholds']['profit_medium'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">ضرر بالا (%)</label>
                                <input type="number" class="form-control" id="portfolio_alert_loss_high" value="{{ settings['portfolio']['alert_thresholds']['loss_high'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">ضرر متوسط (%)</label>
                                <input type="number" class="form-control" id="portfolio_alert_loss_medium" value="{{ settings['portfolio']['alert_thresholds']['loss_medium'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">ضرر کم (%)</label>
                                <input type="number" class="form-control" id="portfolio_alert_loss_low" value="{{ settings['portfolio']['alert_thresholds']['loss_low'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">ضرر خیلی کم (%)</label>
                                <input type="number" class="form-control" id="portfolio_alert_loss_very_low" value="{{ settings['portfolio']['alert_thresholds']['loss_very_low'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">آستانه‌های RSI</h6>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">RSI بالا</label>
                                <input type="number" class="form-control" id="portfolio_rsi_high" value="{{ settings['portfolio']['rsi_thresholds']['high'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">RSI پایین</label>
                                <input type="number" class="form-control" id="portfolio_rsi_low" value="{{ settings['portfolio']['rsi_thresholds']['low'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">آستانه‌های P/B</h6>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <label class="form-label">P/B بالا</label>
                                <input type="number" class="form-control" id="portfolio_pb_high" step="0.1" value="{{ settings['portfolio']['pb_thresholds']['high'] }}">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">P/B پایین</label>
                                <input type="number" class="form-control" id="portfolio_pb_low" step="0.1" value="{{ settings['portfolio']['pb_thresholds']['low'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">آستانه‌های وضعیت</h6>
                        <div class="row">
                            <div class="col-md-2 mb-3">
                                <label class="form-label">عالی (%)</label>
                                <input type="number" class="form-control" id="portfolio_status_excellent" value="{{ settings['portfolio']['status_thresholds']['excellent'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">خیلی خوب (%)</label>
                                <input type="number" class="form-control" id="portfolio_status_very_good" value="{{ settings['portfolio']['status_thresholds']['very_good'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">خوب (%)</label>
                                <input type="number" class="form-control" id="portfolio_status_good" value="{{ settings['portfolio']['status_thresholds']['good'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">متوسط (%)</label>
                                <input type="number" class="form-control" id="portfolio_status_average" value="{{ settings['portfolio']['status_thresholds']['average'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">ضعیف (%)</label>
                                <input type="number" class="form-control" id="portfolio_status_poor" value="{{ settings['portfolio']['status_thresholds']['poor'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">بحرانی (%)</label>
                                <input type="number" class="form-control" id="portfolio_status_very_poor" value="{{ settings['portfolio']['status_thresholds']['very_poor'] }}">
                            </div>
                        </div>
                        
                        <h6 class="section-title">امتیازات تنوع</h6>
                        <div class="row">
                            <div class="col-md-2 mb-3">
                                <label class="form-label">۱۰+ سهم</label>
                                <input type="number" class="form-control" id="portfolio_diversity_10" value="{{ settings['portfolio']['diversity_scores']['10'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">۷+ سهم</label>
                                <input type="number" class="form-control" id="portfolio_diversity_7" value="{{ settings['portfolio']['diversity_scores']['7'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">۵+ سهم</label>
                                <input type="number" class="form-control" id="portfolio_diversity_5" value="{{ settings['portfolio']['diversity_scores']['5'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">۳+ سهم</label>
                                <input type="number" class="form-control" id="portfolio_diversity_3" value="{{ settings['portfolio']['diversity_scores']['3'] }}">
                            </div>
                            <div class="col-md-2 mb-3">
                                <label class="form-label">پیش‌فرض</label>
                                <input type="number" class="form-control" id="portfolio_diversity_default" value="{{ settings['portfolio']['diversity_scores']['default'] }}">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // به‌روزرسانی مقادیر اسلایدرها
        document.querySelectorAll('input[type=range]').forEach(slider => {
            slider.addEventListener('input', function() {
                document.getElementById(this.id + '_val').textContent = this.value;
                updateTotalWeights();
            });
        });
        
        // محاسبه مجموع وزن‌ها
        function updateTotalWeights() {
            let total = 0;
            const eps = parseFloat(document.getElementById('weights_eps_weight')?.value || 0);
            const pb = parseFloat(document.getElementById('weights_pb_weight')?.value || 0);
            const growth = parseFloat(document.getElementById('weights_eps_growth_weight')?.value || 0);
            const pe = parseFloat(document.getElementById('weights_pe_weight')?.value || 0);
            const rsi = parseFloat(document.getElementById('weights_rsi_weight')?.value || 0);
            const volume = parseFloat(document.getElementById('weights_volume_weight')?.value || 0);
            
            total = eps + pb + growth + pe + rsi + volume;
            
            const totalElement = document.getElementById('total_weights');
            if (totalElement) {
                totalElement.textContent = total.toFixed(2);
                totalElement.style.color = Math.abs(total - 1) < 0.01 ? '#4caf50' : '#f44336';
            }
        }
        
        // جمع‌آوری تنظیمات
        function collectSettings() {
            return {
                weights: {
                    eps_weight: parseFloat(document.getElementById('weights_eps_weight').value),
                    pb_weight: parseFloat(document.getElementById('weights_pb_weight').value),
                    eps_growth_weight: parseFloat(document.getElementById('weights_eps_growth_weight').value),
                    pe_weight: parseFloat(document.getElementById('weights_pe_weight').value),
                    rsi_weight: parseFloat(document.getElementById('weights_rsi_weight').value),
                    volume_weight: parseFloat(document.getElementById('weights_volume_weight').value)
                },
                eps_thresholds: {
                    excellent: parseInt(document.getElementById('eps_thresholds_excellent').value),
                    very_good: parseInt(document.getElementById('eps_thresholds_very_good').value),
                    good: parseInt(document.getElementById('eps_thresholds_good').value),
                    average: parseInt(document.getElementById('eps_thresholds_average').value),
                    below_average: parseInt(document.getElementById('eps_thresholds_below_average').value),
                    low: parseInt(document.getElementById('eps_thresholds_low').value),
                    scores: {
                        excellent: parseInt(document.getElementById('eps_scores_excellent').value),
                        very_good: parseInt(document.getElementById('eps_scores_very_good').value),
                        good: parseInt(document.getElementById('eps_scores_good').value),
                        average: parseInt(document.getElementById('eps_scores_average').value),
                        below_average: parseInt(document.getElementById('eps_scores_below_average').value),
                        low: parseInt(document.getElementById('eps_scores_low').value),
                        positive: parseInt(document.getElementById('eps_scores_positive').value),
                        default: parseInt(document.getElementById('eps_scores_default').value)
                    }
                },
                pb_thresholds: {
                    excellent: parseFloat(document.getElementById('pb_thresholds_excellent').value),
                    very_good: parseFloat(document.getElementById('pb_thresholds_very_good').value),
                    good: parseFloat(document.getElementById('pb_thresholds_good').value),
                    average: parseFloat(document.getElementById('pb_thresholds_average').value),
                    scores: {
                        excellent: parseInt(document.getElementById('pb_scores_excellent').value),
                        very_good: parseInt(document.getElementById('pb_scores_very_good').value),
                        good: parseInt(document.getElementById('pb_scores_good').value),
                        average: parseInt(document.getElementById('pb_scores_average').value),
                        poor: parseInt(document.getElementById('pb_scores_poor').value)
                    }
                },
                pe_thresholds: {
                    excellent: parseFloat(document.getElementById('pe_thresholds_excellent').value),
                    very_good: parseFloat(document.getElementById('pe_thresholds_very_good').value),
                    good: parseFloat(document.getElementById('pe_thresholds_good').value),
                    scores: {
                        excellent: parseInt(document.getElementById('pe_scores_excellent').value),
                        very_good: parseInt(document.getElementById('pe_scores_very_good').value),
                        good: parseInt(document.getElementById('pe_scores_good').value),
                        poor: parseInt(document.getElementById('pe_scores_poor').value)
                    }
                },
                rsi_thresholds: {
                    oversold_extreme: parseInt(document.getElementById('rsi_oversold_extreme').value),
                    oversold: parseInt(document.getElementById('rsi_oversold').value),
                    overbought: parseInt(document.getElementById('rsi_overbought').value),
                    overbought_extreme: parseInt(document.getElementById('rsi_overbought_extreme').value),
                    scores: {
                        oversold_extreme: parseInt(document.getElementById('rsi_scores_oversold_extreme').value),
                        oversold: parseInt(document.getElementById('rsi_scores_oversold').value),
                        neutral_low: parseInt(document.getElementById('rsi_scores_neutral_low').value),
                        neutral_high: parseInt(document.getElementById('rsi_scores_neutral_high').value),
                        overbought: parseInt(document.getElementById('rsi_scores_overbought').value)
                    }
                },
                volume_thresholds: {
                    excellent: parseInt(document.getElementById('volume_excellent').value),
                    very_good: parseInt(document.getElementById('volume_very_good').value),
                    good: parseInt(document.getElementById('volume_good').value),
                    average: parseInt(document.getElementById('volume_average').value),
                    scores: {
                        excellent: parseInt(document.getElementById('volume_scores_excellent').value),
                        very_good: parseInt(document.getElementById('volume_scores_very_good').value),
                        good: parseInt(document.getElementById('volume_scores_good').value),
                        average: parseInt(document.getElementById('volume_scores_average').value)
                    }
                },
                filters: {
                    min_volume: parseInt(document.getElementById('filters_min_volume').value),
                    max_pb: parseFloat(document.getElementById('filters_max_pb').value),
                    min_eps: parseInt(document.getElementById('filters_min_eps').value),
                    max_pe: parseFloat(document.getElementById('filters_max_pe').value),
                    rsi_min: parseInt(document.getElementById('filters_rsi_min').value),
                    rsi_max: parseInt(document.getElementById('filters_rsi_max').value),
                    max_1month_return: parseInt(document.getElementById('filters_max_return').value),
                    min_price: parseInt(document.getElementById('filters_min_price').value),
                    max_price: parseInt(document.getElementById('filters_max_price').value)
                },
                disqualifiers: {
                    max_pb_disqualify: parseFloat(document.getElementById('disqualifiers_max_pb').value),
                    min_eps_disqualify: parseInt(document.getElementById('disqualifiers_min_eps').value),
                    max_rsi_disqualify: parseInt(document.getElementById('disqualifiers_max_rsi').value),
                    max_1month_return_disqualify: parseInt(document.getElementById('disqualifiers_max_return').value)
                },
                validation: {
                    min_final_score: parseInt(document.getElementById('validation_min_score').value),
                    max_pb_final: parseFloat(document.getElementById('validation_max_pb').value),
                    max_pe_final: parseFloat(document.getElementById('validation_max_pe').value),
                    max_rsi_final: parseInt(document.getElementById('validation_max_rsi').value),
                    max_stocks_final: parseInt(document.getElementById('validation_max_stocks').value)
                },
                status_thresholds: {
                    excellent: parseInt(document.getElementById('status_excellent').value),
                    very_good: parseInt(document.getElementById('status_very_good').value),
                    good: parseInt(document.getElementById('status_good').value),
                    average: parseInt(document.getElementById('status_average').value),
                    acceptable: parseInt(document.getElementById('status_acceptable').value)
                },
                bubble: {
                    pe_high: parseInt(document.getElementById('bubble_pe_high').value),
                    pb_very_high: parseFloat(document.getElementById('bubble_pb_very_high').value),
                    return_1m_very_high: parseInt(document.getElementById('bubble_return_1m').value),
                    return_3m_very_high: parseInt(document.getElementById('bubble_return_3m').value),
                    volume_ratio_very_high: parseFloat(document.getElementById('bubble_volume_ratio').value),
                    weights: {
                        pe: parseFloat(document.getElementById('bubble_weights_pe').value),
                        pb: parseFloat(document.getElementById('bubble_weights_pb').value),
                        growth: parseFloat(document.getElementById('bubble_weights_growth').value),
                        volume: parseFloat(document.getElementById('bubble_weights_volume').value)
                    }
                },
                intrinsic_value: {
                    pe_multiplier: parseFloat(document.getElementById('intrinsic_pe_multiplier').value),
                    pb_multiplier: parseFloat(document.getElementById('intrinsic_pb_multiplier').value),
                    graham_base: parseFloat(document.getElementById('intrinsic_graham_base').value),
                    graham_growth: parseFloat(document.getElementById('intrinsic_graham_growth').value),
                    dividend_payout: parseFloat(document.getElementById('intrinsic_dividend_payout').value),
                    discount_rate: parseFloat(document.getElementById('intrinsic_discount_rate').value),
                    thresholds: {
                        strong_buy: parseFloat(document.getElementById('intrinsic_thresholds_strong_buy').value),
                        buy: parseFloat(document.getElementById('intrinsic_thresholds_buy').value),
                        cautious_buy: parseFloat(document.getElementById('intrinsic_thresholds_cautious_buy').value),
                        hold: parseFloat(document.getElementById('intrinsic_thresholds_hold').value),
                        cautious_sell: parseFloat(document.getElementById('intrinsic_thresholds_cautious_sell').value),
                        sell: parseFloat(document.getElementById('intrinsic_thresholds_sell').value)
                    },
                    scores: {
                        strong_buy: parseInt(document.getElementById('intrinsic_scores_strong_buy').value),
                        buy: parseInt(document.getElementById('intrinsic_scores_buy').value),
                        cautious_buy: parseInt(document.getElementById('intrinsic_scores_cautious_buy').value),
                        hold: parseInt(document.getElementById('intrinsic_scores_hold').value),
                        cautious_sell: parseInt(document.getElementById('intrinsic_scores_cautious_sell').value),
                        sell: parseInt(document.getElementById('intrinsic_scores_sell').value),
                        strong_sell: parseInt(document.getElementById('intrinsic_scores_strong_sell').value)
                    }
                },
                tape_reading: {
                    demand_supply_max: parseFloat(document.getElementById('tape_demand_supply_max').value),
                    base_score: parseInt(document.getElementById('tape_base_score').value),
                    score_multiplier: parseFloat(document.getElementById('tape_score_multiplier').value),
                    power_index_thresholds: {
                        very_bullish: parseFloat(document.getElementById('tape_power_very_bullish').value),
                        bullish: parseFloat(document.getElementById('tape_power_bullish').value),
                        bearish: parseFloat(document.getElementById('tape_power_bearish').value),
                        very_bearish: parseFloat(document.getElementById('tape_power_very_bearish').value)
                    }
                },
                risk: {
                    beta_thresholds: {
                        very_high: parseFloat(document.getElementById('risk_beta_very_high').value),
                        high: parseFloat(document.getElementById('risk_beta_high').value),
                        medium: parseFloat(document.getElementById('risk_beta_medium').value),
                        low: parseFloat(document.getElementById('risk_beta_low').value)
                    },
                    volume_thresholds: {
                        very_low: parseInt(document.getElementById('risk_volume_very_low').value),
                        low: parseInt(document.getElementById('risk_volume_low').value),
                        medium: parseInt(document.getElementById('risk_volume_medium').value),
                        high: parseInt(document.getElementById('risk_volume_high').value)
                    },
                    volatility_thresholds: {
                        very_high: parseInt(document.getElementById('risk_volatility_very_high').value),
                        high: parseInt(document.getElementById('risk_volatility_high').value),
                        medium: parseInt(document.getElementById('risk_volatility_medium').value)
                    },
                    weights: {
                        beta: parseFloat(document.getElementById('risk_weights_beta').value),
                        liquidity: parseFloat(document.getElementById('risk_weights_liquidity').value),
                        volatility: parseFloat(document.getElementById('risk_weights_volatility').value),
                        rsi: parseFloat(document.getElementById('risk_weights_rsi').value),
                        pb: parseFloat(document.getElementById('risk_weights_pb').value),
                        eps: parseFloat(document.getElementById('risk_weights_eps').value)
                    }
                },
                performance: {
                    base_score: parseInt(document.getElementById('performance_base_score').value),
                    score_multiplier: parseFloat(document.getElementById('performance_score_multiplier').value),
                    cagr_weights: {
                        '1m': parseFloat(document.getElementById('performance_cagr_weights_1m').value),
                        '3m': parseFloat(document.getElementById('performance_cagr_weights_3m').value),
                        '6m': parseFloat(document.getElementById('performance_cagr_weights_6m').value),
                        '1y': parseFloat(document.getElementById('performance_cagr_weights_1y').value),
                        consistency: parseFloat(document.getElementById('performance_cagr_weights_consistency').value)
                    }
                },
                technical: {
                    rsi_thresholds: {
                        oversold_extreme: parseInt(document.getElementById('technical_rsi_oversold_extreme').value),
                        oversold: parseInt(document.getElementById('technical_rsi_oversold').value),
                        overbought: parseInt(document.getElementById('technical_rsi_overbought').value),
                        overbought_extreme: parseInt(document.getElementById('technical_rsi_overbought_extreme').value)
                    },
                    mfi_thresholds: {
                        oversold_extreme: parseInt(document.getElementById('technical_mfi_oversold_extreme').value),
                        oversold: parseInt(document.getElementById('technical_mfi_oversold').value),
                        overbought: parseInt(document.getElementById('technical_mfi_overbought').value),
                        overbought_extreme: parseInt(document.getElementById('technical_mfi_overbought_extreme').value)
                    },
                    base_score: parseInt(document.getElementById('technical_base_score').value),
                    score_multiplier: parseFloat(document.getElementById('technical_score_multiplier').value)
                },
                portfolio: {
                    alert_thresholds: {
                        profit_high: parseInt(document.getElementById('portfolio_alert_profit_high').value),
                        profit_medium: parseInt(document.getElementById('portfolio_alert_profit_medium').value),
                        loss_high: parseInt(document.getElementById('portfolio_alert_loss_high').value),
                        loss_medium: parseInt(document.getElementById('portfolio_alert_loss_medium').value),
                        loss_low: parseInt(document.getElementById('portfolio_alert_loss_low').value),
                        loss_very_low: parseInt(document.getElementById('portfolio_alert_loss_very_low').value)
                    },
                    rsi_thresholds: {
                        high: parseInt(document.getElementById('portfolio_rsi_high').value),
                        low: parseInt(document.getElementById('portfolio_rsi_low').value)
                    },
                    pb_thresholds: {
                        high: parseFloat(document.getElementById('portfolio_pb_high').value),
                        low: parseFloat(document.getElementById('portfolio_pb_low').value)
                    },
                    status_thresholds: {
                        excellent: parseInt(document.getElementById('portfolio_status_excellent').value),
                        very_good: parseInt(document.getElementById('portfolio_status_very_good').value),
                        good: parseInt(document.getElementById('portfolio_status_good').value),
                        average: parseInt(document.getElementById('portfolio_status_average').value),
                        poor: parseInt(document.getElementById('portfolio_status_poor').value),
                        very_poor: parseInt(document.getElementById('portfolio_status_very_poor').value)
                    },
                    diversity_scores: {
                        10: parseInt(document.getElementById('portfolio_diversity_10').value),
                        7: parseInt(document.getElementById('portfolio_diversity_7').value),
                        5: parseInt(document.getElementById('portfolio_diversity_5').value),
                        3: parseInt(document.getElementById('portfolio_diversity_3').value),
                        'default': parseInt(document.getElementById('portfolio_diversity_default').value)
                    }
                }
            };
        }
        
        // ذخیره تنظیمات
        function saveSettings() {
            const settings = collectSettings();
            
            fetch('/settings', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(settings)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('✅ تنظیمات با موفقیت ذخیره شد');
                } else {
                    alert('❌ خطا در ذخیره تنظیمات');
                }
            })
            .catch(error => {
                alert('❌ خطا در ارتباط با سرور');
            });
        }
        
        // بازنشانی به پیش‌فرض
        function resetSettings() {
            if (confirm('آیا از بازنشانی به تنظیمات پیش‌فرض اطمینان دارید؟')) {
                fetch('/settings/reset', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    }
                });
            }
        }
        
        // مقداردهی اولیه
        updateTotalWeights();
    </script>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ============================================================================
# بخش ۲۰: قالب HTML اصلی
# ============================================================================

MAIN_HTML_TEMPLATE = """
<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>🔥 دشبورد فوق پیشرفته بورس ایران</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    {{ font_css|safe }}
    <style>
        /* تنظیمات پایه - این استایل‌ها توسط CSS پویا بازنویسی می‌شوند */
        body { 
            font-family: Tahoma, Arial, sans-serif; 
            background: #0a0a0a; 
            color: #ffffff; 
            padding: 20px; 
        }
        .card { 
            background: #1a1a1a; 
            border: 1px solid #333; 
            border-radius: 12px; 
            margin-bottom: 20px; 
        }
        .card-header { 
            background: #2d2d2d; 
            color: #00bcd4; 
            font-weight: bold; 
            padding: 15px 20px; 
            border-bottom: 1px solid #404040; 
        }
        .card-body { 
            padding: 20px; 
        }
        .stat-card { 
            background: linear-gradient(135deg, #2d2d2d, #1e1e1e); 
            border-radius: 12px; 
            padding: 20px; 
            text-align: center; 
            border: 2px solid #4a4a4a; 
            height: 100%; 
        }
        .stat-value { 
            font-size: 32px; 
            font-weight: bold; 
            margin: 15px 0; 
            color: #00bcd4; 
        }
        .stat-label { 
            color: #ffffff; 
            font-size: 16px; 
            font-weight: 500; 
        }
        .nav-tabs { 
            border-bottom: 2px solid #333; 
            margin-bottom: 20px; 
            flex-wrap: wrap; 
        }
        .nav-tabs .nav-link { 
            color: #888; 
            border: none; 
            padding: 12px 20px; 
        }
        .nav-tabs .nav-link:hover { 
            color: #00bcd4; 
        }
        .nav-tabs .nav-link.active { 
            color: #00bcd4; 
            border-bottom: 3px solid #00bcd4; 
            background: transparent; 
        }
        .table { 
            color: #ffffff; 
            font-size: 14px; 
        }
        .table thead th { 
            background: #1e1e1e; 
            color: #00bcd4; 
            border-bottom: 2px solid #333; 
        }
        .table tbody td { 
            color: #ffffff; 
        }
        .badge-success { 
            background: #4caf50; 
            color: white; 
            padding: 6px 12px; 
            border-radius: 20px; 
        }
        .badge-info { 
            background: #2196f3; 
            color: white; 
            padding: 6px 12px; 
            border-radius: 20px; 
        }
        .badge-warning { 
            background: #ff9800; 
            color: white; 
            padding: 6px 12px; 
            border-radius: 20px; 
        }
        .badge-danger { 
            background: #f44336; 
            color: white; 
            padding: 6px 12px; 
            border-radius: 20px; 
        }
        .badge-secondary { 
            background: #9e9e9e; 
            color: white; 
            padding: 6px 12px; 
            border-radius: 20px; 
        }
        .profit-text { 
            color: #4caf50; 
            font-weight: bold; 
        }
        .loss-text { 
            color: #f44336; 
            font-weight: bold; 
        }
        .btn-primary { 
            background: #00bcd4; 
            border: none; 
            padding: 10px 20px; 
            margin: 5px; 
            border-radius: 8px; 
            font-weight: bold; 
            color: #ffffff;
        }
        .btn-success { 
            background: #4caf50; 
            border: none; 
            padding: 10px 20px; 
            margin: 5px; 
            border-radius: 8px; 
            font-weight: bold; 
            color: #ffffff;
        }
        .btn-info { 
            background: #2196f3; 
            border: none; 
            padding: 10px 20px; 
            margin: 5px; 
            border-radius: 8px; 
            font-weight: bold; 
            color: #ffffff;
        }
        .btn-danger { 
            background: #f44336; 
            border: none; 
            padding: 10px 20px; 
            margin: 5px; 
            border-radius: 8px; 
            font-weight: bold; 
            color: #ffffff;
        }
        .chart-container { 
            background: #1a1a1a; 
            border-radius: 12px; 
            padding: 15px; 
            margin-bottom: 20px; 
            border: 1px solid #333; 
        }
        .pagination .page-link { 
            background: #2d2d2d; 
            color: white; 
            border: 1px solid #404040; 
        }
        .pagination .page-item.active .page-link { 
            background: #00bcd4; 
            border-color: #00bcd4; 
            color: white;
        }
        .search-box { 
            background: #2d2d2d; 
            border: 1px solid #404040; 
            color: white; 
            padding: 10px; 
            border-radius: 8px; 
            width: 100%; 
        }
        .toolbar { 
            background: #1a1a1a; 
            padding: 15px 20px; 
            border-radius: 12px; 
            margin-bottom: 20px; 
            border: 1px solid #333; 
        }
        h1, h2, h3, h4, h5, h6 { 
            color: #ffffff; 
        }
        .section-title { 
            color: #00bcd4; 
            font-size: 20px; 
            margin-bottom: 15px; 
            border-right: 4px solid #00bcd4; 
            padding-right: 15px; 
        }
        .alert-card { 
            background: #2d2d2d; 
            border-right: 6px solid; 
            padding: 15px; 
            margin-bottom: 10px; 
            border-radius: 8px; 
        }
        .alert-card h6 {
            color: #ffffff;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .alert-card ul {
            color: #ffffff;
            margin-bottom: 0;
            padding-right: 20px;
        }
        .alert-card li {
            color: #ffffff;
            margin-bottom: 5px;
        }
        .alert-card small {
            color: #ffffff;
        }
        .alert-card .text-muted {
            color: #888;
        }
        .alert-sell { 
            border-color: #f44336; 
        }
        .alert-buy { 
            border-color: #4caf50; 
        }
        .alert-info { 
            border-color: #00bcd4; 
        }
        .text-muted { 
            color: #888; 
        }
        .form-control, .form-select {
            background: #2d2d2d;
            border: 1px solid #404040;
            color: #ffffff;
        }
        .form-control:focus {
            border-color: #00bcd4;
            box-shadow: 0 0 0 0.2rem rgba(0,188,212,0.25);
        }
        .form-label {
            color: #00bcd4;
            font-weight: bold;
        }
        .text-white {
            color: #ffffff;
        }
        .plotly-graph-div .main-svg {
            background: transparent !important;
        }
        .plotly-graph-div .bg {
            fill: transparent !important;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <!-- هدر -->
        <div class="row mb-4">
            <div class="col-12">
                <h1 class="text-center" style="color: #00bcd4; font-size: 42px; font-weight: 900;">
                    📈 دشبورد فوق پیشرفته بورس ایران <span style="font-size: 18px; color: #888;">v{{ version }}</span>
                </h1>
                <p class="text-center text-muted">
                    آخرین بروزرسانی: {{ stats.last_update or 'ندارد' }}
                </p>
                <p class="text-center text-info">
                    <i class="bi bi-globe"></i> آدرس دسترسی: http://{{ server_ip }}:{{ server_port }}
                </p>
            </div>
        </div>
        
        <!-- کارت‌های آماری -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="stat-card">
                    <i class="bi bi-database" style="color: #00bcd4; font-size: 28px;"></i>
                    <div class="stat-value" id="statMarket">{{ stats.market }}</div>
                    <div class="stat-label">داده بازار</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <i class="bi bi-briefcase" style="color: #4caf50; font-size: 28px;"></i>
                    <div class="stat-value" id="statPortfolio">{{ stats.portfolio }}</div>
                    <div class="stat-label">پورتفو</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <i class="bi bi-search" style="color: #ff9800; font-size: 28px;"></i>
                    <div class="stat-value" id="statBasic">{{ stats.basic }}</div>
                    <div class="stat-label">تحلیل پایه</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <i class="bi bi-pie-chart" style="color: #9c27b0; font-size: 28px;"></i>
                    <div class="stat-value" id="statAdvanced">{{ stats.advanced }}</div>
                    <div class="stat-label">تحلیل پیشرفته</div>
                </div>
            </div>
        </div>
        
        <!-- نوار ابزار -->
        <div class="toolbar">
            <div class="row align-items-center">
                <div class="col-md-12 text-center">
                    <button class="btn btn-primary" onclick="location.reload()">
                        <i class="bi bi-arrow-repeat"></i> بروزرسانی
                    </button>
                    <a href="/export" class="btn btn-success">
                        <i class="bi bi-download"></i> خروجی Excel
                    </a>
                    <a href="/settings/page" class="btn btn-info" target="_blank">
                        <i class="bi bi-gear"></i> تنظیمات پیشرفته
                    </a>
                    <a href="/font-settings/page" class="btn btn-warning" target="_blank">
                        <i class="bi bi-palette"></i> تنظیمات فونت
                    </a>
                    <a href="/debug/log" class="btn btn-secondary" target="_blank">
                        <i class="bi bi-bug"></i> لاگ دیباگ
                    </a>
                </div>
            </div>
        </div>
        
        <!-- تب‌ها -->
        <ul class="nav nav-tabs" id="myTab">
            <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#upload"><i class="bi bi-cloud-upload"></i> آپلود</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#online"><i class="bi bi-wifi"></i> اتصال آنلاین</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#basic"><i class="bi bi-cart-plus"></i> تحلیل پایه</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#advanced"><i class="bi bi-pie-chart"></i> تحلیل پیشرفته</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#portfolio"><i class="bi bi-briefcase"></i> پورتفو</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#market"><i class="bi bi-table"></i> داده بازار</button></li>
        </ul>
        
        <div class="tab-content">
            <!-- تب آپلود -->
            <div class="tab-pane active" id="upload">
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header"><i class="bi bi-database"></i> آپلود داده بازار</div>
                            <div class="card-body text-center">
                                <input type="file" id="marketFile" style="display:none" accept=".xlsx,.xls,.csv">
                                <button class="btn btn-primary btn-lg" onclick="document.getElementById('marketFile').click()">
                                    <i class="bi bi-cloud-upload"></i> انتخاب فایل
                                </button>
                                <div id="marketStatus" class="mt-3"></div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header"><i class="bi bi-briefcase"></i> آپلود پورتفو</div>
                            <div class="card-body text-center">
                                <input type="file" id="portfolioFile" style="display:none" accept=".xlsx,.xls,.csv">
                                <button class="btn btn-success btn-lg" onclick="document.getElementById('portfolioFile').click()">
                                    <i class="bi bi-cloud-upload"></i> انتخاب فایل
                                </button>
                                <div id="portfolioStatus" class="mt-3"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- تب اتصال آنلاین -->
            <div class="tab-pane" id="online">
                <div class="card">
                    <div class="card-header"><i class="bi bi-wifi"></i> اتصال آنلاین به ایزی‌تریدر</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">نام کاربری</label>
                                    <input type="text" class="form-control" id="onlineUsername">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">رمز عبور</label>
                                    <input type="password" class="form-control" id="onlinePassword">
                                </div>
                                <button class="btn btn-primary" onclick="onlineLogin()">ورود</button>
                                <button class="btn btn-danger" onclick="onlineLogout()">خروج</button>
                                <div id="onlineStatus" class="mt-3"></div>
                            </div>
                            <div class="col-md-6">
                                <button class="btn btn-info w-100 mb-3" onclick="fetchMarketData()">
                                    <i class="bi bi-database"></i> دریافت داده‌های بازار (ایزی فیلتر)
                                </button>
                                <button class="btn btn-info w-100" onclick="fetchPortfolioData()">
                                    <i class="bi bi-briefcase"></i> دریافت داده‌های پورتفو
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- تب تحلیل پایه -->
            <div class="tab-pane" id="basic">
                <div class="card">
                    <div class="card-header"><i class="bi bi-star-fill"></i> نتایج تحلیل خرید جدید</div>
                    <div class="card-body">
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <input type="number" class="form-control" id="budget" value="100000000" placeholder="بودجه (ریال)">
                            </div>
                            <div class="col-md-4">
                                <button class="btn btn-primary" onclick="runBasicAnalysis()">اجرای تحلیل</button>
                            </div>
                        </div>
                        <div id="basicCharts" class="chart-container" style="height:400px; display:none;"></div>
                        <div id="basicResults" class="table-responsive mt-3"></div>
                    </div>
                </div>
            </div>
            
            <!-- تب تحلیل پیشرفته -->
            <div class="tab-pane" id="advanced">
                <div class="card">
                    <div class="card-header"><i class="bi bi-pie-chart"></i> تحلیل پیشرفته (۷ روش)</div>
                    <div class="card-body">
                        <button class="btn btn-primary mb-3" onclick="runAdvancedAnalysis()">اجرای تحلیل پیشرفته</button>
                        <div id="advancedCharts1" class="chart-container" style="height:400px; display:none;"></div>
                        <div id="advancedCharts2" class="chart-container" style="height:600px; display:none;"></div>
                        <div id="advancedResults" class="table-responsive"></div>
                    </div>
                </div>
            </div>
            
            <!-- تب پورتفو -->
            <div class="tab-pane" id="portfolio">
                <div class="card">
                    <div class="card-header"><i class="bi bi-briefcase"></i> مدیریت پورتفو</div>
                    <div class="card-body">
                        <button class="btn btn-primary mb-3" onclick="analyzePortfolio()">تحلیل پورتفو</button>
                        <div id="portfolioCharts">
                            <div class="row">
                                <div class="col-md-4"><div id="portfolioPie" class="chart-container" style="height:350px;"></div></div>
                                <div class="col-md-4"><div id="portfolioProfit" class="chart-container" style="height:350px;"></div></div>
                                <div class="col-md-4"><div id="portfolioWeight" class="chart-container" style="height:350px;"></div></div>
                            </div>
                        </div>
                        <div id="portfolioResults"></div>
                    </div>
                </div>
            </div>
            
            <!-- تب داده بازار -->
            <div class="tab-pane" id="market">
                <div class="card">
                    <div class="card-header"><i class="bi bi-table"></i> داده بازار (صفحه‌بندی شده)</div>
                    <div class="card-body">
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <input type="text" class="search-box" id="marketSearch" placeholder="جستجو در همه ستون‌ها...">
                            </div>
                            <div class="col-md-3">
                                <select class="form-control" id="marketPerPage">
                                    <option value="50">۵۰ سطر</option>
                                    <option value="100" selected>۱۰۰ سطر</option>
                                    <option value="200">۲۰۰ سطر</option>
                                    <option value="500">۵۰۰ سطر</option>
                                    <option value="1000">۱۰۰۰ سطر</option>
                                </select>
                            </div>
                            <div class="col-md-3">
                                <button class="btn btn-info w-100" onclick="loadMarketData(1)">بارگذاری</button>
                            </div>
                        </div>
                        <div id="marketTable" class="table-responsive"></div>
                        <div class="row mt-3">
                            <div class="col-md-6" id="marketInfo"></div>
                            <div class="col-md-6">
                                <nav><ul class="pagination justify-content-end" id="marketPagination"></ul></nav>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // آپلود فایل‌ها
        document.getElementById('marketFile').addEventListener('change', function(e) {
            uploadFile(e.target.files[0], '/upload/market', 'marketStatus');
        });
        
        document.getElementById('portfolioFile').addEventListener('change', function(e) {
            uploadFile(e.target.files[0], '/upload/portfolio', 'portfolioStatus');
        });
        
        function uploadFile(file, url, statusId) {
            const formData = new FormData();
            formData.append('file', file);
            
            document.getElementById(statusId).innerHTML = '🔄 در حال آپلود...';
            
            fetch(url, { method: 'POST', body: formData })
            .then(r => r.json())
            .then(d => {
                if (d.success) {
                    document.getElementById(statusId).innerHTML = `✅ آپلود شد: ${d.rows} ردیف`;
                    setTimeout(() => location.reload(), 2000);
                } else {
                    document.getElementById(statusId).innerHTML = `❌ خطا: ${d.message}`;
                }
            })
            .catch(e => {
                document.getElementById(statusId).innerHTML = `❌ خطا: ${e}`;
            });
        }
        
        // اتصال آنلاین
        function onlineLogin() {
            const u = document.getElementById('onlineUsername').value;
            const p = document.getElementById('onlinePassword').value;
            
            document.getElementById('onlineStatus').innerHTML = '🔄 در حال ورود...';
            
            fetch('/online/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: u, password: p})
            })
            .then(r => r.json())
            .then(d => {
                document.getElementById('onlineStatus').innerHTML = d.message;
                // پس از ورود موفق، بعد از 3 ثانیه داده‌ها را دریافت کن
                if (d.success) {
                    setTimeout(() => {
                        fetchMarketData();
                        fetchPortfolioData();
                    }, 3000);
                }
            });
        }
        
        function onlineLogout() {
            fetch('/online/logout', {method: 'POST'})
            .then(() => document.getElementById('onlineStatus').innerHTML = '✅ خارج شد');
        }
        
        function fetchMarketData() {
            document.getElementById('onlineStatus').innerHTML = '🔄 دریافت داده‌های بازار...';
            fetch('/online/fetch/market', {method: 'POST'})
            .then(r => r.json())
            .then(d => {
                document.getElementById('onlineStatus').innerHTML = d.message;
                if (d.success) {
                    setTimeout(() => location.reload(), 2000);
                }
            });
        }
        
        function fetchPortfolioData() {
            document.getElementById('onlineStatus').innerHTML = '🔄 دریافت داده‌های پورتفو...';
            fetch('/online/fetch/portfolio', {method: 'POST'})
            .then(r => r.json())
            .then(d => {
                document.getElementById('onlineStatus').innerHTML = d.message;
                if (d.success) {
                    setTimeout(() => location.reload(), 2000);
                }
            });
        }
        
        // تحلیل پایه
        function runBasicAnalysis() {
            const budget = document.getElementById('budget').value;
            
            fetch('/analyze/basic', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({budget: parseFloat(budget)})
            })
            .then(r => r.json())
            .then(d => {
                if (d.success) {
                    let html = '<table class="table table-hover"><thead><tr>';
                    if (d.results.length > 0) {
                        Object.keys(d.results[0]).forEach(k => html += `<th>${k}</th>`);
                        html += '</tr></thead><tbody>';
                        
                        d.results.forEach(r => {
                            html += '<tr>';
                            Object.values(r).forEach(v => {
                                if (typeof v === 'number') {
                                    if (v > 1000000) v = (v/1000000).toFixed(2) + 'M';
                                    else if (v > 1000) v = (v/1000).toFixed(2) + 'K';
                                    else if (Math.abs(v) < 1) v = v.toFixed(2);
                                    else v = v.toLocaleString();
                                }
                                html += `<td>${v}</td>`;
                            });
                            html += '</tr>';
                        });
                        html += '</tbody></table>';
                        document.getElementById('basicResults').innerHTML = html;
                    }
                    
                    fetch('/charts/basic')
                    .then(r => r.json())
                    .then(c => {
                        if (c.success) {
                            document.getElementById('basicCharts').style.display = 'block';
                            Plotly.newPlot('basicCharts', JSON.parse(c.chart));
                        }
                    });
                } else {
                    alert('خطا: ' + d.message);
                }
            });
        }
        
        // تحلیل پیشرفته
        function runAdvancedAnalysis() {
            fetch('/analyze/advanced', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(r => r.json())
            .then(d => {
                if (d.success) {
                    let html = '<table class="table table-hover"><thead><tr>';
                    if (d.results.length > 0) {
                        Object.keys(d.results[0]).forEach(k => html += `<th>${k}</th>`);
                        html += '</tr></thead><tbody>';
                        
                        d.results.forEach(r => {
                            html += '<tr>';
                            Object.values(r).forEach(v => {
                                if (typeof v === 'number') {
                                    if (v > 1000000) v = (v/1000000).toFixed(2) + 'M';
                                    else if (v > 1000) v = (v/1000).toFixed(2) + 'K';
                                    else v = v.toFixed(2);
                                }
                                html += `<td>${v}</td>`;
                            });
                            html += '</tr>';
                        });
                        html += '</tbody></table>';
                        document.getElementById('advancedResults').innerHTML = html;
                    }
                    
                    fetch('/charts/advanced')
                    .then(r => r.json())
                    .then(c => {
                        if (c.success) {
                            document.getElementById('advancedCharts1').style.display = 'block';
                            document.getElementById('advancedCharts2').style.display = 'block';
                            Plotly.newPlot('advancedCharts1', JSON.parse(c.chart_final));
                            if (c.chart_six) {
                                Plotly.newPlot('advancedCharts2', JSON.parse(c.chart_six));
                            }
                        }
                    });
                } else {
                    alert('خطا: ' + d.message);
                }
            });
        }
        
        // تحلیل پورتفو
        function analyzePortfolio() {
            fetch('/analyze/portfolio', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(r => r.json())
            .then(d => {
                if (d.success) {
                    const a = d.analysis;
                    
                    let html = `
                        <div class="row mb-4">
                            <div class="col-md-3"><div class="stat-card"><div class="stat-value">${a.portfolio_value.toLocaleString()}</div><div class="stat-label">ارزش کل</div></div></div>
                            <div class="col-md-3"><div class="stat-card"><div class="stat-value ${a.total_profit_loss >= 0 ? 'profit-text' : 'loss-text'}">${a.total_profit_loss.toLocaleString()}</div><div class="stat-label">سود/زیان کل</div></div></div>
                            <div class="col-md-3"><div class="stat-card"><div class="stat-value ${a.profit_loss_percent >= 0 ? 'profit-text' : 'loss-text'}">${a.profit_loss_percent.toFixed(2)}%</div><div class="stat-label">درصد سود/زیان</div></div></div>
                            <div class="col-md-3"><div class="stat-card"><div class="stat-value">${Object.keys(a.stock_details).length}</div><div class="stat-label">تعداد سهام</div></div></div>
                        </div>
                        
                        <div class="row mb-4">
                            <div class="col-md-3"><div class="stat-card"><div class="stat-value profit-text">${a.profit_count}</div><div class="stat-label">سهام سودده</div></div></div>
                            <div class="col-md-3"><div class="stat-card"><div class="stat-value loss-text">${a.loss_count}</div><div class="stat-label">سهام زیانده</div></div></div>
                            <div class="col-md-3"><div class="stat-card"><div class="stat-value">${a.diversification_score}</div><div class="stat-label">امتیاز تنوع</div></div></div>
                            <div class="col-md-3"><div class="stat-card"><div class="stat-value">${a.portfolio_risk_level}</div><div class="stat-label">سطح ریسک</div></div></div>
                        </div>
                        
                        <div class="row mb-4">
                            <div class="col-md-4">
                                <div class="alert-card alert-sell">
                                    <h6><i class="bi bi-exclamation-triangle-fill text-danger"></i> هشدارهای فروش</h6>
                                    <ul class="list-unstyled">
                                        ${a.sell_alerts.map(x => `<li><small>${x}</small></li>`).join('') || '<li><small class="text-muted">ندارد</small></li>'}
                                    </ul>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="alert-card alert-buy">
                                    <h6><i class="bi bi-cart-check-fill text-success"></i> پیشنهادات خرید</h6>
                                    <ul class="list-unstyled">
                                        ${a.buy_recommendations.map(x => `<li><small>${x}</small></li>`).join('') || '<li><small class="text-muted">ندارد</small></li>'}
                                    </ul>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="alert-card alert-info">
                                    <h6><i class="bi bi-star-fill text-warning"></i> سهام برتر</h6>
                                    <ul class="list-unstyled">
                                        ${a.good_performers.map(x => `<li><small>${x}</small></li>`).join('') || '<li><small class="text-muted">ندارد</small></li>'}
                                    </ul>
                                </div>
                            </div>
                        </div>
                        
                        <h5 class="section-title">جزئیات سهام موجود</h5>
                        <table class="table table-hover">
                            <thead><tr><th>نماد</th><th>تعداد</th><th>قیمت خرید</th><th>قیمت فعلی</th><th>ارزش</th><th>سود/زیان</th><th>درصد</th><th>وزن</th><th>RSI</th><th>وضعیت</th><th>پیشنهاد</th></tr></thead>
                            <tbody>
                                ${Object.values(a.stock_details).map(s => {
                                    const statusClass = s.status.includes('🌟🌟') ? 'success' : 
                                                       s.status.includes('⭐️⭐️') ? 'info' : 
                                                       s.status.includes('⭐️') ? 'warning' : 
                                                       s.status.includes('⚠️') ? 'warning' : 
                                                       s.status.includes('📊') ? 'secondary' : 'danger';
                                    const rsiClass = s.rsi && s.rsi >= 70 ? 'text-danger' : 
                                                    s.rsi && s.rsi <= 30 ? 'text-success' : '';
                                    return `<tr>
                                        <td><strong>${s.symbol}</strong></td>
                                        <td>${s.quantity.toLocaleString()}</td>
                                        <td>${s.avg_buy_price.toLocaleString()}</td>
                                        <td>${s.current_price.toLocaleString()}</td>
                                        <td>${s.current_value.toLocaleString()}</td>
                                        <td class="${s.profit_loss >= 0 ? 'profit-text' : 'loss-text'}">${s.profit_loss.toLocaleString()}</td>
                                        <td class="${s.profit_loss_percent >= 0 ? 'profit-text' : 'loss-text'}">${s.profit_loss_percent.toFixed(2)}%</td>
                                        <td>${s.weight.toFixed(1)}%</td>
                                        <td class="${rsiClass}">${s.rsi ? s.rsi.toFixed(1) : '-'}</td>
                                        <td><span class="badge-${statusClass}">${s.status}</span></td>
                                        <td><small>${s.recommendation}</small></td>
                                    </tr>`;
                                }).join('')}
                            </tbody>
                        </table>
                        
                        <h5 class="section-title mt-4">سهام فروخته شده</h5>
                        <table class="table table-hover">
                            <thead><tr><th>نماد</th><th>تعداد</th><th>قیمت خرید</th><th>قیمت فروش</th><th>سود/زیان</th><th>درصد</th></tr></thead>
                            <tbody>
                                ${a.sold_stocks.map(s => `
                                    <tr>
                                        <td><strong>${s.symbol}</strong></td>
                                        <td>${s.quantity.toLocaleString()}</td>
                                        <td>${s.avg_buy_price.toLocaleString()}</td>
                                        <td>${s.sell_price.toLocaleString()}</td>
                                        <td class="${s.profit_loss >= 0 ? 'profit-text' : 'loss-text'}">${s.profit_loss.toLocaleString()}</td>
                                        <td class="${s.profit_loss_percent >= 0 ? 'profit-text' : 'loss-text'}">${s.profit_loss_percent.toFixed(2)}%</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                    
                    document.getElementById('portfolioResults').innerHTML = html;
                    
                    fetch('/charts/portfolio')
                    .then(r => r.json())
                    .then(c => {
                        if (c.success) {
                            if (c.charts.pie) Plotly.newPlot('portfolioPie', JSON.parse(c.charts.pie));
                            if (c.charts.profit) Plotly.newPlot('portfolioProfit', JSON.parse(c.charts.profit));
                            if (c.charts.weight) Plotly.newPlot('portfolioWeight', JSON.parse(c.charts.weight));
                        }
                    });
                } else {
                    alert('خطا: ' + d.message);
                }
            });
        }
        
        // داده بازار با صفحه‌بندی
        let marketCurrentPage = 1;
        let marketTotalPages = 1;
        
        function loadMarketData(page = 1) {
            const search = document.getElementById('marketSearch').value;
            const perPage = document.getElementById('marketPerPage').value;
            
            fetch(`/data/market?page=${page}&per_page=${perPage}&search=${encodeURIComponent(search)}`)
            .then(r => r.json())
            .then(d => {
                if (d.success) {
                    let html = '<table class="table table-hover"><thead><tr>';
                    d.columns.forEach(col => html += `<th>${col}</th>`);
                    html += '</tr></thead><tbody>';
                    
                    d.data.forEach(row => {
                        html += '<tr>';
                        d.columns.forEach(col => {
                            let val = row[col];
                            if (val === null || val === undefined) val = '';
                            if (typeof val === 'number') {
                                if (val > 1000000) val = (val/1000000).toFixed(2) + 'M';
                                else if (val > 1000) val = (val/1000).toFixed(2) + 'K';
                                else if (Math.abs(val) < 1) val = val.toFixed(2);
                                else val = val.toLocaleString();
                            }
                            html += `<td>${val}</td>`;
                        });
                        html += '</tr>';
                    });
                    html += '</tbody></table>';
                    document.getElementById('marketTable').innerHTML = html;
                    
                    document.getElementById('marketInfo').innerHTML = `نمایش ${(d.page-1)*d.per_page+1} تا ${Math.min(d.page*d.per_page, d.total)} از ${d.total} رکورد`;
                    
                    marketTotalPages = d.total_pages;
                    marketCurrentPage = d.page;
                    
                    let pagination = '';
                    for (let i = 1; i <= d.total_pages; i++) {
                        pagination += `<li class="page-item ${i === d.page ? 'active' : ''}"><a class="page-link" href="#" onclick="loadMarketData(${i}); return false;">${i}</a></li>`;
                    }
                    document.getElementById('marketPagination').innerHTML = pagination;
                } else {
                    document.getElementById('marketTable').innerHTML = '<p class="text-center text-muted">داده‌ای وجود ندارد</p>';
                    document.getElementById('marketInfo').innerHTML = '';
                    document.getElementById('marketPagination').innerHTML = '';
                }
            })
            .catch(error => {
                console.error('خطا در بارگذاری داده‌ها:', error);
                document.getElementById('marketTable').innerHTML = '<p class="text-center text-danger">خطا در بارگذاری داده‌ها</p>';
            });
        }
        
        document.getElementById('marketSearch').addEventListener('input', () => loadMarketData(1));
        document.getElementById('marketPerPage').addEventListener('change', () => loadMarketData(1));
        
        // بارگذاری اولیه
        setTimeout(() => {
            if (document.getElementById('marketTable')) {
                loadMarketData(1);
            }
        }, 1000);
        
        // بروزرسانی خودکار وضعیت
        setInterval(() => {
            fetch('/online/status')
            .then(r => r.json())
            .then(d => {
                const el = document.getElementById('onlineStatus');
                if (el) el.innerHTML = d.message;
            })
            .catch(() => {});
        }, 5000);
    </script>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ============================================================================
# بخش ۲۱: راه‌اندازی سرور
# ============================================================================

def run_server():
    print(f"\n{'='*80}")
    print(f"🔥 {APP_NAME} - نسخه {VERSION}")
    print(f"{'='*80}")
    print(f"📡 آدرس محلی: http://localhost:{PORT}")
    print(f"📡 آدرس شبکه: http://{LOCAL_IP}:{PORT}")
    print(f"📡 فایل دیباگ: {DEBUG_LOG_FILE}")
    print(f"{'='*80}")
    print(f"📡 سلنیوم: {'✅ فعال' if SELENIUM_AVAILABLE else '❌ غیرفعال'}")
    print(f"📡 دیتا: {DATA_DIR}")
    print(f"📡 تنظیمات: {SETTINGS_FILE}")
    print(f"📡 تنظیمات فونت: {FONT_SETTINGS_FILE}")
    print(f"📡 کوکی‌ها: {COOKIES_FILE}")
    print(f"{'='*80}\n")
    
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

def open_browser():
    time.sleep(2)
    webbrowser.open(f'http://localhost:{PORT}')

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 در حال راه‌اندازی...")
    print("="*80 + "\n")
    
    # پاک کردن لاگ قدیمی
    with open(DEBUG_LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"=== شروع لاگ در {datetime.now().isoformat()} ===\n")
    
    threading.Thread(target=run_server, daemon=True).start()
    open_browser()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 سرور متوقف شد")
        online.logout()
        sys.exit(0)