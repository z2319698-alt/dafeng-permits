import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐許可管理")

# 1. 附件資料庫
DB = {
    "P": {
        "展延": ["清理計畫書", "廢棄物合約", "身分證"],
        "變更": ["變更申請表", "差異對照表", "製程圖"],
        "異動": ["異動申請書", "證明文件"]
    },
    "C": {
        "展延": ["原許可正本", "車照", "證照", "同意文件"],
        "變更": ["變更表", "車證", "保險單"],
        "變更暨展延": ["合併申請書", "更新附件", "統計表"]
    }
}

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    # 讀取所有分頁，尋找有資料的那張
    shs = pd.read_excel(URL, sheet_name=None)
    for n, df in shs.items():
        df.columns = [str(c).strip() for c in df.columns]
        if "許可證名稱" in df.columns:
            return df
    return list(shs.values())[0]

try:
    df = load_data()
    
    # 2. 直接根據你給的最新欄位名稱設定
    C_NAME = "許可證名稱"
    C_DATE = "到期日期"
    C_TYPE = "許可證類型"

    df['D'] = pd.to_datetime(df[C_DATE], errors='coerce')
    df['T'] = df[C_TYPE].fillna("一般")
    
    # 3. 側邊選單
    st.sidebar.header("選單")
    t_list = sorted(df['T'].unique().tolist())
    sel_t = st.sidebar.selectbox("1. 類型", t_list)
    
    sub = df[df['T'] == sel_t].reset_index(drop=True)
    if sub.empty: st.stop()
    sel_n = st.sidebar.radio("2. 許可證", sub[C_NAME].tolist())

    # 4. 主畫面
    row = sub[sub[C_NAME] == sel_n].iloc[0]
    st.title(sel_n)
    
    # 顯示日期
    d_v = row['D']
    st.write("📅 到期日期:", d_v.strftime('%Y-%m-%d') if pd.notnull(d_v) else "未填")
    
    # 5. 辦理指引按鈕
    acts = None
    if "清除" in str(sel_n): acts = DB["C"]
    elif "清理" in str(sel_n) or "計畫" in str(sel_n): acts = DB["P"]

    if acts:
        st.divider()
        st.subheader("🛠️ 辦理項目")
        for a_n in acts.keys():
            # 簡化 Key 避免過長
            if st.button(a_n, key=f"b_{sel_n}_{a_n}"):
                st.session_state["cur"] = a_n
                st.session_state["pid"] = sel_n

        # 顯示勾選清單
        if st.session_state.get("pid") == sel_n:
            cur = st.session_state.get("cur")
            if cur in acts:
                st.success(f"📍 正在辦理：{cur}")
                for f in acts[cur]:
                    st.checkbox(f, key=f"c_{sel_n}_{cur}_{f}")
except Exception as e:
    st.error(f"錯誤: {e}")

st.divider()
with st.expander("數據總表"):
    st.dataframe(df)
