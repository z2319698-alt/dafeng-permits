import streamlit as st
import pandas as pd

st.set_page_config(page_title="環保證照管理系統", layout="wide")

URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)

SHEET_NAME = "大豐既有許可證到期提醒"  # ✅ 你提供的分頁名稱

# ===== 讀取正確分頁 =====
@st.cache_data(show_spinner=False)
def load_main_table():
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    return df

df = load_main_table()

# ===== 欄位清理（避免前後空白/全形半形）=====
df.columns = df.columns.astype(str).str.strip()
for col in ["許可證類型", "許可證名稱", "管制編號"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

if "到期日期" in df.columns:
    df["到期日期"] = pd.to_datetime(df["到期日期"], errors="coerce")

# ===== 必要欄位檢查（缺欄就直接告警）=====
need_cols = ["許可證類型", "許可證名稱", "管制編號", "到期日期"]
missing = [c for c in need_cols if c not in df.columns]
if missing:
    st.error(f"❌ 讀到的分頁缺少欄位：{missing}\n\n實際欄位：{df.columns.tolist()}")
    st.stop()

# ===== Sidebar：選類型 -> 選許可證 =====
st.sidebar.markdown("## 📂 系統導航")

sel_type = st.sidebar.selectbox(
    "選擇類型",
    sorted(df["許可證類型"].dropna().unique().tolist())
)

sub_df = df[df["許可證類型"] == sel_type].copy()

sel_name = st.sidebar.radio(
    "選擇許可證",
    sub_df["許可證名稱"].dropna().tolist()
)

# ===== 主畫面：你要的「中間跳出資料」=====
st.title(f"📄 {sel_name}")

row = sub_df[sub_df["許可證名稱"] == sel_name]
if row.empty:
    st.error("❌ 找不到對應的許可證資料（名稱可能有空白或不一致）")
else:
    r = row.iloc[0]

    st.markdown("### 📌 許可證基本資料")

    c1, c2 = st.columns(2)

    with c1:
        st.metric("管制編號", r["管制編號"])

    with c2:
        st.metric(
            "到期日期",
            r["到期日期"].strftime("%Y-%m-%d") if pd.notna(r["到期日期"]) else "未設定"
        )

# （可選）讓你確認目前類型下有哪些資料
with st.expander("📊 本類型資料（除錯用，可關閉）"):
    st.dataframe(sub_df, use_container_width=True, hide_index=True)
