import streamlit as st
import pandas as pd
from datetime import date
import smtplib
import time
from email.mime.text import MIMEText
from email.header import Header
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. 系統設定與常量定義
# ==========================================
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# 定義欄位名稱變數，方便未來變動時一鍵修改
COL_PERMIT_NAME = "許可證名稱"
COL_EXPIRY_DATE = "到期日期"  # 原 index 3
COL_TYPE = "類型"           # 原 index 0
COL_ID = "管制編號"         # 原 index 1
COL_APPLICANT = "申請人"
COL_STATUS = "狀態"
COL_REVIEW_DATE = "核准日期"

# ==========================================
# 2. 數據層 (Data Layer) - 優化快取機制
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=3600)  # 主資料穩定，緩存 1 小時
def load_base_data():
    try:
        main_df = conn.read(worksheet="大豐既有許可證到期提醒")
        file_df = conn.read(worksheet="附件資料庫")
        # 清洗欄位空格
        main_df.columns = [str(c).strip() for c in main_df.columns]
        file_df.columns = [str(c).strip() for c in file_df.columns]
        return main_df, file_df
    except Exception as e:
        st.error(f"讀取基礎資料失敗: {e}")
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=60)  # 申請紀錄較常變動，緩存 1 分鐘
def load_logs():
    try:
        df = conn.read(worksheet="申請紀錄")
        return df.dropna(how='all')
    except:
        return pd.DataFrame(columns=[COL_PERMIT_NAME, COL_APPLICANT, "申請日期", COL_STATUS, COL_REVIEW_DATE])

# ==========================================
# 3. 邏輯層 (Logic Layer)
# ==========================================
def get_real_status(row_date, today):
    if pd.isna(row_date): return "未設定"
    if row_date < today: return "❌ 已過期"
    elif row_date <= today + pd.Timedelta(days=180): return "⚠️ 準備辦理"
    else: return "✅ 有效"

def get_dynamic_status(permit_name, logs_df, today):
    if logs_df.empty: return "未提送"
    my_logs = logs_df[logs_df[COL_PERMIT_NAME] == permit_name]
    if my_logs.empty: return "未提送"
    
    last_log = my_logs.iloc[-1]
    status = str(last_log[COL_STATUS]).strip()
    
    if status == "已核准":
        try:
            app_d = pd.to_datetime(last_log[COL_REVIEW_DATE])
            if (today - app_d).days > 5: return "未提送"
        except: pass
    return status

# ==========================================
# 4. 表現層 (Presentation Layer)
# ==========================================
def main():
    main_df, file_df = load_base_data()
    logs_df = load_logs()
    today = pd.Timestamp(date.today())

    if main_df.empty:
        st.warning("⚠️ 無法獲取雲端資料，請檢查 Google Sheets 連線。")
        return

    # 預處理日期欄位 (使用名稱定位)
    main_df['判斷日期'] = pd.to_datetime(main_df[COL_EXPIRY_DATE], errors='coerce')
    main_df['最新狀態'] = main_df['判斷日期'].apply(lambda x: get_real_status(x, today))

    # --- 📢 跑馬燈 ---
    upcoming = main_df[main_df['最新狀態'].isin(["❌ 已過期", "⚠️ 準備辦理"])]
    if not upcoming.empty:
        marquee_items = [f"{row['最新狀態']}：{row[COL_PERMIT_NAME]} ({str(row[COL_EXPIRY_DATE])[:10]})" for _, row in upcoming.iterrows()]
        marquee_text = " | ".join(marquee_items)
        st.markdown(f'<div style="background-color: #FFF3E0; padding: 10px; border-radius: 5px; border-left: 5px solid #FF9800; overflow: hidden; white-space: nowrap;"><marquee scrollamount="5" style="color: #E65100; font-weight: bold;">{marquee_text}</marquee></div>', unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🌱 大豐環保許可證管理系統</h1>", unsafe_allow_html=True)
    st.write("---")

    # --- 📂 側邊選單 ---
    if st.sidebar.button("🔄 刷新雲端資料", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.sidebar.button("🏠 回到系統首頁", use_container_width=True):
        st.session_state.selected_actions = set()
        st.rerun()
    
    st.sidebar.divider()
    
    # 使用欄位名選取
    types = sorted(main_df[COL_TYPE].dropna().unique())
    sel_type = st.sidebar.selectbox("1. 選擇類型", types)
    
    sub_main = main_df[main_df[COL_TYPE] == sel_type].copy()
    permits = sub_main[COL_PERMIT_NAME].dropna().unique()
    sel_name = st.sidebar.radio("2. 選擇許可證", permits)

    # 獲取目標資訊
    target_main = sub_main[sub_main[COL_PERMIT_NAME] == sel_name].iloc[0]
    permit_id = str(target_main[COL_ID])
    expiry_val = str(target_main[COL_EXPIRY_DATE])
    dynamic_s = get_dynamic_status(sel_name, logs_df, today)

    # 顯示狀態資訊卡
    st.title(f"📄 {sel_name}")
    status_msg = f"🆔 管制編號：{permit_id}　|　📅 到期日期：{expiry_val[:10]}　|　📢 流程進度：【{dynamic_s}】"
    if "已過期" in target_main['最新狀態']: st.error(status_msg)
    elif "準備辦理" in target_main['最新狀態']: st.warning(status_msg)
    else: st.info(status_msg)

    # --- 🛠️ 申請流程 ---
    st.divider()
    db_info = file_df[file_df[COL_TYPE] == sel_type]
    options = db_info.iloc[:, 1].dropna().unique().tolist() # 辦理項目通常在第二欄

    if options:
        st.subheader("🛠️ 第一步：選擇辦理項目 (可多選)")
        if "selected_actions" not in st.session_state: 
            st.session_state.selected_actions = set()
        
        cols = st.columns(len(options))
        for i, option in enumerate(options):
            is_active = option in st.session_state.selected_actions
            if cols[i].button(option, key=f"btn_{option}", use_container_width=True, type="primary" if is_active else "secondary"):
                if is_active: st.session_state.selected_actions.remove(option)
                else: st.session_state.selected_actions.add(option)
                st.rerun()

        if st.session_state.selected_actions:
            st.divider()
            st.markdown("### 📝 第二步：填寫申請資訊")
            c1, c2 = st.columns(2)
            with c1: user_name = st.text_input("👤 申請人姓名", placeholder="請輸入姓名")
            with c2: apply_date = st.date_input("📅 提出申請日期", value=date.today())

            # 附件處理邏輯
            final_attachments = set()
            for action in st.session_state.selected_actions:
                action_row = db_info[db_info.iloc[:, 1] == action]
                if not action_row.empty:
                    atts = action_row.iloc[0, 3:].dropna().tolist()
                    for item in atts: final_attachments.add(str(item).strip())

            st.write("**📋 必備附件清單：**")
            for item in sorted(list(final_attachments)):
                with st.expander(f"📁 {item}", expanded=True):
                    st.file_uploader(f"請上傳檔案 - {item}", key=f"up_{item}")

            # --- 提交申請 ---
            if st.button("🚀 確認提交申請", type="primary", use_container_width=True):
                if not user_name:
                    st.warning("⚠️ 請填寫姓名！")
                else:
                    submit_request(sel_name, user_name, apply_date, list(st.session_state.selected_actions), logs_df)

    # --- 資料總表 ---
    st.write("---")
    with st.expander("📊 查看所有許可證狀態清單"):
        display_df = main_df[[COL_TYPE, COL_ID, COL_PERMIT_NAME, COL_EXPIRY_DATE, '最新狀態']].copy()
        st.dataframe(display_df, use_container_width=True, hide_index=True)

def submit_request(permit_name, user_name, apply_date, actions, current_logs):
    """處理數據寫入與郵件發送的核心邏輯"""
    try:
        with st.spinner("正在提交申請至雲端..."):
            # 1. 寫入 Google Sheets (建議此處未來改用 append 邏輯)
            new_row = pd.DataFrame([{
                COL_PERMIT_NAME: permit_name,
                COL_APPLICANT: user_name,
                "申請日期": apply_date.strftime("%Y-%m-%d"),
                COL_STATUS: "已提送需求",
                COL_REVIEW_DATE: ""
            }])
            updated_logs = pd.concat([current_logs, new_row], ignore_index=True)
            conn.update(worksheet="申請紀錄", data=updated_logs)
            
            # 2. 發送郵件
            send_email(permit_name, user_name, apply_date, actions)
            
            st.balloons()
            st.success("✅ 申請成功！管理員已收到通知。")
            st.session_state.selected_actions = set()
            st.cache_data.clear()
            time.sleep(2)
            st.rerun()
    except Exception as e:
        st.error(f"提交過程中發生錯誤：{e}")

def send_email(permit_name, user_name, apply_date, actions):
    """發送通知信"""
    try:
        subject = f"【許可證申請】{permit_name}_{user_name}"
        body = f"管理員您好，\n\n同仁 {user_name} 已提交申請。\n許可證：{permit_name}\n日期：{apply_date}\n項目：{', '.join(actions)}"
        
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = st.secrets["email"]["sender"]
        msg['To'] = st.secrets["email"]["receiver"]
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(st.secrets["email"]["sender"], st.secrets["email"]["password"])
            server.sendmail(st.secrets["email"]["sender"], [st.secrets["email"]["receiver"]], msg.as_string())
    except Exception as e:
        st.warning(f"紀錄已存，但通知信發送失敗：{e}")

if __name__ == "__main__":
    main()
