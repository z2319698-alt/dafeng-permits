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

st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# (這裡放你的 CSS 樣式和資料讀取邏輯...)
# ... 

# 當切換到「近期裁處案例」時
if st.session_state.mode == "cases":
    display_penalty_cases()  # 只要這一行，就去讀取 ui_components.py 的內容

# 當在「許可下載區」需要 AI 核對時
# is_match, pdf_dt, pdf_img = ai_verify_background(url, p_date)
