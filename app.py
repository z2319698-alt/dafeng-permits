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
APP_PASSWORD = "你的16位應用程式密碼" 
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

    # --- 核心邏輯：判定狀態 ---
    main_df['判斷日期'] = pd.to_datetime(main_df.iloc[:, 3], errors='coerce')
    def get_real_status(row_date):
        if pd.isna(row_date): return "未設定"
        if row_date < today: return "❌ 已過期"
        elif row_date <= today + pd.Timedelta(days=180): return "⚠️ 準備辦理"
        else: return "✅ 有效"
    main_df['最新狀態'] = main_df['判斷日期'].apply(get_real_status)

    # --- 📢 跑馬燈 ---
    upcoming = main_df[main_df['最新狀態'].isin(["❌ 已過期", "⚠️ 準備辦理"])]
    if not upcoming.empty:
        marquee_text = " | ".join([f"{row['最新狀態']}：{row.iloc[2]}" for _, row in upcoming.iterrows()])
        st.markdown(f'<div style="background-color:#FFF3E0;padding:10px;border-left:5px solid #FF9800;"><marquee scrollamount="5" style="color:#E65100;font-weight:bold;">{marquee_text}</marquee></div>', unsafe_allow_html=True)

    # --- 🌟 大標題 ---
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🌱 大豐環保許可證管理系統</h1>", unsafe_allow_html=True)
    st.write("---")

    # --- 3. 側邊選單 (這裡修正了括號錯誤) ---
    st.sidebar.markdown("## 📂 系統導覽")
    type_options = sorted(main_df.iloc[:, 0].dropna().unique())
    sel_type = st.sidebar.selectbox("1. 選擇類型", type_options)
    
    sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
    permit_options = sub_main.iloc[:, 2].dropna().unique()
    sel_name = st.sidebar.radio("2. 選擇許可證", permit_options)

    # --- 4. 許可證資訊呈現 ---
    target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
    permit_id = str(target_main.iloc[1])
    expiry_date = str(target_main.iloc[3])
    current_status = get_real_status(pd.to_datetime(expiry_date, errors='coerce'))
    clean_date = expiry_date[:10] if expiry_date != 'nan' else "未設定"

    st.title(f"📄 {sel_name}")
    if "已過期" in current_status: st.error(f"🆔 管制編號：{permit_id} | 📅 到期：{clean_date} | 📢 狀態：{current_status}")
    elif "準備辦理" in current_status: st.warning(f"🆔 管制編號：{permit_id} | 📅 到期：{clean_date} | 📢 狀態：{current_status}")
    else: st.info(f"🆔 管制編號：{permit_id} | 📅 到期：{clean_date} | 📢 狀態：{current_status}")
    
    st.divider()

    # --- 6. 第一步：橫向按鈕項目 ---
    db_info = file_df[file_df.iloc[:, 0] == sel_type]
    options = db_info.iloc[:, 1].dropna().unique().tolist()

    if options:
        st.subheader("🛠️ 第一步：選擇辦理項目 (可多選)")
        if "selected_actions" not in st.session_state: st.session_state.selected_actions = set()
        cols = st.columns(len(options))
        for i, option in enumerate(options):
            is_active = option in st.session_state.selected_actions
            if cols[i].button(option, key=f"btn_{option}", use_container_width=True, type="primary" if is_active else "secondary"):
                if is_active: st.session_state.selected_actions.remove(option)
                else: st.session_state.selected_actions.add(option)
                st.rerun()

        # --- 7. 第二步：填寫資訊與上傳 ---
        current_list = st.session_state.selected_actions
        if current_list:
            st.divider()
            st.markdown("### 📝 第二步：填寫申請資訊與附件")
            c1, c2 = st.columns(2)
            with c1: user_name = st.text_input("👤 申請人姓名", placeholder="請輸入姓名")
            with c2: apply_date = st.date_input("📅 提出申請日期", value=date.today())

            final_attachments = set()
            for action in current_list:
                action_row = db_info[db_info.iloc[:, 1] == action]
                if not action_row.empty:
                    items = action_row.iloc[0, 3:].dropna().tolist()
                    for item in items: final_attachments.add(str(item).strip())

            st.write("**📋 附件上傳區：**")
            for item in sorted(list(final_attachments)):
                with st.expander(f"📁 {item}", expanded=True):
                    st.file_uploader(f"請上傳檔案 - {item}", key=f"up_{item}")

            # --- 8. 第三步：背景提出申請 ---
            st.divider()
            st.markdown("### 📤 第三步：確認並送出")
            if st.button("🚀 提出申請", type="primary"):
                if not user_name:
                    st.warning("⚠️ 請先填寫姓名！")
                else:
                    with st.spinner('正自動發送信件通知 Andy...'):
                        if send_background_email(user_name, sel_name, current_list, final_attachments):
                            st.success(f"✅ 申請已送出！系統已直接通知 Andy。")
                            st.balloons()
        else:
            st.write("👆 請點擊按鈕選擇辦理項目。")
    
    # --- 📊 9. 底部總表 ---
    st.write("---")
    with st.expander("📊 查看許可證管理總表"):
        final_display = main_df.copy()
        if len(final_display.columns) > 7: final_display.iloc[:, 7] = final_display['最新狀態']
        st.dataframe(final_display.drop(columns=['判斷日期', '最新狀態']), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
