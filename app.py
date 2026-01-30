# =========================
# PROBE（跑不到就一定顯示）
# =========================
import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="PROBE-環保證照管理系統", layout="wide")

st.error("✅ PROBE：如果你看不到這一行，代表你根本沒在跑這支檔案")
# ⬆️ 看到這行，代表檔案有在跑
# ⬇️ 不看到，代表你改錯檔 / 跑錯 page
# =========================

URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)

SHEET_MASTER = "大豐既有許可證到期提醒"   # 有 管制編號 / 到期日期
SHEET_MENU   = "選擇許可證"             # 你新建、左邊用的分頁


# =========================
# 工具
# =========================
def norm(x):
    if x is None:
        return ""
    s = str(x).replace("\u3000", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


# =========================
# 讀取 Excel（一次）
# =========================
try:
    sheets = pd.read_excel(URL, sheet_name=None)
except Exception as e:
    st.error(f"❌ Excel 讀取失敗：{e}")
    st.stop()

if SHEET_MASTER not in sheets:
    st.error(f"❌ 找不到分頁：{SHEET_MASTER}")
    st.stop()

if SHEET_MENU not in sheets:
    st.error(f"❌ 找不到分頁：{SHEET_MENU}")
    st.stop()

master_df = sheets[SHEET_MASTER].copy()
menu_df   = sheets[SHEET_MENU].copy()

# =========================
# 清理欄位
# =========================
master_df.columns = [norm(c) for c in master_df.columns]
menu_df.columns   = [norm(c) for c in menu_df.columns]

# 必要欄位（數據總表）
REQ_MASTER = ["許可證名稱", "管制編號", "到期日期"]
for c in REQ_MASTER:
    if c not in master_df.columns:
        st.error(f"❌ 總表缺少欄位：{c}")
        st.write("實際欄位：", master_df.columns.tolist())
        st.stop()

master_df["許可證名稱"] = master_df["許可證名稱"].map(norm)
master_df["管制編號"]   = master_df["管制編號"].map(norm)
master_df["到期日期"]   = pd.to_datetime(master_df["到期日期"], errors="coerce")
master_df["_KEY"]        = master_df["許可證名稱"]

# menu：第一欄當 sidebar 顯示名稱
menu_display_col = menu_df.columns[0]
menu_df[menu_display_col] = menu_df[menu_display_col].map(norm)

# 如果 menu 有第二欄，就拿來當「對應總表名稱」
if len(menu_df.columns) >= 2:
    menu_match_col = menu_df.columns[1]
    menu_df[menu_match_col] = menu_df[menu_match_col].map(norm)
else:
    menu_match_col = menu_display_col

menu_df = menu_df[menu_df[menu_display_col] != ""]

# =========================
# Sidebar
# =========================
st.sidebar.markdown("## 📂 選擇許可證")

sel_display = st.sidebar.radio(
    "許可證清單",
    menu_df[menu_display_col].tolist()
)

match_name = menu_df.loc[
    menu_df[menu_display_col] == sel_display,
    menu_match_col
].iloc[0]

# =========================
# 主畫面
# =========================
st.title(f"📄 {sel_display}")

# === 配對總表 ===
hit = master_df[master_df["_KEY"] == match_name].copy()

if hit.empty:
    # 至少一定會看到這一行
    st.markdown(
        f"<h4 style='color:red;'>❌ 找不到對應的總表資料：{match_name}</h4>",
        unsafe_allow_html=True
    )

    with st.expander("DEBUG：總表前 20 筆名稱"):
        st.write(master_df["_KEY"].head(20).tolist())

    st.stop()

# 同名取到期日期最晚
hit = hit.sort_values(by="到期日期", ascending=False, na_position="last")
row = hit.iloc[0]

permit_no = row["管制編號"] if row["管制編號"] else "—"
expire_dt = row["到期日期"].strftime("%Y-%m-%d") if pd.notna(row["到期日期"]) else "未設定"

# === 你要的副標題 ===
st.markdown(
    f"<h4>管制編號：{permit_no}　　到期日期：{expire_dt}</h4>",
    unsafe_allow_html=True
)

st.divider()

with st.expander("📊 對應到的總表資料"):
    st.dataframe(hit, use_container_width=True, hide_index=True)
