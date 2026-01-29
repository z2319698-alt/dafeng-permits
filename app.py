import streamlit as st
import pandas as pd
from datetime import datetime as dt

st.set_page_config(page_title="大豐許可管理", layout="wide")

# 1. 定義辦理項目 (維持你需要的分類)
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

# 2. 讀取與欄位手動強制對齊
df = pd.read_excel(URL, sheet_name=0)

# 根據你提供的清單精準設定欄位名稱
C_NAME = "清除許可證名稱"
C_DATE = "許可證期日"
C_TYPE = "變更項目" # 假設你用這行當作分類，若無則預設為 NA

# 3. 資料清洗
df['D'] = pd.to_datetime(df[C_DATE], errors='coerce')
df['T'] = df[C_TYPE].fillna("廢棄物類") # 給予一個預設分類

# 4. 側邊選單
st.sidebar.header("📂 系統選單")
# 取得不重複的類型清單
t_list = sorted(df['T'].unique().tolist())
sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)

# 根據類型篩選
sub = df[df['T'] == sel_t]
sel_p = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

# 5. 主畫面內容
if sel_p:
    row = sub[sub[C_NAME] == sel_p].iloc[0]
    st.title(sel_p)

    # 顯示日期
    d_obj = row['D']
    d_str = d_obj.strftime('%Y-%m-%d') if pd.notnull(d_obj) else "未填寫"
    st.write("📅 **到期日期：**", d_str)

    # 匹配動作邏輯 (只要名稱有清除就用 C，有清理或計畫就用 P)
    acts = None
    p_name = str(sel_p)
    if "清除" in p_name:
        acts = DB["C"]
