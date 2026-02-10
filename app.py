import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from streamlit_gsheets import GSheetsConnection

# 1. 頁面基礎設定 (必須放在最前面)
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# 2. 初始化 Session State (這步沒做，第 2 行就會報 NameError)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 3. 員工登入頁面邏輯 (中間集中版)
if not st.session_state.logged_in:
    empty_l, login_col, empty_r = st.columns([1, 1.5, 1])
    with login_col:
        st.write("#")
        st.write("#")
        with st.container(border=True):
            st.title("🔐 員工登入")
            st.markdown("請輸入您的認證資訊以進入系統")
            emp_id = st.text_input("👤 員工編號", placeholder="例如: DF001")
            emp_pwd = st.text_input("🔑 登入密碼", type="password", placeholder="****")
            st.write("#")
            if st.button("登入系統", use_container_width=True, type="primary"):
                if emp_id == "DF001" and emp_pwd == "1234":
                    st.session_state.logged_in = True
                    st.success("✅ 登入成功！")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ 員編或密碼錯誤")
    st.stop() # 擋住後面所有程式碼

# --- 4. 引用零件 (登入後才引用，更安全) ---
try:
    from ai_engine import ai_verify_background
    from ui_components import display_penalty_cases
except ImportError:
    st.error("❌ 找不到核心零件，請確認 ai_engine.py 與 ui_components.py 是否已移至根目錄。")
    st.stop()

# --- 5. 接下來接你原本的 CSS、載入資料、跑馬燈等邏輯 ---
# ... (後面完全照舊)
