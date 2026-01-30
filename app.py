import streamlit as st
import pandas as pd

st.set_page_config(page_title="環保證照管理系統", layout="wide")

URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)

SHEET_NAME = "大豐既有許可證到期提醒"

@st.cache_data(show_spinner=False)
def load_main_table():
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    return df

df = load_main_table()

# ===== 欄位清理 =====
df.columns = df.columns.astype(str).str.strip()
for col in ["許可證類型", "許可證名稱", "管制編號"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

if "到期日期" in df.columns:
    df["到期日期"] = pd.to_datetime(df["到期日期"], errors="coerce")

# ===== Sidebar 導覽 =====
st.sidebar.markdown("## 📂 系統導覽")

sel_type = st.sidebar.selectbox(
    "選擇類型",
    sorted(df["許可證類型"].dropna().unique().tolist())
)

sub_df = df[df["許可證類型"] == sel_type].copy()

sel_name = st.sidebar.radio(
    "選擇許可證",
    sub_df["許可證名稱"].dropna().tolist()
)

# ===== 主畫面：直接從總表抓取對應的那一列資料 =====
st.title(f"📄 {sel_name}")

# 直接用你選的名稱去總表(sub_df)找那一列
info = sub_df[sub_df["許可證名稱"] == sel_name].iloc[0]

# 讀取編號與日期（直接從 row 裡面拿）
id_num = info["管制編號"]
# 格式化日期：如果你希望呈現 2027-02-10
dt_val = info["到期日期"].strftime("%Y-%m-%d") if pd.notna(info["到期日期"]) else "未設定"

# 【這就是你要的：名稱正下方直接呈現】
st.write(f"### 管制編號：{id_num} ｜ 到期日期：{dt_val}")

# ===== 下方原本的內容完全不動 =====
st.divider()

with st.expander("📊 數據總表"):
    st.dataframe(sub_df, use_container_width=True, hide_index=True)
