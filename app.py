import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐系統")

# 1. 附件資料庫 (代號 P=清理計畫, C=清除許可)
DB = {
    "P": {
        "展延": ["計畫書", "合約", "身分證"],
        "變更": ["申請表", "對照表", "圖說"],
        "異動": ["異動書", "證明文件"]
    },
    "C": {
        "展延": ["原許可正本", "車照", "證照", "處置同意書"],
        "變更": ["變更表", "車證", "保險單"],
        "變更暨展延": ["合併申請書", "全套附件", "統計表"]
    }
}

U = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

# 2. 讀取與處理
df = pd.read_excel(U, sheet_name=0)
df['D'] = pd.to_datetime(df['到期日期'], errors='coerce')
df['T'] = df['許可證類型'].fillna("NA")
now = dt.now()

# 3. 側邊導航
st.sidebar.header("選單")
ts = sorted(df['T'].unique().tolist())
st_t = st.sidebar.selectbox("1.類型", ts)
sub = df[df['T'] == st_t]
st_p = st.sidebar.radio("2.名稱", sub['許可證名稱'].tolist())

# 4. 主畫面 (不使用 with 避免縮進錯誤)
if st_p:
    r = df[df['許可證名稱'] == st_p].iloc[0]
    st.title(st_p)
    d = r['D']
    st.write("到期日:", d.strftime('%Y-%m-%d') if pd.notnull(d) else "未填")
    
    # 決定顯示哪套按鈕
    acts = None
    if "清除" in str(st_p):
        acts = DB["C"]
    elif "清理" in str(st_p) or "計畫" in str(st_p):
        acts = DB["P"]

    if acts:
        st.divider()
        st.subheader("🛠️ 辦理項目")
        # 改用獨立按鈕，確保每個按鈕都有效
        for n in acts.keys():
            if st.button(n, key=n+str(st_p)):
                st.session_state["cur"] = n
        
        # 顯示選中的清單
        cur = st.session_state.get("cur")
        if cur in acts:
            st.success("📍 正在辦理：" + cur)
            for f in acts[cur]:
                st.checkbox(f, key=f+str(st_p)+cur)

# 5. 底部總表
st.divider()
st.subheader("📊 總表備查")
st.dataframe(df)
