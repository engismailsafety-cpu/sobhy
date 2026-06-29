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
import base64
from dotenv import load_dotenv
import re

# تحميل متغيرات البيئة
load_dotenv()

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
    # استخراج الأرقام من المعرفات
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
# 4. إدارة البريد الإلكتروني
# ============================================
def send_email(observation):
    """إرسال البريد الإلكتروني"""
    try:
        # استخدام SMTP (يمكن استبدال بـ EmailJS API)
        sender_email = os.getenv('EMAIL_SENDER', 'hse@master-alaser.com')
        sender_password = os.getenv('EMAIL_PASSWORD', '')
        receiver_email = os.getenv('EMAIL_RECEIVER', 'hse-team@master-alaser.com')

        if not sender_password:
            st.warning("⚠️ لم يتم تكوين البريد الإلكتروني. يرجى إضافة EMAIL_PASSWORD في ملف .env")
            return False

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"📋 ملاحظة HSE جديدة - {observation['tracking_id']}"

        # محتوى البريد الإلكتروني
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
                    <a href="{os.getenv('APP_URL', 'http://localhost:8501')}" style="background: #667eea; color: white; padding: 12px 30px; border-radius: 10px; text-decoration: none; font-weight: 600;">
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
# 6. الواجهة الرئيسية
# ============================================
def main_app():
    """التطبيق الرئيسي بعد تسجيل الدخول"""
    
    # CSS مخصص
    st.markdown("""
        <style>
            .main-header {
                background: rgba(255,255,255,0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 20px;
                padding: 20px 30px;
                margin-bottom: 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
            }
            .main-title {
                color: white;
                font-size: 24px;
                font-weight: 700;
            }
            .main-title span {
                background: linear-gradient(135deg, #ffd700, #f59e0b);
                color: #1a1a3e;
                padding: 4px 15px;
                border-radius: 30px;
                font-size: 13px;
                font-weight: 700;
            }
            .badge-count {
                background: rgba(255,215,0,0.15);
                color: #ffd700;
                padding: 8px 20px;
                border-radius: 30px;
                border: 1px solid rgba(255,215,0,0.2);
                font-weight: 600;
            }
            .card {
                background: rgba(255,255,255,0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 20px;
                padding: 25px;
                margin-bottom: 25px;
            }
            .card-title {
                color: white;
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 15px;
                border-bottom: 3px solid rgba(255,215,0,0.3);
                padding-bottom: 10px;
            }
            .status-badge {
                padding: 4px 12px;
                border-radius: 30px;
                font-size: 12px;
                font-weight: 600;
                display: inline-block;
            }
            .status-new { background: rgba(59,130,246,0.2); color: #60a5fa; border: 1px solid rgba(59,130,246,0.2); }
            .status-review { background: rgba(251,191,36,0.2); color: #fbbf24; border: 1px solid rgba(251,191,36,0.2); }
            .status-progress { background: rgba(251,146,60,0.2); color: #fb923c; border: 1px solid rgba(251,146,60,0.2); }
            .status-closed { background: rgba(52,211,153,0.2); color: #34d399; border: 1px solid rgba(52,211,153,0.2); }
            .severity-low { background: rgba(52,211,153,0.2); color: #34d399; }
            .severity-medium { background: rgba(251,191,36,0.2); color: #fbbf24; }
            .severity-high { background: rgba(251,146,60,0.2); color: #fb923c; }
            .severity-critical { background: rgba(239,68,68,0.2); color: #fca5a5; }
            .tracking-id { color: #ffd700; font-weight: 700; font-size: 14px; }
            .logout-btn {
                background: rgba(239,68,68,0.1);
                border: 2px solid rgba(239,68,68,0.3);
                color: #fca5a5;
                padding: 8px 20px;
                border-radius: 30px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .logout-btn:hover {
                background: rgba(239,68,68,0.2);
                border-color: #ef4444;
            }
            .stButton > button {
                border-radius: 12px;
                font-weight: 600;
            }
            /* تخصيص حقول الإدخال */
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea,
            .stSelectbox > div > div > select {
                background: rgba(255,255,255,0.05) !important;
                border: 2px solid rgba(255,255,255,0.08) !important;
                color: white !important;
                border-radius: 12px !important;
            }
            .stTextInput > div > div > input:focus,
            .stTextArea > div > div > textarea:focus {
                border-color: #ffd700 !important;
                box-shadow: 0 0 0 4px rgba(255,215,0,0.1) !important;
            }
            .stSelectbox > div > div > select option {
                background: #1a1a3e !important;
                color: white !important;
            }
            /* Dataframe */
            .stDataFrame {
                background: rgba(255,255,255,0.03) !important;
                border-radius: 15px !important;
            }
            .stDataFrame table {
                color: white !important;
            }
            .stDataFrame thead tr th {
                color: #ffd700 !important;
                background: rgba(255,215,0,0.05) !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # ==================== HEADER ====================
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="background: linear-gradient(135deg, #ffd700, #f59e0b); width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 28px; color: #1a1a3e; font-weight: 900;">🌪️</div>
                <div>
                    <div class="main-title">🛡️ نظام HSE <span>ماستر الاعاصير</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        col2_1, col2_2 = st.columns([2, 1])
        with col2_1:
            st.markdown(f'<div class="badge-count">📊 الملاحظات: {len(st.session_state.observations)}</div>', unsafe_allow_html=True)
        with col2_2:
            if st.button("🚪 خروج", use_container_width=True):
                st.session_state.authenticated = False
                st.rerun()

    # ==================== إدخال ملاحظة جديدة ====================
    with st.expander("📝 إدخال ملاحظة جديدة", expanded=True):
        with st.container():
            col1, col2 = st.columns(2)
            
            with col1:
                location = st.text_input("📍 موقع الملاحظة *", placeholder="مثال: المصنع - خط الإنتاج 3")
                obs_type = st.selectbox(
                    "⚠️ نوع الملاحظة *",
                    ["", "فعل غير آمن", "حالة غير آمنة", "سلوك إيجابي", "مخالفة تشريعية"]
                )
                severity = st.selectbox(
                    "🔴 شدة المخاطر *",
                    ["", "منخفضة", "متوسطة", "عالية", "حرجة - تدخل فوري"]
                )
            
            with col2:
                obs_date = st.date_input("📅 تاريخ الملاحظة", datetime.now())
                obs_time = st.time_input("🕐 الوقت", datetime.now().time())
                reporter = st.text_input("👤 اسم المبلغ", placeholder="أدخل اسمك")
                department = st.text_input("🏢 القسم", placeholder="مثال: الصيانة، الإنتاج، السلامة")
            
            description = st.text_area(
                "📄 وصف الملاحظة بالتفصيل *",
                placeholder="قم بوصف الملاحظة بشكل دقيق... (مثال: وجود تسرب زيتي بالقرب من المضخة الرئيسية)",
                height=120
            )
            
            action = st.text_area(
                "🔧 الإجراء المقترح",
                placeholder="اقترح الإجراء التصحيحي المناسب...",
                height=80
            )
            
            # رفع الملفات
            uploaded_files = st.file_uploader(
                "📎 رفع ملفات (صور - فيديو - مستندات)",
                type=['png', 'jpg', 'jpeg', 'gif', 'mp4', 'pdf', 'doc', 'docx'],
                accept_multiple_files=True
            )
            
            if uploaded_files:
                file_names = [f"📄 {f.name} ({f.size/1024:.1f} كيلوبايت)" for f in uploaded_files]
                st.info(" | ".join(file_names))

            # زر الإرسال
            if st.button("🚀 إرسال الملاحظة وتوليد رقم تتبع", use_container_width=True, type="primary"):
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
                        
                        # إرسال البريد الإلكتروني
                        if send_email(new_observation):
                            st.info("📧 تم إرسال إشعار عبر البريد الإلكتروني")
                        else:
                            st.warning("⚠️ لم يتم إرسال البريد الإلكتروني (تأكد من الإعدادات)")
                        
                        st.balloons()
                    else:
                        st.error("❌ حدث خطأ في حفظ البيانات")

    # ==================== تتبع الملاحظات ====================
    st.markdown('<div class="card-title">📋 تتبع الملاحظات</div>', unsafe_allow_html=True)
    
    # فلترة
    col1, col2 = st.columns([1, 3])
    with col1:
        filter_status = st.selectbox(
            "🔍 تصفية حسب الحالة",
            ["الكل", "جديدة", "قيد المراجعة", "قيد التنفيذ", "مغلقة"]
        )
    with col2:
        search_term = st.text_input("🔎 بحث برقم التتبع أو الموقع", placeholder="أدخل رقم التتبع أو الموقع...")
    
    # عرض الملاحظات
    observations = st.session_state.observations
    
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
        
        # إضافة أعمدة ملونة
        def get_status_style(status):
            styles = {
                'جديدة': '🆕 جديدة',
                'قيد المراجعة': '🔍 قيد المراجعة',
                'قيد التنفيذ': '⚙️ قيد التنفيذ',
                'مغلقة': '✅ مغلقة'
            }
            return styles.get(status, status)
        
        df_display['الحالة'] = df_display['status'].apply(get_status_style)
        df_display = df_display.drop('status', axis=1)
        
        # إعادة تسمية الأعمدة
        df_display.columns = ['رقم التتبع', 'الموقع', 'النوع', 'الشدة', 'التاريخ', 'الحالة']
        
        # عرض الجدول
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "رقم التتبع": st.column_config.TextColumn("رقم التتبع", width="small"),
                "الموقع": st.column_config.TextColumn("الموقع", width="medium"),
                "النوع": st.column_config.TextColumn("النوع", width="small"),
                "الشدة": st.column_config.TextColumn("الشدة", width="small"),
                "التاريخ": st.column_config.TextColumn("التاريخ", width="medium"),
                "الحالة": st.column_config.TextColumn("الحالة", width="small"),
            }
        )
        
        # ==================== تفاصيل الملاحظة ====================
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
            if st.button("🔄 تحديث الحالة", use_container_width=True):
                for obs in st.session_state.observations:
                    if obs['tracking_id'] == selected_id:
                        obs['status'] = new_status
                        save_observations(st.session_state.observations)
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