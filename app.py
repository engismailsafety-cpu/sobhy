"""
نظام إدارة ملاحظات السلامة HSE - ماستر الاعاصير
Powered by Streamlit
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import re

# ============================================
# دالة للحصول على المتغيرات البيئية
# ============================================
def get_env(key, default=None):
    """
    الحصول على متغيرات البيئة
    - في Streamlit Cloud: من st.secrets
    - محلياً: من os.environ
    """
    try:
        # محاولة من Streamlit Secrets (للنشر)
        return st.secrets.get(key, default)
    except:
        # محاولة من os.environ (للتطوير المحلي)
        return os.getenv(key, default)

# ============================================
# 1. إعدادات الصفحة
# ============================================
st.set_page_config(
    page_title="نظام HSE - ماستر الاعاصير",
    page_icon="🌪️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# 2. إدارة الجلسة
# ============================================
def init_session_state():
    """تهيئة متغيرات الجلسة"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'observations' not in st.session_state:
        st.session_state.observations = load_observations()
    if 'current_id' not in st.session_state:
        st.session_state.current_id = get_next_id()

# ============================================
# 3. إدارة البيانات (JSON)
# ============================================
DATA_FILE = "data/observations.json"

def load_observations():
    """تحميل الملاحظات من ملف JSON"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('observations', [])
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {e}")
    return []

def save_observations(observations):
    """حفظ الملاحظات في ملف JSON"""
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({'observations': observations}, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"خطأ في حفظ البيانات: {e}")
        return False

def get_next_id():
    """الحصول على الرقم التالي للتتبع"""
    obs = load_observations()
    if not obs:
        return 1
    numbers = []
    for o in obs:
        match = re.search(r'HSE-\d{2}-(\d{4})', o.get('tracking_id', ''))
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers) + 1 if numbers else 1

def generate_tracking_id():
    """توليد رقم تتبع فريد"""
    year = datetime.now().strftime('%y')
    num = str(st.session_state.current_id).zfill(4)
    tracking_id = f"HSE-{year}-{num}"
    st.session_state.current_id += 1
    return tracking_id

# ============================================
# 4. إدارة البريد الإلكتروني (بدون dotenv)
# ============================================
def send_email(observation):
    """إرسال البريد الإلكتروني"""
    try:
        # استخدام الدالة get_env بدلاً من os.getenv مباشرة
        sender_email = get_env('EMAIL_SENDER', 'hse@master-alaser.com')
        sender_password = get_env('EMAIL_PASSWORD', '')
        receiver_email = get_env('EMAIL_RECEIVER', 'hse-team@master-alaser.com')

        if not sender_password:
            st.warning("⚠️ لم يتم تكوين البريد الإلكتروني. يرجى إضافة EMAIL_PASSWORD في متغيرات البيئة")
            return False

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"📋 ملاحظة HSE جديدة - {observation['tracking_id']}"

        # محتوى البريد الإلكتروني (كما هو)
        html_body = f"""
        <html dir="rtl">
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; background: #f7fafc; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; border-radius: 20px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="text-align: center; border-bottom: 3px solid #ffd700; padding-bottom: 20px; margin-bottom: 20px;">
                    <h1 style="color: #1a1a3e;">🌪️ ماستر الاعاصير</h1>
                    <p style="color: #666;">نظام إدارة ملاحظات السلامة</p>
                </div>
                
                <h2 style="color: #2d3748;">📋 ملاحظة جديدة</h2>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;"><strong>رقم التتبع:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; color: #667eea;">{observation['tracking_id']}</td></tr>
                    <tr><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;"><strong>الموقع:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{observation['location']}</td></tr>
                    <tr><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;"><strong>النوع:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{observation['type']}</td></tr>
                    <tr><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;"><strong>شدة المخاطر:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{observation['severity']}</td></tr>
                    <tr><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;"><strong>الوصف:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{observation['description']}</td></tr>
                    <tr><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;"><strong>الإجراء المقترح:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{observation.get('action', 'لم يحدد')}</td></tr>
                    <tr><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;"><strong>المبلغ:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{observation.get('reporter', 'غير مذكور')}</td></tr>
                    <tr><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;"><strong>القسم:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{observation.get('department', 'غير محدد')}</td></tr>
                    <tr><td style="padding: 10px;"><strong>الحالة:</strong></td>
                        <td style="padding: 10px;"><span style="background: #bee3f8; padding: 5px 15px; border-radius: 30px; color: #2b6cb0;">{observation['status']}</span></td></tr>
                </table>
                
                <div style="background: #f7fafc; padding: 15px; border-radius: 10px; margin-top: 20px; text-align: center;">
                    <a href="{get_env('APP_URL', 'http://localhost:8501')}" style="background: #667eea; color: white; padding: 12px 30px; border-radius: 10px; text-decoration: none; font-weight: 600;">
                        🔗 عرض الملاحظة في النظام
                    </a>
                </div>
                
                <p style="color: #718096; font-size: 12px; text-align: center; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 20px;">
                    هذا البريد تم إرساله تلقائياً من نظام HSE - ماستر الاعاصير
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        # إرسال البريد
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        st.error(f"❌ فشل إرسال البريد: {e}")
        return False

# ============================================
# 5. دوال تسجيل الدخول
# ============================================
def login():
    """شاشة تسجيل الدخول"""
    st.markdown("""
        <style>
            .login-container {
                max-width: 400px;
                margin: auto;
                padding: 40px;
                background: linear-gradient(135deg, #0c0e1a 0%, #1a1a3e 50%, #2d1b4e 100%);
                border-radius: 30px;
                border: 1px solid rgba(255,255,255,0.1);
                box-shadow: 0 30px 80px rgba(0,0,0,0.6);
                text-align: center;
            }
            .login-logo {
                font-size: 70px;
                margin-bottom: 10px;
            }
            .login-title {
                color: #ffd700;
                font-size: 32px;
                font-weight: 800;
                text-shadow: 0 0 30px rgba(255,215,0,0.2);
            }
            .login-subtitle {
                color: rgba(255,255,255,0.6);
                font-size: 14px;
                letter-spacing: 4px;
                margin-bottom: 30px;
            }
            .stButton > button {
                width: 100%;
                background: linear-gradient(135deg, #ffd700 0%, #f59e0b 100%);
                color: #1a1a3e;
                font-weight: 700;
                font-size: 18px;
                padding: 12px;
                border: none;
                border-radius: 15px;
            }
            .stButton > button:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 40px rgba(255,215,0,0.3);
            }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div class="login-container">
                    <div class="login-logo">🌪️</div>
                    <div class="login-title">ماستر الاعاصير</div>
                    <div class="login-subtitle">✦ MASTER AL-A'ASER ✦</div>
                    <h3 style="color: white; font-weight: 300; margin-bottom: 20px;">نظام إدارة ملاحظات السلامة</h3>
                </div>
            """, unsafe_allow_html=True)

            username = st.text_input("👤 اسم المستخدم", placeholder="admin", key="login_user")
            password = st.text_input("🔒 كلمة المرور", placeholder="••••••••", type="password", key="login_pass")

            if st.button("🚀 دخول", use_container_width=True):
                if username == "admin" and password == "1234":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")

# ============================================
# 6. الواجهة الرئيسية (نفس الكود السابق)
# ============================================
def main_app():
    """التطبيق الرئيسي بعد تسجيل الدخول"""
    # ... (نفس الكود السابق)
    # لتوفير المساحة، يتم وضع نفس الكود السابق هنا
    st.success("✅ تم تسجيل الدخول بنجاح! جاري تحميل النظام...")
    # ... باقي الكود

# ============================================
# 7. التشغيل الرئيسي
# ============================================
def main():
    """الدالة الرئيسية"""
    init_session_state()
    
    if not st.session_state.authenticated:
        login()
    else:
        main_app()

if __name__ == "__main__":
    main()
