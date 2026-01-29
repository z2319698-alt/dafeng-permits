import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐管理系統")

# 1. 附件資料庫 (P=清理計畫, C=清除許可)
DB = {
    "P": {
        "展延": ["清理計畫書(更新版)", "廢棄物合約影本", "負責人身分證影本"],
        "變更": ["變更申請表", "差異對照表", "製程說明圖"],
        "異動": ["異動申請書", "相關證明文件"]
    },
    "C": {
        "展延": ["原許可正本", "車照", "證照", "處置同意書"],
        "變更": ["變更表", "車證", "保險單"],
        "變更暨展延": ["合併申請書", "全套附件", "統計表"]
    }
}

U = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

# 2. 讀取並自動校正欄位名稱
df = pd.read_excel(U, sheet_name=0)

# 自動尋找關鍵欄位 (防止 KeyError)
def find_col(df, keyword):
    for c in df.columns:
        if keyword in str(c): return c
    return None

c_date = find_col(df, "日期")
c_type = find_col(df, "類型")
c_name = find_col(df, "名稱")

if not c_date or not c_name:
    st.error("Excel 找不到 '日期' 或 '名稱' 欄位，請檢查標題！")
    st.write("目前偵測到的欄位有：", list(df.columns))
    st.stop()

df['D'] = pd.to_datetime(df[c_date], errors='coerce')
df['T'] = df[c_type].fillna("未分類") if c_type else "未分類"
now = dt.now()

# 3. 側邊導航
st.sidebar.header("選單")
ts = sorted(df['T'].unique().tolist())
st_t = st.sidebar.selectbox("1.類型", ts)
sub = df[df['T'] == st_t]
st_p = st.sidebar.radio("2.名稱", sub[c_name].tolist())

# 4. 主畫面
if st_p:
    r = sub[sub[c_name] == st_p].iloc[0]
    st.title(st_p)
    d = r['D']
    st.write("📅 到期日:", d.strftime('%Y-%m-%d') if
