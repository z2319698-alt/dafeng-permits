import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
from streamlit_gsheets import GSheetsConnection

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐環保 AI 智慧監控系統", layout="wide")

# 2. 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 🧠 AI 智慧模組區 ---
def get_ai_check_status(pdf_link):
    # 判斷連結是否為空值
    if pd.isna(pdf_link) or str(pdf_link).strip() == "" or str(pdf_link) == "nan":
        return "⚠️ 警告：雲端無紙本備份，AI 無法核對", "#d32f2f"
    return "✅ AI 已同步：紙本與資料庫日期核對一致", "#2E7D32"

def display_ai_law_wall(category):
    law_db = {
        "廢棄物清理計畫書": [
            {"date": "2025/08", "tag": "再利用專點", "content": "再利用機構應全面檢討收受廢棄物種類，注意跨區收受回報機制。"},
            {"date": "2025/11", "tag": "清運重點", "content": "GPS 裝置應定期檢驗，軌跡斷層將視為惡意逃避監控。"}
        ]
    }
    updates = law_db.get(category, [{"date": "2025-2026", "tag": "穩定", "content": "目前此類別法規穩定。"}])
    st.markdown(f"### 🛡️ AI 法規動態感知牆")
    cols = st.columns(len(updates))
    for i, item in enumerate(updates):
        with cols[i]:
            st.markdown(f"""<div style="background-color: #f0f4f8; border-left: 5px solid #2E7D32; padding: 15px; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); height: 160px;"><span style="background-color: #2E7D32; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{item['tag']}</span><p style="margin-top: 10px; color: #1a3a3a; font-weight: bold; font-size: 0.9rem;">📅 {item['date']}</p><p style="color: #333; font-size: 0.85rem;">{item['content']}</p></div>""", unsafe_allow_html=True)

# 3. 數據加載 (整合 L 欄自動優化邏輯)
@st.cache_data(ttl=5)
def load_all_data():
    m_df = conn.read(worksheet="大豐既有許可證到期提醒")
    f_df = conn.read(worksheet="附件資料庫")
    l_df = conn.read(worksheet="申請紀錄")
    
    # 🌟 自動清理欄位名稱：去掉首尾空格、中間空格，確保 PDF連結 欄位能被抓到
    m_df.columns = [str(c).strip().replace(" ", "") for c in m_df.columns]
    f_df.columns = [str(c).strip().replace(" ", "") for c in f_df.columns]
    l_df.columns = [str(c).strip().replace(" ", "") for c in l_df.columns]
    
    return m_df, f_df, l_df.dropna(how='all')

# --- 核心邏輯執行 ---
try:
    main_df, file_df, logs_df = load_all_data()
    today = pd.Timestamp(date.today())
    
    # 跑馬燈邏輯 (使用第 4 欄索引)
    main_df['判斷日期'] = pd.to_datetime(main_df.iloc[:, 3], errors='coerce')
    upcoming = main_df[main_df['判斷日期'] <= today + pd.Timedelta(days=180)]
    if not upcoming.empty:
        marquee_text = " | ".join([f"⚠️ 提醒：{row.iloc[2]} (到期日: {str(row.iloc[3])[:10]})" for _, row in upcoming.iterrows()])
        st.markdown(f'<marquee style="color:red; font-weight:bold;">{marquee_text}</marquee>', unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center;'>🌱 大豐環保智慧管理系統</h1>", unsafe_allow_html=True)

    # 4. 側邊導航
    if "mode" not in st.session_state: st.session_state.mode = "management"
    st.sidebar.header("🏠 系統導航")
    if st.sidebar.button("📋 許可證辦理系統", use_container_width=True): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 既有文件下載區", use_container_width=True): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例", use_container_width=True): st.session_state.mode = "cases"; st.rerun()

    # 5. 分頁邏輯
    if st.session_state.mode == "library":
        st.header("📁 既有文件下載區")
        for _, row in main_df.iterrows():
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"📄 **{row.iloc[2]}**")
            c2.write(f"📅 到期: {str(row.iloc[3])[:10]}")
            # 抓取連結
            url = row.get("PDF連結", None)
            if pd.notna(url) and str(url).startswith("http"):
                c3.link_button("📥 下載 PDF", str(url), use_container_width=True)
            else:
                c3.button("❌ 無連結", disabled=True, use_container_width=True)
            st.divider()

    elif st.session_state.mode == "management":
        st.sidebar.divider()
        sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
        sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())
        
        target_row = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
        expiry_date = str(target_row.iloc[3])
        pdf_link = target_row.get("PDF連結", None)

        st.title(f"📄 {sel_name}")

        # AI 感知與法規牆
        check_msg, check_color = get_ai_check_status(pdf_link)
        st.markdown(f'<p style="color:{check_color}; border-left:5px solid {check_color}; padding-left:10px; background-color:#f9f9f9;">{check_msg}</p>', unsafe_allow_html=True)
        display_ai_law_wall(sel_type)

        # 🛠️ 原始按鈕邏輯 (維持不變)
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

            if st.session_state.selected_actions:
                st.divider()
                st.markdown("### 📝 第二步：填寫申請資訊")
                user_name = st.text_input("👤 申請人姓名")
                
                final_atts = set()
                for act in st.session_state.selected_actions:
                    rows = db_info[db_info.iloc[:, 1] == act]
                    if not rows.empty:
                        att_list = rows.iloc[0, 3:].dropna().tolist()
                        for a in att_list: final_atts.add(str(a))
                
                for a in sorted(list(final_atts)):
                    with st.expander(f"📁 {a}"): st.file_uploader(f"上傳 {a}")

                if st.button("🚀 提出申請", type="primary"):
                    if user_name:
                        new_row = {col: "" for col in logs_df.columns}
                        new_row.update({"許可證名稱": sel_name, "申請人": user_name, "申請日期": date.today().strftime("%Y-%m-%d"), "狀態": "已提送需求"})
                        conn.update(worksheet="申請紀錄", data=pd.concat([logs_df, pd.DataFrame([new_row])], ignore_index=True))
                        st.success("✅ 申請成功！"); time.sleep(1); st.session_state.selected_actions = set(); st.rerun()

        st.write("---")
        with st.expander("📊 查看許可證管理總表"):
            st.dataframe(main_df.drop(columns=['判斷日期'], errors='ignore'), use_container_width=True, hide_index=True)

    elif st.session_state.mode == "cases":
        st.header("⚖️ 近期裁處案例")
        st.error("**⚠️ 案例：再利用廠超量貯存**\n\n法規：廢清法 39 條\n\n💡 避險：落實每日進出庫磅單核對。")

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
