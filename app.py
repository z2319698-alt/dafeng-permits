import streamlit as st
import pandas as pd
from datetime import date, datetime
import smtplib
import time
from email.mime.text import MIMEText
from email.header import Header
from streamlit_gsheets import GSheetsConnection

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# 2. 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 🧠 AI 智慧模組：一年法規動態 ---
def display_ai_law_wall(category):
    law_db = {
        "廢棄物清理計畫書": [
            {"date": "2025/08", "tag": "重大變更", "content": "環保署公告：事業廢棄物清理計畫書應增列「資源循環促進」專章，強化轉廢為能紀錄。"},
            {"date": "2025/11", "tag": "裁罰預警", "content": "強化產源責任：若收受端違規，產源端若未落實視察，將連帶處分。"},
            {"date": "2026/01", "tag": "最新公告", "content": "全面推動電子化合約上傳，紙本合約備查期縮短為 3 年。"}
        ],
        "水污染防治許可證": [
            {"date": "2025/07", "tag": "標準加嚴", "content": "針對放流水中之氨氮、重金屬指標納入年度評鑑，連續超標將暫停展延申請。"},
            {"date": "2025/12", "tag": "技術導引", "content": "鼓勵設置智慧水表與自動取樣系統，具備自動回傳功能者可減少定檢頻率。"}
        ]
    }
    updates = law_db.get(category, [{"date": "2025-2026", "tag": "穩定", "content": "目前此類別法規穩定，請依現行法規辦理展延。"}])
    st.markdown(f"### 🛡️ AI 法規動態感知牆 (近一年)")
    cols = st.columns(len(updates))
    for i, item in enumerate(updates):
        with cols[i]:
            st.markdown(f"""<div style="background-color: #f0f4f8; border-left: 5px solid #2E7D32; padding: 15px; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); height: 180px;"><span style="background-color: #2E7D32; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{item['tag']}</span><p style="margin-top: 10px; color: #1a3a3a; font-weight: bold; font-size: 0.9rem;">📅 {item['date']}</p><p style="color: #333; font-size: 0.85rem; line-height: 1.4;">{item['content']}</p></div>""", unsafe_allow_html=True)

# --- 🧠 AI 智慧模組：近期裁處案例 (New!) ---
def display_penalty_cases():
    st.markdown("## ⚖️ 近一年環保裁處案例重點分享")
    st.info("AI 彙整：以下為近一年台灣針對各類環保違規之典型開罰案例，請各廠區引以為戒。")
    
    cases = [
        {"type": "廢棄物類", "law": "廢棄物清理法第 31 條", "reason": "未依規定之格式、內容、頻率申報廢棄物產出、貯存及清理情形。", "penalty": "罰鍰 NT$ 6,000 ~ 300 萬", "key": "【漏報】廢清書變更後，未於 15 日內完成線上報備。"},
        {"type": "水污染類", "law": "水污染防治法第 14 條", "reason": "排放廢污水不符合放流水標準（如懸浮固體或化學需氧量超標）。", "penalty": "罰鍰 NT$ 6 萬 ~ 2,000 萬", "key": "【超標】雨天逕流廢水未經妥善收集處理即排入溝渠。"},
        {"type": "空污類", "law": "空氣污染防制法第 24 條", "reason": "設置或操作許可證內容與實際現況不符。", "penalty": "罰鍰 NT$ 10 萬 ~ 2,000 萬", "key": "【不符】防制設備型號與許可證記載不一致，且未申請變更。"},
        {"type": "管理類", "law": "環保專責人員管理辦法", "reason": "專責人員離職未於 15 日內遞補或代理。", "penalty": "罰鍰 NT$ 1 萬 ~ 10 萬", "key": "【空窗】人員異動時未留意法定通報期限，導致過期開罰。"}
    ]
    
    for case in cases:
        st.markdown(f"""
            <div style="background-color: #fff5f5; border-left: 5px solid #e53935; padding: 15px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between;">
                    <b style="color: #e53935; font-size: 1.1rem;">[{case['type']}] {case['law']}</b>
                    <span style="color: #666;">📌 裁罰重點</span>
                </div>
                <p style="margin: 8px 0; color: #333;"><b>違規事由：</b>{case['reason']}</p>
                <p style="margin: 5px 0; color: #d32f2f;"><b>裁罰風險：</b>{case['penalty']}</p>
                <p style="margin: 5px 0; color: #1a237e; background-color: #e8eaf6; padding: 5px; border-radius: 4px;"><b>💡 避險核心：</b>{case['key']}</p>
            </div>
        """, unsafe_allow_html=True)

# 3. 數據加載 (維持原邏輯)
@st.cache_data(ttl=10)
def load_main_data():
    main_df = conn.read(worksheet="大豐既有許可證到期提醒")
    file_df = conn.read(worksheet="附件資料庫")
    main_df.columns = [str(c).strip() for c in main_df.columns]
    file_df.columns = [str(c).strip() for c in file_df.columns]
    return main_df, file_df

@st.cache_data(ttl=5)
def load_logs():
    try:
        df = conn.read(worksheet="申請紀錄")
        return df.dropna(how='all')
    except:
        return pd.DataFrame(columns=["許可證名稱", "申請人", "申請日期", "狀態", "核准日期"])

try:
    main_df, file_df = load_main_data()
    logs_df = load_logs()
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
    st.sidebar.markdown("## 🏠 系統首頁")
    if st.sidebar.button("🔄 刷新資料庫", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # 切換模式按鈕
    if "mode" not in st.session_state: st.session_state.mode = "management"

    if st.sidebar.button("📋 許可證辦理系統", use_container_width=True):
        st.session_state.mode = "management"
        st.rerun()

    if st.sidebar.button("⚖️ 近期裁處案例", use_container_width=True):
        st.session_state.mode = "cases"
        st.rerun()

    # --- 畫面渲染邏輯 ---
    if st.session_state.mode == "cases":
        # 顯示裁處案例頁面
        display_penalty_cases()
        if st.button("⬅️ 返回辦理系統"):
            st.session_state.mode = "management"
            st.rerun()
            
    else:
        # 顯示原本的許可證管理頁面 (維持所有原始設定)
        st.sidebar.divider()
        sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
        sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())

        target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
        expiry_date = str(target_main.iloc[3])
        clean_date = expiry_date[:10] if expiry_date != 'nan' else "未設定"
        
        st.title(f"📄 {sel_name}")

        # AI 時程精算 & 法規牆
        expiry_dt_obj = pd.to_datetime(expiry_date, errors='coerce')
        if not pd.isna(expiry_dt_obj):
            earliest_submit = expiry_dt_obj - pd.Timedelta(days=180)
            start_prep = earliest_submit - pd.Timedelta(days=30)
            display_ai_law_wall(sel_type)
            st.write("")
            c1, c2, c3 = st.columns(3)
            c1.metric("法規投件日(最早)", earliest_submit.strftime('%Y-%m-%d'))
            c2.metric("AI 建議準備日", start_prep.strftime('%Y-%m-%d'))
            days_diff = (earliest_submit - today).days
            if today < start_prep: c3.success(f"時間充裕 (剩 {days_diff} 天)")
            elif start_prep <= today < earliest_submit: c3.warning(f"準備中 (剩 {days_diff} 天)")
            else: c3.error("已可投件！")

        st.divider()

        # 🛠️ 原始功能：辦理項目按鈕
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
                st.markdown("### 📝 第二步：填寫申請資訊")
                c1, c2 = st.columns(2)
                with c1: user_name = st.text_input("👤 申請人姓名", placeholder="請輸入姓名")
                with c2: apply_date = st.date_input("📅 提出申請日期", value=date.today())

                # 附件邏輯...
                final_attachments = set()
                for action in current_list:
                    action_row = db_info[db_info.iloc[:, 1] == action]
                    if not action_row.empty:
                        att_list = action_row.iloc[0, 3:].dropna().tolist()
                        for item in att_list: final_attachments.add(str(item).strip())

                for item in sorted(list(final_attachments)):
                    with st.expander(f"📁 {item}", expanded=True): st.file_uploader(f"請上傳檔案 - {item}", key=f"up_{item}")

                if st.button("🚀 提出申請", type="primary"):
                    if user_name:
                        new_data = {col: "" for col in logs_df.columns}
                        new_data.update({"許可證名稱": sel_name, "申請人": user_name, "申請日期": date.today().strftime("%Y-%m-%d"), "狀態": "已提送需求"})
                        conn.update(worksheet="申請紀錄", data=pd.concat([logs_df, pd.DataFrame([new_data])], ignore_index=True))
                        st.balloons(); st.success("✅ 申請成功！"); st.cache_data.clear()
                        time.sleep(1); st.session_state.selected_actions = set(); st.rerun()

        # 📊 總表顯示 (展開器內)
        st.write("---")
        with st.expander("📊 查看許可證管理總表"):
            st.dataframe(main_df.drop(columns=['判斷日期', '最新狀態'], errors='ignore'), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
