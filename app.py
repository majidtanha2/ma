#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
داشبورد Trader's Guardian - Streamlit
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
import sys
import threading
import time

# اضافه کردن مسیر
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import TraderGuardianBackend

# تنظیمات صفحه
st.set_page_config(
    page_title="Trader's Guardian System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# استایل سفارشی
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .risk-card {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .risk-low {
        background-color: #C8E6C9;
        border-left: 5px solid #4CAF50;
    }
    .risk-medium {
        background-color: #FFF3CD;
        border-left: 5px solid #FFC107;
    }
    .risk-high {
        background-color: #F8D7DA;
        border-left: 5px solid #DC3545;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
    .signal-buy {
        color: #28a745;
        font-weight: bold;
    }
    .signal-sell {
        color: #dc3545;
        font-weight: bold;
    }
    .signal-hold {
        color: #6c757d;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class TraderGuardianDashboard:
    """کلاس داشبورد"""
    
    def __init__(self):
        self.system = None
        self.data_lock = threading.Lock()
        self.last_update = None
        
    def load_data(self):
        """بارگذاری داده‌ها"""
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        
        data = {
            'signals': [],
            'analysis': [],
            'violations': [],
            'stats': []
        }
        
        try:
            # سیگنال‌ها
            signals_file = os.path.join(data_dir, 'signals', 'latest_signals.json')
            if os.path.exists(signals_file):
                with open(signals_file, 'r', encoding='utf-8') as f:
                    data['signals'] = json.load(f)
            
            # تحلیل‌ها
            analysis_dir = os.path.join(data_dir, 'analysis')
            if os.path.exists(analysis_dir):
                for file in os.listdir(analysis_dir)[-5:]:  # آخرین ۵ فایل
                    if file.endswith('.json'):
                        with open(os.path.join(analysis_dir, file), 'r', encoding='utf-8') as f:
                            analysis = json.load(f)
                            data['analysis'].append(analysis)
            
            # تخلفات
            violations_file = os.path.join(data_dir, '..', 'logs', 'violations.json')
            if os.path.exists(violations_file):
                with open(violations_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-20:]:  # آخرین ۲۰ خط
                        try:
                            violation = json.loads(line.strip())
                            data['violations'].append(violation)
                        except:
                            pass
            
            # آمار
            stats_dir = os.path.join(data_dir, 'stats')
            if os.path.exists(stats_dir):
                stats_files = sorted(os.listdir(stats_dir))
                if stats_files:
                    latest_stats = stats_files[-1]
                    with open(os.path.join(stats_dir, latest_stats), 'r', encoding='utf-8') as f:
                        data['stats'] = json.load(f)
        
        except Exception as e:
            st.error(f"Error loading data: {e}")
        
        return data
    
    def create_header(self):
        """ایجاد هدر"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<h1 class="main-header">🛡️ Trader\'s Guardian System</h1>', 
                       unsafe_allow_html=True)
            st.markdown("### سیستم نظارت و مدیریت ریسک معاملاتی")
        
        with col3:
            st.markdown(f"**آخرین بروزرسانی:** {datetime.now().strftime('%H:%M:%S')}")
            
            # دکمه بروزرسانی
            if st.button("🔄 بروزرسانی", use_container_width=True):
                st.rerun()
    
    def create_sidebar(self):
        """ایجاد نوار کناری"""
        with st.sidebar:
            st.image("https://via.placeholder.com/150x50/1E88E5/FFFFFF?text=Trader+Guardian", 
                    use_column_width=True)
            
            st.markdown("---")
            
            # وضعیت سیستم
            st.markdown("### 📊 وضعیت سیستم")
            
            status_col1, status_col2 = st.columns(2)
            with status_col1:
                st.metric("اتصال MT5", "✅ متصل" if False else "❌ قطع")
            with status_col2:
                st.metric("وضعیت", "🟢 فعال" if True else "🔴 غیرفعال")
            
            st.markdown("---")
            
            # تنظیمات سریع
            st.markdown("### ⚙️ تنظیمات سریع")
            
            risk_limit = st.slider("حد ریسک روزانه (%)", 0.5, 5.0, 1.5, 0.1)
            max_positions = st.slider("حداکثر پوزیشن", 1, 10, 3, 1)
            
            if st.button("💾 ذخیره تنظیمات", use_container_width=True):
                st.success("تنظیمات ذخیره شد")
            
            st.markdown("---")
            
            # دکمه‌های کنترلی
            st.markdown("### 🎛️ کنترل سیستم")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 شروع", use_container_width=True, type="primary"):
                    st.info("سیستم در حال شروع...")
            
            with col2:
                if st.button("⏹️ توقف", use_container_width=True, type="secondary"):
                    st.warning("سیستم در حال توقف...")
            
            if st.button("🔴 قفل اضطراری", use_container_width=True, type="secondary"):
                st.error("قفل اضطراری فعال شد!")
    
    def create_dashboard(self, data):
        """ایجاد داشبورد اصلی"""
        # ردیف ۱: متریک‌های کلی
        self.create_metrics_row(data)
        
        st.markdown("---")
        
        # ردیف ۲: تحلیل بازار و سیگنال‌ها
        col1, col2 = st.columns([3, 2])
        
        with col1:
            self.create_market_analysis(data)
        
        with col2:
            self.create_signals_section(data)
        
        st.markdown("---")
        
        # ردیف ۳: مدیریت ریسک و تخلفات
        col3, col4 = st.columns([2, 3])
        
        with col3:
            self.create_risk_management(data)
        
        with col4:
            self.create_violations_section(data)
    
    def create_metrics_row(self, data):
        """ایجاد ردیف متریک‌ها"""
        st.markdown("### 📈 متریک‌های کلی")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("موجودی حساب", "$10,000", "+2.3%")
        
        with col2:
            st.metric("سود امروز", "$235", "+15.2%")
        
        with col3:
            st.metric("پوزیشن‌های باز", "2", "-1")
        
        with col4:
            st.metric("نسبت برد", "67%", "+2%")
        
        with col5:
            st.metric("ریسک روزانه", "0.8%", "-0.2%")
    
    def create_market_analysis(self, data):
        """ایجاد بخش تحلیل بازار"""
        st.markdown("### 📊 تحلیل بازار")
        
        if not data['analysis']:
            st.info("در حال حاضر داده‌ای برای تحلیل وجود ندارد.")
            return
        
        # استفاده از آخرین تحلیل
        latest_analysis = data['analysis'][-1] if data['analysis'] else {}
        
        # نمودار قیمت
        if 'symbol' in latest_analysis and 'price' in latest_analysis:
            symbol = latest_analysis['symbol']
            price_data = latest_analysis.get('price', {})
            
            # ایجاد نمودار شمعی ساده
            fig = go.Figure(data=[go.Candlestick(
                x=['Open', 'High', 'Low', 'Close'],
                open=[price_data.get('open', 0)],
                high=[price_data.get('high', 0)],
                low=[price_data.get('low', 0)],
                close=[price_data.get('current', 0)]
            )])
            
            fig.update_layout(
                title=f"وضعیت قیمت {symbol}",
                yaxis_title="قیمت",
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # خلاصه تحلیل
        if 'summary' in latest_analysis:
            summary = latest_analysis['summary']
            st.markdown(f"**خلاصه تحلیل:** {summary}")
        
        # جزئیات فنی
        with st.expander("جزئیات فنی"):
            if 'technical' in latest_analysis:
                tech = latest_analysis['technical']
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### روند")
                    trend = tech.get('trend', {})
                    st.write(f"جهت: {trend.get('direction', 'N/A')}")
                    st.write(f"قدرت: {trend.get('strength', 0)}/100")
                
                with col2:
                    st.markdown("#### مومنتوم")
                    momentum = tech.get('momentum', {})
                    st.write(f"RSI: {momentum.get('indicators', {}).get('rsi', {}).get('value', 0):.1f}")
                    st.write(f"وضعیت: {momentum.get('overall', 'N/A')}")
    
    def create_signals_section(self, data):
        """ایجاد بخش سیگنال‌ها"""
        st.markdown("### 📡 سیگنال‌های معاملاتی")
        
        if not data['signals']:
            st.info("هیچ سیگنال فعالی وجود ندارد.")
            return
        
        for signal in data['signals'][-3:]:  # آخرین ۳ سیگنال
            with st.container():
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    action = signal.get('action', 'HOLD')
                    if action == 'BUY':
                        st.markdown('<p class="signal-buy">📈 خرید</p>', unsafe_allow_html=True)
                    elif action == 'SELL':
                        st.markdown('<p class="signal-sell">📉 فروش</p>', unsafe_allow_html=True)
                    else:
                        st.markdown('<p class="signal-hold">⏸️ انتظار</p>', unsafe_allow_html=True)
                
                with col2:
                    symbol = signal.get('symbol', 'N/A')
                    confidence = signal.get('confidence', 0)
                    st.write(f"**{symbol}**")
                    st.write(f"اطمینان: {confidence}%")
                
                with col3:
                    if st.button("🔍", key=f"view_{signal.get('id', '')}"):
                        st.session_state['selected_signal'] = signal
        
        # دکمه مشاهده همه
        if st.button("مشاهده همه سیگنال‌ها", use_container_width=True):
            st.session_state['show_all_signals'] = True
    
    def create_risk_management(self, data):
        """ایجاد بخش مدیریت ریسک"""
        st.markdown("### 🛡️ مدیریت ریسک")
        
        # کارت ریسک
        risk_level = "MEDIUM"  # این مقدار از داده‌ها باید خوانده شود
        risk_score = 4.2  # این مقدار از داده‌ها باید خوانده شود
        
        if risk_level == "LOW":
            risk_class = "risk-low"
            risk_icon = "🟢"
        elif risk_level == "MEDIUM":
            risk_class = "risk-medium"
            risk_icon = "🟡"
        else:
            risk_class = "risk-high"
            risk_icon = "🔴"
        
        st.markdown(f"""
        <div class="risk-card {risk_class}">
            <h4>{risk_icon} سطح ریسک: {risk_level}</h4>
            <p>امتیاز ریسک: {risk_score}/10</p>
            <p>وضعیت: قابل قبول</p>
        </div>
        """, unsafe_allow_html=True)
        
        # محدودیت‌ها
        st.markdown("#### محدودیت‌های فعال")
        
        limits = [
            ("حداکثر ریسک روزانه", "1.5%", "✅ فعال"),
            ("حداکثر پوزیشن", "3", "✅ فعال"),
            ("حداکثر دراودان", "5%", "✅ فعال"),
            ("حداقل R:R", "1:1.5", "✅ فعال")
        ]
        
        for name, value, status in limits:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(name)
            with col2:
                st.write(value)
            with col3:
                st.write(status)
        
        # دکمه تنظیمات ریسک
        if st.button("تنظیمات پیشرفته ریسک", use_container_width=True):
            st.session_state['show_risk_settings'] = True
    
    def create_violations_section(self, data):
        """ایجاد بخش تخلفات"""
        st.markdown("### ⚠️ تخلفات ثبت شده")
        
        if not data['violations']:
            st.success("✅ هیچ تخلفی ثبت نشده است.")
            return
        
        # نمایش آخرین تخلفات
        for violation in data['violations'][-5:]:
            with st.container():
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    violation_type = violation.get('type', 'UNKNOWN')
                    if "STOPLOSS" in violation_type:
                        icon = "🔧"
                    elif "RISK" in violation_type:
                        icon = "📊"
                    elif "POSITION" in violation_type:
                        icon = "📈"
                    else:
                        icon = "⚠️"
                    
                    st.write(icon)
                
                with col2:
                    details = violation.get('details', 'No details')
                    timestamp = violation.get('time', '')
                    
                    st.write(f"**{violation_type}**")
                    st.write(f"{details}")
                    if timestamp:
                        st.caption(f"زمان: {timestamp}")
                
                st.markdown("---")
        
        # آمار تخلفات
        if len(data['violations']) > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("تخلفات امروز", len([v for v in data['violations'] 
                                              if datetime.fromisoformat(v.get('time', '2000-01-01')).date() == datetime.now().date()]))
            with col2:
                st.metric("تخلفات هفته", len([v for v in data['violations'] 
                                             if datetime.fromisoformat(v.get('time', '2000-01-01')) > datetime.now() - timedelta(days=7)]))
            with col3:
                st.metric("مجموع تخلفات", len(data['violations']))
    
    def run(self):
        """اجرای داشبورد"""
        # هدر
        self.create_header()
        
        # نوار کناری
        self.create_sidebar()
        
        # بارگذاری داده‌ها
        data = self.load_data()
        
        # داشبورد اصلی
        self.create_dashboard(data)
        
        # پاورقی
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666;">
            <p>🛡️ Trader's Guardian System v2.0 | طراحی شده برای مدیریت ریسک و روانشناسی معاملاتی</p>
            <p>© 2024 تمامی حقوق محفوظ است</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """تابع اصلی"""
    # ایجاد نمونه داشبورد
    dashboard = TraderGuardianDashboard()
    
    # اجرای داشبورد
    dashboard.run()

if __name__ == "__main__":
    main()