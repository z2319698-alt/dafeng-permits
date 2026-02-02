import streamlit as st
import pandas as pd
from datetime import date
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ==========================================
# 🔑 安全設定：請在此填入你的發信帳號資訊
# ==========================================
SENDER_EMAIL = "你的發信信箱@gmail.com" 
APP_PASSWORD = "你的16位應用程式密碼"  # 需去 Google 帳戶申請「應用程式密碼」
RECEIVER_EMAIL = "andy.chen@df-recycle.com"

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# 2. 資料來源
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=5)
def load_all_data():
    main_df = pd.read_excel(URL, sheet_name="大豐既有許可證到期提醒")
    file_df = pd.read_excel(URL, sheet_name="附件資料庫")
    main_df.columns = [str(c).strip() for c in main_df.columns]
    file_df.columns = [str(c).strip() for c in file_df.columns]
    return main_df, file_df

# --- 🚀 背景自動寄信功能 ---
def send_background_email(user_name, sel_name, current_list, attachments):
    subject = f"【系統通知】許可證申請：{sel_name} - {user_name}"
    body = f"""
    Andy 您好，

    同仁 {user_name} 已於 {date.today()} 在管理系統提交申請。

    【許可證名稱】：{sel_name}
    【辦理項目】：{', '.join(current_list)}
    【應繳附件清單】：
    {chr(10).join(['- ' + a for a in attachments])}

    ※ 同仁已在系統上傳附件，請至雲端或後台確認。
    """
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())
        return True
    except Exception as e:
        st.error(f"📧 郵件發送失敗：{e}")
        return False

try:
    main_df, file_df = load_all_data()
    today = pd.Timestamp(date.today())

    # --- 核心邏輯：判定狀態 (同步 Excel 公式邏輯) ---
    main_df['判斷日期'] = pd.to_datetime(main_df.iloc[:, 3], errors='coerce')
    def get_real_status(row_date):
        if pd.isna(row_date): return "未設定"
        if row_date < today: return "❌ 已過期"
        elif row_date <= today + pd.Timedelta(days=180): return "⚠️ 準備辦理"
        else: return "✅ 有效"
    main_df['最新狀態'] = main_df['判斷日期'].apply(get_real_status)

    # --- 📢 跑馬燈 (置頂) ---
    upcoming = main_df[main_df['最新狀態'].isin(["❌ 已過期", "⚠️ 準備辦理"])]
    if not upcoming.empty:
        marquee_text = " | ".join([f"{row['最新狀態']}：{row.iloc[2]}" for _, row in upcoming.iterrows()])
        st.markdown(f'<div style="background-color:#FFF3E0;padding:10px;border-left:5px solid #FF9800;"><marquee scrollamount="5" style="color:#E65100;font-weight:bold;">{marquee_text}</marquee></div>', unsafe_allow_html=True)

    # --- 🌟 大標題 ---
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🌱 大豐環保許可證管理系統</h1>", unsafe_allow_html=True)
    st.write("---")

    # --- 3. 側邊選單 ---
    st.sidebar.markdown("## 📂 系統導覽")
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0
