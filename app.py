import streamlit as st
import pandas as pd
from datetime import date, datetime
from streamlit_gsheets import GSheetsConnection

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# 2. 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_data():
    # 讀取主表
    main_df = conn.read(worksheet="大豐既有許可證到期提醒")
    # 讀取附件資料庫
    file_df = conn.read(worksheet="附件資料庫")
    # 讀取申請紀錄 (如果沒有這張表，建立一個空的)
    try:
        logs_df = conn.read(worksheet="申請紀錄")
        # 確保格式正確，避免讀取到空白列
        logs_df = logs_df.dropna(how='all')
    except:
        logs_df = pd.DataFrame(columns=["許可證名稱", "申請人", "申請日期", "狀態", "核准日期"])
    return main_df, file_df, logs_df

try:
    main_df, file_df, logs_df = load_data()
    today = pd.Timestamp(date.today())

    # --- 狀態判定邏輯 ---
    def get_display_status(permit_name):
        if logs_df.empty:
            return "未提送"
        
        # 找該許可證最後一筆紀錄
        my_logs = logs_df[logs_df["許可證名稱"] == permit_name]
        if my_logs.empty:
            return "未提送"
        
        last_log = my_logs.iloc[-1]
        s = str(last_log["狀態"]).strip()
        
        # 如果是「已核准」，判定是否超過 5 天
        if s == "已核准":
            try:
                app_d = pd.to_datetime(last_log["核准日期"])
                if (today - app_d).days > 5:
                    return "未提送"
            except:
                pass
        return s

    # --- 介面渲染 ---
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🌱 大豐環保許可證管理系統</h1>", unsafe_allow_html=True)
    
    st.sidebar.markdown("## 🏠 系統選單")
    if st.sidebar.button("回到首頁畫面", use_container_width=True):
        st.session_state.selected_actions = set()
        st.rerun()
    st.sidebar.divider()
    
    # 選擇器
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
    sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())

    # 取得目前的動態狀態
    current_p_status = get_display_status(sel_name)
    target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
    permit_id = str(target_main.iloc[1])

    # 顯示詳細資訊
    st.title(f"📄 {sel_name}")
    
    # 根據狀態顯示不同顏色的標籤
    status_color = "gray"
    if current_p_status == "已核准": status_color = "green"
    elif "申請中" in current_p_status or "提送" in current_p_status: status_color = "orange"
    
    st.markdown(f"### 🆔 管制編號：`{permit_id}` | 📢 目前狀態：:{status_color}[【{current_p_status}】]")
    st.divider()

    # --- 辦理項目與申請 ---
    db_info = file_df[file_df.iloc[:, 0] == sel_type]
    options = db_info.iloc[:, 1].dropna().unique().tolist()

    if options:
        st.subheader("🛠️ 第一步：選擇辦理項目 (可多選)")
        if "selected_actions" not in st.session_state:
            st.session_state.selected_actions = set()
            
        cols = st.columns(len(options))
        for i, option in enumerate(options):
            is_active = option in st.session_state.selected_actions
            if cols[i].button(option, key=f"btn_{option}", use_container_width=True, type="primary" if is_active else "secondary"):
                if is_active:
                    st.session_state.selected_actions.remove(option)
                else:
                    st.session_state.selected_actions.add(option)
                st.rerun()

        # 如果有選項目，顯示填寫區域
        if st.session_state.selected_actions:
            st.markdown("---")
            st.subheader("📝 第二步：填寫申請資訊")
            user_name = st.text_input("👤 申請人姓名", placeholder="請輸入您的真實姓名")
            
            if st.button("🚀 確認送出申請", type="primary", use_container_width=True):
                if not user_name:
                    st.error("❌ 請輸入申請人姓名後再送出！")
                else:
                    with st.spinner('正在同步資料到雲端試算表...'):
                        # 建立新紀錄
                        new_log = pd.DataFrame([{
                            "許可證名稱": sel_name,
                            "申請人": user_name,
                            "申請日期": date.today().strftime("%Y-%m-%d"),
                            "狀態": "已提送需求",
                            "核准日期": ""
                        }])
                        # 讀取現有紀錄並合併
                        updated_df = pd.concat([logs_df, new_log], ignore_index=True)
                        # 更新到 Google Sheets
                        conn.update(worksheet="申請紀錄", data=updated_df)
                        
                        st.success(f"✅ 申請已送出！已自動更新為「已提送需求」。")
                        st.session_state.selected_actions = set() # 清空選擇
                        st.balloons() # 撒個彩帶慶祝一下
                        st.rerun()

except Exception as e:
    st.error(f"⚠️ 系統連線異常，請檢查 Google Sheets 設定。錯誤訊息: {e}")
