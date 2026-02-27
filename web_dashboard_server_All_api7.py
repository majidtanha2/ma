#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
🔥 دشبورد فوق پیشرفته بورس ایران - نسخه نهایی با پشتیبانی از API
================================================================================
✅ قابلیت‌ها:
   - لاگین مستقیم در مرورگر داخلی (رفع مشکل ورود)
   - تنظیمات پیشرفته فونت و جداول
   - نمایش صحیح داده‌های بازار
   - اتصال آنلاین به ایزی‌تریدر
   - تحلیل پایه سهام با ۶ معیار اصلی
   - تحلیل پیشرفته ۷ روشی (حباب، ارزش ذاتی، تابلوخوانی، ریسک، عملکرد، تکنیکال)
   - تحلیل پورتفو با محاسبه صحیح سود/زیان
   - خروجی Excel با همه تحلیلها
   - اتصال به API برس‌آی‌آر (brsapi.ir) برای داده‌های لحظه‌ای
================================================================================
نسخه: 4.0.0
تاریخ: 2024
================================================================================
"""

# ============================================================================
# ایمپورت‌های اصلی
# ============================================================================
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
import socket
import random
import string
import csv
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict, Counter
from urllib.parse import urlparse, urljoin, quote, unquote
from contextlib import contextmanager
from functools import wraps, lru_cache
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any
import gc

# ============================================================================
# ایمپورت‌های علمی و تحلیلی
# ============================================================================
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 50)

# ============================================================================
# ایمپورت‌های وب و شبکه
# ============================================================================
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request, send_file, render_template_string, session, make_response, redirect, url_for, flash, g
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

# ============================================================================
# ایمپورت‌های مصورسازی
# ============================================================================
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as py
import plotly.figure_factory as ff
from plotly.colors import n_colors

# ============================================================================
# ایمپورت‌های سلنیوم (اختیاری)
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
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    SELENIUM_AVAILABLE = True
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.utils import ChromeType
        WEBDRIVER_MANAGER_AVAILABLE = True
    except ImportError:
        pass
except ImportError:
    pass

# ============================================================================
# پنهان کردن وارنینگ‌ها
# ============================================================================
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# ============================================================================
# بخش ۱: تنظیمات اولیه و ثابت‌ها
# ============================================================================

VERSION = "4.0.0"
APP_NAME = "دشبورد فوق پیشرفته بورس ایران با پشتیبانی API"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ساختار دایرکتوری‌ها
DATA_DIR = os.path.join(BASE_DIR, 'data')
DOWNLOADS_DIR = os.path.join(DATA_DIR, 'downloads')
UPLOADS_DIR = os.path.join(DATA_DIR, 'uploads')
CACHE_DIR = os.path.join(DATA_DIR, 'cache')
API_CACHE_DIR = os.path.join(DATA_DIR, 'api_cache')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')
TEMP_DIR = os.path.join(DATA_DIR, 'temp')
BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
REPORTS_DIR = os.path.join(DATA_DIR, 'reports')
EXPORTS_DIR = os.path.join(DATA_DIR, 'exports')
PLOTS_DIR = os.path.join(DATA_DIR, 'plots')

# فایل‌های تنظیمات و داده
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')
FONT_SETTINGS_FILE = os.path.join(DATA_DIR, 'font_settings.json')
COOKIES_FILE = os.path.join(DATA_DIR, 'cookies.json')
USER_PREFS_FILE = os.path.join(DATA_DIR, 'user_prefs.json')
ANALYSIS_CACHE_FILE = os.path.join(DATA_DIR, 'analysis_cache.pkl')
PORTFOLIO_FILE = os.path.join(DATA_DIR, 'portfolio.json')
WATCHLIST_FILE = os.path.join(DATA_DIR, 'watchlist.json')
ALERTS_FILE = os.path.join(DATA_DIR, 'alerts.json')

# فایل‌های لاگ
DEBUG_LOG_FILE = os.path.join(LOGS_DIR, f'debug_{datetime.now().strftime("%Y%m")}.log')
ERROR_LOG_FILE = os.path.join(LOGS_DIR, f'error_{datetime.now().strftime("%Y%m")}.log')
ACCESS_LOG_FILE = os.path.join(LOGS_DIR, f'access_{datetime.now().strftime("%Y%m")}.log')
API_LOG_FILE = os.path.join(LOGS_DIR, f'api_{datetime.now().strftime("%Y%m")}.log')

# ایجاد تمام دایرکتوری‌های مورد نیاز
for dir_path in [DATA_DIR, DOWNLOADS_DIR, UPLOADS_DIR, CACHE_DIR, API_CACHE_DIR, 
                 LOGS_DIR, TEMP_DIR, BACKUP_DIR, REPORTS_DIR, EXPORTS_DIR, PLOTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# ============================================================================
# تنظیمات سرور و شبکه
# ============================================================================

def get_local_ip():
    """دریافت IP واقعی سرور برای انتشار روی اینترنت"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            return "127.0.0.1"

def get_public_ip():
    """دریافت IP عمومی (اختیاری)"""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json().get('ip', 'نامشخص')
    except:
        return 'نامشخص'

LOCAL_IP = get_local_ip()
PUBLIC_IP = get_public_ip()
PORT = 8002
HOST = '0.0.0.0'

# ============================================================================
# تنظیمات امنیتی
# ============================================================================

SECRET_KEY = secrets.token_hex(32)
SESSION_TYPE = 'filesystem'
SESSION_PERMANENT = False
SESSION_USE_SIGNER = True
SESSION_COOKIE_SECURE = False  # برای HTTPS باید True شود
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

# ============================================================================
# تنظیمات آپلود فایل
# ============================================================================

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'json', 'pkl'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 مگابایت
UPLOAD_FOLDER = UPLOADS_DIR

def allowed_file(filename):
    """بررسی مجاز بودن پسوند فایل"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================================================
# تنظیمات کش و حافظه
# ============================================================================

CACHE_TTL = {
    'short': 60,           # ۱ دقیقه
    'medium': 300,         # ۵ دقیقه
    'long': 3600,          # ۱ ساعت
    'very_long': 86400,    # ۲۴ ساعت
    'weekly': 604800       # ۱ هفته
}

MAX_CACHE_SIZE = 1024 * 1024 * 1024  # ۱ گیگابایت
CLEANUP_INTERVAL = 3600  # ۱ ساعت

# ============================================================================
# بخش ۲: توابع کمکی و ابزارها
# ============================================================================

# ============================================================================
# ۲-۱: توابع لاگینگ پیشرفته
# ============================================================================

class ColoredFormatter:
    """فرمتر رنگی برای لاگ‌ها"""
    COLORS = {
        'RESET': '\033[0m',
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'MAGENTA': '\033[95m',
        'CYAN': '\033[96m',
        'WHITE': '\033[97m',
        'BOLD': '\033[1m'
    }
    
    @classmethod
    def colorize(cls, text, color):
        return f"{cls.COLORS.get(color, '')}{text}{cls.COLORS['RESET']}"

def debug_log(message, level="INFO", save_to_file=True, print_console=True):
    """
    ثبت لاگ پیشرفته با سطح‌بندی و ذخیره در فایل
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    
    # تعیین رنگ بر اساس سطح
    color_map = {
        'INFO': 'GREEN',
        'WARNING': 'YELLOW',
        'ERROR': 'RED',
        'DEBUG': 'CYAN',
        'CRITICAL': 'MAGENTA',
        'SUCCESS': 'GREEN',
        'API': 'BLUE'
    }
    
    colored_level = ColoredFormatter.colorize(f"[{level}]", color_map.get(level, 'WHITE'))
    log_line = f"[{timestamp}] {colored_level} {message}"
    
    if print_console:
        print(log_line)
    
    if save_to_file:
        try:
            # انتخاب فایل مناسب بر اساس سطح
            if level == 'ERROR' or level == 'CRITICAL':
                log_file = ERROR_LOG_FILE
            elif level == 'API':
                log_file = API_LOG_FILE
            else:
                log_file = DEBUG_LOG_FILE
            
            # ذخیره بدون رنگ در فایل
            clean_line = f"[{timestamp}] [{level}] {message}\n"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(clean_line)
                
            # اگر سطح ERROR است، در فایل خطا هم ذخیره کن
            if level == 'ERROR':
                with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
                    f.write(clean_line)
                    
        except Exception as e:
            print(f"❌ خطا در نوشتن لاگ: {e}")

# ============================================================================
# ۲-۲: توابع کار با تاریخ و زمان
# ============================================================================

def persian_date(date=None, format='%Y/%m/%d'):
    """
    تبدیل تاریخ میلادی به شمسی (تقریبی)
    """
    if date is None:
        date = datetime.now()
    
    # این تابع یک تبدیل ساده است - برای دقت بیشتر از کتابخانه jdatetime استفاده کنید
    persian_months = [
        'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
        'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
    ]
    
    try:
        import jdatetime
        if isinstance(date, datetime):
            persian = jdatetime.datetime.fromgregorian(datetime=date)
            if format == '%Y/%m/%d':
                return f"{persian.year:04d}/{persian.month:02d}/{persian.day:02d}"
            elif format == 'full':
                return f"{persian.day} {persian_months[persian.month-1]} {persian.year}"
            else:
                return persian.strftime(format)
    except ImportError:
        # اگر jdatetime نصب نبود، همان میلادی را برگردان
        if format == '%Y/%m/%d':
            return date.strftime('%Y/%m/%d')
        return str(date)

def time_ago(date):
    """
    نمایش نسبی زمان (مثلاً ۵ دقیقه پیش)
    """
    if not date:
        return 'نامشخص'
    
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date)
        except:
            return date
    
    diff = datetime.now() - date
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} سال پیش"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} ماه پیش"
    elif diff.days > 0:
        return f"{diff.days} روز پیش"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} ساعت پیش"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} دقیقه پیش"
    else:
        return f"{diff.seconds} ثانیه پیش"

# ============================================================================
# ۲-۳: توابع کار با اعداد و فرمت‌ها
# ============================================================================

def format_number(num, with_toman=False, with_comma=True):
    """
    فرمت‌بندی اعداد با جداکننده هزارگان
    """
    if num is None or pd.isna(num):
        return '۰'
    
    try:
        if isinstance(num, str):
            num = float(num.replace(',', ''))
        
        if with_comma:
            if abs(num) >= 1e12:
                formatted = f"{num/1e12:.2f} تریلیون"
            elif abs(num) >= 1e9:
                formatted = f"{num/1e9:.2f} میلیارد"
            elif abs(num) >= 1e6:
                formatted = f"{num/1e6:.2f} میلیون"
            elif abs(num) >= 1e3:
                formatted = f"{num:,.0f}".replace(',', '٬')
            else:
                formatted = f"{num:,.0f}".replace(',', '٬')
        else:
            formatted = f"{num:.0f}"
        
        if with_toman:
            return f"{formatted} تومان"
        return formatted
        
    except:
        return str(num)

def format_percent(value, decimals=2):
    """فرمت‌بندی درصد"""
    try:
        if pd.isna(value):
            return '-%'
        return f"{value:.{decimals}f}%".replace('.', '٫')
    except:
        return '-%'

def safe_divide(a, b, default=0):
    """تقسیم ایمن با بررسی تقسیم بر صفر"""
    try:
        if b == 0 or pd.isna(b) or b is None:
            return default
        return a / b
    except:
        return default

# ============================================================================
# ۲-۴: توابع کار با فایل و حافظه
# ============================================================================

def safe_json_load(file_path, default=None):
    """بارگذاری ایمن فایل JSON"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        debug_log(f"خطا در بارگذاری {file_path}: {e}", "WARNING")
    
    return default if default is not None else {}

def safe_json_save(data, file_path):
    """ذخیره ایمن فایل JSON"""
    try:
        # ایجاد پوشه والد اگر وجود ندارد
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # ذخیره موقت و سپس جایگزینی
        temp_file = file_path + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # جایگزینی فایل اصلی
        shutil.move(temp_file, file_path)
        return True
    except Exception as e:
        debug_log(f"خطا در ذخیره {file_path}: {e}", "ERROR")
        return False

def get_file_size(file_path):
    """دریافت حجم فایل به صورت خوانا"""
    try:
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except:
        return 'نامشخص'

def clean_old_files(directory, days=7, pattern=None):
    """پاک کردن فایل‌های قدیمی"""
    try:
        now = time.time()
        count = 0
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                if pattern and pattern not in filename:
                    continue
                file_time = os.path.getmtime(filepath)
                if now - file_time > days * 86400:
                    os.remove(filepath)
                    count += 1
        return count
    except Exception as e:
        debug_log(f"خطا در پاکسازی {directory}: {e}", "WARNING")
        return 0

# ============================================================================
# ۲-۵: توابع کار با دیتافریم
# ============================================================================

def safe_df_operation(df, operation, *args, **kwargs):
    """اجرای ایمن عملیات روی دیتافریم"""
    try:
        if df is None or df.empty:
            return None
        return operation(df, *args, **kwargs)
    except Exception as e:
        debug_log(f"خطا در عملیات دیتافریم: {e}", "ERROR")
        return None

def normalize_columns(df, mapping):
    """نرمال‌سازی نام ستون‌ها"""
    if df is None or df.empty:
        return df
    
    df = df.copy()
    df.columns = [mapping.get(col, col) for col in df.columns]
    return df

def detect_numeric_columns(df):
    """تشخیص خودکار ستون‌های عددی"""
    if df is None or df.empty:
        return []
    
    numeric_cols = []
    for col in df.columns:
        try:
            pd.to_numeric(df[col])
            numeric_cols.append(col)
        except:
            pass
    
    return numeric_cols

# ============================================================================
# ۲-۶: توابع کار با حافظه و بهینه‌سازی
# ============================================================================

def get_memory_usage():
    """دریافت میزان مصرف حافظه"""
    try:
        import psutil
        process = psutil.Process()
        memory = process.memory_info().rss / 1024 / 1024  # MB
        return f"{memory:.1f} MB"
    except:
        return 'نامشخص'

def optimize_dataframe(df):
    """بهینه‌سازی دیتافریم برای کاهش مصرف حافظه"""
    if df is None or df.empty:
        return df
    
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type != 'object':
            c_min = df[col].min()
            c_max = df[col].max()
            
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
            else:
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
    
    return df
# ============================================================================
# بخش ۳: تنظیمات پیش‌فرض کامل (برگرفته از برنامه اصلی شما با بهبود)
# ============================================================================

DEFAULT_SETTINGS = {
    'version': VERSION,
    'app_name': APP_NAME,
    'last_update': None,
    
    # =========================================================================
    # ۳-۱: وزن‌های تحلیل پایه (۶ معیار اصلی)
    # =========================================================================
    'weights': {
        'eps_weight': 0.40,           # وزن EPS
        'pb_weight': 0.25,             # وزن P/B
        'eps_growth_weight': 0.15,      # وزن رشد EPS
        'pe_weight': 0.10,              # وزن P/E
        'rsi_weight': 0.05,             # وزن RSI
        'volume_weight': 0.05           # وزن حجم معاملات
    },
    
    # =========================================================================
    # ۳-۲: آستانه‌های EPS
    # =========================================================================
    'eps_thresholds': {
        'excellent': 2000,      # عالی
        'very_good': 1000,       # خیلی خوب
        'good': 500,             # خوب
        'average': 200,          # متوسط
        'below_average': 100,    # زیر متوسط
        'low': 50,               # کم
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
    
    # =========================================================================
    # ۳-۳: آستانه‌های P/B
    # =========================================================================
    'pb_thresholds': {
        'excellent': 0.8,        # عالی (ارزان)
        'very_good': 1.2,         # خیلی خوب
        'good': 1.5,              # خوب
        'average': 2.0,           # متوسط
        'scores': {
            'excellent': 100,
            'very_good': 80,
            'good': 60,
            'average': 40,
            'poor': 20
        }
    },
    
    # =========================================================================
    # ۳-۴: آستانه‌های رشد EPS
    # =========================================================================
    'eps_growth_thresholds': {
        'excellent': 50,          # رشد عالی
        'very_good': 30,          # رشد خیلی خوب
        'good': 10,               # رشد خوب
        'average': 0,             # رشد متوسط
        'poor': -10,              # رشد منفی
        'scores': {
            'excellent': 100,
            'very_good': 80,
            'good': 60,
            'average': 40,
            'poor': 20,
            'very_poor': 0
        }
    },
    
    # =========================================================================
    # ۳-۵: آستانه‌های P/E
    # =========================================================================
    'pe_thresholds': {
        'excellent': 8,           # عالی (ارزان)
        'very_good': 12,          # خیلی خوب
        'good': 20,               # خوب
        'scores': {
            'excellent': 100,
            'very_good': 80,
            'good': 60,
            'poor': 30
        }
    },
    
    # =========================================================================
    # ۳-۶: آستانه‌های RSI
    # =========================================================================
    'rsi_thresholds': {
        'oversold_extreme': 20,    # فوق اشباع فروش
        'oversold': 30,            # اشباع فروش
        'overbought': 70,          # اشباع خرید
        'overbought_extreme': 85,  # فوق اشباع خرید
        'scores': {
            'oversold_extreme': 100,
            'oversold': 80,
            'neutral_low': 60,
            'neutral_high': 40,
            'overbought': 20,
            'overbought_extreme': 10
        }
    },
    
    # =========================================================================
    # ۳-۷: آستانه‌های حجم معاملات
    # =========================================================================
    'volume_thresholds': {
        'excellent': 10000000,    # ۱۰ میلیون
        'very_good': 5000000,      # ۵ میلیون
        'good': 1000000,           # ۱ میلیون
        'average': 500000,         # ۵۰۰ هزار
        'scores': {
            'excellent': 100,
            'very_good': 80,
            'good': 60,
            'average': 40,
            'low': 20
        }
    },
    
    # =========================================================================
    # ۳-۸: فیلترهای اولیه
    # =========================================================================
    'filters': {
        'min_volume': 100000,      # حداقل حجم
        'max_pb': 2.5,             # حداکثر P/B
        'min_eps': 50,             # حداقل EPS
        'max_pe': 30,              # حداکثر P/E
        'rsi_min': 20,             # حداقل RSI
        'rsi_max': 80,             # حداکثر RSI
        'max_1month_return': 50,   # حداکثر بازده یک ماهه
        'min_price': 1000,         # حداقل قیمت
        'max_price': 500000,       # حداکثر قیمت
        'min_market_cap': 100000000000,  # حداقل ارزش بازار (۱۰۰ میلیارد)
        'max_debt_to_equity': 2,    # حداکثر نسبت بدهی
        'min_current_ratio': 0.8,   # حداقل نسبت جاری
        'min_quick_ratio': 0.5      # حداقل نسبت آنی
    },
    
    # =========================================================================
    # ۳-۹: معیارهای حذف (Disqualifiers)
    # =========================================================================
    'disqualifiers': {
        'max_pb_disqualify': 3.0,           # حذف اگر P/B > 3
        'min_eps_disqualify': 0,             # حذف اگر EPS منفی
        'max_rsi_disqualify': 85,            # حذف اگر RSI > 85
        'max_1month_return_disqualify': 60,  # حذف اگر بازده ماه > 60%
        'negative_equity': True,              # حذف اگر حقوق صاحبان سهام منفی
        'zero_volume': True,                   # حذف اگر حجم صفر
        'suspended': True                      # حذف اگر نماد متوقف
    },
    
    # =========================================================================
    # ۳-۱۰: اعتبارسنجی نهایی
    # =========================================================================
    'validation': {
        'min_final_score': 50,        # حداقل امتیاز نهایی
        'max_pb_final': 2.0,          # حداکثر P/B در نتایج نهایی
        'max_pe_final': 25,           # حداکثر P/E در نتایج نهایی
        'max_rsi_final': 65,          # حداکثر RSI در نتایج نهایی
        'max_stocks_final': 10,        # حداکثر تعداد سهام در خروجی
        'min_liquidity_final': 500000  # حداقل نقدشوندگی
    },
    
    # =========================================================================
    # ۳-۱۱: آستانه‌های وضعیت
    # =========================================================================
    'status_thresholds': {
        'excellent': 85,       # عالی
        'very_good': 75,       # خیلی خوب
        'good': 65,            # خوب
        'average': 55,         # متوسط
        'acceptable': 50,      # قابل قبول
        'weak': 40,            # ضعیف
        'very_weak': 30        # خیلی ضعیف
    },
    
    # =========================================================================
    # ۳-۱۲: تنظیمات تحلیل حباب (Bubble Analysis)
    # =========================================================================
    'bubble': {
        'pe_high': 25,           # P/E بالا
        'pe_medium_high': 18,    # P/E نسبتاً بالا
        'pe_medium': 12,         # P/E متوسط
        'pe_low': 8,             # P/E پایین
        
        'pb_very_high': 5,       # P/B خیلی بالا
        'pb_high': 3,            # P/B بالا
        'pb_medium': 2,          # P/B متوسط
        'pb_low': 1,             # P/B پایین
        
        'return_1m_very_high': 30,   # بازده یک ماهه خیلی بالا
        'return_1m_high': 20,        # بازده یک ماهه بالا
        'return_1m_medium': 10,      # بازده یک ماهه متوسط
        
        'return_3m_very_high': 80,   # بازده سه ماهه خیلی بالا
        'return_3m_high': 50,        # بازده سه ماهه بالا
        'return_3m_medium': 30,      # بازده سه ماهه متوسط
        
        'volume_ratio_very_high': 3,  # نسبت حجم خیلی بالا
        'volume_ratio_high': 2,       # نسبت حجم بالا
        'volume_ratio_medium': 1.5,   # نسبت حجم متوسط
        
        'weights': {
            'pe': 0.3,                 # وزن P/E
            'pb': 0.3,                 # وزن P/B
            'growth': 0.25,            # وزن رشد
            'volume': 0.15             # وزن حجم
        },
        
        'scores': {
            'very_high_bubble': 100,    # حباب خیلی شدید
            'high_bubble': 80,          # حباب شدید
            'medium_bubble': 60,        # حباب متوسط
            'low_bubble': 40,           # حباب کم
            'no_bubble': 20,            # بدون حباب
            'negative_bubble': 10        # حباب منفی (ارزندگی)
        }
    },
    
    # =========================================================================
    # ۳-۱۳: تنظیمات ارزش ذاتی (Intrinsic Value)
    # =========================================================================
    'intrinsic_value': {
        'pe_multiplier': 8,          # ضریب P/E برای ارزش ذاتی
        'pb_multiplier': 1.5,        # ضریب P/B برای ارزش ذاتی
        'graham_base': 8.5,          # عدد پایه گراهام
        'graham_growth': 2,           # ضریب رشد گراهام
        'dividend_payout': 0.3,       # نسبت تقسیم سود
        'discount_rate': 0.15,        # نرخ تنزیل
        'growth_rate': 0.10,          # نرخ رشد
        'terminal_growth': 0.03,      # نرخ رشد نهایی
        'forecast_years': 5,           # سال‌های پیش‌بینی
        
        'thresholds': {
            'strong_buy': 0.5,         # قیمت < 50% ارزش ذاتی
            'buy': 0.7,                 # قیمت < 70% ارزش ذاتی
            'cautious_buy': 0.9,        # قیمت < 90% ارزش ذاتی
            'hold': 1.1,                # قیمت بین 90% تا 110%
            'cautious_sell': 1.3,       # قیمت > 130% ارزش ذاتی
            'sell': 1.5                 # قیمت > 150% ارزش ذاتی
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
    
    # =========================================================================
    # ۳-۱۴: تنظیمات تابلوخوانی (Tape Reading)
    # =========================================================================
    'tape_reading': {
        'demand_supply_max': 3,           # حداکثر نسبت تقاضا به عرضه
        'price_power_min': -10,           # حداقل قدرت قیمت
        'price_power_max': 10,            # حداکثر قدرت قیمت
        'avg_trade_divisor': 50000000,    # مقسوم‌کننده میانگین معاملات
        'avg_trade_max': 5,                # حداکثر امتیاز میانگین معاملات
        
        'buy_power_thresholds': {
            'very_high': 1000000000,       # ۱ میلیارد
            'high': 500000000,              # ۵۰۰ میلیون
            'medium': 100000000,            # ۱۰۰ میلیون
            'low': 50000000                 # ۵۰ میلیون
        },
        
        'sell_pressure_thresholds': {
            'very_high': 0.7,               # ۷۰%
            'high': 0.6,                     # ۶۰%
            'medium': 0.5                    # ۵۰%
        },
        
        'power_index_thresholds': {
            'very_bullish': 5,               # خیلی صعودی
            'bullish': 2,                     # صعودی
            'bearish': -2,                    # نزولی
            'very_bearish': -5                # خیلی نزولی
        },
        
        'base_score': 50,
        'score_multiplier': 2.5
    },
    
    # =========================================================================
    # ۳-۱۵: تنظیمات تحلیل ریسک
    # =========================================================================
    'risk': {
        'beta_thresholds': {
            'very_high': 1.5,                # ریسک خیلی بالا
            'high': 1.2,                      # ریسک بالا
            'medium': 0.8,                    # ریسک متوسط
            'low': 0.5                        # ریسک پایین
        },
        
        'volume_thresholds': {
            'very_low': 100000,                # نقدشوندگی خیلی کم
            'low': 500000,                      # نقدشوندگی کم
            'medium': 1000000,                  # نقدشوندگی متوسط
            'high': 5000000,                    # نقدشوندگی بالا
            'very_high': 10000000               # نقدشوندگی خیلی بالا
        },
        
        'volatility_thresholds': {
            'very_high': 100,                   # نوسان خیلی بالا
            'high': 50,                          # نوسان بالا
            'medium': 20                         # نوسان متوسط
        },
        
        'liquidity_scores': {
            'very_high': 100,
            'high': 80,
            'medium': 60,
            'low': 40,
            'very_low': 20,
            'zero': 0
        },
        
        'weights': {
            'beta': 0.2,                         # وزن بتا
            'liquidity': 0.2,                     # وزن نقدشوندگی
            'volatility': 0.15,                    # وزن نوسان
            'rsi': 0.15,                           # وزن RSI
            'pb': 0.15,                            # وزن P/B
            'eps': 0.15                             # وزن EPS
        },
        
        'risk_free_rate': 0.20,                    # نرخ بدون ریسک (۲۰%)
        'market_return': 0.35                       # بازده بازار (۳۵%)
    },
    
    # =========================================================================
    # ۳-۱۶: تنظیمات تحلیل عملکرد
    # =========================================================================
    'performance': {
        'cagr_weights': {
            '1m': 0.1,                             # وزن بازده یک ماهه
            '3m': 0.2,                              # وزن بازده سه ماهه
            '6m': 0.3,                              # وزن بازده شش ماهه
            '1y': 0.3,                              # وزن بازده یک ساله
            'consistency': 0.1                       # وزن ثبات
        },
        
        'cagr_multipliers': {
            '1m': 50,                               # ضریب بازده یک ماهه
            '3m': 40,                               # ضریب بازده سه ماهه
            '6m': 30,                               # ضریب بازده شش ماهه
            '1y': 20                                # ضریب بازده یک ساله
        },
        
        'cagr_limits': {
            'min': -10,                             # حداقل بازده قابل قبول
            'max': 20                                # حداکثر بازده مطلوب
        },
        
        'sharpe_ratio_thresholds': {
            'excellent': 2.0,                        # نسبت شارپ عالی
            'good': 1.5,                              # نسبت شارپ خوب
            'average': 1.0,                           # نسبت شارپ متوسط
            'poor': 0.5                               # نسبت شارپ ضعیف
        },
        
        'base_score': 50,
        'score_multiplier': 2.5
    },
    
    # =========================================================================
    # ۳-۱۷: تنظیمات تحلیل تکنیکال پیشرفته
    # =========================================================================
    'technical': {
        'rsi_period': 14,                            # دوره RSI
        'macd_fast': 12,                              # MACD سریع
        'macd_slow': 26,                              # MACD کند
        'macd_signal': 9,                             # سیگنال MACD
        'bb_period': 20,                              # دوره بولینگر
        'bb_std': 2,                                  # انحراف معیار بولینگر
        
        'rsi_thresholds': {
            'oversold_extreme': 20,                    # فوق اشباع فروش
            'oversold': 30,                            # اشباع فروش
            'overbought': 70,                          # اشباع خرید
            'overbought_extreme': 85                   # فوق اشباع خرید
        },
        
        'mfi_thresholds': {
            'oversold_extreme': 20,                    # فوق اشباع فروش
            'oversold': 30,                            # اشباع فروش
            'overbought': 80,                          # اشباع خرید
            'overbought_extreme': 90                   # فوق اشباع خرید
        },
        
        'stoch_k': 14,                                 # دوره %K استوکاستیک
        'stoch_d': 3,                                  # دوره %D استوکاستیک
        
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
            'neutral': 0,
            'mildly_bearish': -1,
            'bearish': -2,
            'very_bearish': -3
        },
        
        'position_scores': {
            'excellent': 2,
            'good': 1,
            'neutral': 0,
            'poor': -1,
            'very_poor': -2
        },
        
        'base_score': 50,
        'score_multiplier': 5,
        
        'indicators': {
            'sma': [5, 10, 20, 30, 50, 200],          # میانگین‌های متحرک ساده
            'ema': [12, 26, 50, 100],                  # میانگین‌های متحرک نمایی
            'volume_ma': [5, 10, 20]                   # میانگین حجم
        }
    },
    
    # =========================================================================
    # ۳-۱۸: تنظیمات تحلیل پورتفو
    # =========================================================================
    'portfolio': {
        'alert_thresholds': {
            'profit_high': 25,                          # سود بالا
            'profit_medium': 15,                        # سود متوسط
            'loss_high': -15,                           # ضرر بالا
            'loss_medium': -10,                         # ضرر متوسط
            'loss_low': -8,                             # ضرر کم
            'loss_very_low': -3                         # ضرر خیلی کم
        },
        
        'rsi_thresholds': {
            'high': 70,                                 # RSI بالا
            'low': 30                                   # RSI پایین
        },
        
        'pb_thresholds': {
            'high': 2.5,                                # P/B بالا
            'low': 0.8                                  # P/B پایین
        },
        
        'status_thresholds': {
            'excellent': 20,                            # وضعیت عالی
            'very_good': 15,                            # وضعیت خیلی خوب
            'good': 10,                                 # وضعیت خوب
            'average': 5,                               # وضعیت متوسط
            'poor': 0,                                  # وضعیت ضعیف
            'very_poor': -10                            # وضعیت خیلی ضعیف
        },
        
        'diversity_scores': {
            10: 100,                                    # ۱۰ نماد مختلف
            7: 80,                                      # ۷ نماد مختلف
            5: 60,                                      # ۵ نماد مختلف
            3: 40,                                      # ۳ نماد مختلف
            'default': 20                               # کمتر از ۳ نماد
        },
        
        'max_portfolio_weight': 0.20,                   # حداکثر وزن یک نماد (۲۰%)
        'min_cash_ratio': 0.05,                         # حداقل نسبت نقدینگی (۵%)
        'rebalance_threshold': 0.10                      # آستانه بازتعادل (۱۰%)
    },
    
    # =========================================================================
    # ۳-۱۹: تنظیمات API برس‌آی‌آر
    # =========================================================================
    'api': {
        'enabled': False,
        'provider': 'brsapi',
        'mobile': '',
        'api_key': '',
        'auto_refresh': True,
        'refresh_interval': 300,                         # ۵ دقیقه
        'use_cache': True,
        'cache_ttl': 300,                                # ۵ دقیقه
        'retry_count': 3,                                # تعداد تلاش مجدد
        'retry_delay': 1,                                # تأخیر بین تلاش‌ها (ثانیه)
        'timeout': 30,                                   # زمان انتظار (ثانیه)
        'user_agent_rotation': True,                     # چرخش User-Agent
        'verify_ssl': True,                              # بررسی SSL
        
        'data_sources': {
            'prices': True,                              # دریافت قیمت‌ها
            'clients': True,                             # دریافت داده مشتریان
            'history': True,                              # دریافت تاریخچه
            'symbols': True,                              # دریافت لیست نمادها
            'news': False,                                # دریافت اخبار
            'events': False                               # دریافت رویدادها
        },
        
        'endpoints': {
            'base': 'https://brsapi.ir',
            'login': '/Api/Auth/Login',
            'prices': '/Api/Market/PriceList',
            'history': '/Api/Market/History',
            'symbols': '/Api/Market/Symbols',
            'clients': '/Api/Clients/Data',
            'news': '/Api/News/List',
            'events': '/Api/Events/List'
        },
        
        'last_sync': None,
        'sync_status': 'never',
        'error_count': 0,
        'success_count': 0,
        'total_requests': 0,
        'avg_response_time': 0
    },
    
    # =========================================================================
    # ۳-۲۰: تنظیمات پایگاه داده و حافظه
    # =========================================================================
    'database': {
        'use_sqlite': False,                             # استفاده از SQLite
        'sqlite_file': os.path.join(DATA_DIR, 'data.db'),
        'use_redis': False,                              # استفاده از Redis
        'redis_host': 'localhost',
        'redis_port': 6379,
        'redis_db': 0,
        'redis_password': '',
        'cache_enabled': True,
        'max_cache_size': 1000,                          # حداکثر آیتم در کش
        'auto_cleanup': True,
        'cleanup_interval': 3600                          # ۱ ساعت
    },
    
    # =========================================================================
    # ۳-۲۱: تنظیمات نمایش و رابط کاربری
    # =========================================================================
    'ui': {
        'theme': 'light',                                 # تم: light/dark
        'font_family': 'Vazir, Tahoma, Arial, sans-serif',
        'font_size': 14,
        'chart_theme': 'plotly',
        'language': 'fa',                                 # زبان: fa/en
        'date_format': '%Y/%m/%d',
        'time_format': '%H:%M:%S',
        'number_format': {
            'decimal_separator': '٫',
            'thousand_separator': '٬',
            'currency': 'تومان'
        },
        'table': {
            'page_size': 25,
            'fixed_header': True,
            'striped_rows': True,
            'hover_effect': True,
            'responsive': True
        },
        'charts': {
            'height': 500,
            'width': '100%',
            'show_legend': True,
            'show_grid': True
        }
    },
    
    # =========================================================================
    # ۳-۲۲: تنظیمات لاگینگ و اشکال‌زدایی
    # =========================================================================
    'logging': {
        'level': 'INFO',                                  # سطح لاگ
        'save_to_file': True,                             # ذخیره در فایل
        'print_console': True,                            # نمایش در کنسول
        'max_file_size': 10 * 1024 * 1024,                # ۱۰ مگابایت
        'backup_count': 5,                                 # تعداد فایل‌های پشتیبان
        'log_requests': True,                             # لاگ درخواست‌ها
        'log_responses': False,                            # لاگ پاسخ‌ها
        'log_performance': True,                           # لاگ عملکرد
        'debug_mode': False                                # حالت اشکال‌زدایی
    },
    
    # =========================================================================
    # ۳-۲۳: تنظیمات بهینه‌سازی
    # =========================================================================
    'optimization': {
        'use_compression': True,                          # استفاده از فشرده‌سازی
        'use_multithreading': True,                        # استفاده از چندنخی
        'max_workers': 4,                                  # حداکثر تعداد نخ‌ها
        'batch_size': 100,                                 # اندازه دسته
        'chunk_size': 10000,                               # اندازه تکه‌ها
        'memory_limit': 1024 * 1024 * 1024,                # ۱ گیگابایت
        'timeout': 300                                     # ۵ دقیقه
    },
    
    # =========================================================================
    # ۳-۲۴: تنظیمات ایزی‌تریدر
    # =========================================================================
    'ez_trader': {
        'enabled': False,
        'username': '',
        'password': '',
        'host': 'localhost',
        'port': 8080,
        'use_ssl': False,
        'auto_connect': False,
        'reconnect_interval': 60,                          # ۱ دقیقه
        'timeout': 30
    },
    
    # =========================================================================
    # ۳-۲۵: تنظیمات هشدار و نوتیفیکیشن
    # =========================================================================
    'alerts': {
        'enabled': True,
        'sound': True,
        'desktop_notification': True,
        'email_notification': False,
        'telegram_bot': False,
        'telegram_token': '',
        'telegram_chat_id': '',
        'email_smtp': '',
        'email_port': 587,
        'email_user': '',
        'email_password': '',
        'email_to': '',
        
        'price_alerts': True,
        'volume_alerts': True,
        'indicator_alerts': True,
        'portfolio_alerts': True,
        
        'check_interval': 60                                # ۱ دقیقه
    }
}

# ============================================================================
# بخش ۴: کلاس Settings (مدیریت تنظیمات پیشرفته)
# ============================================================================

class Settings:
    """
    مدیریت تنظیمات برنامه با قابلیت‌های پیشرفته:
    - بارگذاری و ذخیره خودکار
    - اعتبارسنجی مقادیر
    - تاریخچه تغییرات
    - پشتیبان‌گیری خودکار
    - تنظیمات پویا
    """
    
    def __init__(self, settings_file=SETTINGS_FILE, auto_load=True, auto_backup=True):
        """
        سازنده کلاس Settings
        Args:
            settings_file (str): مسیر فایل تنظیمات
            auto_load (bool): بارگذاری خودکار
            auto_backup (bool): پشتیبان‌گیری خودکار
        """
        self.settings_file = settings_file
        self.backup_dir = os.path.join(DATA_DIR, 'settings_backups')
        self.auto_backup = auto_backup
        self.history = []
        self.change_count = 0
        self.last_save = None
        self.lock = threading.RLock()  # برای دسترسی همزمان
        
        # ایجاد پوشه پشتیبان
        if auto_backup:
            os.makedirs(self.backup_dir, exist_ok=True)
        
        # بارگذاری تنظیمات
        if auto_load:
            self.settings = self.load_settings()
        else:
            self.settings = DEFAULT_SETTINGS.copy()
        
        # اطمینان از وجود تمام کلیدها
        self._ensure_defaults()
        
        debug_log("✅ کلاس Settings راه‌اندازی شد", "INFO")
    
    def _ensure_defaults(self):
        """اطمینان از وجود تمام تنظیمات پیش‌فرض"""
        try:
            # ادغام عمیق تنظیمات
            self.settings = self._deep_merge(DEFAULT_SETTINGS.copy(), self.settings)
            
            # به‌روزرسانی نسخه
            self.settings['version'] = VERSION
            
        except Exception as e:
            debug_log(f"خطا در اطمینان از تنظیمات پیش‌فرض: {e}", "ERROR")
    
    def _deep_merge(self, base, override):
        """
        ادغام عمیق دو دیکشنری
        Args:
            base (dict): دیکشنری پایه
            override (dict): دیکشنری جایگزین
        Returns:
            dict: دیکشنری ادغام شده
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base
    
    def load_settings(self):
        """بارگذاری تنظیمات از فایل"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                
                # ترکیب با تنظیمات پیش‌فرض
                settings = self._deep_merge(DEFAULT_SETTINGS.copy(), loaded)
                
                debug_log(f"✅ تنظیمات از {self.settings_file} بارگذاری شد", "INFO")
                return settings
            else:
                debug_log("📁 فایل تنظیمات یافت نشد، استفاده از پیش‌فرض", "INFO")
                return DEFAULT_SETTINGS.copy()
                
        except Exception as e:
            debug_log(f"❌ خطا در بارگذاری تنظیمات: {e}", "ERROR")
            return DEFAULT_SETTINGS.copy()
    
    def save_settings(self, backup=True):
        """
        ذخیره تنظیمات در فایل
        Args:
            backup (bool): ایجاد پشتیبان
        Returns:
            bool: موفقیت عملیات
        """
        with self.lock:
            try:
                # به‌روزرسانی زمان
                self.settings['last_update'] = datetime.now().isoformat()
                
                # ایجاد پشتیبان
                if backup and self.auto_backup and os.path.exists(self.settings_file):
                    self._create_backup()
                
                # ذخیره در فایل موقت
                temp_file = self.settings_file + '.tmp'
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, ensure_ascii=False, indent=2)
                
                # جایگزینی فایل اصلی
                shutil.move(temp_file, self.settings_file)
                
                self.last_save = datetime.now()
                debug_log("💾 تنظیمات با موفقیت ذخیره شد", "INFO")
                return True
                
            except Exception as e:
                debug_log(f"❌ خطا در ذخیره تنظیمات: {e}", "ERROR")
                return False
    
    def _create_backup(self):
        """ایجاد پشتیبان از فایل تنظیمات"""
        try:
            if os.path.exists(self.settings_file):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = os.path.join(self.backup_dir, f'settings_{timestamp}.json')
                shutil.copy2(self.settings_file, backup_file)
                
                # پاک کردن پشتیبان‌های قدیمی (بیشتر از ۳۰ روز)
                self._clean_old_backups(days=30)
                
                debug_log(f"📦 پشتیبان در {backup_file} ایجاد شد", "INFO")
                
        except Exception as e:
            debug_log(f"⚠️ خطا در ایجاد پشتیبان: {e}", "WARNING")
    
    def _clean_old_backups(self, days=30):
        """پاک کردن پشتیبان‌های قدیمی"""
        try:
            now = time.time()
            for filename in os.listdir(self.backup_dir):
                filepath = os.path.join(self.backup_dir, filename)
                if os.path.isfile(filepath) and filename.startswith('settings_'):
                    file_time = os.path.getmtime(filepath)
                    if now - file_time > days * 86400:
                        os.remove(filepath)
                        debug_log(f"🧹 پشتیبان قدیمی {filename} حذف شد", "INFO")
        except Exception as e:
            debug_log(f"⚠️ خطا در پاکسازی پشتیبان‌ها: {e}", "WARNING")
    
    def get(self, key_path, default=None):
        """
        دریافت مقدار با کلید مسیری (مثلاً 'weights.eps_weight')
        Args:
            key_path (str): مسیر کلید با نقطه
            default: مقدار پیش‌فرض
        Returns:
            مقدار مورد نظر
        """
        try:
            keys = key_path.split('.')
            value = self.settings
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                    if value is None:
                        return default
                else:
                    return default
            return value
        except Exception:
            return default
    
    def set(self, key_path, value, record_history=True):
        """
        تنظیم مقدار با کلید مسیری
        Args:
            key_path (str): مسیر کلید با نقطه
            value: مقدار جدید
            record_history (bool): ثبت در تاریخچه
        Returns:
            bool: موفقیت عملیات
        """
        with self.lock:
            try:
                keys = key_path.split('.')
                target = self.settings
                
                # ثبت تغییر در تاریخچه
                if record_history:
                    old_value = self.get(key_path)
                    self.history.append({
                        'timestamp': datetime.now().isoformat(),
                        'key': key_path,
                        'old_value': old_value,
                        'new_value': value,
                        'change_id': self.change_count
                    })
                    self.change_count += 1
                
                # اعمال تغییر
                for key in keys[:-1]:
                    if key not in target:
                        target[key] = {}
                    target = target[key]
                
                target[keys[-1]] = value
                
                # اعتبارسنجی
                self._validate_setting(key_path, value)
                
                return True
                
            except Exception as e:
                debug_log(f"خطا در تنظیم {key_path}: {e}", "ERROR")
                return False
    
    def _validate_setting(self, key_path, value):
        """
        اعتبارسنجی مقدار تنظیم شده
        Args:
            key_path (str): مسیر کلید
            value: مقدار
        """
        try:
            # اعتبارسنجی‌های خاص
            if 'weight' in key_path:
                # وزن‌ها باید بین ۰ و ۱ باشند
                if not (0 <= value <= 1):
                    debug_log(f"⚠️ وزن {key_path} باید بین ۰ و ۱ باشد", "WARNING")
            
            elif 'interval' in key_path or 'ttl' in key_path:
                # بازه‌های زمانی باید مثبت باشند
                if value <= 0:
                    debug_log(f"⚠️ {key_path} باید مثبت باشد", "WARNING")
            
            elif key_path == 'api.mobile':
                # شماره موبایل باید با ۰۹ شروع شود
                if value and not str(value).startswith('09'):
                    debug_log(f"⚠️ شماره موبایل باید با ۰۹ شروع شود", "WARNING")
            
            elif key_path == 'api.api_key':
                # کلید API باید ۳۲ کاراکتر باشد
                if value and len(str(value)) != 32:
                    debug_log(f"⚠️ کلید API باید ۳۲ کاراکتر باشد", "WARNING")
                    
        except Exception as e:
            debug_log(f"خطا در اعتبارسنجی {key_path}: {e}", "ERROR")
    
    def update(self, updates, record_history=True):
        """
        به‌روزرسانی چندگانه تنظیمات
        Args:
            updates (dict): دیکشنری تغییرات
            record_history (bool): ثبت در تاریخچه
        Returns:
            bool: موفقیت عملیات
        """
        success = True
        for key_path, value in updates.items():
            if not self.set(key_path, value, record_history):
                success = False
        return success
    
    def reset_to_defaults(self, section=None):
        """
        بازنشانی به تنظیمات پیش‌فرض
        Args:
            section (str): بخش خاص (اختیاری)
        Returns:
            bool: موفقیت عملیات
        """
        try:
            if section:
                if section in DEFAULT_SETTINGS:
                    self.settings[section] = DEFAULT_SETTINGS[section].copy()
                    debug_log(f"🔄 بخش {section} به پیش‌فرض بازنشانی شد", "INFO")
            else:
                self.settings = DEFAULT_SETTINGS.copy()
                debug_log("🔄 تمام تنظیمات به پیش‌فرض بازنشانی شد", "INFO")
            
            return self.save_settings()
            
        except Exception as e:
            debug_log(f"خطا در بازنشانی تنظیمات: {e}", "ERROR")
            return False
    
    def export_settings(self, file_path=None):
        """
        خروجی گرفتن از تنظیمات
        Args:
            file_path (str): مسیر فایل خروجی
        Returns:
            dict/None: تنظیمات یا None در صورت خطا
        """
        try:
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, ensure_ascii=False, indent=2)
                debug_log(f"📤 تنظیمات در {file_path} ذخیره شد", "INFO")
            
            return self.settings
            
        except Exception as e:
            debug_log(f"خطا در خروجی تنظیمات: {e}", "ERROR")
            return None
    
    def import_settings(self, file_path, merge=True):
        """
        وارد کردن تنظیمات از فایل
        Args:
            file_path (str): مسیر فایل
            merge (bool): ادغام با تنظیمات فعلی
        Returns:
            bool: موفقیت عملیات
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported = json.load(f)
            
            if merge:
                self.settings = self._deep_merge(self.settings, imported)
            else:
                self.settings = imported
            
            debug_log(f"📥 تنظیمات از {file_path} وارد شد", "INFO")
            return self.save_settings()
            
        except Exception as e:
            debug_log(f"خطا در وارد کردن تنظیمات: {e}", "ERROR")
            return False
    
    def get_history(self, limit=100, key_filter=None):
        """
        دریافت تاریخچه تغییرات
        Args:
            limit (int): حداکثر تعداد
            key_filter (str): فیلتر کلید
        Returns:
            list: تاریخچه
        """
        history = self.history[-limit:]
        
        if key_filter:
            history = [h for h in history if key_filter in h['key']]
        
        return history
    
    def get_stats(self):
        """
        دریافت آمار تنظیمات
        Returns:
            dict: آمار
        """
        return {
            'total_keys': self._count_keys(self.settings),
            'last_save': self.last_save.isoformat() if self.last_save else None,
            'change_count': self.change_count,
            'history_size': len(self.history),
            'backup_count': len(os.listdir(self.backup_dir)) if os.path.exists(self.backup_dir) else 0
        }
    
    def _count_keys(self, d):
        """شمارش تعداد کلیدها در دیکشنری تو در تو"""
        count = 0
        for k, v in d.items():
            count += 1
            if isinstance(v, dict):
                count += self._count_keys(v)
        return count
    
    def get_api_settings(self):
        """دریافت تنظیمات API"""
        return self.settings.get('api', DEFAULT_SETTINGS['api'])
    
    def update_api_settings(self, api_config):
        """به‌روزرسانی تنظیمات API"""
        current_api = self.get_api_settings()
        current_api.update(api_config)
        self.settings['api'] = current_api
        return self.save_settings()
    
    def is_api_enabled(self):
        """بررسی فعال بودن API"""
        api = self.get_api_settings()
        return api.get('enabled', False) and api.get('mobile') and api.get('api_key')
    
    def get_weights(self):
        """دریافت وزن‌های تحلیل"""
        return self.settings.get('weights', DEFAULT_SETTINGS['weights'])
    
    def get_thresholds(self, name):
        """دریافت آستانه‌های مشخص"""
        return self.settings.get(f'{name}_thresholds', {})
    
    def get_filters(self):
        """دریافت فیلترها"""
        return self.settings.get('filters', DEFAULT_SETTINGS['filters'])
    
    def get_disqualifiers(self):
        """دریافت معیارهای حذف"""
        return self.settings.get('disqualifiers', DEFAULT_SETTINGS['disqualifiers'])
    
    def get_validation(self):
        """دریافت تنظیمات اعتبارسنجی"""
        return self.settings.get('validation', DEFAULT_SETTINGS['validation'])
    
    def __getitem__(self, key):
        """دسترسی با []"""
        return self.settings.get(key)
    
    def __setitem__(self, key, value):
        """تنظیم با []"""
        self.set(key, value)
    
    def __contains__(self, key):
        """بررسی وجود کلید"""
        return key in self.settings
    
    def __repr__(self):
        return f"Settings(file='{self.settings_file}', changes={self.change_count})"

# ============================================================================
# بخش ۵: کلاس BrsApiConnector (اتصال به API برس‌آی‌آر)
# ============================================================================

class BrsApiConnector:
    """
    اتصال به API برس‌آی‌آر (brsapi.ir) بر اساس مستندات رسمی
    
    این کلاس از وب‌سرویس رایگان بورس Tsetmc استفاده می‌کند:
    https://BrsApi.ir/Api/Tsetmc/AllSymbols.php?key=YourApiKey&type=Number
    """
    
    # آدرس پایه API (مطابق مستندات)
    BASE_URL = "https://BrsApi.ir"
    
    # مسیرهای API بر اساس مستندات
    ENDPOINTS = {
        'all_symbols': "/Api/Tsetmc/AllSymbols.php",     # دریافت همه نمادها
        # در صورت وجود سرویس‌های دیگر می‌توان اضافه کرد
    }
    
    # نوع اوراق (type)
    SYMBOL_TYPES = {
        'all': 1,           # سهام بورس و فرابورس + صندوق‌های ETF + حق‌تقدم
        'commodity': 2,     # بورس کالا
        'futures': 3,       # آتی
        'bonds': 4,         # اوراق بدهی
        'mortgage': 5,      # تسهیلات مسکن
    }
    
    # لیست User-Agentهای معتبر
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]
    
    def __init__(self, api_key=None, mobile=None, data_dir=None, settings=None):
        """
        سازنده کلاس BrsApiConnector
        
        Args:
            api_key (str): کلید وب‌سرویس دریافتی از پنل (مثال: FreeSV0E1LSgB9RDjuf0QorSLViX8pPG)
            mobile (str): شماره موبایل ثبت شده در پنل (اختیاری - در این API استفاده نمی‌شود)
            data_dir (str): دایرکتوری برای ذخیره کش و داده‌ها
            settings (Settings): شیء تنظیمات برنامه
        """
        self.api_key = api_key
        self.mobile = mobile  # در این API استفاده نمی‌شود ولی برای سازگاری نگه داشته شده
        
        # تنظیمات پیش‌فرض
        self.use_cache = True
        self.cache_ttl = 300  # 5 دقیقه
        self.retry_count = 3
        self.retry_delay = 1
        self.timeout = 30
        self.user_agent_rotation = True
        self.verify_ssl = True  # می‌توانید False کنید اگر مشکل SSL دارید
        
        # دایرکتوری کش
        if data_dir:
            self.cache_dir = os.path.join(data_dir, 'api_cache')
        else:
            self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'api_cache')
        
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # وضعیت اتصال
        self.session = None
        self.is_authenticated = False
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        
        # قفل برای دسترسی همزمان
        self.lock = threading.RLock()
        
        # ایجاد سشن اولیه
        self._create_session()
        
        # تنظیم احراز هویت (فقط کلید API)
        if api_key:
            self.set_authentication(api_key)
        
        debug_log("✅ کلاس BrsApiConnector بر اساس مستندات رسمی راه‌اندازی شد", "API")
    
    def _create_session(self):
        """ایجاد سشن HTTP"""
        try:
            self.session = requests.Session()
            
            # تنظیم User-Agent
            if self.user_agent_rotation:
                self._rotate_user_agent()
            else:
                self.session.headers.update({'User-Agent': self.USER_AGENTS[0]})
            
            # تنظیم هدرهای پیش‌فرض
            self.session.headers.update({
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'fa-IR,fa;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
            })
            
            debug_log("✅ سشن HTTP ایجاد شد", "API")
            
        except Exception as e:
            debug_log(f"❌ خطا در ایجاد سشن: {e}", "ERROR")
            self.session = requests.Session()
    
    def _rotate_user_agent(self):
        """چرخش User-Agent"""
        if self.session:
            user_agent = random.choice(self.USER_AGENTS)
            self.session.headers.update({'User-Agent': user_agent})
    
    def set_authentication(self, api_key):
        """
        تنظیم احراز هویت با API Key
        
        Args:
            api_key (str): کلید وب‌سرویس
        """
        with self.lock:
            self.api_key = api_key
            self.is_authenticated = True
            debug_log(f"✅ احراز هویت با API Key تنظیم شد", "API")
            return True
    
    def _get_cache_key(self, params):
        """تولید کلید کش"""
        params_str = json.dumps(params, sort_keys=True) if params else ""
        return hashlib.md5(params_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key):
        """دریافت از کش"""
        if not self.use_cache:
            return None
        
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            if os.path.exists(cache_file):
                file_time = os.path.getmtime(cache_file)
                if time.time() - file_time < self.cache_ttl:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
        except Exception as e:
            debug_log(f"⚠️ خطا در خواندن کش: {e}", "WARNING")
        
        return None
    
    def _save_to_cache(self, cache_key, data):
        """ذخیره در کش"""
        if not self.use_cache:
            return
        
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            debug_log(f"⚠️ خطا در ذخیره کش: {e}", "WARNING")
    
    def _make_request(self, endpoint, params=None, use_cache=True):
        """
        ارسال درخواست به API
        
        Args:
            endpoint (str): آدرس endpoint
            params (dict): پارامترها
            use_cache (bool): استفاده از کش
        """
        # بررسی احراز هویت
        if not self.is_authenticated or not self.api_key:
            debug_log("⚠️ کلید API تنظیم نشده است", "WARNING")
            return None
        
        # چرخش User-Agent
        if self.user_agent_rotation:
            self._rotate_user_agent()
        
        # اضافه کردن کلید به پارامترها
        if params is None:
            params = {}
        params['key'] = self.api_key
        
        # ساخت URL
        url = urljoin(self.BASE_URL, endpoint)
        
        # مدیریت کش
        cache_key = None
        if use_cache:
            cache_key = self._get_cache_key(params)
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        # تلاش برای ارسال درخواست
        for attempt in range(self.retry_count):
            try:
                start_time = time.time()
                
                debug_log(f"📡 تلاش {attempt + 1}/{self.retry_count}: {url}", "API")
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )
                
                response_time = time.time() - start_time
                self.request_count += 1
                
                debug_log(f"⏱️ زمان پاسخ: {response_time:.2f} ثانیه", "API")
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        
                        # ذخیره در کش
                        if use_cache and cache_key:
                            self._save_to_cache(cache_key, result)
                        
                        self.success_count += 1
                        return result
                        
                    except json.JSONDecodeError:
                        debug_log("❌ خطا در تجزیه JSON", "ERROR")
                        
                elif response.status_code == 401:
                    debug_log("❌ خطای احراز هویت - کلید نامعتبر است", "ERROR")
                    break
                    
                elif response.status_code == 403:
                    debug_log("❌ دسترسی مسدود شده", "ERROR")
                    break
                    
                elif response.status_code == 429:
                    wait_time = 2 ** attempt
                    debug_log(f"⚠️ محدودیت نرخ - صبر {wait_time} ثانیه", "WARNING")
                    time.sleep(wait_time)
                    continue
                    
                elif response.status_code == 404:
                    debug_log(f"❌ خطای 404 - آدرس {url} یافت نشد", "ERROR")
                    break
                    
                else:
                    debug_log(f"❌ خطای HTTP {response.status_code}", "ERROR")
                    
                    if response.status_code >= 500 and attempt < self.retry_count - 1:
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                        continue
                    else:
                        break
                        
            except requests.exceptions.Timeout:
                debug_log(f"❌ زمان درخواست به پایان رسید", "ERROR")
                if attempt < self.retry_count - 1:
                    time.sleep(2 ** attempt)
                else:
                    break
                    
            except requests.exceptions.ConnectionError:
                debug_log(f"❌ خطای اتصال", "ERROR")
                if attempt < self.retry_count - 1:
                    time.sleep(2 ** attempt)
                else:
                    break
                    
            except Exception as e:
                debug_log(f"❌ خطای غیرمنتظره: {str(e)}", "ERROR")
                break
        
        self.error_count += 1
        return None
    
    def get_all_symbols(self, symbol_type=1, use_cache=True):
        """
        دریافت لیست همه نمادها
        
        Args:
            symbol_type (int): نوع اوراق:
                1 = سهام بورس و فرابورس + صندوق‌های ETF + حق‌تقدم
                2 = بورس کالا
                3 = آتی
                4 = اوراق بدهی
                5 = تسهیلات مسکن
            use_cache (bool): استفاده از کش
        
        Returns:
            DataFrame: اطلاعات نمادها
        """
        params = {'type': symbol_type}
        
        result = self._make_request(
            self.ENDPOINTS['all_symbols'],
            params=params,
            use_cache=use_cache
        )
        
        if result and isinstance(result, list):
            df = pd.DataFrame(result)
            
            # استانداردسازی نام ستون‌ها بر اساس مستندات
            column_mapping = {
                'l18': 'نماد',
                'l30': 'نام',
                'isin': 'ISIN',
                'id': 'شناسه داخلی',
                'cs': 'صنعت',
                'cs_id': 'شناسه صنعت',
                'z': 'تعداد سهام',
                'bvol': 'حجم مبنا',
                'mv': 'ارزش بازار',
                'eps': 'EPS',
                'pe': 'P/E',
                'tmin': 'آستانه مجاز پایین',
                'tmax': 'آستانه مجاز بالا',
                'pmin': 'کمترین قیمت',
                'pmax': 'بیشترین قیمت',
                'py': 'قیمت دیروز',
                'pf': 'اولین قیمت',
                'pl': 'آخرین قیمت',
                'plc': 'تغییر آخرین قیمت',
                'plp': 'درصد تغییر آخرین قیمت',
                'pc': 'قیمت پایانی',
                'pcc': 'تغییر قیمت پایانی',
                'pcp': 'درصد تغییر قیمت پایانی',
                'tno': 'تعداد معاملات',
                'tvol': 'حجم معاملات',
                'tval': 'ارزش معاملات',
                'time': 'زمان'
            }
            
            df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
            
            # ایجاد ستون قیمت یکپارچه
            if 'آخرین قیمت' in df.columns:
                df['قیمت'] = df['آخرین قیمت']
            elif 'قیمت پایانی' in df.columns:
                df['قیمت'] = df['قیمت پایانی']
            
            # تبدیل به عدد
            numeric_cols = ['قیمت', 'حجم معاملات', 'ارزش معاملات', 'EPS', 'P/E']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            debug_log(f"✅ {len(df)} نماد دریافت شد", "API")
            return df
        
        debug_log("⚠️ داده‌ای دریافت نشد", "WARNING")
        return pd.DataFrame()
    
    def get_market_prices(self, symbol_type=1, limit=None, use_cache=True):
        """
        دریافت قیمت‌های بازار (همان all_symbols است)
        
        Args:
            symbol_type (int): نوع اوراق
            limit (int): محدودیت تعداد (اختیاری)
            use_cache (bool): استفاده از کش
        """
        df = self.get_all_symbols(symbol_type=symbol_type, use_cache=use_cache)
        
        if not df.empty and limit:
            df = df.head(limit)
        
        return df
    
    def get_dashboard_data(self, use_cache=True):
        """
        دریافت داده‌های داشبورد
        """
        dashboard_data = {
            'prices': pd.DataFrame(),
            'symbols': pd.DataFrame(),
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            # دریافت داده‌ها
            symbols_df = self.get_all_symbols(symbol_type=1, use_cache=use_cache)
            
            if not symbols_df.empty:
                dashboard_data['symbols'] = symbols_df
                dashboard_data['prices'] = symbols_df  # همان داده‌ها
                dashboard_data['success'] = True
                
                debug_log("✅ داده‌های داشبورد دریافت شد", "API")
            
        except Exception as e:
            debug_log(f"❌ خطا در دریافت داده‌ها: {e}", "ERROR")
        
        return dashboard_data
    
    def test_connection(self):
        """تست اتصال به API"""
        try:
            result = self._make_request(
                self.ENDPOINTS['all_symbols'],
                params={'type': 1, 'limit': 1},
                use_cache=False
            )
            
            if result and isinstance(result, list):
                return {
                    'success': True,
                    'message': f'✅ اتصال با موفقیت برقرار شد - {len(result)} نماد دریافت شد'
                }
            else:
                return {
                    'success': False,
                    'message': '❌ خطا در دریافت داده'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'❌ خطا: {str(e)}'
            }
    
    def get_api_stats(self):
        """آمار استفاده از API"""
        success_rate = 0
        if self.request_count > 0:
            success_rate = (self.success_count / self.request_count) * 100
        
        return {
            'authenticated': self.is_authenticated,
            'request_count': self.request_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': round(success_rate, 1)
        }
    
    def clear_cache(self):
        """پاک کردن کش"""
        try:
            count = 0
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, filename))
                    count += 1
            debug_log(f"🧹 {count} فایل کش پاک شد", "API")
            return count
        except Exception as e:
            debug_log(f"⚠️ خطا در پاکسازی کش: {e}", "WARNING")
            return 0
# ============================================================================
# بخش ۶: کلاس DataManager (مدیریت داده‌ها با پشتیبانی از اکسل و API)
# ============================================================================

class DataManager:
    """
    مدیریت داده‌ها با پشتیبانی همزمان از:
    - فایل‌های اکسل (آپلود کاربر)
    - API برس‌آی‌آر
    - کش و حافظه موقت
    - تبدیل و نرمال‌سازی داده‌ها
    """
    
    def __init__(self, data_dir=DATA_DIR, settings=None):
        """
        سازنده کلاس DataManager
        Args:
            data_dir (str): دایرکتوری اصلی داده
            settings (Settings): تنظیمات برنامه
        """
        self.data_dir = data_dir
        self.settings = settings or Settings()
        
        # دایرکتوری‌های تخصصی
        self.uploads_dir = os.path.join(data_dir, 'uploads')
        self.cache_dir = os.path.join(data_dir, 'cache')
        self.api_cache_dir = os.path.join(data_dir, 'api_cache')
        self.portfolio_dir = os.path.join(data_dir, 'portfolio')
        
        # ایجاد دایرکتوری‌ها
        for dir_path in [self.uploads_dir, self.cache_dir, self.api_cache_dir, self.portfolio_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # نمونه API
        self.api_connector = None
        self.api_data = {}
        
        # داده‌های فعلی
        self.market_data = None
        self.portfolio_data = None
        self.watchlist_data = None
        self.symbols_data = None
        
        # متادیتا
        self.last_update = None
        self.data_sources = {}
        self.loaded_files = []
        
        # قفل برای دسترسی همزمان
        self.lock = threading.RLock()
        
        # بارگذاری داده‌های ذخیره شده
        self._load_cached_data()
        
        # اتصال به API اگر فعال باشد
        if self.settings.is_api_enabled():
            self.init_api_connection()
        
        debug_log("✅ DataManager با پشتیبانی از اکسل و API راه‌اندازی شد", "INFO")
    
    def _load_cached_data(self):
        """بارگذاری داده‌های ذخیره شده از کش"""
        try:
            # بارگذاری آخرین داده‌های بازار
            cache_file = os.path.join(self.cache_dir, 'last_market_data.pkl')
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    self.market_data = pickle.load(f)
                debug_log(f"📦 داده‌های بازار از کش بارگذاری شد ({len(self.market_data)} ردیف)", "INFO")
            
            # بارگذاری آخرین داده‌های پورتفو
            portfolio_file = os.path.join(self.portfolio_dir, 'portfolio.json')
            if os.path.exists(portfolio_file):
                with open(portfolio_file, 'r', encoding='utf-8') as f:
                    portfolio_data = json.load(f)
                    if portfolio_data:
                        self.portfolio_data = pd.DataFrame(portfolio_data)
                debug_log(f"📦 داده‌های پورتفو از کش بارگذاری شد", "INFO")
                
        except Exception as e:
            debug_log(f"⚠️ خطا در بارگذاری داده‌های کش: {e}", "WARNING")
    
    def init_api_connection(self):
        """راه‌اندازی اتصال به API"""
        try:
            api_settings = self.settings.get_api_settings()
            
            if api_settings.get('mobile') and api_settings.get('api_key'):
                self.api_connector = BrsApiConnector(
                    api_key=api_settings['api_key'],
                    mobile=api_settings['mobile'],
                    data_dir=self.data_dir,
                    settings=self.settings
                )
                
                # بررسی وضعیت احراز هویت
                if self.api_connector and self.api_connector.is_authenticated:
                    debug_log("✅ اتصال به API برقرار شد", "API")
                    
                    # به‌روزرسانی وضعیت
                    api_settings['sync_status'] = 'success'
                    api_settings['last_sync'] = datetime.now().isoformat()
                    self.settings.update_api_settings(api_settings)
                    
                    return True
                else:
                    debug_log("⚠️ اتصال به API ناموفق بود", "WARNING")
                    api_settings['sync_status'] = 'failed'
                    self.settings.update_api_settings(api_settings)
                    
        except Exception as e:
            debug_log(f"❌ خطا در اتصال به API: {e}", "ERROR")
            traceback.print_exc()
        
        return False
    
    def load_excel_file(self, file_path, file_type='market'):
        """
        بارگذاری فایل اکسل
        Args:
            file_path (str): مسیر فایل اکسل
            file_type (str): نوع فایل (market, portfolio, watchlist)
        Returns:
            DataFrame/None: داده‌های بارگذاری شده
        """
        with self.lock:
            try:
                debug_log(f"📂 در حال بارگذاری فایل اکسل: {file_path}", "INFO")
                
                if not os.path.exists(file_path):
                    debug_log(f"❌ فایل {file_path} وجود ندارد", "ERROR")
                    return None
                
                df = pd.read_excel(file_path)
                
                if df.empty:
                    debug_log("⚠️ فایل خالی است", "WARNING")
                    return None
                
                # ذخیره در حافظه بر اساس نوع
                if file_type == 'market':
                    self.market_data = df
                    self.data_sources['market'] = {
                        'type': 'excel',
                        'file': file_path,
                        'rows': len(df),
                        'timestamp': datetime.now().isoformat()
                    }
                    self._save_to_cache('market_data', df)
                    
                elif file_type == 'portfolio':
                    self.portfolio_data = df
                    self.data_sources['portfolio'] = {
                        'type': 'excel',
                        'file': file_path,
                        'rows': len(df),
                        'timestamp': datetime.now().isoformat()
                    }
                    self._save_portfolio(df)
                
                self.last_update = datetime.now()
                debug_log(f"✅ {len(df)} ردیف از فایل اکسل {file_type} بارگذاری شد", "INFO")
                
                return df
                
            except Exception as e:
                debug_log(f"❌ خطا در بارگذاری فایل اکسل: {e}", "ERROR")
                return None
    
    def _save_to_cache(self, name, data):
        """ذخیره داده در کش"""
        try:
            cache_file = os.path.join(self.cache_dir, f"last_{name}.pkl")
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            debug_log(f"⚠️ خطا در ذخیره کش: {e}", "WARNING")
    
    def _save_portfolio(self, df):
        """ذخیره پورتفو در فایل JSON"""
        try:
            portfolio_file = os.path.join(self.portfolio_dir, 'portfolio.json')
            if isinstance(df, pd.DataFrame):
                records = df.to_dict('records')
                with open(portfolio_file, 'w', encoding='utf-8') as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            debug_log(f"⚠️ خطا در ذخیره پورتفو: {e}", "WARNING")
    
    def load_api_data(self, data_type='prices', use_cache=True):
        """
        بارگذاری داده از API
        Args:
            data_type (str): نوع داده (prices, symbols)
            use_cache (bool): استفاده از کش
        Returns:
            DataFrame: داده‌های دریافتی
        """
        if not self.api_connector or not self.api_connector.is_authenticated:
            if not self.init_api_connection():
                debug_log("⚠️ اتصال به API برقرار نیست", "WARNING")
                return None
        
        try:
            if data_type == 'prices':
                # دریافت داده‌های قیمت
                df = self.api_connector.get_all_symbols(symbol_type=1, use_cache=use_cache)
                
                if df is not None and not df.empty:
                    self.market_data = df
                    self.api_data['prices'] = df
                    self.data_sources['market'] = {
                        'type': 'api',
                        'rows': len(df),
                        'timestamp': datetime.now().isoformat()
                    }
                    debug_log(f"✅ {len(df)} نماد از API دریافت شد", "API")
                    
                    # به‌روزرسانی وضعیت
                    self._update_api_status(success=True)
                    return df
                else:
                    debug_log("⚠️ داده‌ای از API دریافت نشد", "WARNING")
                    self._update_api_status(success=False)
                    
            elif data_type == 'symbols':
                df = self.api_connector.get_all_symbols(use_cache=use_cache)
                if df is not None and not df.empty:
                    self.symbols_data = df
                    self.api_data['symbols'] = df
                    return df
                    
        except Exception as e:
            debug_log(f"❌ خطا در دریافت داده از API: {e}", "ERROR")
            self._update_api_status(success=False, error=str(e))
        
        return None
    
    def _update_api_status(self, success=True, error=None):
        """به‌روزرسانی وضعیت API در تنظیمات"""
        try:
            api_settings = self.settings.get_api_settings()
            api_settings['last_sync'] = datetime.now().isoformat()
            api_settings['sync_status'] = 'success' if success else 'failed'
            
            if error:
                api_settings['last_error'] = error
                api_settings['error_count'] = api_settings.get('error_count', 0) + 1
            else:
                api_settings['success_count'] = api_settings.get('success_count', 0) + 1
            
            self.settings.update_api_settings(api_settings)
            
        except Exception as e:
            debug_log(f"⚠️ خطا در به‌روزرسانی وضعیت API: {e}", "WARNING")
    
    def refresh_api_data(self):
        """به‌روزرسانی دستی داده‌های API"""
        debug_log("🔄 شروع به‌روزرسانی دستی API", "API")
        
        result = self.load_api_data('prices', use_cache=False)
        
        if result is not None and not result.empty:
            debug_log("✅ به‌روزرسانی API با موفقیت انجام شد", "API")
            return True
        else:
            debug_log("❌ به‌روزرسانی API ناموفق بود", "API")
            return False
    
    # ========================================================================
    # ✅ متدهای اصلی برای دریافت داده (مهمترین بخش)
    # ========================================================================
    
    def get_market_data(self, source='auto', force_refresh=False):
        """
        دریافت داده‌های بازار از منبع مشخص
        Args:
            source (str): منبع (auto, api, excel, cache)
            force_refresh (bool): اجبار به به‌روزرسانی
        Returns:
            DataFrame: داده‌های بازار
        """
        with self.lock:
            debug_log(f"📊 درخواست داده با منبع: {source}", "INFO")
            
            # اگر اجبار به به‌روزرسانی است
            if force_refresh:
                if source == 'api' or (source == 'auto' and self.settings.is_api_enabled()):
                    return self.load_api_data('prices', use_cache=False)
            
            # انتخاب منبع
            if source == 'api':
                if self.api_data and 'prices' in self.api_data and not self.api_data['prices'].empty:
                    debug_log(f"📊 استفاده از داده‌های API در حافظه: {len(self.api_data['prices'])} نماد", "API")
                    return self.api_data['prices']
                return self.load_api_data('prices')
                
            elif source == 'excel':
                if self.market_data is not None and not self.market_data.empty:
                    debug_log(f"📊 استفاده از داده‌های اکسل: {len(self.market_data)} نماد", "INFO")
                    return self.market_data
                return None
                
            elif source == 'cache':
                cache_file = os.path.join(self.cache_dir, 'last_market_data.pkl')
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, 'rb') as f:
                            data = pickle.load(f)
                        debug_log(f"📦 استفاده از داده‌های کش: {len(data)} نماد", "INFO")
                        return data
                    except:
                        pass
                return None
                
            else:  # auto
                # اگر API فعال است و داده دارد
                if self.settings.is_api_enabled():
                    if self.api_data and 'prices' in self.api_data and not self.api_data['prices'].empty:
                        debug_log(f"📊 استفاده از داده‌های API (خودکار): {len(self.api_data['prices'])} نماد", "API")
                        return self.api_data['prices']
                    elif self.api_connector:
                        # تلاش برای دریافت از API
                        api_data = self.load_api_data('prices')
                        if api_data is not None and not api_data.empty:
                            return api_data
                
                # در غیر اینصورت از اکسل
                if self.market_data is not None and not self.market_data.empty:
                    debug_log(f"📊 استفاده از داده‌های اکسل (خودکار): {len(self.market_data)} نماد", "INFO")
                    return self.market_data
                
                debug_log("⚠️ هیچ داده‌ای موجود نیست", "WARNING")
                return None
    
    def get_portfolio_data(self):
        """دریافت داده‌های پورتفو"""
        return self.portfolio_data
    
    def get_watchlist_data(self):
        """دریافت لیست پیگیری"""
        return self.watchlist_data
    
    def get_symbols_list(self):
        """دریافت لیست نمادها"""
        if self.symbols_data is not None and not self.symbols_data.empty:
            if 'نماد' in self.symbols_data.columns:
                return self.symbols_data['نماد'].tolist()
        
        if self.market_data is not None and 'نماد' in self.market_data.columns:
            return self.market_data['نماد'].unique().tolist()
        
        return []
    
    # ========================================================================
    # توابع کمکی
    # ========================================================================
    
    def save_uploaded_file(self, uploaded_file, file_type):
        """ذخیره فایل آپلود شده"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{file_type}_{timestamp}.xlsx"
            file_path = os.path.join(self.uploads_dir, filename)
            
            uploaded_file.save(file_path)
            debug_log(f"💾 فایل آپلود شده در {file_path} ذخیره شد", "INFO")
            
            return file_path
            
        except Exception as e:
            debug_log(f"❌ خطا در ذخیره فایل: {e}", "ERROR")
            return None
    
    def get_data_summary(self):
        """دریافت خلاصه وضعیت داده‌ها"""
        summary = {
            'market_data': {
                'available': self.market_data is not None,
                'rows': len(self.market_data) if self.market_data is not None else 0,
                'source': self.data_sources.get('market', {}).get('type', 'none'),
                'timestamp': self.data_sources.get('market', {}).get('timestamp')
            },
            'portfolio_data': {
                'available': self.portfolio_data is not None,
                'rows': len(self.portfolio_data) if self.portfolio_data is not None else 0
            },
            'api': {
                'connected': self.api_connector is not None and self.api_connector.is_authenticated,
                'last_sync': self.settings.get('api.last_sync') if self.settings else None,
                'status': self.settings.get('api.sync_status') if self.settings else None
            },
            'last_update': self.last_update.isoformat() if self.last_update else None
        }
        
        return summary
    
    def get_available_data_sources(self):
        """دریافت لیست منابع داده موجود"""
        sources = []
        
        if self.market_data is not None:
            sources.append({
                'name': 'داده‌های بازار (اکسل)',
                'type': 'excel',
                'rows': len(self.market_data),
                'icon': '📊'
            })
        
        if self.portfolio_data is not None:
            sources.append({
                'name': 'پورتفوی شخصی',
                'type': 'portfolio',
                'rows': len(self.portfolio_data),
                'icon': '💰'
            })
        
        if self.api_connector and self.api_connector.is_authenticated:
            api_settings = self.settings.get_api_settings() if self.settings else {}
            status_text = '🟢 متصل' if api_settings.get('sync_status') == 'success' else '🔴 قطع'
            
            sources.append({
                'name': 'API برس‌آی‌آر',
                'type': 'api',
                'status': status_text,
                'icon': '🌐'
            })
            
            if self.api_data and 'prices' in self.api_data and not self.api_data['prices'].empty:
                sources.append({
                    'name': 'قیمت‌های لحظه‌ای',
                    'type': 'api_data',
                    'rows': len(self.api_data['prices']),
                    'icon': '📈'
                })
        
        return sources
    
    def clear_all_data(self):
        """پاک کردن تمام داده‌ها"""
        with self.lock:
            self.market_data = None
            self.portfolio_data = None
            self.watchlist_data = None
            self.symbols_data = None
            self.api_data = {}
            self.data_sources = {}
            debug_log("🧹 تمام داده‌ها پاک شدند", "INFO")
            return True
    
    def __repr__(self):
        market_count = len(self.market_data) if self.market_data is not None else 0
        api_status = "متصل" if self.api_connector and self.api_connector.is_authenticated else "قطع"
        return f"DataManager(market={market_count}, api={api_status})"
# ============================================================================
# بخش ۷: کلاس AdvancedStockAnalyzer (تحلیلگر پیشرفته سهام)
# ============================================================================

class AdvancedStockAnalyzer:
    """
    تحلیلگر پیشرفته سهام با ۷ روش تحلیلی:
    1. تحلیل پایه (۶ معیار)
    2. تحلیل حباب
    3. تحلیل ارزش ذاتی
    4. تحلیل تابلوخوانی
    5. تحلیل ریسک
    6. تحلیل عملکرد
    7. تحلیل تکنیکال
    """
    
    def __init__(self, settings=None, data_manager=None):
        """
        سازنده کلاس AdvancedStockAnalyzer
        Args:
            settings (Settings): تنظیمات برنامه
            data_manager (DataManager): مدیر داده‌ها
        """
        self.settings = settings or Settings()
        self.data_manager = data_manager
        
        # بارگذاری تنظیمات
        self.weights = self.settings.get_weights()
        self.thresholds = self.settings.settings
        
        # کش تحلیل‌ها برای بهبود عملکرد
        self.analysis_cache = {}
        self.cache_timestamps = {}
        
        # آمار تحلیلها
        self.analysis_count = 0
        self.last_analysis_time = None
        
        debug_log("✅ AdvancedStockAnalyzer با ۷ روش تحلیلی راه‌اندازی شد", "INFO")
    
    # ========================================================================
    # ۷-۱: توابع کمکی محاسباتی
    # ========================================================================
    
    def safe_float(self, value, default=0.0):
        """تبدیل ایمن به float"""
        try:
            if pd.isna(value) or value is None:
                return default
            return float(value)
        except:
            return default
    
    def safe_int(self, value, default=0):
        """تبدیل ایمن به int"""
        try:
            if pd.isna(value) or value is None:
                return default
            return int(float(value))
        except:
            return default
    
    def normalize_score(self, value, min_val, max_val, reverse=False):
        """نرمال‌سازی امتیاز بین ۰ تا ۱۰۰"""
        if pd.isna(value) or value is None:
            return 50
        
        try:
            if max_val == min_val:
                return 50
            
            if reverse:
                # برای معیارهایی که مقدار کمتر بهتر است
                normalized = 100 * (max_val - value) / (max_val - min_val)
            else:
                normalized = 100 * (value - min_val) / (max_val - min_val)
            
            return max(0, min(100, normalized))
            
        except:
            return 50
    
    def calculate_percentile_score(self, series, value, reverse=False):
        """محاسبه امتیاز بر اساس صدک"""
        if series is None or len(series) == 0:
            return 50
        
        try:
            if reverse:
                # مقدار کمتر بهتر
                percentile = (series > value).sum() / len(series) * 100
            else:
                # مقدار بیشتر بهتر
                percentile = (series < value).sum() / len(series) * 100
            
            return percentile
            
        except:
            return 50
    
    # ========================================================================
    # ۷-۲: تحلیل پایه (۶ معیار اصلی)
    # ========================================================================
    
    def calculate_eps_score(self, eps):
        """
        محاسبه امتیاز EPS
        Args:
            eps (float): EPS سهام
        Returns:
            float: امتیاز (۰-۱۰۰)
        """
        eps = self.safe_float(eps)
        
        thresholds = self.thresholds.get('eps_thresholds', {})
        scores = thresholds.get('scores', {})
        
        if eps >= thresholds.get('excellent', 2000):
            return scores.get('excellent', 100)
        elif eps >= thresholds.get('very_good', 1000):
            return scores.get('very_good', 90)
        elif eps >= thresholds.get('good', 500):
            return scores.get('good', 80)
        elif eps >= thresholds.get('average', 200):
            return scores.get('average', 70)
        elif eps >= thresholds.get('below_average', 100):
            return scores.get('below_average', 60)
        elif eps >= thresholds.get('low', 50):
            return scores.get('low', 50)
        elif eps > 0:
            return scores.get('positive', 40)
        else:
            return scores.get('default', 30)
    
    def calculate_pb_score(self, pb):
        """
        محاسبه امتیاز P/B
        Args:
            pb (float): نسبت P/B
        Returns:
            float: امتیاز (۰-۱۰۰)
        """
        pb = self.safe_float(pb)
        
        if pb <= 0:
            return 0
        
        thresholds = self.thresholds.get('pb_thresholds', {})
        scores = thresholds.get('scores', {})
        
        if pb <= thresholds.get('excellent', 0.8):
            return scores.get('excellent', 100)
        elif pb <= thresholds.get('very_good', 1.2):
            return scores.get('very_good', 80)
        elif pb <= thresholds.get('good', 1.5):
            return scores.get('good', 60)
        elif pb <= thresholds.get('average', 2.0):
            return scores.get('average', 40)
        else:
            return scores.get('poor', 20)
    
    def calculate_eps_growth_score(self, eps_growth):
        """
        محاسبه امتیاز رشد EPS
        Args:
            eps_growth (float): درصد رشد EPS
        Returns:
            float: امتیاز (۰-۱۰۰)
        """
        eps_growth = self.safe_float(eps_growth)
        
        thresholds = self.thresholds.get('eps_growth_thresholds', {})
        scores = thresholds.get('scores', {})
        
        if eps_growth >= thresholds.get('excellent', 50):
            return scores.get('excellent', 100)
        elif eps_growth >= thresholds.get('very_good', 30):
            return scores.get('very_good', 80)
        elif eps_growth >= thresholds.get('good', 10):
            return scores.get('good', 60)
        elif eps_growth >= thresholds.get('average', 0):
            return scores.get('average', 40)
        elif eps_growth >= thresholds.get('poor', -10):
            return scores.get('poor', 20)
        else:
            return scores.get('very_poor', 0)
    
    def calculate_pe_score(self, pe):
        """
        محاسبه امتیاز P/E
        Args:
            pe (float): نسبت P/E
        Returns:
            float: امتیاز (۰-۱۰۰)
        """
        pe = self.safe_float(pe)
        
        if pe <= 0:
            return 0
        
        thresholds = self.thresholds.get('pe_thresholds', {})
        scores = thresholds.get('scores', {})
        
        if pe <= thresholds.get('excellent', 8):
            return scores.get('excellent', 100)
        elif pe <= thresholds.get('very_good', 12):
            return scores.get('very_good', 80)
        elif pe <= thresholds.get('good', 20):
            return scores.get('good', 60)
        else:
            return scores.get('poor', 30)
    
    def calculate_rsi_score(self, rsi):
        """
        محاسبه امتیاز RSI
        Args:
            rsi (float): شاخص RSI
        Returns:
            float: امتیاز (۰-۱۰۰)
        """
        rsi = self.safe_float(rsi)
        
        if pd.isna(rsi) or rsi == 0:
            return 50
        
        thresholds = self.thresholds.get('rsi_thresholds', {})
        scores = thresholds.get('scores', {})
        
        if rsi <= thresholds.get('oversold_extreme', 20):
            return scores.get('oversold_extreme', 100)
        elif rsi <= thresholds.get('oversold', 30):
            return scores.get('oversold', 80)
        elif rsi >= thresholds.get('overbought_extreme', 85):
            return scores.get('overbought_extreme', 10)
        elif rsi >= thresholds.get('overbought', 70):
            return scores.get('overbought', 20)
        elif rsi <= thresholds.get('neutral_low', 40):
            return scores.get('neutral_low', 60)
        else:
            return scores.get('neutral_high', 40)
    
    def calculate_volume_score(self, volume):
        """
        محاسبه امتیاز حجم معاملات
        Args:
            volume (float): حجم معاملات
        Returns:
            float: امتیاز (۰-۱۰۰)
        """
        volume = self.safe_float(volume)
        
        thresholds = self.thresholds.get('volume_thresholds', {})
        scores = thresholds.get('scores', {})
        
        if volume >= thresholds.get('excellent', 10000000):
            return scores.get('excellent', 100)
        elif volume >= thresholds.get('very_good', 5000000):
            return scores.get('very_good', 80)
        elif volume >= thresholds.get('good', 1000000):
            return scores.get('good', 60)
        elif volume >= thresholds.get('average', 500000):
            return scores.get('average', 40)
        else:
            return scores.get('low', 20)
    
    def calculate_base_score(self, row):
        """
        محاسبه امتیاز پایه ترکیبی
        Args:
            row (Series): ردیف داده سهام
        Returns:
            dict: امتیازات و جزئیات
        """
        scores = {}
        details = {}
        
        # استخراج مقادیر
        eps = row.get('EPS', row.get('eps', 0))
        pb = row.get('P/B', row.get('pb', row.get('P_B', 0)))
        eps_growth = row.get('رشد EPS', row.get('eps_growth', 0))
        pe = row.get('P/E', row.get('pe', row.get('P_E', 0)))
        rsi = row.get('RSI', row.get('rsi', 50))
        volume = row.get('حجم', row.get('volume', 0))
        
        # محاسبه امتیاز هر معیار
        scores['eps'] = self.calculate_eps_score(eps)
        scores['pb'] = self.calculate_pb_score(pb)
        scores['eps_growth'] = self.calculate_eps_growth_score(eps_growth)
        scores['pe'] = self.calculate_pe_score(pe)
        scores['rsi'] = self.calculate_rsi_score(rsi)
        scores['volume'] = self.calculate_volume_score(volume)
        
        # ذخیره جزئیات
        details['EPS'] = eps
        details['P/B'] = pb
        details['رشد EPS'] = eps_growth
        details['P/E'] = pe
        details['RSI'] = rsi
        details['حجم'] = volume
        
        # محاسبه امتیاز نهایی با وزن‌ها
        final_score = (
            scores['eps'] * self.weights.get('eps_weight', 0.40) +
            scores['pb'] * self.weights.get('pb_weight', 0.25) +
            scores['eps_growth'] * self.weights.get('eps_growth_weight', 0.15) +
            scores['pe'] * self.weights.get('pe_weight', 0.10) +
            scores['rsi'] * self.weights.get('rsi_weight', 0.05) +
            scores['volume'] * self.weights.get('volume_weight', 0.05)
        )
        
        return {
            'امتیاز پایه': final_score,
            'جزئیات پایه': details,
            'امتیازات جزئی': scores
        }
    
    # ========================================================================
    # ۷-۳: تحلیل حباب (Bubble Analysis)
    # ========================================================================
    
    def calculate_bubble_score(self, row):
        """
        محاسبه امتیاز حباب (هرچه بیشتر = حباب بیشتر)
        Args:
            row (Series): ردیف داده سهام
        Returns:
            dict: امتیاز حباب و جزئیات
        """
        bubble_config = self.thresholds.get('bubble', {})
        weights = bubble_config.get('weights', {})
        
        # استخراج مقادیر
        pe = self.safe_float(row.get('P/E', 0))
        pb = self.safe_float(row.get('P/B', 0))
        growth = self.safe_float(row.get('رشد', row.get('growth', 0)))
        volume_ratio = self.safe_float(row.get('نسبت حجم', row.get('volume_ratio', 1)))
        
        # محاسبه امتیاز هر بخش
        scores = {}
        
        # امتیاز P/E
        if pe <= bubble_config.get('pe_low', 8):
            scores['pe'] = 20
        elif pe <= bubble_config.get('pe_medium', 12):
            scores['pe'] = 40
        elif pe <= bubble_config.get('pe_medium_high', 18):
            scores['pe'] = 60
        elif pe <= bubble_config.get('pe_high', 25):
            scores['pe'] = 80
        else:
            scores['pe'] = 100
        
        # امتیاز P/B
        if pb <= bubble_config.get('pb_low', 1):
            scores['pb'] = 20
        elif pb <= bubble_config.get('pb_medium', 2):
            scores['pb'] = 40
        elif pb <= bubble_config.get('pb_high', 3):
            scores['pb'] = 60
        elif pb <= bubble_config.get('pb_very_high', 5):
            scores['pb'] = 80
        else:
            scores['pb'] = 100
        
        # امتیاز رشد
        if growth >= bubble_config.get('return_1m_very_high', 30):
            scores['growth'] = 100
        elif growth >= bubble_config.get('return_1m_high', 20):
            scores['growth'] = 80
        elif growth >= bubble_config.get('return_1m_medium', 10):
            scores['growth'] = 60
        else:
            scores['growth'] = 40
        
        # امتیاز حجم
        if volume_ratio >= bubble_config.get('volume_ratio_very_high', 3):
            scores['volume'] = 100
        elif volume_ratio >= bubble_config.get('volume_ratio_high', 2):
            scores['volume'] = 80
        elif volume_ratio >= bubble_config.get('volume_ratio_medium', 1.5):
            scores['volume'] = 60
        else:
            scores['volume'] = 40
        
        # امتیاز نهایی حباب
        final_score = (
            scores['pe'] * weights.get('pe', 0.3) +
            scores['pb'] * weights.get('pb', 0.3) +
            scores['growth'] * weights.get('growth', 0.25) +
            scores['volume'] * weights.get('volume', 0.15)
        )
        
        # تشخیص سطح حباب
        bubble_scores = bubble_config.get('scores', {})
        if final_score >= 80:
            level = 'very_high_bubble'
            description = 'حباب بسیار شدید'
        elif final_score >= 60:
            level = 'high_bubble'
            description = 'حباب شدید'
        elif final_score >= 40:
            level = 'medium_bubble'
            description = 'حباب متوسط'
        elif final_score >= 20:
            level = 'low_bubble'
            description = 'حباب کم'
        else:
            level = 'no_bubble'
            description = 'بدون حباب'
        
        return {
            'امتیاز حباب': final_score,
            'سطح حباب': description,
            'امتیاز': bubble_scores.get(level, 50),
            'جزئیات': {
                'P/E': pe,
                'P/B': pb,
                'رشد': growth,
                'نسبت حجم': volume_ratio
            },
            'امتیازات جزئی': scores
        }
    
    # ========================================================================
    # ۷-۴: تحلیل ارزش ذاتی (Intrinsic Value)
    # ========================================================================
    
    def calculate_intrinsic_value(self, row):
        """
        محاسبه ارزش ذاتی سهام با چند روش
        Args:
            row (Series): ردیف داده سهام
        Returns:
            dict: ارزش ذاتی و نسبت‌ها
        """
        iv_config = self.thresholds.get('intrinsic_value', {})
        
        # استخراج مقادیر
        price = self.safe_float(row.get('قیمت', row.get('price', 0)))
        eps = self.safe_float(row.get('EPS', row.get('eps', 0)))
        bv = self.safe_float(row.get('ارزش دفتری', row.get('book_value', 0)))
        growth = self.safe_float(row.get('رشد', row.get('growth', 0))) / 100
        
        if price <= 0 or eps <= 0:
            return {
                'ارزش ذاتی': 0,
                'نسبت قیمت به ارزش': 0,
                'توصیه': 'نامشخص',
                'امتیاز': 50,
                'روش‌ها': {}
            }
        
        methods = {}
        
        # روش ۱: ارزش ذاتی بر اساس P/E معقول
        fair_pe = iv_config.get('pe_multiplier', 8)
        iv_pe = eps * fair_pe
        methods['P/E'] = {
            'ارزش': iv_pe,
            'نسبت': price / iv_pe if iv_pe > 0 else 0
        }
        
        # روش ۲: ارزش ذاتی بر اساس P/B معقول
        fair_pb = iv_config.get('pb_multiplier', 1.5)
        iv_pb = bv * fair_pb
        methods['P/B'] = {
            'ارزش': iv_pb,
            'نسبت': price / iv_pb if iv_pb > 0 else 0
        }
        
        # روش ۳: فرمول گراهام
        graham_base = iv_config.get('graham_base', 8.5)
        graham_growth = iv_config.get('graham_growth', 2)
        iv_graham = eps * (graham_base + graham_growth * growth * 100)
        methods['گراهام'] = {
            'ارزش': iv_graham,
            'نسبت': price / iv_graham if iv_graham > 0 else 0
        }
        
        # روش ۴: DDM (Dividend Discount Model)
        dividend = eps * iv_config.get('dividend_payout', 0.3)
        discount_rate = iv_config.get('discount_rate', 0.15)
        growth_rate = iv_config.get('growth_rate', 0.10)
        
        if discount_rate > growth_rate:
            iv_ddm = dividend / (discount_rate - growth_rate)
        else:
            iv_ddm = dividend / discount_rate
        
        methods['DDM'] = {
            'ارزش': iv_ddm,
            'نسبت': price / iv_ddm if iv_ddm > 0 else 0
        }
        
        # میانگین ارزش ذاتی
        valid_values = [v['ارزش'] for v in methods.values() if v['ارزش'] > 0]
        if valid_values:
            avg_iv = sum(valid_values) / len(valid_values)
        else:
            avg_iv = 0
        
        # نسبت قیمت به ارزش
        price_to_value = price / avg_iv if avg_iv > 0 else 0
        
        # تشخیص سطح
        thresholds = iv_config.get('thresholds', {})
        scores = iv_config.get('scores', {})
        
        if price_to_value <= thresholds.get('strong_buy', 0.5):
            level = 'strong_buy'
            recommendation = 'خرید قوی'
        elif price_to_value <= thresholds.get('buy', 0.7):
            level = 'buy'
            recommendation = 'خرید'
        elif price_to_value <= thresholds.get('cautious_buy', 0.9):
            level = 'cautious_buy'
            recommendation = 'خرید محتاطانه'
        elif price_to_value <= thresholds.get('hold', 1.1):
            level = 'hold'
            recommendation = 'نگهداری'
        elif price_to_value <= thresholds.get('cautious_sell', 1.3):
            level = 'cautious_sell'
            recommendation = 'فروش محتاطانه'
        elif price_to_value <= thresholds.get('sell', 1.5):
            level = 'sell'
            recommendation = 'فروش'
        else:
            level = 'strong_sell'
            recommendation = 'فروش قوی'
        
        return {
            'ارزش ذاتی': avg_iv,
            'نسبت قیمت به ارزش': price_to_value,
            'توصیه': recommendation,
            'امتیاز': scores.get(level, 50),
            'روش‌ها': methods,
            'جزئیات': {
                'قیمت': price,
                'EPS': eps,
                'ارزش دفتری': bv,
                'نرخ رشد': growth
            }
        }
    
    # ========================================================================
    # ۷-۵: تحلیل تابلوخوانی (Tape Reading)
    # ========================================================================
    
    def calculate_tape_reading_score(self, row):
        """
        تحلیل تابلوخوانی (عرضه و تقاضا)
        Args:
            row (Series): ردیف داده سهام
        Returns:
            dict: امتیاز تابلوخوانی
        """
        tape_config = self.thresholds.get('tape_reading', {})
        
        # استخراج مقادیر
        real_buy = self.safe_float(row.get('خرید حقیقی', 0))
        real_sell = self.safe_float(row.get('فروش حقیقی', 0))
        legal_buy = self.safe_float(row.get('خرید حقوقی', 0))
        legal_sell = self.safe_float(row.get('فروش حقوقی', 0))
        volume = self.safe_float(row.get('حجم', 0))
        price_change = self.safe_float(row.get('درصد تغییر', 0))
        
        # محاسبه شاخص‌ها
        real_net = real_buy - real_sell
        legal_net = legal_buy - legal_sell
        
        # نسبت تقاضا به عرضه
        if real_sell > 0:
            demand_supply = real_buy / real_sell
        else:
            demand_supply = 2 if real_buy > 0 else 1
        
        # قدرت خرید
        buy_power = real_buy + legal_buy
        
        # فشار فروش
        if (real_buy + real_sell) > 0:
            sell_pressure = real_sell / (real_buy + real_sell)
        else:
            sell_pressure = 0.5
        
        # قدرت قیمت
        price_power = price_change
        
        # میانگین حجم معاملات
        avg_trade = volume / tape_config.get('avg_trade_divisor', 50000000)
        
        # شاخص قدرت ترکیبی
        power_index = (
            (real_net / 1e9) * 2 +
            (legal_net / 1e9) * 1.5 +
            price_power * 0.5 +
            (demand_supply - 1) * 10
        )
        
        # محدود کردن
        power_index = max(-10, min(10, power_index))
        
        # تشخیص روند
        thresholds = tape_config.get('power_index_thresholds', {})
        if power_index >= thresholds.get('very_bullish', 5):
            trend = 'very_bullish'
            trend_desc = 'بسیار صعودی'
        elif power_index >= thresholds.get('bullish', 2):
            trend = 'bullish'
            trend_desc = 'صعودی'
        elif power_index <= thresholds.get('very_bearish', -5):
            trend = 'very_bearish'
            trend_desc = 'بسیار نزولی'
        elif power_index <= thresholds.get('bearish', -2):
            trend = 'bearish'
            trend_desc = 'نزولی'
        else:
            trend = 'neutral'
            trend_desc = 'خنثی'
        
        # امتیاز نهایی
        base_score = tape_config.get('base_score', 50)
        multiplier = tape_config.get('score_multiplier', 2.5)
        
        final_score = base_score + power_index * multiplier
        final_score = max(0, min(100, final_score))
        
        return {
            'امتیاز تابلو': final_score,
            'روند': trend_desc,
            'شاخص قدرت': power_index,
            'جزئیات': {
                'خالص حقیقی': real_net,
                'خالص حقوقی': legal_net,
                'نسبت تقاضا به عرضه': demand_supply,
                'قدرت خرید': buy_power,
                'فشار فروش': sell_pressure,
                'قدرت قیمت': price_power,
                'میانگین معاملات': avg_trade
            }
        }
    
    # ========================================================================
    # ۷-۶: تحلیل ریسک (Risk Analysis)
    # ========================================================================
    
    def calculate_risk_score(self, row):
        """
        تحلیل ریسک سهام
        Args:
            row (Series): ردیف داده سهام
        Returns:
            dict: امتیاز ریسک (هرچه کمتر = ریسک کمتر)
        """
        risk_config = self.thresholds.get('risk', {})
        weights = risk_config.get('weights', {})
        
        # استخراج مقادیر
        beta = self.safe_float(row.get('بتا', row.get('beta', 1)))
        volume = self.safe_float(row.get('حجم', 0))
        volatility = self.safe_float(row.get('نوسان', row.get('volatility', 30)))
        rsi = self.safe_float(row.get('RSI', 50))
        pb = self.safe_float(row.get('P/B', 1))
        eps = self.safe_float(row.get('EPS', 0))
        
        scores = {}
        
        # امتیاز بتا (ریسک سیستماتیک)
        beta_thresholds = risk_config.get('beta_thresholds', {})
        if beta <= beta_thresholds.get('low', 0.5):
            scores['beta'] = 20
        elif beta <= beta_thresholds.get('medium', 0.8):
            scores['beta'] = 40
        elif beta <= beta_thresholds.get('high', 1.2):
            scores['beta'] = 60
        elif beta <= beta_thresholds.get('very_high', 1.5):
            scores['beta'] = 80
        else:
            scores['beta'] = 100
        
        # امتیاز نقدشوندگی (حجم)
        volume_thresholds = risk_config.get('volume_thresholds', {})
        liquidity_scores = risk_config.get('liquidity_scores', {})
        
        if volume >= volume_thresholds.get('very_high', 10000000):
            scores['liquidity'] = liquidity_scores.get('very_high', 20)
        elif volume >= volume_thresholds.get('high', 5000000):
            scores['liquidity'] = liquidity_scores.get('high', 40)
        elif volume >= volume_thresholds.get('medium', 1000000):
            scores['liquidity'] = liquidity_scores.get('medium', 60)
        elif volume >= volume_thresholds.get('low', 500000):
            scores['liquidity'] = liquidity_scores.get('low', 80)
        else:
            scores['liquidity'] = liquidity_scores.get('very_low', 100)
        
        # امتیاز نوسان
        vol_thresholds = risk_config.get('volatility_thresholds', {})
        if volatility <= vol_thresholds.get('medium', 20):
            scores['volatility'] = 20
        elif volatility <= vol_thresholds.get('high', 50):
            scores['volatility'] = 50
        else:
            scores['volatility'] = 80
        
        # امتیاز RSI (اشباع خرید ریسک است)
        if rsi >= 70:
            scores['rsi'] = 80
        elif rsi >= 60:
            scores['rsi'] = 60
        elif rsi >= 40:
            scores['rsi'] = 40
        else:
            scores['rsi'] = 20
        
        # امتیاز P/B (P/B بالا ریسک است)
        if pb <= 1:
            scores['pb'] = 20
        elif pb <= 2:
            scores['pb'] = 40
        elif pb <= 3:
            scores['pb'] = 60
        elif pb <= 4:
            scores['pb'] = 80
        else:
            scores['pb'] = 100
        
        # امتیاز EPS (EPS منفی ریسک است)
        if eps <= 0:
            scores['eps'] = 100
        elif eps < 100:
            scores['eps'] = 60
        else:
            scores['eps'] = 30
        
        # امتیاز نهایی ریسک (وزن‌دار)
        final_score = (
            scores['beta'] * weights.get('beta', 0.2) +
            scores['liquidity'] * weights.get('liquidity', 0.2) +
            scores['volatility'] * weights.get('volatility', 0.15) +
            scores['rsi'] * weights.get('rsi', 0.15) +
            scores['pb'] * weights.get('pb', 0.15) +
            scores['eps'] * weights.get('eps', 0.15)
        )
        
        # سطح ریسک
        if final_score <= 30:
            level = 'کم'
            level_desc = 'ریسک پایین'
        elif final_score <= 50:
            level = 'متوسط'
            level_desc = 'ریسک متوسط'
        elif final_score <= 70:
            level = 'زیاد'
            level_desc = 'ریسک بالا'
        else:
            level = 'خیلی زیاد'
            level_desc = 'ریسک خیلی بالا'
        
        return {
            'امتیاز ریسک': final_score,
            'سطح ریسک': level_desc,
            'جزئیات': {
                'بتا': beta,
                'نقدشوندگی': volume,
                'نوسان': volatility,
                'RSI': rsi,
                'P/B': pb,
                'EPS': eps
            },
            'امتیازات جزئی': scores
        }
    
    # ========================================================================
    # ۷-۷: تحلیل عملکرد (Performance Analysis)
    # ========================================================================
    
    def calculate_performance_score(self, row):
        """
        تحلیل عملکرد سهام
        Args:
            row (Series): ردیف داده سهام
        Returns:
            dict: امتیاز عملکرد
        """
        perf_config = self.thresholds.get('performance', {})
        weights = perf_config.get('cagr_weights', {})
        
        # استخراج مقادیر بازده
        return_1m = self.safe_float(row.get('بازده ۱ ماهه', row.get('return_1m', 0)))
        return_3m = self.safe_float(row.get('بازده ۳ ماهه', row.get('return_3m', 0)))
        return_6m = self.safe_float(row.get('بازده ۶ ماهه', row.get('return_6m', 0)))
        return_1y = self.safe_float(row.get('بازده ۱ ساله', row.get('return_1y', 0)))
        
        # محاسبه نرخ رشد مرکب سالانه (CAGR)
        cagr_scores = {}
        
        # بازده یک ماهه
        if return_1m >= 20:
            cagr_scores['1m'] = 100
        elif return_1m >= 10:
            cagr_scores['1m'] = 80
        elif return_1m >= 5:
            cagr_scores['1m'] = 60
        elif return_1m >= 0:
            cagr_scores['1m'] = 40
        else:
            cagr_scores['1m'] = 20
        
        # بازده سه ماهه
        if return_3m >= 30:
            cagr_scores['3m'] = 100
        elif return_3m >= 20:
            cagr_scores['3m'] = 80
        elif return_3m >= 10:
            cagr_scores['3m'] = 60
        elif return_3m >= 0:
            cagr_scores['3m'] = 40
        else:
            cagr_scores['3m'] = 20
        
        # بازده شش ماهه
        if return_6m >= 50:
            cagr_scores['6m'] = 100
        elif return_6m >= 30:
            cagr_scores['6m'] = 80
        elif return_6m >= 15:
            cagr_scores['6m'] = 60
        elif return_6m >= 0:
            cagr_scores['6m'] = 40
        else:
            cagr_scores['6m'] = 20
        
        # بازده یک ساله
        if return_1y >= 80:
            cagr_scores['1y'] = 100
        elif return_1y >= 50:
            cagr_scores['1y'] = 80
        elif return_1y >= 25:
            cagr_scores['1y'] = 60
        elif return_1y >= 0:
            cagr_scores['1y'] = 40
        else:
            cagr_scores['1y'] = 20
        
        # محاسبه ثبات (انحراف معیار بازده‌ها)
        returns = [return_1m, return_3m, return_6m, return_1y]
        valid_returns = [r for r in returns if not pd.isna(r)]
        
        if len(valid_returns) > 1:
            consistency = 100 - np.std(valid_returns) * 2
            consistency = max(0, min(100, consistency))
        else:
            consistency = 50
        
        cagr_scores['consistency'] = consistency
        
        # امتیاز نهایی عملکرد
        final_score = (
            cagr_scores['1m'] * weights.get('1m', 0.1) +
            cagr_scores['3m'] * weights.get('3m', 0.2) +
            cagr_scores['6m'] * weights.get('6m', 0.3) +
            cagr_scores['1y'] * weights.get('1y', 0.3) +
            cagr_scores['consistency'] * weights.get('consistency', 0.1)
        )
        
        # سطح عملکرد
        if final_score >= 80:
            level = 'عالی'
        elif final_score >= 60:
            level = 'خوب'
        elif final_score >= 40:
            level = 'متوسط'
        else:
            level = 'ضعیف'
        
        return {
            'امتیاز عملکرد': final_score,
            'سطح عملکرد': level,
            'جزئیات': {
                'بازده ۱ ماهه': return_1m,
                'بازده ۳ ماهه': return_3m,
                'بازده ۶ ماهه': return_6m,
                'بازده ۱ ساله': return_1y,
                'ثبات': consistency
            },
            'امتیازات جزئی': cagr_scores
        }
    
    # ========================================================================
    # ۷-۸: تحلیل تکنیکال پیشرفته
    # ========================================================================
    
    def calculate_technical_score(self, row):
        """
        تحلیل تکنیکال پیشرفته
        Args:
            row (Series): ردیف داده سهام
        Returns:
            dict: امتیاز تکنیکال
        """
        tech_config = self.thresholds.get('technical', {})
        
        # استخراج مقادیر
        price = self.safe_float(row.get('قیمت', 0))
        rsi = self.safe_float(row.get('RSI', 50))
        mfi = self.safe_float(row.get('MFI', row.get('mfi', 50)))
        stoch_k = self.safe_float(row.get('Stoch_K', row.get('stoch_k', 50)))
        stoch_d = self.safe_float(row.get('Stoch_D', row.get('stoch_d', 50)))
        
        # اندیکاتورهای میانگین متحرک
        sma_5 = self.safe_float(row.get('SMA_5', 0))
        sma_10 = self.safe_float(row.get('SMA_10', 0))
        sma_20 = self.safe_float(row.get('SMA_20', 0))
        sma_50 = self.safe_float(row.get('SMA_50', 0))
        sma_200 = self.safe_float(row.get('SMA_200', 0))
        
        scores = {}
        
        # امتیاز RSI
        rsi_thresholds = tech_config.get('rsi_thresholds', {})
        if rsi <= rsi_thresholds.get('oversold_extreme', 20):
            scores['rsi'] = tech_config.get('scores', {}).get('strong_buy', 2)
        elif rsi <= rsi_thresholds.get('oversold', 30):
            scores['rsi'] = tech_config.get('scores', {}).get('buy', 1)
        elif rsi >= rsi_thresholds.get('overbought_extreme', 85):
            scores['rsi'] = tech_config.get('scores', {}).get('strong_sell', -2)
        elif rsi >= rsi_thresholds.get('overbought', 70):
            scores['rsi'] = tech_config.get('scores', {}).get('sell', -1)
        else:
            scores['rsi'] = tech_config.get('scores', {}).get('neutral', 0)
        
        # امتیاز MFI
        mfi_thresholds = tech_config.get('mfi_thresholds', {})
        if mfi <= mfi_thresholds.get('oversold_extreme', 20):
            scores['mfi'] = 2
        elif mfi <= mfi_thresholds.get('oversold', 30):
            scores['mfi'] = 1
        elif mfi >= mfi_thresholds.get('overbought_extreme', 90):
            scores['mfi'] = -2
        elif mfi >= mfi_thresholds.get('overbought', 80):
            scores['mfi'] = -1
        else:
            scores['mfi'] = 0
        
        # امتیاز میانگین متحرک
        ma_score = 0
        if sma_5 > 0 and sma_20 > 0:
            if price > sma_5 > sma_20:
                ma_score += tech_config.get('ma_scores', {}).get('very_bullish', 3)
            elif price > sma_5:
                ma_score += tech_config.get('ma_scores', {}).get('bullish', 2)
            elif price < sma_5 < sma_20:
                ma_score += tech_config.get('ma_scores', {}).get('very_bearish', -3)
            elif price < sma_5:
                ma_score += tech_config.get('ma_scores', {}).get('bearish', -2)
        
        scores['ma'] = ma_score
        
        # امتیاز موقعیت نسبت به میانگین‌ها
        position_score = 0
        if sma_50 > 0:
            if price > sma_50 * 1.2:
                position_score += tech_config.get('position_scores', {}).get('excellent', 2)
            elif price > sma_50:
                position_score += tech_config.get('position_scores', {}).get('good', 1)
            elif price < sma_50 * 0.8:
                position_score += tech_config.get('position_scores', {}).get('poor', -1)
            elif price < sma_50:
                position_score += tech_config.get('position_scores', {}).get('neutral', 0)
        
        scores['position'] = position_score
        
        # امتیاز استوکاستیک
        if stoch_k > 80 and stoch_d > 80:
            scores['stoch'] = -1
        elif stoch_k < 20 and stoch_d < 20:
            scores['stoch'] = 1
        else:
            scores['stoch'] = 0
        
        # جمع امتیازات تکنیکال
        total_score = sum(scores.values())
        
        # تبدیل به مقیاس ۰-۱۰۰
        base_score = tech_config.get('base_score', 50)
        multiplier = tech_config.get('score_multiplier', 5)
        final_score = base_score + total_score * multiplier
        final_score = max(0, min(100, final_score))
        
        # تشخیص سیگنال
        if total_score >= 4:
            signal = 'خرید قوی'
        elif total_score >= 2:
            signal = 'خرید'
        elif total_score <= -4:
            signal = 'فروش قوی'
        elif total_score <= -2:
            signal = 'فروش'
        else:
            signal = 'خنثی'
        
        return {
            'امتیاز تکنیکال': final_score,
            'سیگنال': signal,
            'امتیاز خالص': total_score,
            'جزئیات': {
                'RSI': rsi,
                'MFI': mfi,
                'SMA وضعیت': ma_score,
                'موقعیت': position_score,
                'استوکاستیک': stoch_k
            },
            'امتیازات جزئی': scores
        }
    
    # ========================================================================
    # ۷-۹: تحلیل کامل ترکیبی
    # ========================================================================
    
    def full_analysis(self, market_data, portfolio_data=None):
        """
        تحلیل کامل سهام با تمام ۷ روش
        Args:
            market_data (DataFrame): داده‌های بازار
            portfolio_data (DataFrame): داده‌های پورتفو
        Returns:
            DataFrame: نتایج تحلیل کامل
        """
        if market_data is None or market_data.empty:
            debug_log("⚠️ داده‌ای برای تحلیل وجود ندارد", "WARNING")
            return pd.DataFrame()
        
        start_time = time.time()
        results = []
        
        # ایجاد دیکشنری پورتفو برای دسترسی سریع
        portfolio_dict = {}
        if portfolio_data is not None and not portfolio_data.empty:
            for _, row in portfolio_data.iterrows():
                symbol = row.get('نماد', '')
                if symbol:
                    portfolio_dict[symbol] = {
                        'تعداد': row.get('تعداد', 0),
                        'قیمت خرید': row.get('قیمت خرید', 0),
                        'ارزش خرید': row.get('ارزش خرید', 0)
                    }
        
        # تحلیل هر سهام
        total_rows = len(market_data)
        for idx, row in market_data.iterrows():
            try:
                symbol = row.get('نماد', f"نماد_{idx}")
                
                # تحلیل پایه
                base_result = self.calculate_base_score(row)
                
                # تحلیل حباب
                bubble_result = self.calculate_bubble_score(row)
                
                # تحلیل ارزش ذاتی
                iv_result = self.calculate_intrinsic_value(row)
                
                # تحلیل تابلوخوانی
                tape_result = self.calculate_tape_reading_score(row)
                
                # تحلیل ریسک
                risk_result = self.calculate_risk_score(row)
                
                # تحلیل عملکرد
                perf_result = self.calculate_performance_score(row)
                
                # تحلیل تکنیکال
                tech_result = self.calculate_technical_score(row)
                
                # امتیاز نهایی ترکیبی (میانگین وزنی)
                final_score = (
                    base_result['امتیاز پایه'] * 0.25 +
                    (100 - bubble_result['امتیاز حباب']) * 0.10 +
                    iv_result['امتیاز'] * 0.15 +
                    tape_result['امتیاز تابلو'] * 0.10 +
                    (100 - risk_result['امتیاز ریسک']) * 0.15 +
                    perf_result['امتیاز عملکرد'] * 0.10 +
                    tech_result['امتیاز تکنیکال'] * 0.15
                )
                
                # تعیین وضعیت نهایی
                status_thresholds = self.thresholds.get('status_thresholds', {})
                if final_score >= status_thresholds.get('excellent', 85):
                    status = '🟢 عالی'
                elif final_score >= status_thresholds.get('very_good', 75):
                    status = '🔵 خیلی خوب'
                elif final_score >= status_thresholds.get('good', 65):
                    status = '🟡 خوب'
                elif final_score >= status_thresholds.get('average', 55):
                    status = '🟠 متوسط'
                elif final_score >= status_thresholds.get('acceptable', 50):
                    status = '⚪ قابل قبول'
                else:
                    status = '🔴 ضعیف'
                
                # اطلاعات پورتفو
                portfolio_info = portfolio_dict.get(symbol, {})
                
                # محاسبه سود/زیان اگر در پورتفو باشد
                profit_loss = None
                profit_percent = None
                if portfolio_info and portfolio_info.get('قیمت خرید', 0) > 0:
                    current_price = row.get('قیمت', 0)
                    buy_price = portfolio_info.get('قیمت خرید', 0)
                    if current_price > 0 and buy_price > 0:
                        profit_percent = ((current_price - buy_price) / buy_price) * 100
                        profit_loss = (current_price - buy_price) * portfolio_info.get('تعداد', 0)
                
                # جمع‌آوری نتایج
                result_row = {
                    'نماد': symbol,
                    'نام': row.get('نام', row.get('شرکت', '')),
                    'قیمت': row.get('قیمت', 0),
                    'حجم': row.get('حجم', 0),
                    'ارزش': row.get('ارزش', 0),
                    
                    # امتیازات اصلی
                    'امتیاز پایه': round(base_result['امتیاز پایه'], 1),
                    'امتیاز حباب': round(bubble_result['امتیاز حباب'], 1),
                    'امتیاز ارزش ذاتی': iv_result['امتیاز'],
                    'امتیاز تابلو': round(tape_result['امتیاز تابلو'], 1),
                    'امتیاز ریسک': round(risk_result['امتیاز ریسک'], 1),
                    'امتیاز عملکرد': round(perf_result['امتیاز عملکرد'], 1),
                    'امتیاز تکنیکال': round(tech_result['امتیاز تکنیکال'], 1),
                    
                    # امتیاز نهایی
                    'امتیاز نهایی': round(final_score, 1),
                    'وضعیت': status,
                    
                    # اطلاعات تحلیلی
                    'حباب': bubble_result.get('سطح حباب', ''),
                    'ارزش ذاتی': round(iv_result.get('ارزش ذاتی', 0), 0),
                    'نسبت P/IV': round(iv_result.get('نسبت قیمت به ارزش', 0), 2),
                    'توصیه ارزش ذاتی': iv_result.get('توصیه', ''),
                    'روند تابلو': tape_result.get('روند', ''),
                    'شاخص قدرت': round(tape_result.get('شاخص قدرت', 0), 1),
                    'سطح ریسک': risk_result.get('سطح ریسک', ''),
                    'سطح عملکرد': perf_result.get('سطح عملکرد', ''),
                    'سیگنال تکنیکال': tech_result.get('سیگنال', ''),
                    
                    # معیارهای پایه
                    'EPS': row.get('EPS', 0),
                    'P/E': row.get('P/E', 0),
                    'P/B': row.get('P/B', 0),
                    'RSI': row.get('RSI', 50),
                    
                    # اطلاعات پورتفو
                    'در پورتفو': '✅' if symbol in portfolio_dict else '❌',
                    'تعداد': portfolio_info.get('تعداد', 0),
                    'قیمت خرید': portfolio_info.get('قیمت خرید', 0),
                    'سود/زیان (تومان)': profit_loss,
                    'درصد سود/زیان': profit_percent,
                    
                    # متادیتا
                    'تاریخ تحلیل': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
                
                results.append(result_row)
                
                # گزارش پیشرفت
                if (idx + 1) % 50 == 0:
                    debug_log(f"📊 تحلیل {idx + 1}/{total_rows} سهام انجام شد", "INFO")
                    
            except Exception as e:
                debug_log(f"❌ خطا در تحلیل {row.get('نماد', 'نامشخص')}: {e}", "ERROR")
                continue
        
        # ایجاد دیتافریم نتایج
        if results:
            df_results = pd.DataFrame(results)
            
            # مرتب‌سازی بر اساس امتیاز نهایی
            df_results = df_results.sort_values('امتیاز نهایی', ascending=False)
            
            # محاسبه آمار
            elapsed_time = time.time() - start_time
            self.analysis_count += 1
            self.last_analysis_time = datetime.now()
            
            debug_log(f"✅ تحلیل کامل {len(results)} سهام در {elapsed_time:.1f} ثانیه انجام شد", "INFO")
            
            return df_results
        else:
            return pd.DataFrame()
    
    # ========================================================================
    # ۷-۱۰: تحلیل مقایسه‌ای منابع داده
    # ========================================================================
    
    def compare_data_sources(self):
        """
        مقایسه تحلیل‌های API و اکسل
        Returns:
            dict: نتایج مقایسه
        """
        if not self.data_manager:
            return {
                'available': False,
                'message': 'مدیر داده در دسترس نیست'
            }
        
        # دریافت داده از هر دو منبع
        api_data = self.data_manager.get_market_data(source='api')
        excel_data = self.data_manager.get_market_data(source='excel')
        
        if api_data is None or excel_data is None:
            return {
                'available': False,
                'message': 'هر دو منبع داده در دسترس نیستند'
            }
        
        # تحلیل هر دو مجموعه
        api_analysis = self.full_analysis(api_data)
        excel_analysis = self.full_analysis(excel_data)
        
        if api_analysis.empty or excel_analysis.empty:
            return {
                'available': False,
                'message': 'تحلیل یکی از منابع ناموفق بود'
            }
        
        # مقایسه نمادهای مشترک
        api_symbols = set(api_analysis['نماد'].unique())
        excel_symbols = set(excel_analysis['نماد'].unique())
        common_symbols = api_symbols & excel_symbols
        
        comparison = {
            'available': True,
            'api_count': len(api_analysis),
            'excel_count': len(excel_analysis),
            'common_count': len(common_symbols),
            'api_time': datetime.now().isoformat(),
            'excel_time': self.data_manager.last_update.isoformat() if self.data_manager.last_update else None,
            'correlation': 0,
            'differences': []
        }
        
        # محاسبه همبستگی برای نمادهای مشترک
        common_scores = []
        for symbol in list(common_symbols)[:50]:  # محدود به ۵۰ نماد
            api_row = api_analysis[api_analysis['نماد'] == symbol]
            excel_row = excel_analysis[excel_analysis['نماد'] == symbol]
            
            if not api_row.empty and not excel_row.empty:
                api_score = api_row.iloc[0]['امتیاز نهایی']
                excel_score = excel_row.iloc[0]['امتیاز نهایی']
                common_scores.append((api_score, excel_score))
                
                # تفاوت‌های قابل توجه
                if abs(api_score - excel_score) > 10:
                    comparison['differences'].append({
                        'نماد': symbol,
                        'امتیاز API': api_score,
                        'امتیاز اکسل': excel_score,
                        'تفاوت': api_score - excel_score
                    })
        
        # محاسبه همبستگی
        if len(common_scores) > 1:
            api_scores = [s[0] for s in common_scores]
            excel_scores = [s[1] for s in common_scores]
            
            try:
                correlation = np.corrcoef(api_scores, excel_scores)[0, 1]
                comparison['correlation'] = round(correlation, 3)
            except:
                pass
        
        return comparison
    
    # ========================================================================
    # ۷-۱۱: ذخیره و بارگذاری تحلیل‌ها
    # ========================================================================
    
    def save_analysis(self, analysis_df, filename=None):
        """
        ذخیره نتایج تحلیل در فایل
        Args:
            analysis_df (DataFrame): نتایج تحلیل
            filename (str): نام فایل
        Returns:
            str: مسیر فایل ذخیره شده
        """
        if analysis_df is None or analysis_df.empty:
            return None
        
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"analysis_{timestamp}.xlsx"
            
            file_path = os.path.join(REPORTS_DIR, filename)
            
            # ذخیره با چند شیت
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # شیت اصلی
                analysis_df.to_excel(writer, sheet_name='تحلیل کامل', index=False)
                
                # شیت خلاصه
                summary = analysis_df[['نماد', 'امتیاز نهایی', 'وضعیت', 'توصیه ارزش ذاتی']].head(20)
                summary.to_excel(writer, sheet_name='۲۰ سهام برتر', index=False)
                
                # شیت آمار
                stats = pd.DataFrame([{
                    'تعداد سهام تحلیل شده': len(analysis_df),
                    'میانگین امتیاز': analysis_df['امتیاز نهایی'].mean(),
                    'حداکثر امتیاز': analysis_df['امتیاز نهایی'].max(),
                    'حداقل امتیاز': analysis_df['امتیاز نهایی'].min(),
                    'انحراف معیار': analysis_df['امتیاز نهایی'].std(),
                    'تاریخ تحلیل': datetime.now().strftime('%Y-%m-%d %H:%M')
                }])
                stats.to_excel(writer, sheet_name='آمار', index=False)
            
            debug_log(f"💾 نتایج تحلیل در {file_path} ذخیره شد", "INFO")
            return file_path
            
        except Exception as e:
            debug_log(f"❌ خطا در ذخیره تحلیل: {e}", "ERROR")
            return None
    
    def get_analysis_summary(self, analysis_df):
        """
        دریافت خلاصه آماری تحلیل
        Args:
            analysis_df (DataFrame): نتایج تحلیل
        Returns:
            dict: خلاصه آمار
        """
        if analysis_df is None or analysis_df.empty:
            return {}
        
        summary = {
            'تعداد کل': len(analysis_df),
            'میانگین امتیاز': round(analysis_df['امتیاز نهایی'].mean(), 1),
            'میانه امتیاز': round(analysis_df['امتیاز نهایی'].median(), 1),
            'انحراف معیار': round(analysis_df['امتیاز نهایی'].std(), 1),
            'حداکثر امتیاز': round(analysis_df['امتیاز نهایی'].max(), 1),
            'حداقل امتیاز': round(analysis_df['امتیاز نهایی'].min(), 1),
        }
        
        # توزیع وضعیت‌ها
        status_counts = analysis_df['وضعیت'].value_counts().to_dict()
        summary['توزیع وضعیت'] = status_counts
        
        # بهترین و بدترین سهام
        if len(analysis_df) > 0:
            best = analysis_df.nlargest(1, 'امتیاز نهایی').iloc[0]
            worst = analysis_df.nsmallest(1, 'امتیاز نهایی').iloc[0]
            
            summary['بهترین سهام'] = {
                'نماد': best['نماد'],
                'امتیاز': best['امتیاز نهایی'],
                'وضعیت': best['وضعیت']
            }
            
            summary['بدترین سهام'] = {
                'نماد': worst['نماد'],
                'امتیاز': worst['امتیاز نهایی'],
                'وضعیت': worst['وضعیت']
            }
        
        return summary
    
    def __repr__(self):
        return f"AdvancedStockAnalyzer(analyses={self.analysis_count}, last={self.last_analysis_time})"
# ============================================================================
# بخش ۸: کلاس AdvancedPortfolioAnalyzer (تحلیلگر پیشرفته پورتفو)
# ============================================================================

class AdvancedPortfolioAnalyzer:
    """
    تحلیلگر پیشرفته پورتفوی سهام با قابلیت‌های:
    - محاسبه سود/زیان واقعی
    - تحلیل تنوع‌بخشی
    - محاسبه ریسک پورتفو
    - بهینه‌سازی وزن‌ها
    - پیشنهاد خرید/فروش
    - تحلیل همبستگی
    """
    
    def __init__(self, settings=None):
        """
        سازنده کلاس AdvancedPortfolioAnalyzer
        Args:
            settings (Settings): تنظیمات برنامه
        """
        self.settings = settings or Settings()
        self.portfolio_config = self.settings.settings.get('portfolio', {})
        
        self.analysis_cache = {}
        self.last_analysis = None
        
        debug_log("✅ AdvancedPortfolioAnalyzer راه‌اندازی شد", "INFO")
    
    # ========================================================================
    # ۸-۱: توابع کمکی محاسبات پورتفو
    # ========================================================================
    
    def calculate_position_value(self, row, current_prices=None):
        """
        محاسبه ارزش موقعیت
        Args:
            row (Series): ردیف پورتفو
            current_prices (dict): قیمت‌های فعلی
        Returns:
            dict: ارزش و سود/زیان
        """
        symbol = row.get('نماد', '')
        quantity = self.safe_float(row.get('تعداد', 0))
        buy_price = self.safe_float(row.get('قیمت خرید', 0))
        buy_value = quantity * buy_price
        
        # قیمت فعلی
        if current_prices and symbol in current_prices:
            current_price = current_prices[symbol]
        else:
            current_price = self.safe_float(row.get('قیمت فعلی', buy_price))
        
        current_value = quantity * current_price
        
        # سود/زیان
        profit_loss = current_value - buy_value
        profit_percent = (profit_loss / buy_value * 100) if buy_value > 0 else 0
        
        return {
            'ارزش خرید': buy_value,
            'ارزش فعلی': current_value,
            'سود/زیان': profit_loss,
            'درصد سود/زیان': profit_percent,
            'قیمت خرید': buy_price,
            'قیمت فعلی': current_price,
            'تعداد': quantity
        }
    
    def safe_float(self, value, default=0.0):
        """تبدیل ایمن به float"""
        try:
            if pd.isna(value) or value is None:
                return default
            return float(value)
        except:
            return default
    
    # ========================================================================
    # ۸-۲: تحلیل پورتفو
    # ========================================================================
    
    def analyze_portfolio(self, portfolio_df, market_df=None, current_prices=None):
        """
        تحلیل کامل پورتفو
        Args:
            portfolio_df (DataFrame): داده‌های پورتفو
            market_df (DataFrame): داده‌های بازار
            current_prices (dict): قیمت‌های فعلی
        Returns:
            dict: نتایج تحلیل پورتفو
        """
        if portfolio_df is None or portfolio_df.empty:
            return {
                'status': 'empty',
                'message': 'پورتفو خالی است',
                'total_value': 0,
                'total_profit': 0,
                'positions': []
            }
        
        # استخراج قیمت‌های فعلی از market_df
        if current_prices is None and market_df is not None:
            current_prices = {}
            for _, row in market_df.iterrows():
                symbol = row.get('نماد', '')
                price = row.get('قیمت', row.get('قیمت پایانی', 0))
                if symbol and price > 0:
                    current_prices[symbol] = price
        
        # تحلیل هر موقعیت
        positions = []
        total_buy_value = 0
        total_current_value = 0
        total_profit = 0
        
        for idx, row in portfolio_df.iterrows():
            try:
                position = self.calculate_position_value(row, current_prices)
                symbol = row.get('نماد', f"موقعیت_{idx}")
                
                position.update({
                    'نماد': symbol,
                    'نام': row.get('نام', row.get('شرکت', '')),
                    'صنعت': row.get('صنعت', row.get('گروه', 'نامشخص')),
                })
                
                positions.append(position)
                
                total_buy_value += position['ارزش خرید']
                total_current_value += position['ارزش فعلی']
                total_profit += position['سود/زیان']
                
            except Exception as e:
                debug_log(f"❌ خطا در تحلیل موقعیت {row.get('نماد', 'نامشخص')}: {e}", "ERROR")
        
        # محاسبه آمار کل
        total_profit_percent = (total_profit / total_buy_value * 100) if total_buy_value > 0 else 0
        
        # تحلیل تنوع‌بخشی
        diversity_analysis = self.analyze_diversity(positions)
        
        # تحلیل ریسک
        risk_analysis = self.analyze_portfolio_risk(positions, market_df)
        
        # بهترین و بدترین موقعیت
        if positions:
            sorted_positions = sorted(positions, key=lambda x: x['درصد سود/زیان'], reverse=True)
            best_position = sorted_positions[0]
            worst_position = sorted_positions[-1]
        else:
            best_position = None
            worst_position = None
        
        # محاسبه وزن‌ها
        for pos in positions:
            pos['وزن'] = (pos['ارزش فعلی'] / total_current_value * 100) if total_current_value > 0 else 0
        
        # تعیین وضعیت کلی
        status_thresholds = self.portfolio_config.get('status_thresholds', {})
        
        if total_profit_percent >= status_thresholds.get('excellent', 20):
            overall_status = '🟢 عالی'
        elif total_profit_percent >= status_thresholds.get('very_good', 15):
            overall_status = '🔵 خیلی خوب'
        elif total_profit_percent >= status_thresholds.get('good', 10):
            overall_status = '🟡 خوب'
        elif total_profit_percent >= status_thresholds.get('average', 5):
            overall_status = '⚪ متوسط'
        elif total_profit_percent >= status_thresholds.get('poor', 0):
            overall_status = '🟠 ضعیف'
        else:
            overall_status = '🔴 خیلی ضعیف'
        
        result = {
            'status': 'success',
            'overall_status': overall_status,
            'total_positions': len(positions),
            'total_buy_value': total_buy_value,
            'total_current_value': total_current_value,
            'total_profit': total_profit,
            'total_profit_percent': total_profit_percent,
            'best_position': best_position,
            'worst_position': worst_position,
            'positions': positions,
            'diversity': diversity_analysis,
            'risk': risk_analysis,
            'analysis_time': datetime.now().isoformat()
        }
        
        self.last_analysis = result
        debug_log(f"✅ تحلیل پورتفو با {len(positions)} موقعیت انجام شد", "INFO")
        
        return result
    
    # ========================================================================
    # ۸-۳: تحلیل تنوع‌بخشی
    # ========================================================================
    
    def analyze_diversity(self, positions):
        """
        تحلیل تنوع‌بخشی پورتفو
        Args:
            positions (list): لیست موقعیت‌ها
        Returns:
            dict: تحلیل تنوع
        """
        if not positions:
            return {}
        
        # تعداد نمادهای مختلف
        symbols = [p['نماد'] for p in positions]
        unique_symbols = set(symbols)
        
        # تنوع صنایع
        industries = [p.get('صنعت', 'نامشخص') for p in positions]
        unique_industries = set(industries)
        
        # شاخص تمرکز (HHI - Herfindahl-Hirschman Index)
        total_value = sum(p['ارزش فعلی'] for p in positions)
        if total_value > 0:
            weights = [(p['ارزش فعلی'] / total_value) ** 2 for p in positions]
            hhi = sum(weights) * 10000  # مقیاس ۰-۱۰۰۰۰
        else:
            hhi = 10000
        
        # امتیاز تنوع
        diversity_scores = self.portfolio_config.get('diversity_scores', {})
        
        if len(unique_symbols) >= 10:
            diversity_score = diversity_scores.get(10, 100)
        elif len(unique_symbols) >= 7:
            diversity_score = diversity_scores.get(7, 80)
        elif len(unique_symbols) >= 5:
            diversity_score = diversity_scores.get(5, 60)
        elif len(unique_symbols) >= 3:
            diversity_score = diversity_scores.get(3, 40)
        else:
            diversity_score = diversity_scores.get('default', 20)
        
        # تحلیل تمرکز
        if hhi < 1500:
            concentration = 'پایین'
        elif hhi < 2500:
            concentration = 'متوسط'
        else:
            concentration = 'بالا'
        
        return {
            'تعداد نمادها': len(unique_symbols),
            'تعداد صنایع': len(unique_industries),
            'شاخص تمرکز HHI': round(hhi, 0),
            'سطح تمرکز': concentration,
            'امتیاز تنوع': diversity_score,
            'صنایع': list(unique_industries),
            'نمادها': list(unique_symbols)
        }
    
    # ========================================================================
    # ۸-۴: تحلیل ریسک پورتفو
    # ========================================================================
    
    def analyze_portfolio_risk(self, positions, market_df=None):
        """
        تحلیل ریسک پورتفو
        Args:
            positions (list): لیست موقعیت‌ها
            market_df (DataFrame): داده‌های بازار
        Returns:
            dict: تحلیل ریسک
        """
        if not positions:
            return {}
        
        total_value = sum(p['ارزش فعلی'] for p in positions)
        
        # محاسبه میانگین موزون معیارهای ریسک
        weighted_beta = 0
        weighted_pe = 0
        weighted_pb = 0
        weighted_volume = 0
        
        valid_positions = 0
        
        for pos in positions:
            weight = pos['ارزش فعلی'] / total_value if total_value > 0 else 0
            
            # بتا (اگر در داده‌های بازار باشد)
            beta = self.safe_float(pos.get('بتا', 1))
            weighted_beta += beta * weight
            
            # P/E
            pe = self.safe_float(pos.get('P/E', 10))
            if pe > 0:
                weighted_pe += pe * weight
            
            # P/B
            pb = self.safe_float(pos.get('P/B', 1))
            if pb > 0:
                weighted_pb += pb * weight
            
            # حجم معاملات (نقدشوندگی)
            volume = self.safe_float(pos.get('حجم', 100000))
            weighted_volume += volume * weight
            
            valid_positions += 1
        
        # سطح ریسک کلی
        risk_score = 0
        
        # ریسک بتا
        if weighted_beta > 1.5:
            beta_risk = 80
        elif weighted_beta > 1.2:
            beta_risk = 60
        elif weighted_beta > 0.8:
            beta_risk = 40
        else:
            beta_risk = 20
        
        # ریسک P/E
        if weighted_pe > 20:
            pe_risk = 70
        elif weighted_pe > 15:
            pe_risk = 50
        elif weighted_pe > 10:
            pe_risk = 30
        else:
            pe_risk = 10
        
        # ریسک نقدشوندگی
        if weighted_volume < 100000:
            liquidity_risk = 80
        elif weighted_volume < 500000:
            liquidity_risk = 60
        elif weighted_volume < 1000000:
            liquidity_risk = 40
        else:
            liquidity_risk = 20
        
        # میانگین موزون
        risk_score = (beta_risk * 0.4 + pe_risk * 0.3 + liquidity_risk * 0.3)
        
        # سطح ریسک
        if risk_score >= 70:
            risk_level = '🔴 بالا'
        elif risk_score >= 50:
            risk_level = '🟡 متوسط'
        else:
            risk_level = '🟢 پایین'
        
        return {
            'امتیاز ریسک': round(risk_score, 0),
            'سطح ریسک': risk_level,
            'بتای پورتفو': round(weighted_beta, 2),
            'P/E میانگین': round(weighted_pe, 1),
            'P/B میانگین': round(weighted_pb, 2),
            'نقدشوندگی میانگین': int(weighted_volume),
            'جزئیات': {
                'ریسک بتا': beta_risk,
                'ریسک P/E': pe_risk,
                'ریسک نقدشوندگی': liquidity_risk
            }
        }
    
    # ========================================================================
    # ۸-۵: بهینه‌سازی پورتفو
    # ========================================================================
    
    def optimize_portfolio(self, portfolio_df, market_df=None, target_return=None):
        """
        بهینه‌سازی وزن‌های پورتفو
        Args:
            portfolio_df (DataFrame): داده‌های پورتفو
            market_df (DataFrame): داده‌های بازار
            target_return (float): بازده هدف
        Returns:
            dict: پیشنهادات بهینه‌سازی
        """
        if portfolio_df is None or portfolio_df.empty:
            return {}
        
        # تحلیل فعلی
        current = self.analyze_portfolio(portfolio_df, market_df)
        
        suggestions = []
        
        # بررسی وزن‌های بیش از حد
        max_weight = self.portfolio_config.get('max_portfolio_weight', 0.20)
        
        for pos in current['positions']:
            if pos['وزن'] > max_weight * 100:
                suggestions.append({
                    'نوع': 'کاهش وزن',
                    'نماد': pos['نماد'],
                    'وزن فعلی': pos['وزن'],
                    'وزن هدف': max_weight * 100,
                    'مقدار کاهش': pos['ارزش فعلی'] * (1 - max_weight * 100 / pos['وزن']),
                    'دلیل': f'وزن بیشتر از حد مجاز ({max_weight*100}%)'
                })
        
        # بررسی موقعیت‌های با سود بالا
        alert_thresholds = self.portfolio_config.get('alert_thresholds', {})
        
        for pos in current['positions']:
            if pos['درصد سود/زیان'] > alert_thresholds.get('profit_high', 25):
                suggestions.append({
                    'نوع': 'برداشت سود',
                    'نماد': pos['نماد'],
                    'سود فعلی': pos['درصد سود/زیان'],
                    'ارزش سود': pos['سود/زیان'],
                    'دلیل': 'سود بالا - پیشنهاد برداشت بخشی از سود'
                })
        
        # بررسی موقعیت‌های با ضرر
        for pos in current['positions']:
            if pos['درصد سود/زیان'] < alert_thresholds.get('loss_high', -15):
                suggestions.append({
                    'نوع': 'بررسی ضرر',
                    'نماد': pos['نماد'],
                    'ضرر فعلی': pos['درصد سود/زیان'],
                    'ارزش ضرر': abs(pos['سود/زیان']),
                    'دلیل': 'ضرر بالا - بررسی علت و تصمیم‌گیری'
                })
        
        # پیشنهاد افزایش تنوع
        if current['diversity']['تعداد نمادها'] < 5:
            suggestions.append({
                'نوع': 'افزایش تنوع',
                'تعداد فعلی': current['diversity']['تعداد نمادها'],
                'تعداد پیشنهادی': 5,
                'دلیل': 'تنوع پایین - افزایش ریسک'
            })
        
        return {
            'current': current,
            'suggestions': suggestions,
            'optimization_time': datetime.now().isoformat()
        }
    
    # ========================================================================
    # ۸-۶: ذخیره و بارگذاری پورتفو
    # ========================================================================
    
    def save_portfolio(self, portfolio_df, filename=None):
        """
        ذخیره پورتفو در فایل
        Args:
            portfolio_df (DataFrame): داده‌های پورتفو
            filename (str): نام فایل
        Returns:
            str: مسیر فایل
        """
        if portfolio_df is None or portfolio_df.empty:
            return None
        
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"portfolio_{timestamp}.xlsx"
            
            file_path = os.path.join(PORTFOLIO_DIR, filename)
            portfolio_df.to_excel(file_path, index=False)
            
            debug_log(f"💾 پورتفو در {file_path} ذخیره شد", "INFO")
            return file_path
            
        except Exception as e:
            debug_log(f"❌ خطا در ذخیره پورتفو: {e}", "ERROR")
            return None
    
    def load_portfolio(self, file_path):
        """
        بارگذاری پورتفو از فایل
        Args:
            file_path (str): مسیر فایل
        Returns:
            DataFrame: داده‌های پورتفو
        """
        try:
            if not os.path.exists(file_path):
                debug_log(f"❌ فایل {file_path} وجود ندارد", "ERROR")
                return None
            
            df = pd.read_excel(file_path)
            debug_log(f"📂 پورتفو از {file_path} بارگذاری شد", "INFO")
            return df
            
        except Exception as e:
            debug_log(f"❌ خطا در بارگذاری پورتفو: {e}", "ERROR")
            return None


# ============================================================================
# بخش ۹: کلاس EZTraderConnector (اتصال به ایزی‌تریدر)
# ============================================================================

class EZTraderConnector:
    """
    اتصال به ایزی‌تریدر برای دریافت داده‌های آنلاین
    و انجام معاملات خودکار
    """
    
    def __init__(self, settings=None):
        """
        سازنده کلاس EZTraderConnector
        Args:
            settings (Settings): تنظیمات برنامه
        """
        self.settings = settings or Settings()
        self.ez_config = self.settings.settings.get('ez_trader', {})
        
        self.connected = False
        self.session = None
        self.username = self.ez_config.get('username', '')
        self.password = self.ez_config.get('password', '')
        self.host = self.ez_config.get('host', 'localhost')
        self.port = self.ez_config.get('port', 8080)
        self.use_ssl = self.ez_config.get('use_ssl', False)
        
        # وضعیت اتصال
        self.last_connection = None
        self.connection_attempts = 0
        self.data_cache = {}
        
        debug_log("✅ EZTraderConnector راه‌اندازی شد", "INFO")
    
    def connect(self):
        """
        اتصال به ایزی‌تریدر
        Returns:
            bool: موفقیت اتصال
        """
        try:
            # پروتکل مناسب
            protocol = "https" if self.use_ssl else "http"
            base_url = f"{protocol}://{self.host}:{self.port}"
            
            self.session = requests.Session()
            
            # تلاش برای اتصال
            response = self.session.get(f"{base_url}/api/status", timeout=10)
            
            if response.status_code == 200:
                self.connected = True
                self.last_connection = datetime.now()
                debug_log(f"✅ اتصال به ایزی‌تریدر در {base_url} برقرار شد", "INFO")
                return True
            else:
                debug_log(f"⚠️ پاسخ نامعتبر از ایزی‌تریدر: {response.status_code}", "WARNING")
                return False
                
        except requests.exceptions.ConnectionError:
            debug_log(f"❌ خطا در اتصال به ایزی‌تریدر در {self.host}:{self.port}", "ERROR")
            return False
        except Exception as e:
            debug_log(f"❌ خطای غیرمنتظره در اتصال به ایزی‌تریدر: {e}", "ERROR")
            return False
    
    def disconnect(self):
        """قطع اتصال از ایزی‌تریدر"""
        self.connected = False
        self.session = None
        debug_log("🔌 اتصال از ایزی‌تریدر قطع شد", "INFO")
    
    def login(self, username=None, password=None):
        """
        ورود به ایزی‌تریدر
        Args:
            username (str): نام کاربری
            password (str): رمز عبور
        Returns:
            bool: موفقیت ورود
        """
        if not self.connected and not self.connect():
            return False
        
        username = username or self.username
        password = password or self.password
        
        if not username or not password:
            debug_log("⚠️ نام کاربری یا رمز عبور وارد نشده", "WARNING")
            return False
        
        try:
            protocol = "https" if self.use_ssl else "http"
            login_url = f"{protocol}://{self.host}:{self.port}/api/login"
            
            login_data = {
                'username': username,
                'password': password
            }
            
            response = self.session.post(login_url, json=login_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', False):
                    debug_log(f"✅ ورود به ایزی‌تریدر با نام {username} موفقیت‌آمیز بود", "INFO")
                    
                    # ذخیره توکن اگر وجود داشته باشد
                    self.token = result.get('token', '')
                    return True
                else:
                    debug_log(f"❌ خطا در ورود: {result.get('message', 'نامشخص')}", "ERROR")
                    return False
            else:
                debug_log(f"❌ خطای HTTP {response.status_code} در ورود", "ERROR")
                return False
                
        except Exception as e:
            debug_log(f"❌ خطا در ورود به ایزی‌تریدر: {e}", "ERROR")
            return False
    
    def get_portfolio(self):
        """
        دریافت پورتفوی ایزی‌تریدر
        Returns:
            DataFrame: داده‌های پورتفو
        """
        if not self.connected:
            if not self.connect():
                return pd.DataFrame()
        
        try:
            protocol = "https" if self.use_ssl else "http"
            url = f"{protocol}://{self.host}:{self.port}/api/portfolio"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                    debug_log(f"✅ پورتفو با {len(df)} موقعیت از ایزی‌تریدر دریافت شد", "INFO")
                    return df
                else:
                    debug_log("⚠️ داده‌های پورتفو نامعتبر است", "WARNING")
                    return pd.DataFrame()
            else:
                debug_log(f"❌ خطا در دریافت پورتفو: {response.status_code}", "ERROR")
                return pd.DataFrame()
                
        except Exception as e:
            debug_log(f"❌ خطا در دریافت پورتفو از ایزی‌تریدر: {e}", "ERROR")
            return pd.DataFrame()
    
    def get_market_data(self):
        """
        دریافت داده‌های بازار از ایزی‌تریدر
        Returns:
            DataFrame: داده‌های بازار
        """
        if not self.connected:
            if not self.connect():
                return pd.DataFrame()
        
        try:
            protocol = "https" if self.use_ssl else "http"
            url = f"{protocol}://{self.host}:{self.port}/api/market"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                    debug_log(f"✅ داده‌های بازار با {len(df)} نماد از ایزی‌تریدر دریافت شد", "INFO")
                    return df
                else:
                    debug_log("⚠️ داده‌های بازار نامعتبر است", "WARNING")
                    return pd.DataFrame()
            else:
                debug_log(f"❌ خطا در دریافت داده‌های بازار: {response.status_code}", "ERROR")
                return pd.DataFrame()
                
        except Exception as e:
            debug_log(f"❌ خطا در دریافت داده‌های بازار از ایزی‌تریدر: {e}", "ERROR")
            return pd.DataFrame()
    
    def place_order(self, symbol, order_type, quantity, price=None):
        """
        ثبت سفارش در ایزی‌تریدر
        Args:
            symbol (str): نماد
            order_type (str): نوع سفارش (buy/sell)
            quantity (int): تعداد
            price (float): قیمت (اختیاری)
        Returns:
            dict: نتیجه سفارش
        """
        if not self.connected:
            if not self.connect():
                return {'success': False, 'message': 'عدم اتصال به ایزی‌تریدر'}
        
        try:
            protocol = "https" if self.use_ssl else "http"
            url = f"{protocol}://{self.host}:{self.port}/api/order"
            
            order_data = {
                'symbol': symbol,
                'type': order_type,
                'quantity': quantity
            }
            
            if price:
                order_data['price'] = price
            
            response = self.session.post(url, json=order_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                debug_log(f"✅ سفارش {order_type} {symbol} با موفقیت ثبت شد", "INFO")
                return result
            else:
                debug_log(f"❌ خطا در ثبت سفارش: {response.status_code}", "ERROR")
                return {'success': False, 'message': f'HTTP Error {response.status_code}'}
                
        except Exception as e:
            debug_log(f"❌ خطا در ثبت سفارش در ایزی‌تریدر: {e}", "ERROR")
            return {'success': False, 'message': str(e)}
    
    def get_orders(self):
        """
        دریافت لیست سفارشات
        Returns:
            DataFrame: سفارشات
        """
        if not self.connected:
            return pd.DataFrame()
        
        try:
            protocol = "https" if self.use_ssl else "http"
            url = f"{protocol}://{self.host}:{self.port}/api/orders"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                    debug_log(f"✅ {len(df)} سفارش از ایزی‌تریدر دریافت شد", "INFO")
                    return df
                else:
                    return pd.DataFrame()
            else:
                return pd.DataFrame()
                
        except Exception as e:
            debug_log(f"❌ خطا در دریافت سفارشات: {e}", "ERROR")
            return pd.DataFrame()
    
    def get_account_info(self):
        """
        دریافت اطلاعات حساب
        Returns:
            dict: اطلاعات حساب
        """
        if not self.connected:
            return {}
        
        try:
            protocol = "https" if self.use_ssl else "http"
            url = f"{protocol}://{self.host}:{self.port}/api/account"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                debug_log("✅ اطلاعات حساب دریافت شد", "INFO")
                return data
            else:
                return {}
                
        except Exception as e:
            debug_log(f"❌ خطا در دریافت اطلاعات حساب: {e}", "ERROR")
            return {}
    
    def check_connection(self):
        """
        بررسی وضعیت اتصال
        Returns:
            bool: وضعیت اتصال
        """
        if not self.connected:
            return False
        
        try:
            protocol = "https" if self.use_ssl else "http"
            url = f"{protocol}://{self.host}:{self.port}/api/ping"
            
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                return True
            else:
                self.connected = False
                return False
                
        except:
            self.connected = False
            return False
    
    def get_status(self):
        """
        دریافت وضعیت کامل اتصال
        Returns:
            dict: وضعیت
        """
        return {
            'connected': self.connected,
            'host': self.host,
            'port': self.port,
            'ssl': self.use_ssl,
            'last_connection': self.last_connection.isoformat() if self.last_connection else None,
            'attempts': self.connection_attempts,
            'username': self.username
        }
    
    def __repr__(self):
        status = "✅ متصل" if self.connected else "❌ قطع"
        return f"EZTraderConnector(host={self.host}:{self.port}, status={status})"


# ============================================================================
# بخش ۱۰: کلاس AlertManager (مدیریت هشدارها)
# ============================================================================

class AlertManager:
    """
    مدیریت هشدارها و نوتیفیکیشن‌ها
    """
    
    def __init__(self, settings=None):
        """
        سازنده کلاس AlertManager
        Args:
            settings (Settings): تنظیمات برنامه
        """
        self.settings = settings or Settings()
        self.alert_config = self.settings.settings.get('alerts', {})
        
        self.alerts = []
        self.notification_history = []
        self.last_check = None
        
        # بارگذاری هشدارهای ذخیره شده
        self.load_alerts()
        
        debug_log("✅ AlertManager راه‌اندازی شد", "INFO")
    
    def load_alerts(self):
        """بارگذاری هشدارهای ذخیره شده"""
        try:
            if os.path.exists(ALERTS_FILE):
                with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                    self.alerts = json.load(f)
                debug_log(f"📦 {len(self.alerts)} هشدار بارگذاری شد", "INFO")
        except Exception as e:
            debug_log(f"⚠️ خطا در بارگذاری هشدارها: {e}", "WARNING")
    
    def save_alerts(self):
        """ذخیره هشدارها"""
        try:
            with open(ALERTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.alerts, f, ensure_ascii=False, indent=2)
            debug_log(f"💾 {len(self.alerts)} هشدار ذخیره شد", "INFO")
        except Exception as e:
            debug_log(f"⚠️ خطا در ذخیره هشدارها: {e}", "WARNING")
    
    def add_alert(self, alert):
        """
        افزودن هشدار جدید
        Args:
            alert (dict): اطلاعات هشدار
        Returns:
            str: شناسه هشدار
        """
        alert['id'] = str(uuid.uuid4())
        alert['created_at'] = datetime.now().isoformat()
        alert['active'] = True
        alert['triggered'] = False
        alert['triggered_count'] = 0
        
        self.alerts.append(alert)
        self.save_alerts()
        
        debug_log(f"🔔 هشدار جدید اضافه شد: {alert.get('name', 'بدون نام')}", "INFO")
        return alert['id']
    
    def remove_alert(self, alert_id):
        """
        حذف هشدار
        Args:
            alert_id (str): شناسه هشدار
        Returns:
            bool: موفقیت
        """
        initial_count = len(self.alerts)
        self.alerts = [a for a in self.alerts if a.get('id') != alert_id]
        
        if len(self.alerts) < initial_count:
            self.save_alerts()
            debug_log(f"🗑️ هشدار {alert_id} حذف شد", "INFO")
            return True
        
        return False
    
    def check_alerts(self, market_data):
        """
        بررسی هشدارها
        Args:
            market_data (DataFrame): داده‌های بازار
        Returns:
            list: هشدارهای فعال شده
        """
        if market_data is None or market_data.empty:
            return []
        
        triggered = []
        
        for alert in self.alerts:
            if not alert.get('active', False):
                continue
            
            symbol = alert.get('symbol')
            alert_type = alert.get('type')
            condition = alert.get('condition')
            value = alert.get('value')
            
            # پیدا کردن داده نماد
            symbol_data = market_data[market_data['نماد'] == symbol]
            if symbol_data.empty:
                continue
            
            row = symbol_data.iloc[0]
            
            # بررسی بر اساس نوع
            triggered_flag = False
            current_value = None
            
            if alert_type == 'price':
                current_value = row.get('قیمت', 0)
                if condition == '>':
                    triggered_flag = current_value > value
                elif condition == '<':
                    triggered_flag = current_value < value
                elif condition == '=':
                    triggered_flag = abs(current_value - value) < 0.01 * value
            
            elif alert_type == 'volume':
                current_value = row.get('حجم', 0)
                if condition == '>':
                    triggered_flag = current_value > value
                elif condition == '<':
                    triggered_flag = current_value < value
            
            elif alert_type == 'percent_change':
                current_value = row.get('درصد تغییر', 0)
                if condition == '>':
                    triggered_flag = current_value > value
                elif condition == '<':
                    triggered_flag = current_value < value
            
            if triggered_flag and not alert.get('triggered', False):
                # هشدار فعال شد
                alert['triggered'] = True
                alert['triggered_count'] = alert.get('triggered_count', 0) + 1
                alert['last_triggered'] = datetime.now().isoformat()
                
                triggered.append({
                    'id': alert['id'],
                    'name': alert.get('name', ''),
                    'symbol': symbol,
                    'type': alert_type,
                    'current_value': current_value,
                    'threshold': value,
                    'message': alert.get('message', f'هشدار {symbol} فعال شد')
                })
                
                # ارسال نوتیفیکیشن
                self.send_notification(triggered[-1])
        
        if triggered:
            self.save_alerts()
        
        self.last_check = datetime.now()
        return triggered
    
    def send_notification(self, alert_info):
        """
        ارسال نوتیفیکیشن
        Args:
            alert_info (dict): اطلاعات هشدار
        """
        # ذخیره در تاریخچه
        self.notification_history.append({
            **alert_info,
            'sent_at': datetime.now().isoformat()
        })
        
        # نوتیفیکیشن دسکتاپ
        if self.alert_config.get('desktop_notification', True):
            try:
                import plyer
                plyer.notification.notify(
                    title=f"هشدار بورس - {alert_info['symbol']}",
                    message=alert_info['message'],
                    timeout=5
                )
            except:
                pass
        
        # صدا
        if self.alert_config.get('sound', True):
            try:
                import winsound
                winsound.Beep(1000, 500)
            except:
                pass
        
        debug_log(f"🔔 نوتیفیکیشن ارسال شد: {alert_info['message']}", "INFO")
    
    def get_alerts(self, active_only=False):
        """
        دریافت لیست هشدارها
        Args:
            active_only (bool): فقط هشدارهای فعال
        Returns:
            list: لیست هشدارها
        """
        if active_only:
            return [a for a in self.alerts if a.get('active', False)]
        return self.alerts
    
    def get_notification_history(self, limit=50):
        """
        دریافت تاریخچه نوتیفیکیشن‌ها
        Args:
            limit (int): حداکثر تعداد
        Returns:
            list: تاریخچه
        """
        return self.notification_history[-limit:]
    
    def clear_history(self):
        """پاک کردن تاریخچه"""
        self.notification_history = []
        debug_log("🧹 تاریخچه نوتیفیکیشن‌ها پاک شد", "INFO")
    
    def __repr__(self):
        active = sum(1 for a in self.alerts if a.get('active', False))
        return f"AlertManager(alerts={len(self.alerts)}, active={active})"
# ============================================================================
# بخش ۱۱: راه‌اندازی Flask و SocketIO
# ============================================================================

# ============================================================================
# ۱۱-۱: ایجاد اپلیکیشن Flask
# ============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_TYPE'] = SESSION_TYPE
app.config['SESSION_PERMANENT'] = SESSION_PERMANENT
app.config['SESSION_USE_SIGNER'] = SESSION_USE_SIGNER
app.config['SESSION_COOKIE_SECURE'] = SESSION_COOKIE_SECURE
app.config['SESSION_COOKIE_HTTPONLY'] = SESSION_COOKIE_HTTPONLY
app.config['SESSION_COOKIE_SAMESITE'] = SESSION_COOKIE_SAMESITE
app.config['PERMANENT_SESSION_LIFETIME'] = PERMANENT_SESSION_LIFETIME
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ============================================================================
# ۱۱-۲: تنظیم CORS
# ============================================================================

CORS(app, resources={r"/api/*": {"origins": "*"}})

# ============================================================================
# ۱۱-۳: راه‌اندازی SocketIO
# ============================================================================

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ============================================================================
# ۱۱-۴: ایجاد نمونه‌های اصلی
# ============================================================================

settings = Settings()
data_manager = DataManager(settings=settings)
analyzer = AdvancedStockAnalyzer(settings=settings, data_manager=data_manager)
portfolio_analyzer = AdvancedPortfolioAnalyzer(settings=settings)
alert_manager = AlertManager(settings=settings)
ez_trader = EZTraderConnector(settings=settings)

# ============================================================================
# بخش ۱۲: توابع کمکی Flask
# ============================================================================

@app.context_processor
def utility_processor():
    """اضافه کردن توابع کمکی به تمام قالب‌ها"""
    return dict(
        now=datetime.now,
        format_number=format_number,
        format_percent=format_percent,
        persian_date=persian_date,
        time_ago=time_ago,
        app_version=VERSION,
        app_name=APP_NAME
    )

@app.before_request
def before_request():
    """قبل از هر درخواست"""
    # ثبت لاگ درخواست
    debug_log(f"📨 {request.method} {request.path}", "ACCESS")
    
    # تنظیم زبان
    session['lang'] = 'fa'

@app.after_request
def after_request(response):
    """بعد از هر درخواست"""
    # ثبت لاگ پاسخ
    debug_log(f"📨 پاسخ {response.status_code}", "ACCESS")
    return response

@app.errorhandler(404)
def not_found_error(error):
    """خطای ۴۰۴"""
    return render_template_string('''
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>خطای ۴۰۴ - صفحه یافت نشد</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { font-family: Vazir, Tahoma, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; }
            .error-card { background: white; border-radius: 20px; padding: 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
            .error-code { font-size: 120px; font-weight: bold; color: #667eea; line-height: 1; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="error-card text-center">
                        <div class="error-code">۴۰۴</div>
                        <h2 class="mb-4">صفحه مورد نظر یافت نشد!</h2>
                        <p class="text-muted mb-4">صفحه‌ای که به دنبال آن هستید وجود ندارد یا حذف شده است.</p>
                        <a href="/" class="btn btn-primary btn-lg">بازگشت به داشبورد</a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''), 404

@app.errorhandler(500)
def internal_error(error):
    """خطای ۵۰۰"""
    debug_log(f"❌ خطای داخلی سرور: {error}", "ERROR")
    traceback.print_exc()
    return render_template_string('''
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>خطای ۵۰۰ - خطای داخلی سرور</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { font-family: Vazir, Tahoma, sans-serif; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); min-height: 100vh; display: flex; align-items: center; }
            .error-card { background: white; border-radius: 20px; padding: 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
            .error-code { font-size: 120px; font-weight: bold; color: #f5576c; line-height: 1; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="error-card text-center">
                        <div class="error-code">۵۰۰</div>
                        <h2 class="mb-4">خطای داخلی سرور!</h2>
                        <p class="text-muted mb-4">متأسفانه خطایی در سرور رخ داده است. لطفاً بعداً تلاش کنید.</p>
                        <a href="/" class="btn btn-danger btn-lg">بازگشت به داشبورد</a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''), 500

# ============================================================================
# بخش ۱۳: مسیرهای اصلی (Routes)
# ============================================================================

# ============================================================================
# ۱۳-۱: صفحه اصلی (داشبورد)
# ============================================================================

@app.route('/')
def index():
    """صفحه اصلی داشبورد"""
    try:
        # دریافت منبع داده از پارامتر
        data_source = request.args.get('source', 'auto')
        
        # دریافت داده‌ها
        market_data = data_manager.get_market_data(source=data_source)
        portfolio_data = data_manager.get_portfolio_data()
        
        # تحلیل داده‌ها
        if market_data is not None and not market_data.empty:
            analysis_results = analyzer.full_analysis(market_data, portfolio_data)
            
            # آمار کلی
            if not analysis_results.empty:
                stats = {
                    'total_stocks': len(analysis_results),
                    'avg_score': round(analysis_results['امتیاز نهایی'].mean(), 1),
                    'max_score': round(analysis_results['امتیاز نهایی'].max(), 1),
                    'min_score': round(analysis_results['امتیاز نهایی'].min(), 1),
                    'top_stocks': analysis_results.nlargest(5, 'امتیاز نهایی')[['نماد', 'امتیاز نهایی', 'وضعیت']].to_dict('records'),
                    'data_source': 'API' if data_source == 'api' or (data_source == 'auto' and data_manager.settings.is_api_enabled()) else 'Excel',
                    'last_update': time_ago(data_manager.last_update) if data_manager.last_update else 'هرگز'
                }
            else:
                analysis_results = pd.DataFrame()
                stats = {
                    'total_stocks': 0,
                    'avg_score': 0,
                    'max_score': 0,
                    'min_score': 0,
                    'top_stocks': [],
                    'data_source': 'ندارد',
                    'last_update': 'هرگز'
                }
        else:
            analysis_results = pd.DataFrame()
            stats = {
                'total_stocks': 0,
                'avg_score': 0,
                'max_score': 0,
                'min_score': 0,
                'top_stocks': [],
                'data_source': 'ندارد',
                'last_update': 'هرگز'
            }
        
        # دریافت تنظیمات API
        api_settings = settings.get_api_settings()
        
        # دریافت منابع داده موجود
        available_sources = data_manager.get_available_data_sources()
        
        return render_template_string(BASE_TEMPLATE, 
                                     analysis_results=analysis_results.to_dict('records') if not analysis_results.empty else [],
                                     stats=stats,
                                     api_settings=api_settings,
                                     available_sources=available_sources,
                                     data_source=data_source,
                                     request=request)
        
    except Exception as e:
        debug_log(f"❌ خطا در صفحه اصلی: {e}", "ERROR")
        traceback.print_exc()
        return f"خطا در بارگذاری صفحه: {str(e)}"

# ============================================================================
# ۱۳-۲: صفحه آپلود فایل
# ============================================================================

@app.route('/upload', methods=['POST'])
def upload_file():
    """آپلود فایل اکسل"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'فایلی ارسال نشده است'})
        
        file = request.files['file']
        file_type = request.form.get('type', 'market')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'نام فایل معتبر نیست'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'فرمت فایل باید Excel یا CSV باشد'})
        
        # ذخیره فایل
        file_path = data_manager.save_uploaded_file(file, file_type)
        
        if not file_path:
            return jsonify({'success': False, 'error': 'خطا در ذخیره فایل'})
        
        # بارگذاری داده‌ها
        df = data_manager.load_excel_file(file_path, file_type)
        
        if df is None:
            return jsonify({'success': False, 'error': 'خطا در خواندن فایل'})
        
        # ارسال رویداد از طریق SocketIO
        socketio.emit('file_uploaded', {
            'type': file_type,
            'rows': len(df),
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'message': f'فایل با موفقیت آپلود شد. {len(df)} ردیف خوانده شد.',
            'rows': len(df),
            'type': file_type,
            'preview': df.head(5).to_dict('records') if len(df) > 0 else []
        })
        
    except Exception as e:
        debug_log(f"❌ خطا در آپلود فایل: {e}", "ERROR")
        return jsonify({'success': False, 'error': str(e)})

# ============================================================================
# ۱۳-۳: صفحه تنظیمات API
# ============================================================================

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings_page():
    """صفحه تنظیمات API"""
    if request.method == 'POST':
        # ذخیره تنظیمات API
        api_config = {
            'enabled': request.form.get('api_enabled') == 'on',
            'mobile': request.form.get('api_mobile', '').strip(),
            'api_key': request.form.get('api_key', '').strip(),
            'auto_refresh': request.form.get('auto_refresh') == 'on',
            'refresh_interval': int(request.form.get('refresh_interval', 300)),
            'use_cache': request.form.get('use_cache') == 'on',
            'cache_ttl': int(request.form.get('cache_ttl', 300)),
            'user_agent_rotation': request.form.get('user_agent_rotation') == 'on',
            'verify_ssl': request.form.get('verify_ssl') == 'on',
            'data_sources': {
                'prices': request.form.get('source_prices') == 'on',
                'clients': request.form.get('source_clients') == 'on',
                'history': request.form.get('source_history') == 'on',
                'symbols': request.form.get('source_symbols') == 'on'
            }
        }
        
        settings.update_api_settings(api_config)
        
        # راه‌اندازی مجدد اتصال API
        if api_config['enabled']:
            data_manager.init_api_connection()
        
        flash('تنظیمات با موفقیت ذخیره شد', 'success')
        return redirect(url_for('api_settings_page'))
    
    # نمایش صفحه تنظیمات
    api_settings = settings.get_api_settings()
    available_sources = data_manager.get_available_data_sources()
    
    return render_template_string(API_SETTINGS_TEMPLATE, 
                                 api_settings=api_settings, 
                                 available_sources=available_sources)

# ============================================================================
# ۱۳-۴: APIهای RESTful
# ============================================================================

@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """به‌روزرسانی دستی داده‌های API"""
    try:
        result = data_manager.refresh_api_data()
        
        if result:
            socketio.emit('data_refreshed', {
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            })
            return jsonify({
                'success': True,
                'message': 'داده‌ها با موفقیت به‌روزرسانی شدند'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'خطا در دریافت داده از API'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/status', methods=['GET'])
def api_status():
    """دریافت وضعیت API"""
    try:
        api_settings = settings.get_api_settings()
        api_stats = data_manager.api_connector.get_api_stats() if data_manager.api_connector else {}
        
        return jsonify({
            'enabled': api_settings.get('enabled', False),
            'connected': data_manager.api_connector is not None and data_manager.api_connector.is_authenticated,
            'last_sync': api_settings.get('last_sync'),
            'sync_status': api_settings.get('sync_status'),
            'stats': api_stats,
            'data_sources': api_settings.get('data_sources', {})
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/test-connection', methods=['POST'])
def api_test_connection():
    """تست اتصال به API"""
    try:
        data = request.json
        
        test_connector = BrsApiConnector(
            api_key=data.get('api_key'),
            mobile=data.get('mobile'),
            data_dir=DATA_DIR,
            settings=settings
        )
        
        result = test_connector.test_connection()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/market-data', methods=['GET'])
def get_market_data():
    """دریافت داده‌های بازار"""
    try:
        source = request.args.get('source', 'auto')
        limit = int(request.args.get('limit', 100))
        
        df = data_manager.get_market_data(source=source)
        
        if df is not None and not df.empty:
            # محدود کردن تعداد
            if len(df) > limit:
                df = df.head(limit)
            
            return jsonify({
                'success': True,
                'data': df.to_dict('records'),
                'count': len(df),
                'source': source
            })
        else:
            return jsonify({
                'success': False,
                'error': 'داده‌ای موجود نیست'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/analysis', methods=['GET'])
def get_analysis():
    """دریافت نتایج تحلیل"""
    try:
        source = request.args.get('source', 'auto')
        limit = int(request.args.get('limit', 50))
        
        market_data = data_manager.get_market_data(source=source)
        portfolio_data = data_manager.get_portfolio_data()
        
        if market_data is not None and not market_data.empty:
            results = analyzer.full_analysis(market_data, portfolio_data)
            
            if not results.empty:
                # محدود کردن تعداد
                if len(results) > limit:
                    results = results.head(limit)
                
                summary = analyzer.get_analysis_summary(results)
                
                return jsonify({
                    'success': True,
                    'data': results.to_dict('records'),
                    'summary': summary,
                    'count': len(results)
                })
        
        return jsonify({
            'success': False,
            'error': 'تحلیل امکان‌پذیر نیست'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/portfolio-analysis', methods=['POST', 'GET'])
def portfolio_analysis():
    """تحلیل پورتفو"""
    try:
        if request.method == 'POST':
            # دریافت پورتفو از درخواست
            data = request.json
            portfolio_df = pd.DataFrame(data.get('positions', []))
        else:
            # استفاده از پورتفوی فعلی
            portfolio_df = data_manager.get_portfolio_data()
        
        # دریافت داده‌های بازار
        market_df = data_manager.get_market_data()
        
        # تحلیل
        result = portfolio_analyzer.analyze_portfolio(portfolio_df, market_df)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/alerts', methods=['GET', 'POST', 'DELETE'])
def alerts_api():
    """مدیریت هشدارها"""
    try:
        if request.method == 'GET':
            # دریافت لیست هشدارها
            active_only = request.args.get('active_only', 'false').lower() == 'true'
            alerts = alert_manager.get_alerts(active_only)
            return jsonify({
                'success': True,
                'alerts': alerts
            })
            
        elif request.method == 'POST':
            # افزودن هشدار جدید
            data = request.json
            alert_id = alert_manager.add_alert(data)
            return jsonify({
                'success': True,
                'alert_id': alert_id
            })
            
        elif request.method == 'DELETE':
            # حذف هشدار
            alert_id = request.args.get('id')
            if alert_id:
                success = alert_manager.remove_alert(alert_id)
                return jsonify({
                    'success': success
                })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/export', methods=['POST'])
def export_data():
    """خروجی گرفتن از داده‌ها"""
    try:
        data = request.json
        export_type = data.get('type', 'analysis')
        format_type = data.get('format', 'excel')
        
        if export_type == 'analysis':
            # خروجی تحلیل
            source = data.get('source', 'auto')
            market_data = data_manager.get_market_data(source=source)
            portfolio_data = data_manager.get_portfolio_data()
            
            if market_data is not None:
                results = analyzer.full_analysis(market_data, portfolio_data)
                
                if not results.empty:
                    filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    file_path = analyzer.save_analysis(results, filename)
                    
                    if file_path and os.path.exists(file_path):
                        return send_file(
                            file_path,
                            as_attachment=True,
                            download_name=filename,
                            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        )
        
        return jsonify({'success': False, 'error': 'خطا در خروجی'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    """پاک کردن کش"""
    try:
        cache_type = request.json.get('type', 'all')
        
        if cache_type == 'api' and data_manager.api_connector:
            count = data_manager.api_connector.clear_cache()
            message = f'{count} فایل کش API پاک شد'
        elif cache_type == 'data':
            data_manager.clear_all_data()
            message = 'تمام داده‌ها پاک شدند'
        else:
            # پاک کردن همه
            if data_manager.api_connector:
                data_manager.api_connector.clear_cache()
            data_manager.clear_all_data()
            message = 'تمام کش و داده‌ها پاک شدند'
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# ============================================================================
# بخش ۱۴: رویدادهای SocketIO
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """اتصال کلاینت"""
    debug_log(f"🟢 کلاینت متصل شد: {request.sid}", "SOCKET")
    emit('connected', {'message': 'اتصال برقرار شد', 'sid': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """قطع اتصال کلاینت"""
    debug_log(f"🔴 کلاینت قطع شد: {request.sid}", "SOCKET")

@socketio.on('subscribe')
def handle_subscribe(data):
    """اشتراک در یک کانال"""
    room = data.get('room', 'general')
    join_room(room)
    emit('subscribed', {'room': room, 'message': f'اشتراک در {room} فعال شد'})

@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """لغو اشتراک"""
    room = data.get('room', 'general')
    leave_room(room)
    emit('unsubscribed', {'room': room, 'message': f'اشتراک در {room} لغو شد'})

@socketio.on('request_refresh')
def handle_refresh_request(data):
    """درخواست به‌روزرسانی"""
    source = data.get('source', 'auto')
    
    # به‌روزرسانی در نخ جداگانه
    def refresh_task():
        result = data_manager.refresh_api_data()
        if result:
            socketio.emit('data_refreshed', {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'source': source
            }, room=request.sid)
    
    thread = threading.Thread(target=refresh_task)
    thread.start()
    
    emit('refresh_started', {'message': 'به‌روزرسانی شروع شد'})

@socketio.on('get_realtime_price')
def handle_realtime_price(data):
    """درخواست قیمت لحظه‌ای"""
    symbol = data.get('symbol')
    
    if symbol and data_manager.api_connector:
        # دریافت قیمت
        prices = data_manager.api_connector.get_market_prices(symbols=[symbol])
        
        if not prices.empty:
            price_data = prices.iloc[0].to_dict()
            emit('realtime_price', {
                'symbol': symbol,
                'data': price_data,
                'timestamp': datetime.now().isoformat()
            })

# ============================================================================
# بخش ۱۵: قالب‌های HTML (نسخه اصلاح شده)
# ============================================================================

# قالب پایه - اصلاح شده
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ app_name }} - نسخه {{ app_version }}</title>
    
    <!-- Bootstrap 5 RTL -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Vazir Font -->
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v30.1.0/dist/font-face.css" rel="stylesheet">
    
    <!-- Plotly -->
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    
    <!-- Socket.IO -->
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    
    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    
    <style>
        body {
            font-family: Vazir, Tahoma, sans-serif;
            background-color: #f8f9fa;
            padding-bottom: 70px;
        }
        
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .navbar-brand {
            color: white !important;
            font-weight: bold;
        }
        
        .nav-link {
            color: rgba(255,255,255,0.9) !important;
            transition: all 0.3s;
        }
        
        .nav-link:hover {
            color: white !important;
            transform: translateY(-2px);
        }
        
        .card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            transition: all 0.3s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.2);
        }
        
        .card-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px 15px 0 0 !important;
            font-weight: bold;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .stat-label {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .table {
            border-radius: 15px;
            overflow: hidden;
        }
        
        .table thead th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
        }
        
        .badge-excellent { background: #28a745; color: white; padding: 5px 10px; border-radius: 20px; }
        .badge-very-good { background: #17a2b8; color: white; padding: 5px 10px; border-radius: 20px; }
        .badge-good { background: #ffc107; color: black; padding: 5px 10px; border-radius: 20px; }
        .badge-average { background: #fd7e14; color: white; padding: 5px 10px; border-radius: 20px; }
        .badge-weak { background: #dc3545; color: white; padding: 5px 10px; border-radius: 20px; }
        
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .footer {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 10px 0;
            position: fixed;
            bottom: 0;
            width: 100%;
            z-index: 1000;
        }
        
        .rtl {
            direction: rtl;
        }
        
        .ltr {
            direction: ltr;
        }
    </style>
</head>
<body>
    <!-- ناوبری -->
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">
                <i class="fas fa-chart-line"></i> {{ app_name }}
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/">
                            <i class="fas fa-home"></i> داشبورد
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="uploadFile()">
                            <i class="fas fa-upload"></i> آپلود فایل
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/api/settings">
                            <i class="fas fa-plug"></i> اتصال به API
                        </a>
                    </li>
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown">
                            <i class="fas fa-download"></i> خروجی
                        </a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="#" onclick="exportData('analysis')">خروجی تحلیل</a></li>
                            <li><a class="dropdown-item" href="#" onclick="exportData('portfolio')">خروجی پورتفو</a></li>
                        </ul>
                    </li>
                </ul>
                <span class="navbar-text">
                    <span id="connection-status" class="badge bg-success">
                        <i class="fas fa-circle"></i> آنلاین
                    </span>
                    <span class="mx-2">نسخه {{ app_version }}</span>
                </span>
            </div>
        </div>
    </nav>

    <!-- محتوای اصلی -->
    <div class="container-fluid mt-4">
        <!-- نوار وضعیت API -->
        {% if api_settings and api_settings.enabled %}
        <div class="alert alert-info alert-dismissible fade show" role="alert">
            <i class="fas fa-sync fa-spin"></i>
            منبع داده فعلی: <strong>{{ stats.data_source if stats else 'نامشخص' }}</strong>
            {% if stats and stats.data_source == 'API' %}
                <span class="badge bg-success">آنلاین</span>
                آخرین به‌روزرسانی: {{ stats.last_update if stats.last_update else 'نامشخص' }}
            {% else %}
                <span class="badge bg-warning">آفلاین (فایل اکسل)</span>
            {% endif %}
            
            <div class="btn-group me-2" role="group">
                <a href="/?source=auto" class="btn btn-sm btn-{{ 'primary' if data_source == 'auto' else 'secondary' }}">خودکار</a>
                <a href="/?source=api" class="btn btn-sm btn-{{ 'primary' if data_source == 'api' else 'secondary' }}">API</a>
                <a href="/?source=excel" class="btn btn-sm btn-{{ 'primary' if data_source == 'excel' else 'secondary' }}">اکسل</a>
            </div>
            
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        {% endif %}

        <!-- کارت‌های آمار -->
        {% if stats %}
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="stat-card">
                    <i class="fas fa-chart-pie fa-2x"></i>
                    <div class="stat-number">{{ stats.total_stocks }}</div>
                    <div class="stat-label">تعداد سهام تحلیل شده</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                    <i class="fas fa-star fa-2x"></i>
                    <div class="stat-number">{{ stats.avg_score }}</div>
                    <div class="stat-label">میانگین امتیاز</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                    <i class="fas fa-arrow-up fa-2x"></i>
                    <div class="stat-number">{{ stats.max_score }}</div>
                    <div class="stat-label">بیشترین امتیاز</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                    <i class="fas fa-clock fa-2x"></i>
                    <div class="stat-number">{{ stats.last_update }}</div>
                    <div class="stat-label">آخرین به‌روزرسانی</div>
                </div>
            </div>
        </div>

        <!-- ۵ سهام برتر -->
        {% if stats.top_stocks %}
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-trophy"></i> ۵ سهام برتر
                    </div>
                    <div class="card-body">
                        <div class="row">
                            {% for stock in stats.top_stocks %}
                            <div class="col-md-2 col-6 mb-3">
                                <div class="card bg-light">
                                    <div class="card-body text-center">
                                        <h5>{{ stock['نماد'] }}</h5>
                                        <h3 class="text-primary">{{ stock['امتیاز نهایی'] }}</h3>
                                        <span class="badge {% if 'عالی' in stock['وضعیت'] %}bg-success{% elif 'خوب' in stock['وضعیت'] %}bg-info{% else %}bg-warning{% endif %}">
                                            {{ stock['وضعیت'] }}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}
        {% endif %}

        <!-- جدول تحلیل -->
        {% if analysis_results %}
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-table"></i> نتایج تحلیل سهام
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-hover" id="analysisTable">
                                <thead>
                                    <tr>
                                        <th>نماد</th>
                                        <th>قیمت</th>
                                        <th>امتیاز پایه</th>
                                        <th>امتیاز حباب</th>
                                        <th>ارزش ذاتی</th>
                                        <th>امتیاز تابلو</th>
                                        <th>امتیاز ریسک</th>
                                        <th>امتیاز تکنیکال</th>
                                        <th>امتیاز نهایی</th>
                                        <th>وضعیت</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for row in analysis_results %}
                                    <tr>
                                        <td><strong>{{ row['نماد'] }}</strong></td>
                                        <td>{{ format_number(row['قیمت']) if row['قیمت'] else '۰' }}</td>
                                        <td>{{ row['امتیاز پایه'] }}</td>
                                        <td>{{ row['امتیاز حباب'] }}</td>
                                        <td>{{ format_number(row['ارزش ذاتی']) if row['ارزش ذاتی'] else '۰' }}</td>
                                        <td>{{ row['امتیاز تابلو'] }}</td>
                                        <td>{{ row['امتیاز ریسک'] }}</td>
                                        <td>{{ row['امتیاز تکنیکال'] }}</td>
                                        <td><strong>{{ row['امتیاز نهایی'] }}</strong></td>
                                        <td>
                                            {% if '🟢' in row['وضعیت'] %}
                                                <span class="badge bg-success">{{ row['وضعیت'] }}</span>
                                            {% elif '🔵' in row['وضعیت'] %}
                                                <span class="badge bg-info">{{ row['وضعیت'] }}</span>
                                            {% elif '🟡' in row['وضعیت'] %}
                                                <span class="badge bg-warning">{{ row['وضعیت'] }}</span>
                                            {% elif '🟠' in row['وضعیت'] %}
                                                <span class="badge bg-warning">{{ row['وضعیت'] }}</span>
                                            {% else %}
                                                <span class="badge bg-danger">{{ row['وضعیت'] }}</span>
                                            {% endif %}
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% else %}
        <div class="alert alert-warning text-center">
            <i class="fas fa-exclamation-triangle"></i>
            داده‌ای برای نمایش وجود ندارد. لطفاً فایل اکسل آپلود کنید یا API را فعال نمایید.
        </div>
        {% endif %}
    </div>

    <!-- فوتر -->
    <div class="footer">
        <div class="container">
            <span>{{ app_name }} - تمام حقوق محفوظ است © ۱۴۰۳</span>
        </div>
    </div>

    <!-- Modal آپلود فایل -->
    <div class="modal fade" id="uploadModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">آپلود فایل اکسل</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="uploadForm" enctype="multipart/form-data">
                        <div class="mb-3">
                            <label for="fileType" class="form-label">نوع فایل</label>
                            <select class="form-select" id="fileType" name="type">
                                <option value="market">داده‌های بازار</option>
                                <option value="portfolio">پورتفوی شخصی</option>
                                <option value="watchlist">لیست پیگیری</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="file" class="form-label">فایل Excel</label>
                            <input class="form-control" type="file" id="file" name="file" accept=".xlsx,.xls">
                        </div>
                    </form>
                    <div id="uploadProgress" class="progress d-none">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%">در حال آپلود...</div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">انصراف</button>
                    <button type="button" class="btn btn-primary" onclick="submitUpload()">آپلود</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- DataTables -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/dataTables.bootstrap5.min.css">
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/dataTables.bootstrap5.min.js"></script>
    
    <script>
        // اتصال Socket.IO
        const socket = io();
        
        socket.on('connect', function() {
            console.log('✅ متصل به سرور');
            $('#connection-status').removeClass('bg-danger').addClass('bg-success').html('<i class="fas fa-circle"></i> آنلاین');
        });
        
        socket.on('disconnect', function() {
            console.log('❌ قطع اتصال از سرور');
            $('#connection-status').removeClass('bg-success').addClass('bg-danger').html('<i class="fas fa-circle"></i> قطع');
        });
        
        socket.on('data_refreshed', function(data) {
            console.log('🔄 داده‌ها به‌روزرسانی شدند:', data);
            showNotification('داده‌ها با موفقیت به‌روزرسانی شدند', 'success');
            setTimeout(() => location.reload(), 2000);
        });
        
        // توابع کمکی
        function uploadFile() {
            $('#uploadModal').modal('show');
        }
        
        function submitUpload() {
            var formData = new FormData($('#uploadForm')[0]);
            
            $('#uploadProgress').removeClass('d-none');
            
            $.ajax({
                url: '/upload',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    $('#uploadProgress').addClass('d-none');
                    $('#uploadModal').modal('hide');
                    
                    if (response.success) {
                        showNotification(response.message, 'success');
                        setTimeout(() => location.reload(), 2000);
                    } else {
                        showNotification(response.error, 'danger');
                    }
                },
                error: function(xhr) {
                    $('#uploadProgress').addClass('d-none');
                    showNotification('خطا در آپلود فایل', 'danger');
                }
            });
        }
        
        function exportData(type) {
            $.ajax({
                url: '/api/export',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({type: type, format: 'excel'}),
                xhrFields: {
                    responseType: 'blob'
                },
                success: function(blob) {
                    var url = window.URL.createObjectURL(blob);
                    var a = document.createElement('a');
                    a.href = url;
                    a.download = type + '_' + new Date().toISOString().slice(0,19).replace(/:/g, '-') + '.xlsx';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    showNotification('خروجی با موفقیت دریافت شد', 'success');
                },
                error: function() {
                    showNotification('خطا در دریافت خروجی', 'danger');
                }
            });
        }
        
        function refreshApiData() {
            $.ajax({
                url: '/api/refresh',
                type: 'POST',
                success: function(response) {
                    if (response.success) {
                        showNotification(response.message, 'success');
                    } else {
                        showNotification(response.error, 'danger');
                    }
                },
                error: function() {
                    showNotification('خطا در ارتباط با سرور', 'danger');
                }
            });
        }
        
        function showNotification(message, type) {
            var alertHtml = '<div class="alert alert-' + type + ' alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3" style="z-index: 9999;">' +
                message +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
                '</div>';
            
            $('body').append(alertHtml);
            
            setTimeout(function() {
                $('.alert').alert('close');
            }, 5000);
        }
        
        // فعال‌سازی DataTable
        $(document).ready(function() {
            {% if analysis_results %}
            $('#analysisTable').DataTable({
                language: {
                    url: '//cdn.datatables.net/plug-ins/1.13.4/i18n/fa.json'
                },
                order: [[8, 'desc']], // مرتب‌سازی بر اساس امتیاز نهایی
                pageLength: 25,
                responsive: true
            });
            {% endif %}
        });
        
        // به‌روزرسانی خودکار هر ۵ دقیقه
        {% if api_settings and api_settings.auto_refresh %}
        setInterval(function() {
            refreshApiData();
        }, {{ api_settings.refresh_interval * 1000 if api_settings.refresh_interval else 300000 }});
        {% endif %}
    </script>
</body>
</html>
'''
# قالب تنظیمات API
API_SETTINGS_TEMPLATE = '''
<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تنظیمات API - {{ app_name }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v30.1.0/dist/font-face.css" rel="stylesheet">
    <style>
        body {
            font-family: Vazir, Tahoma, sans-serif;
            background-color: #f8f9fa;
            padding: 20px;
        }
        
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin-bottom: 30px;
            border-radius: 15px;
        }
        
        .card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .card-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px 15px 0 0 !important;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        .connection-status {
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .status-success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status-error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- ناوبری -->
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container-fluid">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-arrow-right"></i> بازگشت به داشبورد
                </a>
            </div>
        </nav>
        
        <!-- فلش messages -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <!-- تنظیمات API -->
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-plug"></i> تنظیمات اتصال به API بورس ایران</h5>
                    </div>
                    <div class="card-body">
                        <form method="POST">
                            <!-- فعالسازی API -->
                            <div class="form-check form-switch mb-3">
                                <input class="form-check-input" type="checkbox" id="api_enabled" name="api_enabled" 
                                       {% if api_settings.enabled %}checked{% endif %}>
                                <label class="form-check-label" for="api_enabled">فعالسازی اتصال به API</label>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">شماره موبایل (با ۰۹)</label>
                                    <input type="text" class="form-control" name="api_mobile" 
                                           value="{{ api_settings.mobile }}" placeholder="مثال: 09123456789">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">کلید وب‌سرویس (۳۲ کاراکتر)</label>
                                    <input type="text" class="form-control" name="api_key" 
                                           value="{{ api_settings.api_key }}" placeholder="کلید ۳۲ رقمی">
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <div class="form-check form-switch">
                                        <input class="form-check-input" type="checkbox" id="auto_refresh" name="auto_refresh"
                                               {% if api_settings.auto_refresh %}checked{% endif %}>
                                        <label class="form-check-label" for="auto_refresh">به‌روزرسانی خودکار</label>
                                    </div>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">فاصله به‌روزرسانی (ثانیه)</label>
                                    <input type="number" class="form-control" name="refresh_interval" 
                                           value="{{ api_settings.refresh_interval }}" min="60" max="3600">
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <div class="form-check form-switch">
                                        <input class="form-check-input" type="checkbox" id="use_cache" name="use_cache"
                                               {% if api_settings.use_cache %}checked{% endif %}>
                                        <label class="form-check-label" for="use_cache">استفاده از حافظه پنهان</label>
                                    </div>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">مدت اعتبار کش (ثانیه)</label>
                                    <input type="number" class="form-control" name="cache_ttl" 
                                           value="{{ api_settings.cache_ttl }}" min="60" max="86400">
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <div class="form-check form-switch">
                                        <input class="form-check-input" type="checkbox" id="user_agent_rotation" name="user_agent_rotation"
                                               {% if api_settings.user_agent_rotation %}checked{% endif %}>
                                        <label class="form-check-label" for="user_agent_rotation">چرخش User-Agent</label>
                                    </div>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <div class="form-check form-switch">
                                        <input class="form-check-input" type="checkbox" id="verify_ssl" name="verify_ssl"
                                               {% if api_settings.verify_ssl %}checked{% endif %}>
                                        <label class="form-check-label" for="verify_ssl">بررسی SSL</label>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card mt-3">
                                <div class="card-header">
                                    <h6>منابع داده فعال</h6>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-3">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="source_prices" name="source_prices"
                                                       {% if api_settings.data_sources.prices %}checked{% endif %}>
                                                <label class="form-check-label" for="source_prices">قیمت‌ها</label>
                                            </div>
                                        </div>
                                        <div class="col-md-3">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="source_clients" name="source_clients"
                                                       {% if api_settings.data_sources.clients %}checked{% endif %}>
                                                <label class="form-check-label" for="source_clients">مشتریان</label>
                                            </div>
                                        </div>
                                        <div class="col-md-3">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="source_history" name="source_history"
                                                       {% if api_settings.data_sources.history %}checked{% endif %}>
                                                <label class="form-check-label" for="source_history">تاریخچه</label>
                                            </div>
                                        </div>
                                        <div class="col-md-3">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="source_symbols" name="source_symbols"
                                                       {% if api_settings.data_sources.symbols %}checked{% endif %}>
                                                <label class="form-check-label" for="source_symbols">لیست نمادها</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-4">
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-save"></i> ذخیره تنظیمات
                                </button>
                                <button type="button" class="btn btn-success" onclick="testConnection()">
                                    <i class="fas fa-plug"></i> تست اتصال
                                </button>
                                <button type="button" class="btn btn-info" onclick="clearCache()">
                                    <i class="fas fa-trash"></i> پاک کردن کش
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            
            <!-- وضعیت اتصال -->
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-info-circle"></i> وضعیت اتصال</h5>
                    </div>
                    <div class="card-body">
                        <div id="connectionStatus" class="connection-status 
                            {% if api_settings.sync_status == 'success' %}status-success{% else %}status-error{% endif %}">
                            <h6>وضعیت فعلی:</h6>
                            <p>
                                {% if api_settings.enabled %}
                                    {% if api_settings.sync_status == 'success' %}
                                        <i class="fas fa-check-circle text-success"></i> متصل
                                    {% else %}
                                        <i class="fas fa-exclamation-circle text-danger"></i> قطع
                                    {% endif %}
                                {% else %}
                                    <i class="fas fa-power-off text-secondary"></i> غیرفعال
                                {% endif %}
                            </p>
                            
                            {% if api_settings.last_sync %}
                            <p>آخرین همگام‌سازی: {{ time_ago(api_settings.last_sync) }}</p>
                            {% endif %}
                        </div>
                        
                        <h6 class="mt-3">منابع داده موجود:</h6>
                        <ul class="list-group">
                            {% for source in available_sources %}
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                {{ source.icon }} {{ source.name }}
                                {% if source.type == 'api' %}
                                    <span class="badge {% if source.status == '🟢 متصل' %}bg-success{% else %}bg-danger{% endif %}">
                                        {{ source.status }}
                                    </span>
                                {% else %}
                                    <span class="badge bg-info">{{ source.rows }} ردیف</span>
                                {% endif %}
                            </li>
                            {% endfor %}
                        </ul>
                        
                        <div id="testResult" class="mt-3"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        function testConnection() {
            var mobile = $('input[name="api_mobile"]').val();
            var apiKey = $('input[name="api_key"]').val();
            
            if (!mobile || !apiKey) {
                showMessage('لطفاً شماره موبایل و کلید API را وارد کنید', 'danger');
                return;
            }
            
            $('#testResult').html('<div class="alert alert-info">در حال تست اتصال...</div>');
            
            $.ajax({
                url: '/api/test-connection',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({mobile: mobile, api_key: apiKey}),
                success: function(response) {
                    if (response.success) {
                        $('#testResult').html('<div class="alert alert-success">✅ ' + response.message + '</div>');
                        $('#connectionStatus').removeClass('status-error').addClass('status-success')
                            .html('<h6>وضعیت فعلی:</h6><p><i class="fas fa-check-circle text-success"></i> متصل</p>');
                    } else {
                        $('#testResult').html('<div class="alert alert-danger">❌ ' + response.message + '</div>');
                    }
                },
                error: function() {
                    $('#testResult').html('<div class="alert alert-danger">خطا در ارتباط با سرور</div>');
                }
            });
        }
        
        function clearCache() {
            if (!confirm('آیا از پاک کردن کش اطمینان دارید؟')) {
                return;
            }
            
            $.ajax({
                url: '/api/clear-cache',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({type: 'api'}),
                success: function(response) {
                    if (response.success) {
                        showMessage(response.message, 'success');
                    } else {
                        showMessage(response.error, 'danger');
                    }
                }
            });
        }
        
        function showMessage(message, type) {
            var alertHtml = '<div class="alert alert-' + type + ' alert-dismissible fade show mt-3">' +
                message +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
                '</div>';
            
            $('#testResult').html(alertHtml);
        }
    </script>
</body>
</html>
'''

# ============================================================================
# بخش ۱۶: وظایف زمانبندی شده (Scheduled Tasks)
# ============================================================================

def scheduled_api_refresh():
    """وظیفه زمانبندی شده برای به‌روزرسانی خودکار API"""
    while True:
        try:
            # بررسی تنظیمات
            if settings and settings.is_api_enabled():
                api_settings = settings.get_api_settings()
                
                if api_settings.get('auto_refresh', False):
                    refresh_interval = api_settings.get('refresh_interval', 300)
                    
                    debug_log("🔄 اجرای به‌روزرسانی خودکار API", "SCHEDULER")
                    
                    # به‌روزرسانی داده‌ها
                    if data_manager:
                        result = data_manager.refresh_api_data()
                        
                        if result:
                            # ارسال رویداد به کلاینت‌ها
                            socketio.emit('data_refreshed', {
                                'status': 'success',
                                'timestamp': datetime.now().isoformat(),
                                'auto': True
                            })
                            
                            # بررسی هشدارها
                            if alert_manager and data_manager.market_data is not None:
                                triggered = alert_manager.check_alerts(data_manager.market_data)
                                if triggered:
                                    socketio.emit('alerts_triggered', {
                                        'alerts': triggered,
                                        'count': len(triggered)
                                    })
                    
                    # sleep
                    time.sleep(refresh_interval)
                else:
                    time.sleep(60)  # اگر خودکار فعال نیست، هر دقیقه بررسی کن
            else:
                time.sleep(60)  # اگر API فعال نیست، هر دقیقه بررسی کن
                
        except Exception as e:
            debug_log(f"❌ خطا در وظیفه زمانبندی شده: {e}", "ERROR")
            time.sleep(60)  # در صورت خطا، ۱ دقیقه صبر کن

def cleanup_scheduler():
    """وظیفه زمانبندی شده برای پاکسازی فایل‌های موقت"""
    while True:
        try:
            time.sleep(CLEANUP_INTERVAL)
            
            debug_log("🧹 اجرای پاکسازی دوره‌ای", "SCHEDULER")
            
            # پاکسازی فایل‌های موقت
            if data_manager:
                data_manager.cleanup_temp_files(days=1)
            
            # پاکسازی کش قدیمی API
            if data_manager and data_manager.api_connector:
                data_manager.api_connector._clean_cache(max_age_hours=24)
            
            # پاکسازی لاگ‌های قدیمی
            clean_old_files(LOGS_DIR, days=30, pattern='.log')
            
            # پاکسازی گزارش‌های قدیمی
            clean_old_files(REPORTS_DIR, days=7, pattern='.xlsx')
            
        except Exception as e:
            debug_log(f"❌ خطا در وظیفه پاکسازی: {e}", "ERROR")

# ============================================================================
# بخش ۱۷: شروع نخ‌های زمانبندی
# ============================================================================

# نخ به‌روزرسانی API
refresh_thread = threading.Thread(target=scheduled_api_refresh, daemon=True)
refresh_thread.start()
debug_log("✅ نخ به‌روزرسانی خودکار API راه‌اندازی شد", "SCHEDULER")

# نخ پاکسازی
cleanup_thread = threading.Thread(target=cleanup_scheduler, daemon=True)
cleanup_thread.start()
debug_log("✅ نخ پاکسازی دوره‌ای راه‌اندازی شد", "SCHEDULER")

# ============================================================================
# بخش ۱۸: اجرای اصلی برنامه
# ============================================================================

if __name__ == '__main__':
    try:
        debug_log(f"🔥 شروع {APP_NAME} نسخه {VERSION}", "INFO")
        debug_log(f"📂 دایرکتوری اصلی: {BASE_DIR}", "INFO")
        debug_log(f"💾 حافظه مصرفی: {get_memory_usage()}", "INFO")
        
        # نمایش آدرس‌های دسترسی
        local_ip = get_local_ip()
        
        debug_log(f"🌐 سرور روی آدرس‌های زیر در دسترس است:", "INFO")
        debug_log(f"   📍 محلی: http://127.0.0.1:{PORT}", "INFO")
        debug_log(f"   📍 شبکه: http://{local_ip}:{PORT}", "INFO")
        debug_log(f"   📍 همه: http://0.0.0.0:{PORT}", "INFO")
        
        # باز کردن مرورگر
        webbrowser.open(f"http://127.0.0.1:{PORT}")
        
        # اجرای برنامه
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=PORT, 
            debug=False, 
            allow_unsafe_werkzeug=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        debug_log("👋 برنامه توسط کاربر متوقف شد", "INFO")
        
    except Exception as e:
        debug_log(f"❌ خطای بحرانی: {e}", "CRITICAL")
        traceback.print_exc()
        
    finally:
        debug_log("📊 آمار نهایی:", "INFO")
        debug_log(f"   - تعداد درخواست‌های API: {data_manager.api_connector.request_count if data_manager.api_connector else 0}", "INFO")
        debug_log(f"   - تعداد تحلیلها: {analyzer.analysis_count}", "INFO")
        debug_log(f"   - تعداد هشدارها: {len(alert_manager.alerts)}", "INFO")
        debug_log(f"👋 خداحافظ!", "INFO")                    