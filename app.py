import streamlit as st
import pandas as pd

st.set_page_config(page_title="最小測試-證照顯示", layout="wide")

# ========= 直接讀「數據總表」 =========
# ⚠️ 這裡的 sheet_name 請填「實際包含 管制編號 / 到期日期 的那一張」
SHEET_NAME = "數據總表"   # ← 如果不是這個名字，請改成實際的

URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)

df = pd.read_excel(URL, sheet_name=SHEET_NAME)

# ========= 基本防呆 =========
st.write("🔎 目前讀取的欄位：", df.columns.tolist())
st.write("🔎 資料筆數：", len(df))

# 清理字串（非常重要）
df["許可證名稱"] = df["許可證名稱"].astype(str).str.strip()

# ========= Sidebar =========
st.sidebar.header("系統導航（測試）")

sel_name = st.sidebar.radio(
    "選擇許可證",
    df["許可證名稱"].tolist()
)

# ========= 主畫面 =========
st.title(f"📄 {sel_name}")

# ========= 關鍵：顯示資料 =========
row = df[df["許可證名稱"] == sel_name]

st.write("🔍 篩選後是否有資料：", not row.empty)
st.write("🔍 篩選後資料：")
st.dataframe(row)

if row.empty:
    st.error("❌ 找不到對應的許可證資料（名稱對不到）")
else:
    r = row.iloc[0]

    st.markdown("## 📌 許可證基本資料")

    c1, c2 = st.columns(2)

    with c1:
        st.metric("管制編號", r["管制編號"])

    with c2:
        st.metric(
            "到期日期",
            pd.to_datetime(r["到期日期"]).strftime("%Y-%m-%d")
        )
