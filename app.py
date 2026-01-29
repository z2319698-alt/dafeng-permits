import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐系統", layout="wide")

DB = {
    "清理計畫": {
        "展延": ["清理計畫書(更新版)", "廢棄物合約影本", "負責人身分證影本"],
        "變更": ["變更申請表", "差異對照表", "製程說明圖"],
        "異動": ["異動申請書", "相關證明文件"]
    },
    "清除許可": {
        "展延": ["原許可證正本", "車輛照片", "駕駛員證照", "處置同意文件"],
        "變更": ["變更申請表", "車輛證明", "有效保險單"],
        "變更暨展延": ["合併申請書", "全套更新附件", "清除量統計表"]
    }
}

U = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load():
    df = pd.read_excel(U, sheet_name='大豐既有許可證到期提醒')
    df['到期日期'] = pd.to_datetime(df['到期日期'], errors='coerce')
    df['許可證類型'] = df['許可證類型'].fillna("未分類")
    return df

try:
    df = load()
except Exception as e:
    st.error(f"讀取錯誤: {e}")
    st.stop()

now = dt.now()
urg = df[(df['到期日期'] <= now + pd.Timedelta(days=180)) & (df['到期日期'].notnull())]
if not urg.empty:
    m_list = [f"🚨 {r['許可證名稱']}(剩{(r['到期日期']-now).days}天)" for _,r in urg.iterrows()]
    txt = "  ".join(m_list)
    st.markdown(f'<marquee style="color:white;background:#ff4b4b;padding:8px;border-radius:5px;">{txt}</marquee>', unsafe_allow_html=True)

with st.sidebar:
    st.header("📂 導航")
    t_list = sorted(df['許可證類型'].unique().tolist())
    sel_t = st.selectbox("1.類型", t_list)
    st.divider()
    sub = df[df['許可證類型'] == sel_t]
    sel_p = st.radio("2.名稱", sub['許可證名稱'].tolist()) if not sub.empty else None

if sel_p:
    row = df[df['許可證名稱'] == sel_p].iloc[0]
    st.title(sel_p)
    c1, c2, c3 = st.columns(3)
    d = row['到期日期']
    vd = d.strftime('%Y-%m-%d') if pd.notnull(d) else "未填"
    c1.metric("到期日", vd)
    rem = (d - now).days if pd.notnull(d) else "N/A"
    c2.metric("剩餘天數", f"{rem}天")
    c3.metric("類型", row['許可證類型'])
    st.divider()
    
    acts = None
    if "清除" in str(sel_p): acts = DB["清除
