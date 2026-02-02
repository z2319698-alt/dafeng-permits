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

# 💡 修正讀取邏輯：設定 TTL=10 避免 API 爆炸，同時確保資料完整性
@st.cache_data(ttl=10)
def load_all_data():
    # 讀取主表
    main_df = conn.read(worksheet="大豐既有許可證到期提醒")
    # 讀取附件資料庫 (這就是包含「變更展延」那一列的地方)
    file_df = conn.read(worksheet="附件資料庫")
    
    try:
        logs_df = conn.read(worksheet="申請紀錄")
    except:
        logs_df = pd.DataFrame(columns=["許可證名稱", "申請人", "申請日期", "狀態", "核准日期"])
    
    # 清理欄位標題空格，避免因為空格找不到資料
    main_df.columns = [str(c).strip() for c in main_df.columns]
    file_df.columns = [str(c).strip() for c in file_df.columns]
    
    return main_df, file_df, logs_df

try:
    # 載入資料
    main_df, file_df, logs_df = load_all_data()
    today = pd.Timestamp(date.today())

    # --- 核心判定邏輯 ---
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
        marquee_text = " | ".join([f"{row['最新狀態']}：{row.iloc[2]} (到期日: {str(row.iloc[3])[:10]})" for _, row in upcoming.iterrows()])
        st.markdown(f'<div style="background-color: #FFF3E0; padding: 10px; border-radius: 5px; border-left: 5px solid #FF9800; overflow: hidden; white-space: nowrap;"><marquee scrollamount="5" style="color: #E65100; font-weight: bold;">{marquee_text}</marquee></div>', unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🌱 大豐環保許可證管理系統</h1>", unsafe_allow_html=True)
    st.write("---")

    # --- 📂 側邊選單 ---
    st.sidebar.markdown("## 🏠 系統選頁")
    if st.sidebar.button("🔄 刷新資料 (解決總表不動)", use_container_width=True):
        st.cache_data.clear() # 💡 這裡會清空快取，強迫去抓 Excel 最新的狀態
        st.rerun()
    
    st.sidebar.divider()
    # 這裡確保類型選擇是正確的
    all_types = sorted(main_df.iloc[:, 0].dropna().unique())
    sel_type = st.sidebar.selectbox("1. 選擇類型", all_types)
    
    sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())

    # --- 顯示目前狀態 ---
    target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
    permit_id = str(target_main.iloc[1])
    expiry_date = str(target_main.iloc[3])
    
    # 💡 修正：目前狀態直接顯示 Excel 第一頁的內容 (連動你說的那張圖)
    # 假設「目前狀態」是在 Excel 的第 6 個欄位 (索引 5)
    excel_status = str(target_main.iloc[5]) if len(target_main) > 5 else "未定義"

    st.title(f"📄 {sel_name}")
    status_msg = f"🆔 管制編號：{permit_id}　|　📅 到期日期：{expiry_date[:10]}　|　📢 目前狀態：【{excel_status}】"
    st.info(status_msg)
    st.divider()

    # --- 🛠️ 辦理項目 (解決「變更展延」不見的問題) ---
    # 確保從「附件資料庫」抓取對應類型的所有項目
    db_info = file_df[file_df.iloc[:, 0] == sel_type]
    options = db_info.iloc[:, 1].dropna().unique().tolist()

    if options:
        st.subheader("🛠️ 第一步：選擇辦理項目 (可多選)")
        if "selected_actions" not in st.session_state: st.session_state.selected_actions = set()
        
        cols = st.columns(len(options))
        for i, option in enumerate(options):
            is_active = option in st.session_state.selected_actions
            if cols[i].button(option, key=f"btn_{option}", use_container_width=True, 
                              type="primary" if is_active else "secondary"):
                if is_active: st.session_state.selected_actions.remove(option)
                else: st.session_state.selected_actions.add(option)
                st.rerun()

        # 第二步填寫邏輯 (略，維持原狀)
        current_list = st.session_state.selected_actions
        if current_list:
            st.divider()
            user_name = st.text_input("👤 申請人姓名")
            if st.button("🚀 提出申請", type="primary"):
                # 寫入 Excel 邏輯 (維持你之前成功的 concat 寫法)
                # ... (略)
                st.cache_data.clear() # 寫入後清空快取
                st.success("申請成功！")
                st.rerun()

    # --- 📊 總表部分 (解決總表不動問題) ---
    st.write("---")
    with st.expander("📊 查看許可證管理總表", expanded=True):
        # 這裡顯示 main_df，因為上面有 load_all_data，且有按鈕可以 cache_clear
        display_df = main_df.drop(columns=['判斷日期', '最新狀態'], errors='ignore')
        st.dataframe(display_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
