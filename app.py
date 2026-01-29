import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐系統")

# 1. 附件資料
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

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

# 2. 讀取
df = pd.read_excel(URL, sheet_name=0)
for c in df.columns:
    if "日期" in str(c): c_dt = c
    if "類型" in str(c): c_tp = c
    if "名稱" in str(c): c_nm = c

df['D'] = pd.to_datetime(df[c_dt], errors='coerce')
df['T'] = df[c_tp].fillna("NA")

# 3. 側邊選單
st.sidebar.header("選單")
t_list = sorted(df['T'].unique().tolist())
s_t = st.sidebar.selectbox("1.類型", t_list)
sub = df[df['T'] == s_t]
s_p = st.sidebar.radio("2.名稱", sub[c_nm].tolist())

# 4. 主畫面 (移除縮進以防截斷)
if not s_p:
    st.stop()

row = sub[sub[c_nm] == s_p].iloc[0]
st.title(s_p)

# 顯示日期
d_obj = row['D']
d_str = "未填"
if pd.notnull(d_obj):
    d_str = d_obj.strftime('%Y-%m-%d')
st.write("📅 到期日:", d_str)

# 匹配附件清單
acts = None
if "清除" in str(s_p):
    acts = DB["C"]
if "清理" in str(s_p) or "計畫" in str(s_p):
    acts = DB["P"]

if not acts:
    st.info("💡 暫無指引")
    st.stop()

st.divider()
st.subheader("🛠️ 辦理項目")

# 按鈕 (預先定義 key 避免截斷)
for n in acts.keys():
    k = "btn" + str(n) + str(s_p)
    if st.button(n, key=k):
        st.session_state["cur"] = n

# 顯示內容
cur = st.session_state.get("cur")
if cur in acts:
    st.success("📍 正在辦理：" + cur)
    for f in acts[cur]:
        ck = "ck" + str(f) + str(s_p) + str(cur)
        st.checkbox(f, key=ck)

st.divider()
st.dataframe(df)
