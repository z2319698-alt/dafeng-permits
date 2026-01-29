import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁配置
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 定義法規動作庫 (根據關鍵字匹配，供按鈕顯示使用)
ACTION_DATABASE = {
    "廢棄物": {"展延": "📅 期滿前 2-3 個月提出。", "變更": "⚙️ 產出量/種類變更 15-30 日內提出。", "異動": "🔄 基本資料修正。"},
    "空污": {"展延": "📅 期滿前 3-6 個月提出。", "變更": "⚙️ 設備變更前需重新申請。", "異動": "🔄 參數微調紀錄。"},
    "水污": {"展延": "📅 期滿前 4-6 個月提出。", "變更": "⚙️ 負責人變更 30 日內。", "異動": "🔄 系統修正。"},
    "毒化物": {"展延": "📅 期滿前 1-3 個月提出。", "變更": "⚙️ 種類增減前需申請。", "異動": "🔄 聯絡人變更。"},
    "應回收": {"展延": "📅 期滿前 1 個月提出。", "變更": "⚙️ 廠址變更需重新辦理登記。"}
}

# 3. 讀取資料
sheet_url = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    # 讀取 Excel
    df = pd.read_excel(sheet_url, sheet_name='大豐既有許可證到期提醒')
    df['到期日期'] = pd.to_datetime(df['到期日期'], errors='coerce')
    # 確保「許可證類型」沒有空值，方便分類
    df['許可證類型'] = df['許可證類型'].fillna("未分類")
    return df

df = load_data()
today = datetime.now()

# 4. 頂部警報跑馬燈
urgent = df[(df['到期日期'] <= today + pd.Timedelta(days=180)) & (df['到期日期'].notnull())]
if not urgent.empty:
    alert_text = "　　".join([f"🚨 {row['許可證名稱']} (剩 {(row['到期日期']-today).days} 天)" for _, row in urgent.iterrows()])
    st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{alert_text}</marquee></div>', unsafe_allow_html=True)

# 5. 左側分類導航欄
with st.sidebar:
    st.header("📂 系統導航")
    
    # 第一層：直接抓 Excel 裡的「許可證類型」
    type_list = sorted(df['許可證類型
