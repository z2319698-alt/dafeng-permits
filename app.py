import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
import smtplib
import sys
import os
from email.mime.text import MIMEText
from email.header import Header
from streamlit_gsheets import GSheetsConnection

# --- 核心修復：強制指向 .devcontainer 內的「工具」資料夾 ---
# 取得目前 app.py 所在的根目錄
base_path = os.path.dirname(os.path.abspath(__file__))

# 拼接出你目前的真實路徑：.devcontainer/工具
# 注意：這裡的名稱必須跟你在 GitHub 看到的一模一樣 (包含大小寫)
secret_path = os.path.join(base_path, ".devcontainer", "工具")

# 把這個秘密路徑塞進 Python 的搜尋清單
if secret_path not in sys.path:
    sys.path.insert(0, secret_path)

# --- 引用模組 (因為已經指路，所以直接 import 檔案名稱即可) ---
try:
    from ai_engine import ai_verify_background
    from ui_components import display_penalty_cases
except ImportError as e:
    st.error(f"❌ 還是找不到零件！")
    st.info(f"系統嘗試尋找的路徑是：{secret_path}")
    st.write(f"目前資料夾內的檔案有：{os.listdir(secret_path) if os.path.exists(secret_path) else '路徑不存在'}")

# --- 1. 頁面基礎設定 ---
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; }
    p, h1, h2, h3, span, label, .stMarkdown { color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #262730 !important; }
    .stDataFrame { background-color: #FFFFFF; }
    @keyframes marquee {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    .marquee-container {
        overflow: hidden; white-space: nowrap; background: #4D0000; color: #FF4D4D;
        padding: 10px 0; font-weight: bold; border: 1px solid #FF4D4D; border-radius: 5px; margin-bottom: 20px;
    }
    .marquee-text { display: inline-block; animation: marquee 15s linear infinite; }
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
        st.markdown(f"""<div class="marquee-container"><div class="marquee-text">🚨 警告：以下許可證已逾期，請立即處理：{" / ".join(expired_items)} 🚨</div></div>""", unsafe_allow_html=True)

    if "mode" not in st.session_state: st.session_state.mode = "home"
    
    # 側邊欄導航
    st.sidebar.markdown("## 🏠 系統導航")
    if st.sidebar.button("🏠 系統首頁"): st.session_state.mode = "home"; st.rerun()
    if st.sidebar.button("📋 許可證辦理系統"): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 許可下載區"): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例"): st.session_state.mode = "cases"; st.rerun()
    st.sidebar.divider()
    if st.sidebar.button("🔄 更新資料庫"): st.cache_data.clear(); st.rerun()

    # --- 頁面分配 ---
    if st.session_state.mode == "home":
        st.title("🚀 大豐環保許可證管理系統")
        st.markdown("---")
        st.markdown("### 💡 核心功能導引")

    elif st.session_state.mode == "library":
        st.header("📁 許可下載區 (AI 比對)")
        for idx, row in main_df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            p_name, p_date = row.iloc[2], row.iloc[3]
            c1.markdown(f"📄 **{p_name}**")
            c2.write(f"📅 到期: {str(p_date)[:10]}")
            url = row.get("PDF連結", "")
            if pd.notna(url) and str(url).strip().startswith("http"):
                # 直接使用零件
                is_match, pdf_dt, pdf_img = ai_verify_background(str(url).strip(), p_date)
                c3.link_button("📥 下載 PDF", str(url).strip())
                if not is_match:
                    c4.error(f"⚠️ 異常: {pdf_dt}")
                else:
                    c4.success("✅ 一致")
            st.divider()

    elif st.session_state.mode == "cases":
        display_penalty_cases() # 直接使用零件

    elif st.session_state.mode == "management":
        st.write("辦理系統運作中...")

    with st.expander("📊 許可證總覽表", expanded=True):
        st.dataframe(main_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
