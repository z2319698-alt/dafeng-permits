import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐系統")

# 改用英文 Key 避免匹配截斷
DB = {
    "P": {
        "展延": ["計畫書", "合約", "身分證"],
        "變更": ["申請表", "對照表", "圖說"],
        "異動": ["異動書", "證明文件"]
    },
    "C": {
        "展延": ["原許可正本", "車照", "證照"],
        "變更": ["變更表", "車證", "保單"],
        "變更暨展延": ["合併表", "全套附件", "統計表"]
    }
}

U = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load():
    df = pd.read_excel(U, sheet_name=0)
    df['D'] = pd.to_datetime(df['到期日期'], errors='coerce')
    df['T'] = df['許可證類型'].fillna("NA")
    return df

try:
    df = load()
except:
    st.stop()

now = dt.now()
with st.sidebar:
    st.header("選單")
    ts = sorted(df['T'].unique().tolist())
    st_t = st.selectbox("1.類型", ts)
    sub = df[df['T'] == st_t]
    st_p = st.radio("2.名稱", sub['許可證名稱'].tolist())

if st_p:
    r = df[df['許可證名稱'] == st_p].iloc[0]
    st.title(st_p)
    d = r['D']
    st.write("到期日:", d.strftime('%Y-%m-%d'))
    
    # 邏輯判斷拆成兩行
    acts = None
    if "清除" in str(st_p):
        acts = DB["C"]
    elif "清理" in str(st_p):
        acts = DB["P"]

    if acts:
        st.divider()
        for n in acts.keys():
            if st.button(n, key=n+str(st_p)):
                st.session_state["cur"] = n
        
        cur = st.session_state.get("cur")
        if cur in acts:
            st.success("辦理:" + cur)
            for f in acts[cur]:
                st.checkbox(f, key=f+str(st_p))

with st.expander("總表"):
