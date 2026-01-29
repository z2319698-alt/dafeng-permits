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

# 2. 讀取與欄位安全偵測
df = pd.read_excel(URL, sheet_name=0)

# 預設變數防止 NameError
c_dt, c_tp, c_nm = None, None, None

for c in df.columns:
    col_str = str(c)
    if "日期" in col_str: c_dt = c
    if "類型" in col_str: c_tp = c
    if "名稱" in col_str: c_nm = c

# 檢查關鍵欄位是否存在
if not c_dt or not c_nm:
    st.error("❌ Excel 欄位對應失敗！")
    st.write("程式找不到包含 '日期' 或 '名稱' 的欄位。")
    st.write("目前 Excel 內的欄位有：", list(df.columns))
    st.stop()

# 3. 資料處理
df['D'] = pd.to_datetime(df[c_dt], errors='coerce')
df['T'] = df[c_tp].fillna("未分類") if c_tp else "未分類"

# 4. 側邊選單
st.sidebar.header("📂 導航選單")
t_list = sorted(df['T'].unique().tolist())
s_t = st.sidebar.selectbox("1. 選擇類型", t_list)
sub = df[df['T'] == s_t]
s_p = st.sidebar.radio("2. 選擇許可證名稱", sub[c_nm].tolist())

# 5. 主畫面內容
if s_p:
    row = sub[sub[c_nm] == s_p].iloc[0]
    st.title(s_p)

    # 顯示日期
    d_obj = row['D']
    d_str = d_obj.strftime('%Y-%m-%d') if pd.notnull(d_obj) else "未填寫"
    st.write("📅 **到期日期：**", d_str)

    # 匹配按鈕邏輯
    acts = None
    if "清除" in str(s_p):
        acts = DB["C"]
    elif "清理" in str(s_p) or "計畫" in str(s_p):
        acts = DB["P"]

    if acts:
        st.divider()
        st.subheader("🛠️ 辦理項目指引")
        # 平鋪按鈕避免截斷
        for n in acts.keys():
            k
