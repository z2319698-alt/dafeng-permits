import streamlit as st
import pandas as pd

# 1. 頁面設定
st.set_page_config(page_title="最終測試", layout="wide")

# 2. 強制定義一個紫色大標題，如果這行沒出現，代表你的代碼根本沒更新成功
st.markdown("<h1 style='color: purple;'>紫色測試標題：如果看到這行代表更新成功</h1>", unsafe_allow_html=True)

# 3. 直接讀取資料 (不進快取)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

try:
    df = pd.read_excel(URL)
    df.columns = [str(c).strip() for c in df.columns]
    
    # 這裡直接把 C 欄名稱 (索引2) 和 E 欄日期 (索引4) 黏起來
    # 這是你要的：C2-C17 + E2-E17
    df["組合"] = df.apply(lambda r: f"{r.iloc[2]} ({str(r.iloc[4])[:10]})", axis=1)
    
    # 4. 側邊選單
    sel = st.sidebar.radio("請選擇許可證", df["組合"].tolist())
    
    # 5. 畫面呈現
    st.subheader("目前選中：")
    st.title(sel) # 這裡顯示的 sel 已經內含 (日期) 了
    
    # 顯示原始資料核對
    st.write("目前抓到的日期原始資料：", df.iloc[0, 4])

except Exception as e:
    st.error(f"錯誤：{e}")
