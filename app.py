import streamlit as st
import pandas as pd

# ================= 基本設定 =================
st.set_page_config(page_title="環保證照管理系統", layout="wide")

URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)

SHEET_NAME = "大豐既有許可證到期提醒"

# ================= 讀取資料 =================
@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)

    # 欄位清理（避免前後空白）
    df.columns = df.columns.astype(str).str.strip()
    df["許可證類型"] = df["許可證類型"].astype(str).str.strip()
    df["許可證名稱"] = df["許可證名稱"].astype(str).str.strip()
    df["管制編號"] = df["管制編號"].astype(str).str.strip()
    df["到期日期"] = pd.to_datetime(df["到期日期"], errors="coerce")

    return df

df = load_data()

# ================= Sidebar =================
st.sidebar.markdown("## 📂 系統導航")

sel_type = st.sidebar.selectbox(
    "選擇類型",
    sorted(df["許可證類型"].dropna().unique().tolist())
)

sub_df = df[df["許可證類型"] == sel_type].copy()

sel_name = st.sidebar.radio(
    "選擇許可證",
    sub_df["許可證名稱"].dropna().unique().tolist()
)

# ================= 主畫面 =================
st.title(f"📄 {sel_name}")

# ===== 這裡開始：完全照你示意圖的方式呈現（標題正下方一行）=====
row_df = sub_df[sub_df["許可證名稱"] == sel_name].copy()

# 同名多筆時：取到期日期最晚那一筆（避免抓到空日期或舊資料）
row_df = row_df.sort_values(by="到期日期", ascending=False, na_position="last")

if row_df.empty:
    permit_no = "—"
    expire_dt = "未設定"
else:
    info = row_df.iloc[0]
    permit_no = info["管制編號"] if pd.notna(info["管制編號"]) and str(info["管制編號"]).strip() else "—"
    expire_dt = info["到期日期"].strftime("%Y-%m-%d") if pd.notna(info["到期日期"]) else "未設定"

# ✅ 你要的那一行（字級/間距/粗細模仿你貼的示意圖）
st.markdown(
    f"""
    <div style="
        margin-top: 6px;
        margin-bottom: 18px;
        font-size: 30px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: 0.5px;
    ">
        管制編號：<span style="font-weight:800;">{permit_no}</span>
        <span style="display:inline-block; width: 22px;"></span>
        到期日期：<span style="font-weight:800;">{expire_dt}</span>
    </div>
    """,
    unsafe_allow_html=True
)

# ================= 下面原本的東西（可留可刪） =================
st.divider()

with st.expander("📊 數據總表"):
    st.dataframe(sub_df, use_container_width=True, hide_index=True)
