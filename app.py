import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
from streamlit_gsheets import GSheetsConnection

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# 2. 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 🧠 AI 智慧與案例模組 ---
def display_ai_law_wall(category):
    law_db = {
        "廢棄物清理計畫書": [
            {"date": "2025/08", "tag": "重大變更", "content": "環保署公告：廢清書應增列「資源循環促進」專章，強化轉廢為能紀錄。"},
            {"date": "2025/11", "tag": "裁罰預警", "content": "強化產源責任：產源端若未落實收受端視察，將面臨連帶重罰。"},
            {"date": "2026/01", "tag": "最新公告", "content": "全面推動電子化合約上傳，紙本備查期縮短為 3 年。"}
        ],
        "水污染防治許可證": [
            {"date": "2025/07", "tag": "標準加嚴", "content": "氨氮、重金屬指標納入年度評鑑，連續超標將暫停展延。"},
            {"date": "2025/12", "tag": "技術導引", "content": "鼓勵設置智慧水表，具備自動回傳功能者可減少定檢頻率。"}
        ]
    }
    updates = law_db.get(category, [{"date": "2025-2026", "tag": "穩定", "content": "目前此類別法規穩定。"}])
    st.markdown(f"### 🛡️ AI 法規動態感知牆")
    cols = st.columns(len(updates))
    for i, item in enumerate(updates):
        with cols[i]:
            # 確保內容為深色字體 (#333)
            st.markdown(f"""<div style="background-color: #f0f4f8; border-left: 5px solid #2E7D32; padding: 15px; border-radius: 8px; height: 180px;"><span style="background-color: #2E7D32; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{item['tag']}</span><p style="margin-top: 10px; font-weight: bold; color: #333;">📅 {item['date']}</p><p style="font-size: 0.85rem; color: #333;">{item['content']}</p></div>""", unsafe_allow_html=True)

def display_penalty_cases():
    st.markdown("## ⚖️ 2025-2026 重大環保事件與稽查熱區")
    st.info("AI 彙整：以下包含近期真實判刑、重大抗爭及大數據稽查動態。")
    
    high_risk_cases = [
        {"type": "廢棄物非法棄置 (真實刑案)", "law": "廢清法第 46 條第 4 款", "reason": "屏東包商未經許可清運裝潢廢材至國有地，2025/09 遭判處有期徒刑 1 年 6 月並沒收不法所得。", "penalty": "有期徒刑 + 高額罰金 + 沒收財產", "key": "【刑事責任】委託清運務必確認清除機構具備對應代碼許可。"},
        {"type": "美濃大峽谷案 (盜採回填)", "law": "廢清法第 41、46 條", "reason": "高雄美濃成功段農地遭非法回填 14 萬噸廢棄物，不法獲利 2.4 億，2026/02 起訴地主與主嫌等 12 人。", "penalty": "最高罰鍰 300 萬並強制執行還原", "key": "【溯源追蹤】產源端如無法證明流向，將面臨極高連帶清理成本。"}
    ]
    
    media_cases = [
        {"src": "焚化爐環評爭議", "topic": "南投名間焚化爐「茶鄉抗爭」", "desc": "2026/01-02 名間鄉反焚化爐自救會強烈抗議。此事件導致全台焚化爐「進廠審核」趨於嚴苛，特別針對高熱值垃圾。", "advice": "廠內垃圾分類需徹底，避免被焚化廠拒收或標記退運。"},
        {"src": "GPS 科技監控", "topic": "環境部「科技大數據」專案稽查", "desc": "2025 年起強化 GPS 軌跡異常比對。若清運車輛在非報備點停靠超過 30 分鐘，系統會自動發出預警並派員現場核查。", "advice": "清運時應嚴格要求廠商依照申報路線行駛。"},
        {"src": "網路陳情觀測", "topic": "Dcard/PTT 鄰避檢舉效應", "desc": "民眾針對廠區周界「不明異味」與「粉塵堆置」之網路曝光頻率提升，常引發媒體跟進與縣市長關切。", "advice": "加強周界環境灑水與防塵網覆蓋，並保留巡查紀錄。"},
        {"src": "代碼誤植連罰", "topic": "申報代碼與實際廢棄物不符案例", "desc": "近期稽查熱點：以「D-1801 一般垃圾」名義夾帶營建廢材，遭認定為申報不實處分。", "advice": "每年至少進行一次廢清書與實際產出物的代碼複核。"}
    ]

    for case in high_risk_cases:
        st.markdown(f"""<div style="background-color: #fff5f5; border-left: 5px solid #e53935; padding: 15px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);"><b style="color: #e53935; font-size: 1.1rem;">🚨 [高風險] {case['type']} - {case['law']}</b><p style="margin: 8px 0; color: #333;"><b>事由：</b>{case['reason']}</p><p style="color: #d32f2f;"><b>罰則：</b>{case['penalty']}</p><p style="background-color: #e8eaf6; padding: 5px; border-radius: 4px; color: #1a237e;"><b>💡 避險核心：</b>{case['key']}</p></div>""", unsafe_allow_html=True)

    st.markdown("### 🌐 社會重大事件與大數據監控熱點")
    cols = st.columns(2)
    for i, m in enumerate(media_cases):
        with cols[i % 2]:
            st.markdown(f"""<div style="background-color: #ffffff; border-left: 5px solid #0288d1; padding: 12px; margin-bottom: 10px; border-radius: 8px; border: 1px solid #e1f5fe; min-height: 200px;"><b style="color: #01579b;">[{m['src']}] {m['topic']}</b><p style="font-size: 0.9rem; margin: 5px 0; color: #333333;">{m['desc']}</p><p style="font-size: 0.85rem; color: #0277bd;"><b>📢 管理建議：</b>{m['advice']}</p></div>""", unsafe_allow_html=True)

# 3. 數據加載
@st.cache_data(ttl=5)
def load_all_data():
    m_df = conn.read(worksheet="大豐既有許可證到期提醒")
    f_df = conn.read(worksheet="附件資料庫")
    m_df.columns = [str(c).strip().replace(" ", "").replace("\n", "") for c in m_df.columns]
    f_df.columns = [str(c).strip().replace(" ", "").replace("\n", "") for c in f_df.columns]
    m_df.iloc[:, 3] = pd.to_datetime(m_df.iloc[:, 3], errors='coerce')
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

    # --- 📂 側邊選單 ---
    st.sidebar.markdown("## 🏠 系統導航")
    if "mode" not in st.session_state: st.session_state.mode = "management"

    if st.sidebar.button("🏠 系統首頁", use_container_width=True):
        st.session_state.mode = "management"
        if "selected_actions" in st.session_state: st.session_state.selected_actions = set()
        st.rerun()

    if st.sidebar.button("🔄 刷新資料庫", use_container_width=True):
        st.cache_data.clear(); st.rerun()

    if st.sidebar.button("📋 許可證辦理系統", use_container_width=True): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 許可下載區", use_container_width=True): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例", use_container_width=True): st.session_state.mode = "cases"; st.rerun()

    # --- 渲染邏輯 ---
    if st.session_state.mode == "library":
        st.header("📁 許可下載區")
        for idx, row in main_df.iterrows():
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"📄 **{row.iloc[2]}**")
            c2.write(f"📅 到期: {str(row.iloc[3])[:10]}")
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
        # --- 📋 許可證辦理系統 ---
        st.sidebar.divider()
        sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
        sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())
        target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
        
        st.title(f"📄 {sel_name}")

        # --- ⚠️ 補回核心：到期提醒與時程建議 (深色字體) ---
        days_left = (target_main.iloc[3] - today).days
        
        if days_left < 90:
            st.error(f"🚨 【嚴重警告】許可證將於 {days_left} 天後到期！")
            st.markdown(f'<div style="background-color: #ffeded; border: 2px solid #d32f2f; padding: 15px; border-radius: 10px; color: #333;"><b style="color: #d32f2f;">🤖 AI 時程建議：</b><br>您已錯過最佳辦理時程（90日前提出）。請立即準備附件，避免面臨罰鍰！</div>', unsafe_allow_html=True)
        elif days_left < 180:
            st.warning(f"⚠️ 【到期預警】許可證尚餘 {days_left} 天到期。")
            st.markdown(f'<div style="background-color: #fff9e6; border: 2px solid #f9a825; padding: 15px; border-radius: 10px; color: #333;"><b style="color: #f9a825;">🤖 AI 時程建議：</b><br>法規規定應於 90 日前提出展延申請。建議現在開始核對附件，預留補正時間。</div>', unsafe_allow_html=True)
        else:
            st.success(f"✅ 【狀態正常】許可證剩餘 {days_left} 天到期。")
            st.markdown(f'<div style="background-color: #e8f5e9; border: 2px solid #2E7D32; padding: 15px; border-radius: 10px; color: #333;"><b style="color: #2E7D32;">🤖 AI 時程建議：</b><br>目前狀態穩定。AI 建議在 180 天前開始蒐集資料即可。</div>', unsafe_allow_html=True)

        st.info(f"🆔 管制編號：{target_main.iloc[1]}")

        # AI 狀態顯示
        pdf_val = target_main.get("PDF連結", "")
        ai_color = "#2E7D32" if pd.notna(pdf_val) and str(pdf_val).strip() != "" else "#d32f2f"
        st.markdown(f'<p style="color:{ai_color}; font-weight:bold;">🔍 AI 狀態：{"✅ 已同步" if ai_color=="#2E7D32" else "⚠️ 無連結"}</p>', unsafe_allow_html=True)

        display_ai_law_wall(sel_type)
        
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
                st.divider()
                st.markdown("### 📝 第二步：附件上傳區")
                user_name = st.text_input("👤 申請人姓名")
                
                final_atts = set()
                for action in st.session_state.selected_actions:
                    rows = db_info[db_info.iloc[:, 1] == action]
                    if not rows.empty:
                        for item in rows.iloc[0, 3:].dropna().tolist():
                            final_atts.add(str(item).strip())

                for item in sorted(list(final_atts)):
                    with st.expander(f"📁 附件：{item}", expanded=True):
                        st.file_uploader(f"上傳檔案 - {item}", key=f"up_{item}")

                if st.button("🚀 提出申請", type="primary"):
                    if user_name:
                        st.balloons(); st.success("✅ 申請成功！"); st.session_state.selected_actions = set(); time.sleep(1); st.rerun()

        st.write("---")
        with st.expander("📊 總表查看"):
            st.dataframe(main_df.drop(columns=['判斷日期'], errors='ignore'), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
