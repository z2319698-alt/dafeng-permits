import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="測試中", layout="wide")

# 2. ！！！關鍵測試點！！！
# 如果你在網頁上沒看到下面這行「橘色大字」，代表你的 GitHub 更新根本沒生效！
st.markdown("<h1 style='color: orange;'>🔥 測試中：如果你看到這行，代表 GitHub 同步成功了</h1>", unsafe_allow_html=True)

# 3. 抓取資料並強行呈現 C 欄與 D 欄
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

try:
    # 每次都重新抓取，不使用快取
    df = pd.read_excel(URL, sheet_name="大豐既有許可證到期提醒")
    
    # 強制合併 C 欄 (Index 2) 與 D 欄 (Index 3)
    # 我們在產生選單時就把它黏起來
    df["組合標題"] = df.apply(lambda r: f"{str(r.iloc[2])} ({str(r.iloc[3])[:10]})", axis=1)
    
    # 側邊選單
    sel = st.sidebar.radio("請選擇許可證", df["組合標題"].tolist())
    
    # ✅ 標題直接噴出你選到的組合（含日期）
    st.title(f"📄 {sel}")
    
    st.write("目前讀取到的 D 欄原始數據：", df.iloc[0, 3])

except Exception as e:
    st.error(f"錯誤：{e}")
