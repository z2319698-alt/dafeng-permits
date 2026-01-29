import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐許可管理", layout="wide")

# 1. 定義辦理項目
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

# 2. 讀取與欄位對齊
df = pd.read_excel(URL, sheet_name=0)
C_NAME = "清除許可證名稱"
C_DATE = "許可證期日"
C_TYPE = "變更項目"

df['D'] = pd.to_datetime(df[C_DATE], errors='coerce')
df['T'] = df[C_TYPE].fillna("廢棄物類")

# 3. 側邊選單
st.sidebar.header("📂 系統選單")
t_list = sorted(df['T'].unique().tolist())
sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)

# 篩選子集
sub = df[df['T'] == sel_t]
# 這裡加一個檢查，如果子集為空就不繼續
if sub.empty:
    st.warning("此分類下無資料")
    st.stop()

sel_p = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

# 4. 主畫面內容
# 這裡使用篩選後的 sub 再做一次過濾，並檢查是否抓得到 row
final_selection = sub[sub[C_NAME] == sel_p]

if not final_selection.empty:
    row = final_selection.iloc[0]
    st.title(sel_p)

    # 顯示日期
    d_obj = row['D']
    d_str = d_obj.strftime('%Y-%m-%d') if pd.notnull(d_obj) else "未填寫"
    st.write("📅 **到期日期：**", d_str)

    # 匹配動作邏輯
    acts = None
    p_name = str(sel_p)
    if "清除" in p_name:
        acts = DB["C"]
    elif "清理" in p_name or "計畫" in p_name:
        acts
