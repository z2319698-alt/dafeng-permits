import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# 2. 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_data():
    main_df = conn.read(worksheet="大豐既有許可證到期提醒")
    file_df = conn.read(worksheet="附件資料庫")
    try:
        logs_df = conn.read(worksheet="申請紀錄")
        logs_df = logs_df.dropna(how='all')
    except:
        logs_df = pd.DataFrame(columns=["許可證名稱", "申請人", "申請日期", "狀態", "核准日期"])
    return main_df, file_df, logs_df

try:
    main_df, file_df, logs_df = load_data()
    today = pd.Timestamp(date.today())

    # --- 🏆 1. 跑馬燈區 (保證出現版) ---
    # 先將日期轉為 Datetime 格式
    marquee_df = main_df.copy()
    marquee_df.iloc[:, 3] = pd.to_datetime(marquee_df.iloc[:, 3], errors='coerce')
    # 篩選 90 天內到期的
    upcoming = marquee_df[(marquee_df.iloc[:, 3].notna()) & (marquee_df.iloc[:, 3] <= today + timedelta(days=90)) & (marquee_df.iloc[:, 3] >= today)]
    
    if not upcoming.empty:
        marquee_items = [f"⚠️ {row.iloc[2]} 將於 {row.iloc[3].strftime('%Y-%m-%d')} 到期" for _, row in upcoming.iterrows()]
        marquee_text = "　　　　".join(marquee_items)
        st.markdown(f"""
            <div style="background-color: #FFF3E0; padding: 12px; border-radius: 8px; border: 2px solid #FFB74D; margin-bottom: 20px;">
                <marquee scrollamount="6" style="color: #E65100; font-weight: bold; font-size: 18px;">{marquee_text}</marquee>
            </div>
        """, unsafe_allow_html=True)

    # --- 2. 側邊欄 (按鈕與篩選器) ---
    st.sidebar.markdown("## 🏠 系統選單")
    # 補回首頁按鈕
    if st.sidebar.button("🏠 回到首頁畫面", use_container_width=True):
        st.session_state.selected_actions = set()
        st.rerun()
    
    st.sidebar.divider()
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
    sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())

    # --- 3. 狀態判定與詳細資訊 ---
    def get_display_status(permit_name):
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

    current_p_status = get_display_status(sel_name)
    target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
    permit_id = str(target_main.iloc[1])
    try:
        expiry_val = pd.to_datetime(target_main.iloc[3]).strftime('%Y-%m-%d')
    except:
        expiry_val = str(target_main.iloc[3])

    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🌱 大豐環保許可證管理系統</h1>", unsafe_allow_html=True)
    st.title(f"📄 {sel_name}")
    st.error(f"📅 許可證到期日期：{expiry_val}")
    
    status_color = "gray"
    if current_p_status == "已核准": status_color = "green"
    elif "提送" in current_p_status or "申請中" in current_p_status: status_color = "orange"
    st.info(f"🆔 管制編號：{permit_id}　|　📢 目前狀態：:{status_color}[【{current_p_status}】]")
    
    st.divider()

    # --- 4. 辦理項目申請區 ---
    db_info = file_df[file_df.iloc[:, 0] == sel_type]
    options = db_info.iloc[:, 1].dropna().unique().tolist()
    if options:
        st.subheader("🛠️ 第一步：選擇辦理項目")
        if "selected_actions" not in st.session_state: st.session_state.selected_actions = set()
        cols = st.columns(len(options))
        for i, option in enumerate(options):
            is_active = option in st.session_state.selected_actions
            if cols[i].button(option, key=f"btn_{option}", use_container_width=True, type="primary" if is_active else "secondary"):
                if is_active: st.session_state.selected_actions.remove(option)
                else: st.session_state.selected_actions.add(option)
                st.rerun()

        if st.session_state.selected_actions:
            user_name = st.text_input("👤 申請人姓名")
            if st.button("🚀 確認送出申請", type="primary"):
                if not user_name: st.error("❌ 請輸入姓名")
                else:
                    new_log = pd.DataFrame([{"許可證名稱": sel_name, "申請人": user_name, "申請日期": date.today().strftime("%Y-%m-%d"), "狀態": "已提送需求", "核准日期": ""}])
                    updated_df = pd.concat([logs_df, new_log], ignore_index=True)
                    conn.update(worksheet="申請紀錄", data=updated_df)
                    st.success(f"✅ 申請已送出！")
                    st.session_state.selected_actions = set()
                    st.rerun()

    # --- 🏆 5. 收放式總表 (Expander) ---
    st.write("")
    with st.expander("📊 點擊展開/收合：許可證完整資料總覽", expanded=False):
        display_df = main_df.copy()
        # 嘗試格式化日期列
        try:
            display_df.iloc[:, 3] = pd.to_datetime(display_df.iloc[:, 3], errors='coerce').dt.strftime('%Y-%m-%d')
        except:
            pass
        st.dataframe(display_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"系統錯誤: {e}")
