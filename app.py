import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐系統")

# 1. 附件庫
DB = {
    "P": {
        "展延": ["計畫書", "合約", "身分證"],
        "變更": ["申請表", "對照表", "圖說"],
        "異動": ["異動書", "證明文件"]
    },
    "C": {
        "展延": ["許可正本", "車照", "證照", "同意書"],
        "變更": ["變更表", "車證", "保單"],
        "變更暨展延": ["合併表", "全套附件", "統計表"]
    }
}

U = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

# 2. 讀取
df = pd.read_excel(U, sheet_name=0)

# 自動找欄位
def f_col(df, k):
    for c in df.columns:
        if k in str(c): return c
    return None

c_dt = f_col(df, "日期")
c_tp = f_col(df, "類型")
c_nm = f_col(df, "名稱")

if not c_dt or not c_nm:
    st.error("找不到日期或名稱欄位")
    st.stop()

df['D'] = pd.to_datetime(df[c_dt], errors='coerce')
df['T'] = df[c_tp].fillna("NA") if c_tp else "NA"

# 3. 選單
st.sidebar.header("選單")
ts = sorted(df['T'].unique().tolist())
s_t = st.sidebar.selectbox("1.類型", ts)
sub = df[df['T'] == s_t]
s_p = st.sidebar.radio("2.名稱", sub[c_name].tolist() if 'c_name' in locals() else sub[c_nm].tolist())

# 4. 畫面
if s_p:
    r = sub[sub[c_nm] == s_p].iloc[0]
    st.title(s_p)
    
    # 日期顯示 (改為最簡單的寫法避免截斷)
    d_obj = r['D']
    if pd.notnull(d_obj):
        d_str = d_obj.strftime('%Y-%m-%d')
        st.write("📅 到期日:", d_str)
    else:
        st.write("📅 到期日: 未填")

    # 按鈕邏輯
    acts = None
    if "清除" in str(s_p):
        acts = DB["C"]
    elif "清理" in str(s_p) or "計畫" in str(s_p):
        acts = DB["P"]

    if acts:
        st.divider()
        for n in acts.keys():
            if st.button(n, key=n+
