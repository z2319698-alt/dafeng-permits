import streamlit as st
import pandas as pd
from datetime import date
import urllib.parse
import smtplib
import time  # 💡 為了讓彩帶飛一下
from email.mime.text import MIMEText
from email.header import Header
from streamlit_gsheets import GSheetsConnection

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# 2. 資料來源
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_all_data():
    main_df = conn.read(worksheet="大豐既有許可證到期提醒")
    file_df = conn.read(worksheet="附件資料庫")
    try:
        # 讀取現有紀錄，並清除全空行
        logs_df = conn.read(worksheet="申請紀錄")
        logs_df = logs_df.dropna(how='all')
    except:
        logs_df = pd.DataFrame(columns=["許可證名稱", "申請人", "申請日期", "狀態", "核准日期"])
    
    main_df.columns = [str(c).strip() for c in main_df.columns]
    file_df.columns = [str(c).strip() for c in file_df.columns]
    return main_df, file_df, logs_df

# --- 自動發信函式 ---
def send_auto_email(subject, body):
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = st.secrets["email"]["sender"]
        msg['To'] = st.secrets["email"]["receiver"]
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(st.secrets["email"]["sender"], st.secrets["email"]["password"])
            server.sendmail(st.secrets["email"]["sender"], [st.secrets["email"]["receiver"]], msg.as_string())
        return True
    except Exception as e:
        st.error(f"❌ 郵件發送失敗：{e}")
        return False

try:
    main_df, file_df, logs_df = load_all_data()
    today = pd.Timestamp(date.today())

    # --- 核心判定邏輯 ---
    main_df['判斷日期'] = pd.to_datetime(main_df.iloc[:, 3], errors='coerce')
    def get_real_status(row_date):
        if pd.isna(row_date): return "未設定"
        if row_date < today: return "❌ 已過期"
        elif row_date <= today + pd.Timedelta(days=180): return "⚠️ 準備辦理"
        else: return "✅ 有效"

    def get_dynamic_status(permit_name):
        if logs_df.empty: return "未提送"
        my_logs = logs_df[logs_df["許可證名稱"] == permit_name]
        if my_logs.empty: return "未提送"
        last_log = my_logs.iloc[-1]
        s = str(last_log["狀態"]).strip()
        if s == "已核准":
            try:
                app_d = pd.to_datetime(last_log["核准日期"])
                if (today - app_d).days > 5: return "未提送"
            except: pass
        return s

    main_df['最新狀態'] = main_df['判斷日期'].apply(get_real_status)

    # --- 📢 跑馬燈功能 ---
    upcoming = main_df[main_df['最新狀態'].isin(["❌ 已過期", "⚠️ 準備辦理"])]
    if not upcoming.empty:
        marquee_text = " | ".join([f"{row['最新狀態']}：{row.iloc[2]} (到期日: {str(row.iloc[3])[:10]})" for _, row in upcoming.iterrows()])
        st.markdown(f'<div style="background-color: #FFF3E0; padding: 10px; border-radius: 5px; border-left: 5px solid #FF9800; overflow: hidden; white-space: nowrap;"><marquee scrollamount="5" style="color: #E65100; font-weight: bold;">{marquee_text}</marquee></div>', unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🌱 大豐環保許可證管理系統</h1>", unsafe_allow_html=True)
    st.write("---")

    st.sidebar.markdown("## 🏠 系統首頁")
    if st.sidebar.button("回到首頁畫面", use_container_width=True):
        st.session_state.selected_actions = set()
        st.rerun()
    
    st.sidebar.divider()
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
    sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())

    target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
    permit_id = str(target_main.iloc[1])
    expiry_date = str(target_main.iloc[3])
    current_status = get_real_status(pd.to_datetime(expiry_date, errors='coerce'))
    dynamic_s = get_dynamic_status(sel_name)
    clean_date = expiry_date[:10] if expiry_date != 'nan' else "未設定"

    st.title(f"📄 {sel_name}")
    status_msg = f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}　|　📢 目前狀態：【{dynamic_s}】"
    if "已過期" in current_status: st.error(status_msg)
    elif "準備辦理" in current_status: st.warning(status_msg)
    else: st.info(status_msg)
    st.divider()

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
                    att_list = action_row.iloc[0, 3:].dropna().tolist()
                    for item in att_list: final_attachments.add(str(item).strip())

            st.write("**📋 附件上傳區：**")
            for item in sorted(list(final_attachments)):
                with st.expander(f"📁 {item}", expanded=True): st.file_uploader(f"請上傳檔案 - {item}", key=f"up_{item}")

            st.divider()
            if st.button("🚀 提出申請", type="primary"):
                if not user_name:
                    st.warning("⚠️ 請填寫姓名！")
                else:
                    # 💡 A. 寫入 Excel (修正：將新資料與舊資料合併後一起寫回)
                    new_log = pd.DataFrame([{
                        "許可證名稱": sel_name,
                        "申請人": user_name,
                        "申請日期": date.today().strftime("%Y-%m-%d"),
                        "狀態": "已提送需求",
                        "核准日期": ""
                    }])
                    # 確保將新紀錄「接在」舊紀錄後面
                    updated_logs = pd.concat([logs_df, new_log], ignore_index=True)
                    conn.update(worksheet="申請紀錄", data=updated_logs)
                    
                    # B. 自動發信
                    subject = f"【許可證申請】{sel_name}_{user_name}_{apply_date}"
                    body = f"Andy 您好，\n\n同仁 {user_name} 已於 {apply_date} 提交申請。\n許可證：{sel_name}\n辦理項目：{', '.join(current_list)}\n\n附件請至系統查看。"
                    
                    if send_auto_email(subject, body):
                        st.balloons() # 💡 先噴彩帶
                        st.success("✅ 申請紀錄已更新，並已自動發信給 Andy！")
                        time.sleep(2) # 💡 暫停兩秒讓彩帶飛完
                        st.session_state.selected_actions = set()
                        st.rerun()
        else:
            st.write("👆 請點擊上方橫向按鈕選擇辦理項目。")
    
    st.write("---")
    with st.expander("📊 查看許可證管理總表"):
        final_display = main_df.copy()
        if len(final_display.columns) > 7: final_display.iloc[:, 7] = final_display['最新狀態']
        final_display = final_display.drop(columns=['判斷日期', '最新狀態'])
        st.dataframe(final_display, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
