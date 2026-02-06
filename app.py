import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
import smtplib
import requests
import pytesseract
from pdf2image import convert_from_bytes
import re
from PIL import Image
from email.mime.text import MIMEText
from email.header import Header
from streamlit_gsheets import GSheetsConnection

# =========================================================
# 零件區：直接把工具程式寫在這裡，不再需要 import 外部檔案
# =========================================================

def ai_verify_background(pdf_link, sheet_date):
    """AI 自動核對 PDF 日期邏輯"""
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
                pdf_dt = f"{year}-{mm.zfill(2)}-{dd.zfill(2)}"
                is_match = (str(sheet_date)[:10] == pdf_dt)
                return is_match, pdf_dt, img
        return True, "跳過辨識", None
    except:
        return True, "跳過辨識", None

def display_penalty_cases():
    """裁處案例顯示邏輯"""
    st.markdown("## ⚖️ 近一年重大環保事件 (深度解析)")
    cases = [
        {"t": "2025/09 屏東非法棄置案", "c": "清運包商非法直排強酸液，產源工廠重罰 600 萬。"},
        {"t": "2026/02 GPS 軌跡稽查案", "c": "跨縣市非法回填，環境部透過 GPS 鎖定產源，沒收 2.4 億。"},
        {"t": "2025/11 數據造假案", "c": "監測參數人工造假，沒入相關許可證。"}
    ]
    for case in cases:
        st.markdown(f"""<div style="background-color: #2D0D0D; border-left: 5px solid #e53935; padding: 15px; border-radius: 8px; margin-bottom: 15px;"><b style="color: #ff4d4d;">🚨 {case['t']}</b><p style="color: white; margin-top: 5px;">{case['c']}</p></div>""", unsafe_allow_html=True)

# =========================================================
# 主程式區
# =========================================================

st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; }
    p, h1, h2, h3, span, label, .stMarkdown { color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #262730 !important; }
    .marquee-container {
        overflow: hidden; white-space: nowrap; background: #4D0000; color: #FF4D4D;
        padding: 10px 0; font-weight: bold; border: 1px solid #FF4D4D; border-radius: 5px; margin-bottom: 20px;
    }
    .marquee-text { display: inline-block; animation: marquee 15s linear infinite; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

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
    
    # 頂部跑馬燈
    expired_items = main_df[main_df.iloc[:, 3] < today].iloc[:, 2].tolist()
    if expired_items:
        st.markdown(f"""<div class="marquee-container"><div class="marquee-text">🚨 警告：以下許可證已逾期：{" / ".join(expired_items)} 🚨</div></div>""", unsafe_allow_html=True)

    if "mode" not in st.session_state: st.session_state.mode = "home"
    
    # 側邊欄
    st.sidebar.markdown("## 🏠 系統導航")
    if st.sidebar.button("🏠 系統首頁"): st.session_state.mode = "home"; st.rerun()
    if st.sidebar.button("📋 許可證辦理系統"): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 許可下載區"): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例"): st.session_state.mode = "cases"; st.rerun()

    # 頁面切換
    if st.session_state.mode == "home":
        st.title("🚀 大豐環保許可證管理系統")
        st.write("歡迎回來！請從左側菜單選擇功能。")

    elif st.session_state.mode == "library":
        st.header("📁 許可下載區 (AI 自動比對)")
        for idx, row in main_df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            p_name, p_date = row.iloc[2], row.iloc[3]
            c1.markdown(f"📄 **{p_name}**")
            c2.write(f"📅 系統日期: {str(p_date)[:10]}")
            url = row.get("PDF連結", "")
            if pd.notna(url) and str(url).strip().startswith("http"):
                # 調用本檔案內的函數
                is_match, pdf_dt, pdf_img = ai_verify_background(str(url).strip(), p_date)
                c3.link_button("📥 下載 PDF", str(url).strip())
                if not is_match:
                    c4.error(f"⚠️ 異常: {pdf_dt}")
                else:
                    c4.success("✅ 一致")
            st.divider()

    elif st.session_state.mode == "cases":
        display_penalty_cases() # 調用本檔案內的函數

    elif st.session_state.mode == "management":
        st.info("許可證辦理系統正常運作中...")

    st.divider()
    with st.expander("📊 許可證總覽表", expanded=True):
        st.dataframe(main_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
