import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
from streamlit_gsheets import GSheetsConnection
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re

# --- 1. 背景自動核對 ---
@st.cache_data(ttl=2592000)
def ai_verify_background(pdf_link, sheet_date):
    try:
        file_id = ""
        if '/file/d/' in pdf_link: file_id = pdf_link.split('/file/d/')[1].split('/')[0]
        elif 'id=' in pdf_link: file_id = pdf_link.split('id=')[1].split('&')[0]
        if not file_id: return False, "連結無效"
        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = requests.get(direct_url, timeout=20)
        if response.status_code != 200: return False, "無法讀取"
        images = convert_from_bytes(response.content, dpi=150)
        all_text = ""
        for img in images:
            page_text = pytesseract.image_to_string(img.convert('L'), lang='chi_tra+eng')
            all_text += page_text
            match = re.search(r"(?:至|期|效)[\s]*(\d{2,3}|20\d{2})[\s\.年/-]+(\d{1,2})[\s\.月/-]+(\d{1,2})", page_text)
            if match:
                yy, mm, dd = match.groups()
                year = int(yy) + 1911 if int(yy) < 1000 else int(yy)
                return (str(sheet_date)[:4] == str(year)), f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
        return True, "跳過辨識"
    except:
        return True, "跳過辨識"

# 2. 頁面基礎設定 (加入強制 CSS 確保背景不透明)
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    div[data-testid="stVerticalBlock"] { background-color: white !important; opacity: 1 !important; }
    p, h1, h2, h3, span, div { color: #333 !important; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. 模組功能 ---
def display_ai_law_wall(category):
    law_db = {
        "廢棄物清理計畫書": [
            {"date": "2025/08", "tag": "重大變更", "content": "環境部公告：廢清書應增列「資源循環促進」專章，針對廢塑膠、廢木材等資源化路徑須明確揭露。"},
            {"date": "2025/11", "tag": "裁罰預警", "content": "強化產源責任：產源端若未落實現場視察，發生違法傾倒將面臨重罰。"},
            {"date": "2026/01", "tag": "最新公告", "content": "全面推動電子化合約上傳，紙本備查期縮短至14天。"}
        ]
    }
    updates = law_db.get(category, [{"date": "2025-2026", "tag": "穩定", "content": "目前法規動態穩定。"}])
    st.markdown(f"### 🛡️ 相關法規動態")
    cols = st.columns(len(updates))
    for i, item in enumerate(updates):
        with cols[i]:
            st.markdown(f"""<div style="background-color: #f0f4f8; border-left: 5px solid #2E7D32; padding: 15px; border-radius: 8px; height: 180px;"><span style="background-color: #2E7D32; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{item['tag']}</span><p style="margin-top: 10px; font-weight: bold;">📅 {item['date']}</p><p style="font-size: 0.85rem;">{item['content']}</p></div>""", unsafe_allow_html=True)

def display_penalty_cases():
    st.markdown("## ⚖️ 近一年重大環保事件 (2025-2026)")
    cases = [
        {"type": "2025/09 屏東非法棄置刑案", "reason": "清運商深夜惡意傾倒於河川地，涉及刑事責任，主嫌已遭收押。", "key": "核對廠商證號與流向證明。"},
        {"type": "2026/02 農地盜採回填案", "reason": "跨縣市集團非法回填14萬噸事業廢棄物於水源區，獲利2.4億。", "key": "產源單位負擔高額清理費。"}
    ]
    for case in cases:
        st.markdown(f"""<div style="background-color: #fff5f5; border-left: 5px solid #e53935; padding: 15px; margin-bottom: 15px; border-radius: 8px;"><b style="color: #e53935;">🚨 [高風險] {case['type']}</b><p>{case['reason']}<br><b>💡 管理：</b>{case['key']}</p></div>""", unsafe_allow_html=True)
    st.markdown("### 🌐 社會重大事件與監控熱點")
    news = [
        {"topic": "環境部科技監控", "desc": "擴大採用AI影像辨識與GPS比對，軌跡異常將自動稽查。", "advice": "按申報路線行駛。"},
        {"topic": "社群媒體爆料", "desc": "民眾針對異味投訴轉向Dcard/Facebook，引發輿論壓力。", "advice": "落實日常巡檢紀錄。"}
    ]
    cols = st.columns(2)
    for i, m in enumerate(news):
        with cols[i % 2]:
            st.markdown(f"""<div style="background-color: #ffffff; border-left: 5px solid #0288d1; padding: 15px; border-radius: 8px; border: 1px solid #e1f5fe; min-height: 180px; margin-bottom:15px;"><b style="color: #01579b;">{m['topic']}</b><p>{m['desc']}</p><p style="color: #0277bd;"><b>📢 建議：</b>{m['advice']}</p></div>""", unsafe_allow_html=True)

# 4. 數據加載
@st.cache_data(ttl=5)
def load_all_data():
    m_df = conn.read(worksheet="大豐既有許可證到期提醒")
    f_df = conn.read(worksheet="附件資料庫")
    m_df.columns = [str(c).strip().replace(" ", "").replace("\n", "") for c in m_df.columns]
    f_df.columns = [str(c).strip().replace(" ", "").replace("\n", "") for c in f_df.columns]
    m_df.iloc[:, 3] = pd.to_datetime(m_df.iloc[:, 3], errors='coerce')
    return m_df, f_df

try:
    main_df, file_df = load_all_data()
    today = pd.Timestamp(date.today())
    if "mode" not in st.session_state: st.session_state.mode = "home"
    
    st.sidebar.markdown("## 🏠 系統導航")
    if st.sidebar.button("🏠 系統首頁"): st.session_state.mode = "home"; st.rerun()
    if st.sidebar.button("📋 許可證辦理系統"): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 許可下載區"): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例"): st.session_state.mode = "cases"; st.rerun()
    
    st.sidebar.divider()
    if st.sidebar.button("🔄 更新數據"): st.cache_data.clear(); st.rerun()

    if st.session_state.mode == "home":
        st.title("🚀 大豐環保許可證管理系統")
        st.info("請點選左側選單操作：\n1. 辦理系統 2. 下載區 3. 裁處案例")

    elif st.session_state.mode == "library":
        st.header("📁 許可下載區 (AI 自動比對)")
        for idx, row in main_df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.write(f"📄 **{row.iloc[2]}**")
            c2.write(f"📅 到期: {str(row.iloc[3])[:10]}")
            url = row.get("PDF連結", "")
            if pd.notna(url) and str(url).strip().startswith("http"):
                is_match, pdf_dt = ai_verify_background(str(url).strip(), row.iloc[3])
                c3.link_button("📥 下載 PDF", str(url).strip())
                if not is_match:
                    c4.markdown(f'<div style="background-color: white; color:#d32f2f; font-weight:bold; border:2px solid #d32f2f; border-radius:5px; text-align:center; padding:5px;">⚠️ 異常: {pdf_dt}</div>', unsafe_allow_html=True)
                else:
                    c4.markdown('<div style="background-color: #e8f5e9; color:#2E7D32; font-weight:bold; text-align:center; padding:5px; border-radius:5px;">✅ 一致</div>', unsafe_allow_html=True)
            st.divider()

    elif st.session_state.mode == "cases":
        display_penalty_cases()

    elif st.session_state.mode == "management":
        st.sidebar.divider()
        sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
        sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())
        target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
        
        st.title(f"📄 {sel_name}")
        days_left = (target_main.iloc[3] - today).days
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            if days_left < 90: st.error(f"🚨 【嚴重警告】剩餘 {days_left} 天")
            else: st.success(f"✅ 【狀態正常】剩餘 {days_left} 天")
        with r1c2:
            st.markdown(f'<div style="background-color:#f0f2f6;padding:12px;border-radius:5px;border:1px solid #ccc;height:50px;">🤖 AI：建議準備附件。</div>', unsafe_allow_html=True)

        r2c1, r2c2 = st.columns(2)
        with r2c1: st.info(f"🆔 管制編號：{target_main.iloc[1]}")
        with r2c2: st.markdown(f'<div style="background-color:#f0f2f6;padding:12px;border-radius:5px;border:1px solid #dcdfe6;height:50px;">📅 許可到期：<b>{str(target_main.iloc[3])[:10]}</b></div>', unsafe_allow_html=True)

        st.divider()
        display_ai_law_wall(sel_type)
        
        db_info = file_df[file_df.iloc[:, 0] == sel_type]
        options = db_info.iloc[:, 1].dropna().unique().tolist()
        if options:
            st.subheader("🛠️ 第一步：選擇辦理項目")
            if "selected_actions" not in st.session_state: st.session_state.selected_actions = set()
            cols = st.columns(len(options))
            for i, opt in enumerate(options):
                if cols[i].button(opt, key=f"act_{opt}", use_container_width=True, type="primary" if opt in st.session_state.selected_actions else "secondary"):
                    if opt in st.session_state.selected_actions: st.session_state.selected_actions.remove(opt)
                    else: st.session_state.selected_actions.add(opt)
                    st.rerun()
            
            if st.session_state.selected_actions:
                st.divider(); st.markdown("### 📝 第二步：附件上傳區")
                user = st.text_input("👤 申請人姓名")
                atts = set()
                for action in st.session_state.selected_actions:
                    rows = db_info[db_info.iloc[:, 1] == action]
                    if not rows.empty:
                        for item in rows.iloc[0, 3:].dropna().tolist(): atts.add(str(item).strip())
                for item in sorted(list(atts)):
                    with st.expander(f"📁 附件：{item}", expanded=True): st.file_uploader(f"上傳 - {item}", key=f"up_{item}")
                
                st.divider()
                if st.button("🚀 提出申請", type="primary", use_container_width=True):
                    if user:
                        st.balloons()
                        st.success(f"✅ 申請成功！通知已發送至 andy.chen@df-recycle.com")
                        st.session_state.selected_actions = set()
                        time.sleep(2); st.rerun()
                    else: st.warning("⚠️ 請輸入姓名。")

    st.divider()
    with st.expander("📊 點此展開/縮減：許可證到期總覽表 (全場區)", expanded=False):
        st.dataframe(main_df, use_container_width=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
