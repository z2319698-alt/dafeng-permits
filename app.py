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

# 過濾出該類型的所有資料
sub_df = df[df["許可證類型"] == sel_type].copy()

sel_name = st.sidebar.radio(
    "選擇許可證",
    sub_df["許可證名稱"].dropna().tolist()
)

# ===== 主畫面：關鍵就在這幾行 =====
st.title(f"📄 {sel_name}")

# 【核心修正】直接精準抓取對應的那一列
target_row = sub_df[sub_df["許可證名稱"] == sel_name]

if not target_row.empty:
    # 抓取第一筆符合的資料
    info = target_row.iloc[0]
    
    # 格式化日期
    dt_str = info["到期日期"].strftime("%Y-%m-%d") if pd.notna(info["到期日期"]) else "未設定"
    
    # 直接在標題下方噴出文字
    st.write(f"### 🆔 管制編號：{info['管制編號']} ｜ 📅 到期日期：{dt_str}")
else:
    st.warning("無法從總表中提取編號與日期，請檢查名稱是否完全一致。")

# 保留原本的其他功能
st.divider()

with st.expander("📊 數據總表"):
    st.dataframe(sub_df, use_container_width=True, hide_index=True)
