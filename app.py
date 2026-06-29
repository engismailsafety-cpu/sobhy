"""
نظام إدارة ملاحظات السلامة HSE - ماستر الاعاصير
Powered by Streamlit
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
# 2. دالة الحصول على المتغيرات البيئية
# ============================================
def get_env(key, default=None):
    """
    الحصول على متغيرات البيئة
    - في Streamlit Cloud: من st.secrets
    - محلياً: من os.environ
    """
    try:
        # محاولة من Streamlit Secrets (للنشر على Streamlit Cloud)
        return st.secrets.get(key, default)
    except:
        # محاولة من os.environ (للتطوير المحلي)
        return os.getenv(key, default)

# ============================================
# 3. إدارة الجلسة
# ============================================
def init_session_state():
    """تهيئة متغيرات الجلسة"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'observations' not in st.session_state:
        st.session_state.observations = load_observations()
    if 'current_id' not in st.session_state:
        st.session_state.current_id = get_next_id()
    if 'page' not in st.session_state:
        st.session_state.page = 'main'

# ============================================
# 4. إدارة البيانات (JSON)
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
        # لا نعرض الخطأ للمستخدم لتجنب تسريب المعلومات
        print(f"خطأ في تحميل البيانات: {e}")
    return []

def save_observations(observations):
    """حفظ الملاحظات في ملف JSON"""
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({'observations': observations}, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"خطأ في حفظ البيانات: {e}")
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
# 5. إدارة البريد الإلكتروني
# ============================================
def send_email(observation):
    """إرسال البريد الإلكتروني"""
    try:
        # الحصول على إعدادات البريد من المتغيرات البيئية
        sender_email = get_env('EMAIL_SENDER', 'hse@master-alaser.com')
        sender_password = get_env('EMAIL_PASSWORD', '')
        receiver_email = get_env('EMAIL_RECEIVER', 'hse-team@master-alaser.com')

        # إذا لم توجد كلمة مرور، لا نحاول الإرسال
        if not sender_password:
            return False

        # إنشاء رسالة البريد
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"📋 ملاحظة HSE جديدة - {observation['tracking_id']}"

        # محتوى البريد الإلكتروني (HTML)
        html_body = f"""
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; background: #f7fafc; padding: 20px; }}
                .container {{ max-width: 600px; margin: auto; background: white; border-radius: 20px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; border-bottom: 3px solid #ffd700; padding-bottom: 20px; margin-bottom: 20px; }}
                .header h1 {{ color: #1a1a3e; }}
                .header p {{ color: #666; }}
                .info-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .info-table td {{ padding: 10px; border-bottom: 1px solid #e2e8f0; }}
                .info-table .label {{ font-weight: bold; }}
                .info-table .value {{ color: #667eea; }}
                .status-badge {{ background: #bee3f8; padding: 5px 15px; border-radius: 30px; color: #2b6cb0; }}
                .footer {{ text-align: center; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 20px; color: #718096; font-size: 12px; }}
                .button {{ background: #667eea; color: white; padding: 12px 30px; border-radius: 10px; text-decoration: none; font-weight: 600; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌪️ ماستر الاعاصير</h1>
                    <p>نظام إدارة ملاحظات السلامة</p>
                </div>
                
                <h2>📋 ملاحظة جديدة</h2>
                
                <table class="info-table">
                    <tr>
                        <td class="label">رقم التتبع:</td>
                        <td class="value">{observation['tracking_id']}</td>
                    </tr>
                    <tr>
                        <td class="label">الموقع:</td>
                        <td>{observation['location']}</td>
                    </tr>
                    <tr>
                        <td class="label">النوع:</td>
                        <td>{observation['type']}</td>
                    </tr>
                    <tr>
                        <td class="label">شدة المخاطر:</td>
                        <td>{observation['severity']}</td>
                    </tr>
                    <tr>
                        <td class="label">الوصف:</td>
                        <td>{observation['description']}</td>
                    </tr>
                    <tr>
                        <td class="label">الإجراء المقترح:</td>
                        <td>{observation.get('action', 'لم يحدد')}</td>
                    </tr>
                    <tr>
                        <td class="label">المبلغ:</td>
                        <td>{observation.get('reporter', 'غير مذكور')}</td>
                    </tr>
                    <tr>
                        <td class="label">القسم:</td>
                        <td>{observation.get('department', 'غير محدد')}</td>
                    </tr>
                    <tr>
                        <td class="label">الحالة:</td>
                        <td><span class="status-badge">{observation['status']}</span></td>
                    </tr>
                </table>
                
                <div style="text-align: center; margin-top: 20px;">
                    <a href="{get_env('APP_URL', 'http://localhost:8501')}" class="button">
                        🔗 عرض الملاحظة في النظام
                    </a>
                </div>
                
                <div class="footer">
                    هذا البريد تم إرساله تلقائياً من نظام HSE - ماستر الاعاصير
                </div>
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
        print(f"❌ فشل إرسال البريد: {e}")
        return False

# ============================================
# 6. شاشة تسجيل الدخول
# ============================================
def login_screen():
    """شاشة تسجيل الدخول"""
    
    # CSS مخصص لشاشة الدخول
    st.markdown("""
        <style>
            .login-container {
                max-width: 420px;
                margin: 60px auto;
                padding: 50px 40px;
                background: linear-gradient(145deg, #0c0e1a 0%, #1a1a3e 50%, #2d1b4e 100%);
                border-radius: 30px;
                border: 1px solid rgba(255,255,255,0.08);
                box-shadow: 0 30px 80px rgba(0,0,0,0.6);
                text-align: center;
            }
            .login-logo {
                font-size: 80px;
                margin-bottom: 5px;
                display: block;
            }
            .login-title {
                color: #ffd700;
                font-size: 34px;
                font-weight: 800;
                text-shadow: 0 0 40px rgba(255,215,0,0.15);
                margin: 5px 0;
            }
            .login-subtitle {
                color: rgba(255,255,255,0.4);
                font-size: 13px;
                letter-spacing: 6px;
                margin-bottom: 25px;
                font-weight: 300;
            }
            .login-sub {
                color: rgba(255,255,255,0.7);
                font-size: 16px;
                font-weight: 300;
                margin-bottom: 30px;
            }
            .login-container .stTextInput > div > div > input {
                background: rgba(255,255,255,0.06) !important;
                border: 2px solid rgba(255,255,255,0.08) !important;
                color: white !important;
                border-radius: 12px !important;
                padding: 12px 16px !important;
                font-size: 15px !important;
            }
            .login-container .stTextInput > div > div > input:focus {
                border-color: #ffd700 !important;
                box-shadow: 0 0 0 4px rgba(255,215,0,0.08) !important;
                background: rgba(255,255,255,0.1) !important;
            }
            .login-container .stTextInput > div > div > input::placeholder {
                color: rgba(255,255,255,0.3) !important;
            }
            .login-container .stButton > button {
                width: 100%;
                background: linear-gradient(135deg, #ffd700 0%, #f59e0b 100%);
                color: #1a1a3e;
                font-weight: 700;
                font-size: 18px;
                padding: 14px;
                border: none;
                border-radius: 12px;
                margin-top: 10px;
                transition: all 0.3s ease;
            }
            .login-container .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 40px rgba(255,215,0,0.25);
            }
            .login-error {
                background: rgba(239,68,68,0.12);
                border: 1px solid rgba(239,68,68,0.2);
                color: #fca5a5;
                padding: 12px;
                border-radius: 12px;
                margin-top: 15px;
                font-size: 14px;
            }
            /* إخفاء label الحقول */
            .login-container .stTextInput label {
                display: none !important;
            }
            /* تنسيق المسافات */
            .login-container .stTextInput {
                margin-bottom: 15px;
            }
        </style>
    """, unsafe_allow_html=True)

    # عرض شاشة الدخول
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div class="login-container">
                    <span class="login-logo">🌪️</span>
                    <div class="login-title">ماستر الاعاصير</div>
                    <div class="login-subtitle">✦ MASTER AL-A'ASER ✦</div>
                    <div class="login-sub">نظام إدارة ملاحظات السلامة</div>
                </div>
            """, unsafe_allow_html=True)
            
            # حقول الدخول
            username = st.text_input(
                "اسم المستخدم",
                placeholder="👤 أدخل اسم المستخدم",
                key="login_user",
                label_visibility="collapsed"
            )
            
            password = st.text_input(
                "كلمة المرور",
                placeholder="🔒 أدخل كلمة المرور",
                type="password",
                key="login_pass",
                label_visibility="collapsed"
            )
            
            # زر الدخول
            if st.button("🚀 دخول", use_container_width=True, key="login_btn"):
                if username == "admin" and password == "1234":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.markdown(
                        '<div class="login-error">❌ اسم المستخدم أو كلمة المرور غير صحيحة</div>',
                        unsafe_allow_html=True
                    )

# ============================================
# 7. الواجهة الرئيسية (بعد تسجيل الدخول)
# ============================================
def main_app():
    """التطبيق الرئيسي بعد تسجيل الدخول"""
    
    # ========== CSS مخصص ==========
    st.markdown("""
        <style>
            /* خلفية الصفحة */
            .stApp {
                background: linear-gradient(135deg, #0c0e1a 0%, #1a1a3e 50%, #2d1b4e 100%);
            }
            
            /* تنسيق البطاقات */
            .main-card {
                background: rgba(255,255,255,0.04);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 20px;
                padding: 25px 30px;
                margin-bottom: 25px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            }
            
            .card-title {
                color: white;
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 20px;
                padding-bottom: 12px;
                border-bottom: 3px solid rgba(255,215,0,0.2);
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            /* الهيدر */
            .app-header {
                background: rgba(255,255,255,0.04);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 20px;
                padding: 18px 25px;
                margin-bottom: 25px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 15px;
            }
            
            .header-left {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .header-logo {
                width: 45px;
                height: 45px;
                border-radius: 50%;
                background: linear-gradient(135deg, #ffd700, #f59e0b);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                font-weight: 900;
                color: #1a1a3e;
                box-shadow: 0 0 30px rgba(255,215,0,0.15);
            }
            
            .header-title {
                color: white;
                font-size: 22px;
                font-weight: 700;
            }
            
            .header-title span {
                background: linear-gradient(135deg, #ffd700, #f59e0b);
                color: #1a1a3e;
                padding: 3px 14px;
                border-radius: 30px;
                font-size: 12px;
                font-weight: 700;
                margin-right: 8px;
            }
            
            .header-right {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .badge-count {
                background: rgba(255,215,0,0.12);
                color: #ffd700;
                padding: 8px 18px;
                border-radius: 30px;
                border: 1px solid rgba(255,215,0,0.15);
                font-weight: 600;
                font-size: 14px;
            }
            
            .logout-btn {
                background: rgba(239,68,68,0.08);
                border: 2px solid rgba(239,68,68,0.15);
                color: #fca5a5;
                padding: 8px 22px;
                border-radius: 30px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 14px;
            }
            .logout-btn:hover {
                background: rgba(239,68,68,0.15);
                border-color: rgba(239,68,68,0.3);
            }
            
            /* تنسيق حقول الإدخال */
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea,
            .stSelectbox > div > div > select,
            .stDateInput > div > div > input,
            .stTimeInput > div > div > input {
                background: rgba(255,255,255,0.04) !important;
                border: 2px solid rgba(255,255,255,0.06) !important;
                color: white !important;
                border-radius: 12px !important;
                padding: 12px 16px !important;
                font-size: 14px !important;
            }
            
            .stTextInput > div > div > input:focus,
            .stTextArea > div > div > textarea:focus,
            .stSelectbox > div > div > select:focus {
                border-color: #ffd700 !important;
                box-shadow: 0 0 0 4px rgba(255,215,0,0.06) !important;
                background: rgba(255,255,255,0.06) !important;
            }
            
            .stTextInput > div > div > input::placeholder,
            .stTextArea > div > div > textarea::placeholder {
                color: rgba(255,255,255,0.25) !important;
            }
            
            .stSelectbox > div > div > select option {
                background: #1a1a3e !important;
                color: white !important;
            }
            
            /* تنسيق الأزرار */
            .stButton > button {
                border-radius: 12px !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
            }
            .stButton > button:hover {
                transform: translateY(-2px) !important;
            }
            
            /* تنسيق الأزرار الرئيسية */
            .btn-primary > button {
                background: linear-gradient(135deg, #ffd700 0%, #f59e0b 100%) !important;
                color: #1a1a3e !important;
                border: none !important;
                padding: 12px 24px !important;
                font-size: 16px !important;
            }
            .btn-primary > button:hover {
                box-shadow: 0 8px 30px rgba(255,215,0,0.2) !important;
            }
            
            /* تنسيق التوسيع */
            .streamlit-expanderHeader {
                background: rgba(255,255,255,0.03) !important;
                border: 1px solid rgba(255,255,255,0.06) !important;
                border-radius: 12px !important;
                color: white !important;
                font-weight: 600 !important;
            }
            .streamlit-expanderHeader:hover {
                background: rgba(255,255,255,0.06) !important;
            }
            .streamlit-expanderContent {
                background: rgba(255,255,255,0.02) !important;
                border-radius: 0 0 12px 12px !important;
                padding: 20px !important;
            }
            
            /* تنسيق المعلومات */
            .stAlert {
                border-radius: 12px !important;
                background: rgba(255,255,255,0.04) !important;
                border: 1px solid rgba(255,255,255,0.06) !important;
                color: rgba(255,255,255,0.8) !important;
            }
            
            /* تنسيق البيانات الجدولية */
            .stDataFrame {
                background: rgba(255,255,255,0.02) !important;
                border-radius: 15px !important;
            }
            .stDataFrame table {
                color: rgba(255,255,255,0.9) !important;
            }
            .stDataFrame thead tr th {
                color: #ffd700 !important;
                background: rgba(255,215,0,0.05) !important;
                font-weight: 600 !important;
            }
            .stDataFrame tbody tr:hover {
                background: rgba(255,255,255,0.03) !important;
            }
            
            /* تنسيق التوست (الإشعارات) */
            .stSuccess {
                background: rgba(52,211,153,0.1) !important;
                border: 1px solid rgba(52,211,153,0.15) !important;
                color: #34d399 !important;
            }
            .stError {
                background: rgba(239,68,68,0.1) !important;
                border: 1px solid rgba(239,68,68,0.15) !important;
                color: #fca5a5 !important;
            }
            .stWarning {
                background: rgba(251,191,36,0.1) !important;
                border: 1px solid rgba(251,191,36,0.15) !important;
                color: #fbbf24 !important;
            }
            .stInfo {
                background: rgba(59,130,246,0.1) !important;
                border: 1px solid rgba(59,130,246,0.15) !important;
                color: #60a5fa !important;
            }
            
            /* تنسيق علامات الحالة */
            .status-tag {
                display: inline-block;
                padding: 4px 14px;
                border-radius: 30px;
                font-size: 12px;
                font-weight: 600;
            }
            .status-new { background: rgba(59,130,246,0.15); color: #60a5fa; border: 1px solid rgba(59,130,246,0.15); }
            .status-review { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.15); }
            .status-progress { background: rgba(251,146,60,0.15); color: #fb923c; border: 1px solid rgba(251,146,60,0.15); }
            .status-closed { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.15); }
            
            /* تنسيق شدة المخاطر */
            .severity-low { background: rgba(52,211,153,0.12); color: #34d399; padding: 3px 12px; border-radius: 30px; font-size: 13px; font-weight: 600; }
            .severity-medium { background: rgba(251,191,36,0.12); color: #fbbf24; padding: 3px 12px; border-radius: 30px; font-size: 13px; font-weight: 600; }
            .severity-high { background: rgba(251,146,60,0.12); color: #fb923c; padding: 3px 12px; border-radius: 30px; font-size: 13px; font-weight: 600; }
            .severity-critical { background: rgba(239,68,68,0.12); color: #fca5a5; padding: 3px 12px; border-radius: 30px; font-size: 13px; font-weight: 600; }
            
            /* تنسيق معرف التتبع */
            .tracking-id {
                color: #ffd700;
                font-weight: 700;
                font-size: 14px;
                font-family: 'Courier New', monospace;
            }
            
            /* تخصيص شريط التمرير */
            ::-webkit-scrollbar { width: 6px; }
            ::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); border-radius: 10px; }
            ::-webkit-scrollbar-thumb { background: rgba(255,215,0,0.2); border-radius: 10px; }
            ::-webkit-scrollbar-thumb:hover { background: rgba(255,215,0,0.3); }
            
            /* تنسيق الأعمدة */
            .stColumns {
                gap: 20px;
            }
            
            /* تنسيق التبويبات */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
            }
            .stTabs [data-baseweb="tab"] {
                background: rgba(255,255,255,0.03);
                border-radius: 12px;
                padding: 8px 20px;
                color: rgba(255,255,255,0.6);
                font-weight: 500;
            }
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background: rgba(255,215,0,0.08);
                color: #ffd700;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # ========== الهيدر ==========
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
            <div class="app-header">
                <div class="header-left">
                    <div class="header-logo">🌪️</div>
                    <div class="header-title">
                        🛡️ نظام HSE <span>ماستر الاعاصير</span>
                    </div>
                </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
                <div class="header-right">
                    <span class="badge-count">📊 <span id="obs-count">""", unsafe_allow_html=True)
        st.write(f"{len(st.session_state.observations)}")
        st.markdown("""</span></span>
                    <button class="logout-btn" onclick="location.href='?logout=true'">🚪 خروج</button>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # معالجة الخروج
    import urllib.parse
    query_params = st.query_params
    if query_params.get('logout') == 'true':
        st.session_state.authenticated = False
        st.query_params.clear()
        st.rerun()
    
    # ========== إدخال ملاحظة جديدة ==========
    with st.expander("📝 إدخال ملاحظة جديدة", expanded=True):
        
        col1, col2 = st.columns(2)
        
        with col1:
            location = st.text_input(
                "📍 موقع الملاحظة *",
                placeholder="مثال: المصنع - خط الإنتاج 3",
                key="location_input"
            )
            obs_type = st.selectbox(
                "⚠️ نوع الملاحظة *",
                ["", "فعل غير آمن", "حالة غير آمنة", "سلوك إيجابي", "مخالفة تشريعية"],
                key="type_input"
            )
            severity = st.selectbox(
                "🔴 شدة المخاطر *",
                ["", "منخفضة", "متوسطة", "عالية", "حرجة - تدخل فوري"],
                key="severity_input"
            )
        
        with col2:
            obs_date = st.date_input(
                "📅 تاريخ الملاحظة",
                datetime.now(),
                key="date_input"
            )
            obs_time = st.time_input(
                "🕐 الوقت",
                datetime.now().time(),
                key="time_input"
            )
            reporter = st.text_input(
                "👤 اسم المبلغ",
                placeholder="أدخل اسمك",
                key="reporter_input"
            )
            department = st.text_input(
                "🏢 القسم",
                placeholder="مثال: الصيانة، الإنتاج، السلامة",
                key="department_input"
            )
        
        description = st.text_area(
            "📄 وصف الملاحظة بالتفصيل *",
            placeholder="قم بوصف الملاحظة بشكل دقيق... (مثال: وجود تسرب زيتي بالقرب من المضخة الرئيسية)",
            height=120,
            key="description_input"
        )
        
        action = st.text_area(
            "🔧 الإجراء المقترح",
            placeholder="اقترح الإجراء التصحيحي المناسب...",
            height=80,
            key="action_input"
        )
        
        # رفع الملفات
        uploaded_files = st.file_uploader(
            "📎 رفع ملفات (صور - فيديو - مستندات)",
            type=['png', 'jpg', 'jpeg', 'gif', 'mp4', 'pdf', 'doc', 'docx'],
            accept_multiple_files=True,
            key="file_uploader"
        )
        
        if uploaded_files:
            file_names = [f"📄 {f.name} ({f.size/1024:.1f} كيلوبايت)" for f in uploaded_files]
            st.info(" | ".join(file_names))
        
        # زر الإرسال
        if st.button("🚀 إرسال الملاحظة وتوليد رقم تتبع", use_container_width=True, key="submit_btn"):
            # التحقق من الحقول المطلوبة
            if not location or not obs_type or not severity or not description:
                st.error("⚠️ الرجاء تعبئة جميع الحقول المطلوبة (*)")
            else:
                # إنشاء الملاحظة
                obs_datetime = datetime.combine(obs_date, obs_time).isoformat()
                
                new_observation = {
                    "tracking_id": generate_tracking_id(),
                    "location": location,
                    "type": obs_type,
                    "severity": severity,
                    "description": description,
                    "action": action,
                    "reporter": reporter,
                    "department": department,
                    "date": obs_datetime,
                    "status": "جديدة",
                    "files": [f.name for f in uploaded_files] if uploaded_files else [],
                    "created_at": datetime.now().isoformat()
                }
                
                # حفظ
                st.session_state.observations.insert(0, new_observation)
                if save_observations(st.session_state.observations):
                    st.success(f"✅ تم إضافة الملاحظة بنجاح! رقم التتبع: {new_observation['tracking_id']}")
                    
                    # إرسال البريد الإلكتروني (محاولة)
                    email_sent = send_email(new_observation)
                    if email_sent:
                        st.info("📧 تم إرسال إشعار عبر البريد الإلكتروني")
                    
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ حدث خطأ في حفظ البيانات")
    
    # ========== تتبع الملاحظات ==========
    st.markdown("""
        <div style="background: rgba(255,255,255,0.04); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.06); border-radius: 20px; padding: 25px 30px; margin-bottom: 25px;">
            <div class="card-title">📋 تتبع الملاحظات</div>
    """, unsafe_allow_html=True)
    
    # فلترة
    col1, col2 = st.columns([1, 3])
    with col1:
        filter_status = st.selectbox(
            "🔍 تصفية حسب الحالة",
            ["الكل", "جديدة", "قيد المراجعة", "قيد التنفيذ", "مغلقة"],
            key="filter_status"
        )
    with col2:
        search_term = st.text_input(
            "🔎 بحث برقم التتبع أو الموقع",
            placeholder="أدخل رقم التتبع أو الموقع...",
            key="search_term"
        )
    
    # عرض الملاحظات
    observations = st.session_state.observations.copy()
    
    # تطبيق الفلترة
    if filter_status != "الكل":
        observations = [o for o in observations if o.get('status') == filter_status]
    
    if search_term:
        term = search_term.lower().strip()
        observations = [
            o for o in observations
            if term in o.get('tracking_id', '').lower()
            or term in o.get('location', '').lower()
            or term in o.get('description', '').lower()
        ]
    
    if not observations:
        st.info("📭 لا توجد ملاحظات لعرضها")
    else:
        # تحويل إلى DataFrame للعرض
        df = pd.DataFrame(observations)
        
        # اختيار الأعمدة للعرض
        display_cols = ['tracking_id', 'location', 'type', 'severity', 'status', 'date']
        df_display = df[display_cols].copy()
        
        # تنسيق التواريخ
        df_display['date'] = df_display['date'].apply(
            lambda x: datetime.fromisoformat(x).strftime('%Y-%m-%d %H:%M') if x else 'غير محدد'
        )
        
        # إضافة أعمدة ملونة للحالة
        def get_status_label(status):
            labels = {
                'جديدة': '🆕 جديدة',
                'قيد المراجعة': '🔍 قيد المراجعة',
                'قيد التنفيذ': '⚙️ قيد التنفيذ',
                'مغلقة': '✅ مغلقة'
            }
            return labels.get(status, status)
        
        df_display['الحالة'] = df_display['status'].apply(get_status_label)
        
        # إعادة تسمية الأعمدة
        df_display.columns = ['رقم التتبع', 'الموقع', 'النوع', 'الشدة', 'الحالة', 'التاريخ', 'الحالة_مع_ايموجي']
        
        # عرض الجدول
        st.dataframe(
            df_display[['رقم التتبع', 'الموقع', 'النوع', 'الشدة', 'التاريخ', 'الحالة_مع_ايموجي']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "رقم التتبع": st.column_config.TextColumn("رقم التتبع", width="small"),
                "الموقع": st.column_config.TextColumn("الموقع", width="medium"),
                "النوع": st.column_config.TextColumn("النوع", width="small"),
                "الشدة": st.column_config.TextColumn("الشدة", width="small"),
                "التاريخ": st.column_config.TextColumn("التاريخ", width="medium"),
                "الحالة_مع_ايموجي": st.column_config.TextColumn("الحالة", width="small"),
            }
        )
        
        # ========== تفاصيل الملاحظة وتحديث الحالة ==========
        st.markdown("---")
        st.markdown("### 🔍 تفاصيل الملاحظة وتحديث الحالة")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_id = st.selectbox(
                "اختر ملاحظة لعرض التفاصيل",
                options=[o['tracking_id'] for o in observations],
                key="select_obs"
            )
        
        with col2:
            new_status = st.selectbox(
                "تغيير الحالة",
                ["جديدة", "قيد المراجعة", "قيد التنفيذ", "مغلقة"],
                key="change_status"
            )
            if st.button("🔄 تحديث الحالة", use_container_width=True, key="update_status_btn"):
                for obs in st.session_state.observations:
                    if obs['tracking_id'] == selected_id:
                        obs['status'] = new_status
                        if save_observations(st.session_state.observations):
                            st.success(f"✅ تم تحديث حالة الملاحظة {selected_id} إلى {new_status}")
                            st.rerun()
                        break
        
        # عرض تفاصيل الملاحظة المختارة
        selected_obs = next((o for o in observations if o['tracking_id'] == selected_id), None)
        if selected_obs:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                    **📌 رقم التتبع:** `{selected_obs['tracking_id']}`  
                    **📍 الموقع:** {selected_obs['location']}  
                    **⚠️ النوع:** {selected_obs['type']}  
                    **🔴 الشدة:** {selected_obs['severity']}  
                    **📅 التاريخ:** {datetime.fromisoformat(selected_obs['date']).strftime('%Y-%m-%d %H:%M') if selected_obs.get('date') else 'غير محدد'}
                """)
            with col2:
                st.markdown(f"""
                    **👤 المبلغ:** {selected_obs.get('reporter', 'غير مذكور')}  
                    **🏢 القسم:** {selected_obs.get('department', 'غير محدد')}  
                    **📎 المرفقات:** {len(selected_obs.get('files', []))} ملف  
                    **🔄 الحالة:** {selected_obs.get('status', 'غير محدد')}
                """)
            
            st.markdown("**📄 الوصف:**")
            st.info(selected_obs['description'])
            
            if selected_obs.get('action'):
                st.markdown("**🔧 الإجراء المقترح:**")
                st.success(selected_obs['action'])
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# 8. التشغيل الرئيسي
# ============================================
def main():
    """الدالة الرئيسية للتطبيق"""
    
    # تهيئة متغيرات الجلسة
    init_session_state()
    
    # التحقق من المصادقة
    if not st.session_state.authenticated:
        login_screen()
    else:
        main_app()

# تشغيل التطبيق
if __name__ == "__main__":
    main()
