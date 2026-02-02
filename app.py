import streamlit as st
import pandas as pd
from datetime import date
import smtplib
import time
from email.mime.text import MIMEText
from email.header import Header
from streamlit_gsheets import GSheetsConnection

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# 2. 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 💡 優化：設定 10 秒快取，避免頻繁讀取導致 Quota Exceeded
@st.cache_data(ttl=10)
def load_all_data():
    main_df = conn.read(worksheet="大豐既有許可證到期提醒")
    file_df = conn.read(worksheet="附件資料庫")
    try:
        logs_df = conn.read(worksheet="申請紀錄")
        logs_df = logs_df.dropna(how='all')
    except:
        logs_df = pd.DataFrame(columns=["許可證名稱", "申請人", "申請日期", "狀態", "核准日期"])
    
    # 清理欄位標題
    main_df.columns = [str(c).strip() for c in main_df.columns]
    file_df.columns = [str(c).strip() for c in file_df.columns]
    return main_df, file_df, logs_df

try:
    # 讀取資料
    main_df, file_df, logs_df = load_all_data()
    today = pd.Timestamp(date.today())

    # --- 判定邏輯 (用於顏色判定) ---
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
        return str(my_logs.iloc[-1]["狀態"]).strip()

    main_df['最新狀態'] = main_df['判斷日期'].apply(get_real_status)

    # --- 📢 跑馬燈 ---
    upcoming = main_df[main_df['最新狀態'].isin(["❌ 已過期", "⚠️ 準備辦理"])]
    if not upcoming.empty:
        marquee_text = " | ".join([f"{row['最新狀態']}：{row.iloc[2]} (到期日: {str(row.iloc[3])[:10]})" for _, row in upcoming.iterrows()])
        st.markdown(f'<div style="background-color: #FFF3E0; padding: 10px; border-radius: 5px; border-left: 5px solid #FF9800; overflow: hidden; white-space: nowrap;"><marquee scrollamount="5" style="color: #E65100; font-weight: bold;">{marquee_text}</marquee></div>', unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🌱 大豐環保許可證管理系統</h1>", unsafe_allow_html=True)
    st.write("---")

    # --- 📂 側邊選單 ---
    st.sidebar.markdown("## 🏠 系統首頁")
    if st.sidebar.button("回到首頁畫面", use_container_width=True):
        st.cache_data.clear() # 💡 點擊回到首頁時強制清空快取，抓取最新資料
        st.rerun()
    
    st.sidebar.divider()
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
    sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())

    # 當前資訊顯示
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

    # --- 申請按鈕 (略，維持原本功能) ---
    if st.button("🚀 提出申請", type="primary"):
        # 寫入邏輯... (此處省略部分重複代碼以保持簡潔，請保留你原本的寫入邏輯)
        # 寫入後記得加上這行來刷新：
        st.cache_data.clear()
        st.rerun()

    # --- 📊 總表部分 (修改為適度快取) ---
    st.write("---")
    with st.expander("📊 查看許可證管理總表", expanded=True):
        # 💡 直接顯示 main_df，移除輔助欄位
        display_df = main_df.drop(columns=['判斷日期', '最新狀態'], errors='ignore')
        st.dataframe(display_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
