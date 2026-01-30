import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐許可管理", layout="wide")

# 1. 附件資料庫 (對應展延/變更/變更暨展延)
DB = {
    "P": {
        "展延": ["清理計畫書(更新版)", "廢棄物合約影本", "負責人身分證"],
        "變更": ["變更申請表", "差異對照表", "製程說明圖"],
        "異動": ["異動申請書", "相關證明文件"]
    },
    "C": {
        "展延": ["原許可正本", "車照", "證照", "處置同意文件"],
        "變更": ["變更表", "車證", "有效保險單"],
        "變更暨展延": ["合併申請書", "全套更新附件", "清除量統計表"]
    }
}

URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

# 2. 讀取並偵測欄位
@st.cache_data(ttl=60)
def load():
    all_sh = pd.read_excel(URL, sheet_name=None)
    for name, df in all_sh.items():
        df.columns = [str(c).strip() for c in df.columns]
        # 只要有「名稱」跟「日期」就認定是我們要的分頁
        if any("名稱" in c for c in df.columns) and any("日期" in c for c in df.columns):
            return df
    return list(all_sh.values())[0]

try:
    df = load()
    
    # 根據你提供的最新欄位清單進行對齊
    c_nm = next(c for c in df.columns if "名稱" in c)
    c_dt = next(c for c in df.columns if "日期" in c)
    c_tp = next((c for c in df.columns if "類型" in c), None)

    df['D'] = pd.to_datetime(df[c_dt], errors='coerce')
    df['T'] = df[c_tp].fillna("一般管理") if c_tp else "一般管理"
    now = dt.now()

    # 3. 側邊選單
    st.sidebar.header("📂 系統選單")
    t_list = sorted(df['T'].unique().tolist())
    s_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    
    sub = df[df['T'] == s_t].reset_index(drop=True)
    if sub.empty: st.stop()
    s_n = st.sidebar.radio("2. 選擇許可證", sub[c_nm].tolist())

    # 4. 主畫面
    row = sub[sub[c_nm] == s_n].iloc[0]
    st.title(f"📄 {s_n}")
    
    col1, col2 = st.columns(2)
    d_val = row['D']
    col1.metric("到期日期", d_val.strftime('%Y-%m-%d') if pd.notnull(d_val) else "未填寫")
    
    rem = (d_val - now).days if pd.notnull(d_val) else None
    color = "red" if (rem and rem < 90) else "green"
    col2.markdown(f"**剩餘天數：** <span style='color:{color};font-size:24px;'>{rem if rem else 'N/A'} 天</span>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("🛠️ 辦理項目指引")

    # 判斷是「清除」還是「清理」
    acts = None
    if "清除" in str(s_n): acts = DB["C"]
    elif "清理" in str(s_n) or "計畫" in str(s_n): acts = DB["P"]

    if acts:
        # 按鈕排版
        cols = st.columns(len(acts))
        for i, a_n in enumerate(acts.keys()):
            if cols[i].button(a_n, key=f"b_{s_n}_{a_n}", use_container_width
