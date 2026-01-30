import re
import streamlit as st
import pandas as pd

st.set_page_config(page_title="環保證照管理系統", layout="wide")

URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)
SHEET_NAME = "大豐既有許可證到期提醒"

# ---------- 文字正規化：用來「標題」對「總表許可證名稱」 ----------
def norm_text(x: str) -> str:
    if x is None:
        return ""
    s = str(x)
    s = s.replace("\u3000", " ")        # 全形空白
    s = re.sub(r"\s+", " ", s).strip()  # 連續空白壓成單一空白
    s = s.replace("📄", "").strip()     # 你標題常會加 icon，拔掉
    return s

@st.cache_data(show_spinner=False)
def load_master():
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)

    # 欄位名清理
    df.columns = df.columns.astype(str).str.strip()

    # 必要欄位檢查
    need = ["許可證類型", "許可證名稱", "管制編號", "到期日期"]
    missing = [c for c in need if c not in df.columns]
    if missing:
        # 這裡不要 st.stop，讓畫面能顯示錯誤
        raise ValueError(f"分頁缺少欄位：{missing}，實際欄位：{df.columns.tolist()}")

    # 型別/字串清理
    df["許可證類型"] = df["許可證類型"].astype(str).map(norm_text)
    df["許可證名稱"] = df["許可證名稱"].astype(str).map(norm_text)
    df["管制編號"] = df["管制編號"].astype(str).map(norm_text)
    df["到期日期"] = pd.to_datetime(df["到期日期"], errors="coerce")

    # 做一個「正規化後的 key」欄位給配對用
    df["_key_name"] = df["許可證名稱"].map(norm_text)

    return df

def render_title_and_match(title_text: str, master_df: pd.DataFrame):
    """
    你要的核心：用『畫面標題文字』去 master_df 配對，然後顯示管制編號/到期日期
    """
    key = norm_text(title_text)

    # 先做完全相等配對
    hit = master_df[master_df["_key_name"] == key].copy()

    # 如果完全相等找不到，再做「包含」模糊配對（避免標題多了字）
    if hit.empty:
        hit = master_df[master_df["_key_name"].str.contains(re.escape(key), na=False)].copy()

    # 再不行，反方向包含（避免 master 名稱更長）
    if hit.empty:
        hit = master_df[master_df["_key_name"].map(lambda x: key in x)].copy()

    if hit.empty:
        st.markdown(
            f"<h4 style='color:#ff6b6b;'>找不到對應資料：『{title_text}』</h4>",
            unsafe_allow_html=True
        )
        # 給你可驗證的資訊：到底 master 裡有哪些 key（只顯示前 20）
        with st.expander("🔍 除錯：總表前 20 個許可證名稱（正規化後）"):
            st.write(master_df["_key_name"].head(20).tolist())
        return

    # 同名多筆：取到期日期最晚（你也可改最早）
    hit = hit.sort_values(by="到期日期", ascending=False, na_position="last")
    r = hit.iloc[0]

    permit_no = r["管制編號"] if pd.notna(r["管制編號"]) and str(r["管制編號"]).strip() else "—"
    expire_dt = r["到期日期"].strftime("%Y-%m-%d") if pd.notna(r["到期日期"]) else "未設定"

    # ✅ 你要的那一行（就一行，跟你想要的一樣）
    st.markdown(
        f"<h4>管制編號：{permit_no}　　到期日期：{expire_dt}</h4>",
        unsafe_allow_html=True
    )

    # 讓你確定到底配到哪一筆（必要時打開看）
    with st.expander("🔎 除錯：實際配對到的資料列"):
        st.dataframe(hit.drop(columns=["_key_name"]), use_container_width=True, hide_index=True)

# ================== 主程式 ==================
try:
    master = load_master()
except Exception as e:
    st.error(f"資料讀取失敗：{e}")
    st.stop()

# Sidebar：這裡只是給你方便選標題（你真正系統中「title_text」可能來自別處）
st.sidebar.markdown("## 📂 系統導航（示範）")
sel_type = st.sidebar.selectbox("選擇類型", sorted(master["許可證類型"].dropna().unique().tolist()))
sub = master[master["許可證類型"] == sel_type].copy()
sel_title = st.sidebar.radio("選擇許可證", sub["許可證名稱"].dropna().unique().tolist())

# 這就是你頁面上的標題（你原本系統如果是別的 title，就把那個 title 丟進去）
st.title(f"📄 {sel_title}")

# ✅ 核心：用「標題文字」去 master 配對並顯示
render_title_and_match(sel_title, master)

st.divider()

with st.expander("📊 數據總表（當前類型）"):
    st.dataframe(sub.drop(columns=["_key_name"]), use_container_width=True, hide_index=True)
