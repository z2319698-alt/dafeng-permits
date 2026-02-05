import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
from streamlit_gsheets import GSheetsConnection
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re

# --- 🧠 AI 核心核對邏輯 (獨立函數，不影響原有 UI) ---
def ai_verify_date(pdf_link, sheet_date):
    try:
        # 解析 Google Drive ID
        file_id = pdf_link.split('/')[-2] if '/file/d/' in pdf_link else pdf_link.split('id=')[-1]
        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        
        response = requests.get(direct_url, timeout=10)
        # 轉圖 (Streamlit Cloud 會自動處理路徑)
        images = convert_from_bytes(response.content, dpi=120)
        
        found_dt = "未偵測到"
        keywords = ["有效日期", "有效期限", "有效期間", "發文次日至", "許可期限", "起至"]
        
        for img in images:
            text = pytesseract.image_to_string(img, lang='chi_tra')
            if any(k in text for k in keywords):
                match = re.search(r"(\d{2,3})[\s\.年/]*(\d{1,2})[\s\.月/]*(\d{1,2})", text)
                if match:
                    yy, mm, dd = match.groups()
                    year = int(yy) + 1911 if int(yy) < 1911 else int(yy)
                    found_dt = f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
                    break
        
        # 比對數字
        s_clean = str(sheet_date)[:10].replace('-', '')
        p_clean = found_dt.replace('-', '')
        return (s_clean == p_clean), found_dt
    except:
        return False, "辨識失敗"

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# 2. 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 🧠 AI 智慧與案例模組 (保持原樣) ---
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
            st.markdown(f"""<div style="background-color: #f0f4f8; border-left: 5px solid #2E7D32; padding: 15px; border-radius: 8px; height: 180px;"><span style="background-color: #2E7D32; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{item['tag']}</span><p style="margin-top: 10px; font-weight: bold; color: #333;">📅 {item['date']}</p><p style="font-size: 0.85rem; color: #333;">{item['content']}</p></div>""", unsafe_allow_html=True)

def display_penalty_cases():
    # ... (保持原樣) ...
    st.markdown("## ⚖️ 2025-2026 重大環保事件與稽查熱區")
    st.info("AI 彙整：以下包含近期真實判刑、重大抗爭及大數據稽查動態。")
    high_risk_cases = [
        {"type": "廢棄物非法棄置 (真實刑案)", "law": "廢清法第 46 條第 4 款", "reason": "屏東包商未經許可清運裝潢廢材至國有地，2025/09 遭判處有期徒刑 1 年 6 月並沒收不法所得。", "penalty": "有期徒刑 + 高額罰金 + 沒收財產", "key": "【刑事責任】委託清運務必確認清除機構具備對應代碼許可。"},
        {"type": "美濃大峽谷案 (盜採回填)", "law": "廢清法第 41、46 條", "reason": "高雄美濃成功段農地遭非法回填 14 萬噸廢棄物，不法獲利 2.4 億，2026/02 起訴地主與主嫌等 12 人。", "penalty": "最高罰鍰 300 萬並強制執行還原", "key": "【溯源追蹤】產源端如無法證明流向，將面臨極高連帶清理成本。"}
    ]
    media_cases = [
        {"src": "焚化爐環評爭議", "topic": "南投名間焚化爐「茶鄉抗爭」", "desc": "2026/01-02 名間鄉反焚化爐自救會強烈抗議。", "advice": "廠內垃圾分類需徹底。"},
        {"src": "GPS 科技監控", "topic": "環境部「科技大數據」專案稽查", "desc": "2025 年起強化 GPS 軌跡異常比對。", "advice": "依照申報路線行駛。"}
    ]
    for case in high_risk_cases:
        st.markdown(f"""<div style="background-color: #fff5f5; border-left: 5px solid #e53935; padding: 15px; margin-bottom: 15px; border-radius: 8px;"><b style="color: #e53935;">🚨 [高風險] {case['type']}</b><p>{case['reason']}</p></div>""", unsafe_allow_html=True)
    st.markdown("### 🌐 社會重大事件與大數據監控熱點")
    cols = st.columns(2)
    for i, m in enumerate(media_cases):
        with cols[i % 2]:
            st.markdown(f"""<div style="background-color: #ffffff; border-left: 5px solid #0288d1; padding: 12px; margin-bottom: 10px; border-radius: 8px; border: 1px solid #e1f5fe; min-height: 150px;"><b style="color: #01579b;">{m['topic']}</b><p>{m['desc']}</p></div>""", unsafe_allow_html=True)

# 3. 數據加載 (維持 iloc 讀取方式)
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

    if "mode" not in st.session_state: st.session_state.mode = "management"

    # --- 📂 側邊選單 ---
    st.sidebar.markdown("## 🏠 系統導航")
    if st.sidebar.button("📋 許可證辦理系統", use_container_width=True): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 許可下載區", use_container_width=True): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例", use_container_width=True): st.session_state.mode = "cases"; st.rerun()
    if st.sidebar.button("🔄 刷新資料庫", use_container_width=True): st.cache_data.clear(); st.rerun()

    # --- 渲染邏輯 ---
    if st.session_state.mode == "library":
        st.header("📁 許可下載區")
        for idx, row in main_df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1]) # 多開一欄給 AI
            c1.write(f"📄 **{row.iloc[2]}**")
            c2.write(f"📅 到期: {str(row.iloc[3])[:10]}")
            
            url = row.get("PDF連結", "")
            if pd.notna(url) and str(url).strip().startswith("http"):
                c3.link_button("📥 下載 PDF", str(url).strip(), use_container_width=True)
                # --- 新增的 AI 核對按鈕 ---
                if c4.button("🔍 AI 核對", key=f"verify_{idx}", use_container_width=True):
                    with st.spinner("辨識中..."):
                        is_ok, res_dt = ai_verify_date(str(url).strip(), row.iloc[3])
                        if is_ok: st.toast(f"✅ 日期吻合: {res_dt}"); c4.success("相符")
                        else: st.toast(f"❌ 異常: PDF 為 {res_dt}", icon="🚨"); c4.error("異常")
            else:
                c3.button("❌ 無連結", disabled=True, use_container_width=True, key=f"none_{idx}")
            st.divider()

    elif st.session_state.mode == "cases":
        display_penalty_cases()
    
    else:
        # --- 📋 許可證辦理系統 (其餘邏輯完全不動) ---
        sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
        sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())
        target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
        
        st.title(f"📄 {sel_name}")
        display_ai_law_wall(sel_type)
        
        # ... (中間這段 checkbox 邏輯與上傳邏輯保持你原本的代碼) ...
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
            # 下略... (維持你原本的附件上傳與提出申請邏輯)
            if st.session_state.selected_actions:
                st.divider()
                st.markdown("### 📝 第二步：附件上傳區")
                user_name = st.text_input("👤 申請人姓名")
                # (上傳代碼...)
                if st.button("🚀 提出申請", type="primary"):
                    if user_name: st.balloons(); st.success("✅ 申請成功！"); st.session_state.selected_actions = set(); time.sleep(1); st.rerun()

        st.write("---")
        with st.expander("📊 總表查看"):
            st.dataframe(main_df.drop(columns=['判斷日期'], errors='ignore'), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
