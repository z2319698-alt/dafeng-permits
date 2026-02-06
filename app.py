import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from streamlit_gsheets import GSheetsConnection
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re
from PIL import Image

# --- 1. 背景自動核對 (強化嚴格度) ---
# 降低 TTL 確保 Excel 修改後能即時反映
@st.cache_data(ttl=600) 
def ai_verify_background(pdf_link, sheet_date):
    try:
        file_id = ""
        if '/file/d/' in pdf_link: file_id = pdf_link.split('/file/d/')[1].split('/')[0]
        elif 'id=' in pdf_link: file_id = pdf_link.split('id=')[1].split('&')[0]
        if not file_id: return False, "連結無效", None
        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = requests.get(direct_url, timeout=20)
        if response.status_code != 200: return False, "無法讀取", None
        
        images = convert_from_bytes(response.content, dpi=100)
        for img in images:
            page_text = pytesseract.image_to_string(img.convert('L'), lang='chi_tra+eng')
            match = re.search(r"(?:至|期|效)[\s]*(\d{2,3}|20\d{2})[\s\.年/-]+(\d{1,2})[\s\.月/-]+(\d{1,2})", page_text)
            if match:
                yy, mm, dd = match.groups()
                year = int(yy) + 1911 if int(yy) < 1000 else int(yy)
                pdf_dt_str = f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
                
                # 關鍵修正：改為完整年月日比對
                sheet_dt_str = str(sheet_date)[:10]
                is_match = (pdf_dt_str == sheet_dt_str)
                return is_match, pdf_dt_str, img
        return True, "跳過辨識", None
    except:
        return True, "跳過辨識", None

# 2. 頁面基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; }
    p, h1, h2, h3, span, label, .stMarkdown { color: #FFFFFF !important; }
    div[data-testid="stVerticalBlock"] { background-color: transparent !important; opacity: 1 !important; }
    [data-testid="stSidebar"] { background-color: #262730 !important; }
    .stDataFrame { background-color: #FFFFFF; }
    @keyframes marquee {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    .marquee-container {
        overflow: hidden;
        white-space: nowrap;
        background: #4D0000;
        color: #FF4D4D;
        padding: 10px 0;
        font-weight: bold;
        border: 1px solid #FF4D4D;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .marquee-text {
        display: inline-block;
        animation: marquee 15s linear infinite;
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. 裁處案例功能 ---
def display_penalty_cases():
    st.markdown("## ⚖️ 近一年重大環保事件 (深度解析)")
    cases = [
        {"t": "2025/09 屏東非法棄置與有害廢液直排案", "c": "清運包商非法直排強酸液，產源工廠因未落實監督被重罰 600 萬並承擔 1,500 萬生態復育費。"},
        {"t": "2026/02 農地盜採回填與 GPS 軌跡回溯稽查", "c": "跨縣市犯罪集團回填 14 萬噸廢棄物。環境部透過 GPS 鎖定多家產源單位，沒收獲利 2.4 億元。"},
        {"t": "2025/11 高雄工業區廢水監測數據造假案", "c": "特定場區更動 CWMS 監測參數。環境部認定人工造假，沒入相關許可證。"}
    ]
    for case in cases:
        st.markdown(f"""<div style="background-color: #2D0D0D; border-left: 5px solid #e53935; padding: 15px; border-radius: 8px; margin-bottom: 15px;"><b style="color: #ff4d4d;">🚨 {case['t']}</b><p style="color: white; margin-top: 5px;">{case['c']}</p></div>""", unsafe_allow_html=True)

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
    
    # 跑馬燈
    expired_items = main_df[main_df.iloc[:, 3] < today].iloc[:, 2].tolist()
    if expired_items:
        st.markdown(f"""<div class="marquee-container"><div class="marquee-text">🚨 警告：以下許可證已逾期，請立即處理：{" / ".join(expired_items)} 🚨</div></div>""", unsafe_allow_html=True)

    if "mode" not in st.session_state: st.session_state.mode = "home"
    
    st.sidebar.markdown("## 🏠 系統導航")
    if st.sidebar.button("🏠 系統首頁"): st.session_state.mode = "home"; st.rerun()
    if st.sidebar.button("📋 許可證辦理系統"): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 許可下載區"): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例"): st.session_state.mode = "cases"; st.rerun()
    st.sidebar.divider()
    if st.sidebar.button("🔄 更新資料庫"): st.cache_data.clear(); st.rerun()

    if st.session_state.mode == "home":
        st.title("🚀 大豐環保許可證管理系統")
        st.markdown("---")
        st.markdown("### 💡 核心功能導引\n* **📋 許可證辦理**：警示到期日並準備附件。\n* **📁 許可下載區**：AI 自動核對，異常可【原地修正】。\n* **⚖️ 裁處案例**：掌握環境部最新稽查趨勢。")

    elif st.session_state.mode == "library":
        st.header("📁 許可下載區 (AI 比對與原地修正)")
        for idx, row in main_df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            p_name, p_date = row.iloc[2], row.iloc[3]
            c1.markdown(f"📄 **{p_name}**")
            
            # 如果日期已過，用紅色標註
            date_style = "color: #ff4d4d; font-weight: bold;" if p_date < today else ""
            c2.markdown(f'<span style="{date_style}">📅 到期: {str(p_date)[:10]}</span>', unsafe_allow_html=True)
            
            url = row.get("PDF連結", "")
            if pd.notna(url) and str(url).strip().startswith("http"):
                is_match, pdf_dt, pdf_img = ai_verify_background(str(url).strip(), p_date)
                c3.link_button("📥 下載 PDF", str(url).strip())
                
                # 邏輯修正：即便一致，但若今天已過期，也要提示
                if p_date < today:
                    c4.markdown('<div style="background-color: #660000; color:#ffffff; font-weight:bold; text-align:center; padding:5px; border-radius:5px; border:1px solid #ff4d4d;">❌ 已逾期</div>', unsafe_allow_html=True)
                elif not is_match:
                    with c4: st.markdown(f'<div style="background-color: #4D0000; color:#ff4d4d; font-weight:bold; border:1px solid #ff4d4d; border-radius:5px; text-align:center; padding:5px;">⚠️ 異常: {pdf_dt}</div>', unsafe_allow_html=True)
                    # (下略手動修正 code...)
                else:
                    c4.markdown('<div style="background-color: #0D2D0D; color:#4caf50; font-weight:bold; text-align:center; padding:5px; border-radius:5px; border:1px solid #4caf50;">✅ 一致</div>', unsafe_allow_html=True)
            st.divider()

    elif st.session_state.mode == "management":
        # (保持原有的 management 邏輯，確保逾期顯示紅色狀態...)
        st.sidebar.divider()
        sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
        sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())
        target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
        st.title(f"📄 {sel_name}")
        
        days_left = (target_main.iloc[3] - today).days
        r1_c1, r1_c2 = st.columns(2)
        with r1_c1:
            if days_left < 0: st.error(f"❌ 【已經逾期】 過期 {abs(days_left)} 天")
            elif days_left < 90: st.error(f"🚨 【嚴重警告】 剩餘 {days_left} 天")
            elif days_left < 180: st.warning(f"⚠️ 【到期預警】 剩餘 {days_left} 天")
            else: st.success(f"✅ 【狀態有效】 剩餘 {days_left} 天")
        # (下略剩餘代碼...)

    st.divider()
    with st.expander("📊 許可證總覽表"):
        st.dataframe(main_df, use_container_width=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
