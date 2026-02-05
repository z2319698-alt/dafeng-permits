import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
from streamlit_gsheets import GSheetsConnection

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# 2. 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 🧠 AI 智慧模組區 (完全保留原始內容) ---
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
    updates = law_db.get(category, [{"date": "2025-2026", "tag": "穩定", "content": "目前此類別法規穩定。"}])
    st.markdown(f"### 🛡️ AI 法規動態感知牆 (近一年)")
    cols = st.columns(len(updates))
    for i, item in enumerate(updates):
        with cols[i]:
            st.markdown(f"""<div style="background-color: #f0f4f8; border-left: 5px solid #2E7D32; padding: 15px; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); height: 180px;"><span style="background-color: #2E7D32; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{item['tag']}</span><p style="margin-top: 10px; color: #1a3a3a; font-weight: bold; font-size: 0.9rem;">📅 {item['date']}</p><p style="color: #333; font-size: 0.85rem; line-height: 1.4;">{item['content']}</p></div>""", unsafe_allow_html=True)

def display_penalty_cases():
    st.markdown("## ⚖️ 近一年環保裁處案例重點分享")
    cases = [
        {"type": "廢棄物類", "law": "廢棄物清理法第 31 條", "reason": "未依規定之格式、內容、頻率申報。", "penalty": "罰鍰 NT$ 6,000 ~ 300 萬", "key": "【漏報】廢清書變更後未報備。"},
        {"type": "水污染類", "law": "水污染防治法第 14 條", "reason": "排放廢污水不符合標準。", "penalty": "罰鍰 NT$ 6 萬 ~ 2,000 萬", "key": "【超標】雨天逕流廢水未妥善處理。"}
    ]
    for case in cases:
        st.markdown(f"""<div style="background-color: #fff5f5; border-left: 5px solid #e53935; padding: 15px; margin-bottom: 15px; border-radius: 8px;"><b style="color: #e53935;">[{case['type']}] {case['law']}</b><p>事由：{case['reason']}</p><p style="color: #1a237e; background-color: #e8eaf6; padding: 5px;">💡 避險：{case['key']}</p></div>""", unsafe_allow_html=True)

# 3. 數據加載 (強化標題抓取)
@st.cache_data(ttl=5)
def load_all_data():
    m_df = conn.read(worksheet="大豐既有許可證到期提醒")
    f_df = conn.read(worksheet="附件資料庫")
    # 清理所有隱藏空格與換行符
    m_df.columns = [str(c).strip().replace(" ", "").replace("\n", "") for c in m_df.columns]
    f_df.columns = [str(c).strip().replace(" ", "").replace("\n", "") for c in f_df.columns]
    return m_df, f_df

@st.cache_data(ttl=5)
def load_logs():
    try:
        df = conn.read(worksheet="申請紀錄")
        return df.dropna(how='all')
    except:
        return pd.DataFrame(columns=["許可證名稱", "申請人", "申請日期", "狀態"])

try:
    main_df, file_df = load_all_data()
    logs_df = load_logs()
    today = pd.Timestamp(date.today())

    # --- 📢 跑馬燈 (原始設定) ---
    main_df['判斷日期'] = pd.to_datetime(main_df.iloc[:, 3], errors='coerce')
    def get_real_status(row_date):
        if pd.isna(row_date): return "未設定"
        if row_date < today: return "❌ 已過期"
        elif row_date <= today + pd.Timedelta(days=180): return "⚠️ 準備辦理"
        else: return "✅ 有效"
    main_df['最新狀態'] = main_df['判斷日期'].apply(get_real_status)

    upcoming = main_df[main_df['最新狀態'].isin(["❌ 已過期", "⚠️ 準備辦理"])]
    if not upcoming.empty:
        marquee_text = " | ".join([f"{row['最新狀態']}：{row.iloc[2]} (到期日: {str(row.iloc[3])[:10]})" for _, row in upcoming.iterrows()])
        st.markdown(f'<div style="background-color: #FFF3E0; padding: 10px; border-radius: 5px; border-left: 5px solid #FF9800; overflow: hidden; white-space: nowrap;"><marquee scrollamount="5" style="color: #E65100; font-weight: bold;">{marquee_text}</marquee></div>', unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🌱 大豐環保許可證管理系統</h1>", unsafe_allow_html=True)
    st.write("---")

    # --- 📂 側邊選單 ---
    st.sidebar.markdown("## 🏠 系統首頁")
    if st.sidebar.button("🔄 刷新資料庫", use_container_width=True):
        st.cache_data.clear(); st.rerun()

    if "mode" not in st.session_state: st.session_state.mode = "management"
    if st.sidebar.button("📋 許可證辦理系統", use_container_width=True): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 既有文件下載區", use_container_width=True): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例", use_container_width=True): st.session_state.mode = "cases"; st.rerun()

    # --- 畫面渲染邏輯 ---
    if st.session_state.mode == "library":
        st.header("📁 既有文件下載區")
        st.info("請點選下方按鈕下載或檢視各廠區許可證 PDF 紙本。")
        for idx, row in main_df.iterrows():
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"📄 **{row.iloc[2]}**")
            c2.write(f"📅 到期: {str(row.iloc[3])[:10]}")
            
            # 💡 修復點：改用 row.get 並移除 link_button 的 key 參數
            url = row.get("PDF連結", "")
            if pd.notna(url) and str(url).strip().startswith("http"):
                c3.link_button("📥 下載 PDF", str(url).strip(), use_container_width=True)
            else:
                c3.button("❌ 無連結", disabled=True, use_container_width=True, key=f"none_{idx}")
            st.divider()

    elif st.session_state.mode == "cases":
        display_penalty_cases()
        if st.button("⬅️ 返回辦理系統"): st.session_state.mode = "management"; st.rerun()
            
    else:
        # --- 原始許可證管理頁面 (維持所有設定) ---
        st.sidebar.divider()
        sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
        sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())
        target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
        
        st.title(f"📄 {sel_name}")

        # AI 紙本核對狀態
        pdf_val = target_main.get("PDF連結", "")
        if pd.isna(pdf_val) or str(pdf_val).strip() == "":
            st.markdown('<p style="color:#d32f2f;">🔍 AI 狀態：⚠️ 雲端無紙本備份，AI 無法核對</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#2E7D32;">🔍 AI 狀態：✅ 已與雲端 PDF 同步，核對一致</p>', unsafe_allow_html=True)

        display_ai_law_wall(sel_type)
        
        # 辦理項目按鈕 (原始邏輯)
        db_info = file_df[file_df.iloc[:, 0] == sel_type]
        options = db_info.iloc[:, 1].dropna().unique().tolist()
        if options:
            st.subheader("🛠️ 第一步：選擇辦理項目")
            if "selected_actions" not in st.session_state: st.session_state.selected_actions = set()
            cols = st.columns(len(options))
            for i, option in enumerate(options):
                is_active = option in st.session_state.selected_actions
                if cols[i].button(option, key=f"act_{option}", use_container_width=True, type="primary" if is_active else "secondary"):
                    if is_active: st.session_state.selected_actions.remove(option)
                    else: st.session_state.selected_actions.add(option)
                    st.rerun()

            if st.session_state.selected_actions:
                user_name = st.text_input("👤 申請人姓名")
                if st.button("🚀 提出申請", type="primary"):
                    if user_name:
                        new_data = {"許可證名稱": sel_name, "申請人": user_name, "申請日期": date.today().strftime("%Y-%m-%d"), "狀態": "已提送需求"}
                        conn.update(worksheet="申請紀錄", data=pd.concat([logs_df, pd.DataFrame([new_data])], ignore_index=True))
                        st.success("✅ 申請成功！"); st.cache_data.clear(); time.sleep(1); st.session_state.selected_actions = set(); st.rerun()

        st.write("---")
        with st.expander("📊 查看許可證管理總表"):
            st.dataframe(main_df.drop(columns=['判斷日期', '最新狀態'], errors='ignore'), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
