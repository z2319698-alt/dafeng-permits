import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from streamlit_gsheets import GSheetsConnection

# --- 引用根目錄零件 ---
from ai_engine import ai_verify_background
from ui_components import display_penalty_cases

# 頁面基礎設定
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# CSS 樣式
st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; }
    p, h1, h2, h3, span, label, .stMarkdown { color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #262730 !important; }
    .stDataFrame { background-color: #FFFFFF; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
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
    
    # 初始化 session_state (修正你看到的報錯)
    if "mode" not in st.session_state: st.session_state.mode = "home"
    if "selected_actions" not in st.session_state: st.session_state.selected_actions = set()

    # 逾期跑馬燈
    expired_items = main_df[main_df.iloc[:, 3] < today].iloc[:, 2].tolist()
    if expired_items:
        st.markdown(f'<div class="marquee-container"><div class="marquee-text">🚨 警告：以下許可證已逾期：{" / ".join(expired_items)}</div></div>', unsafe_allow_html=True)

    # 側邊欄
    st.sidebar.markdown("## 🏠 系統導航")
    if st.sidebar.button("🏠 系統首頁"): st.session_state.mode = "home"; st.rerun()
    if st.sidebar.button("📋 許可證辦理系統"): st.session_state.mode = "management"; st.rerun()
    if st.sidebar.button("📁 許可下載區"): st.session_state.mode = "library"; st.rerun()
    if st.sidebar.button("⚖️ 近期裁處案例"): st.session_state.mode = "cases"; st.rerun()
    st.sidebar.divider()
    if st.sidebar.button("🔄 更新資料庫"): st.cache_data.clear(); st.rerun()

    # --- 頁面分流 ---
    if st.session_state.mode == "home":
        st.title("🚀 大豐環保許可證管理系統")
        st.markdown("---")
        st.markdown("### 💡 核心功能\n* **📋 許可證辦理**：自動比對附件與到期日。\n* **📁 許可下載區**：AI 自動比對 PDF 日期。\n* **⚖️ 裁處案例**：掌握環境部最新稽查趨勢。")

    elif st.session_state.mode == "cases":
        display_penalty_cases() # 呼叫 ui_components.py

    elif st.session_state.mode == "library":
        st.header("📁 許可下載區 (AI 比對)")
        for idx, row in main_df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            p_name, p_date, url = row.iloc[2], row.iloc[3], row.get("PDF連結", "")
            c1.markdown(f"📄 **{p_name}**")
            c2.write(f"📅 到期: {str(p_date)[:10]}")
            if pd.notna(url) and str(url).startswith("http"):
                is_match, pdf_dt, pdf_img = ai_verify_background(str(url).strip(), p_date)
                c3.link_button("📥 下載", str(url).strip())
                if not is_match:
                    c4.error(f"⚠️ 異常: {pdf_dt}")
                    with st.expander("🛠️ 修正"):
                        if pdf_img: st.image(pdf_img, use_container_width=True)
                        new_date = st.date_input("正確日期", value=p_date.date(), key=f"f_{idx}")
                        if st.button("更新", key=f"b_{idx}"):
                            main_df.loc[idx, main_df.columns[3]] = pd.to_datetime(new_date)
                            conn.update(worksheet="大豐既有許可證到期提醒", data=main_df)
                            st.success("更新成功！"); time.sleep(1); st.rerun()
                else:
                    c4.success("✅ 一致")
            st.divider()

    elif st.session_state.mode == "management":
        # ... (此處保留你原本 management 模式的邏輯，包含寄信功能)
        st.info("許可證辦理系統運行中...")
        # 為了簡潔，這裡暫時簡化，你可以把原本 management 的代碼貼回來

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
