import re
import streamlit as st
import pandas as pd

st.set_page_config(page_title="環保證照管理系統", layout="wide")

URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE"
    "/export?format=xlsx"
)

SHEET_MASTER = "大豐既有許可證到期提醒"   # 數據總表（有 管制編號 / 到期日期）
SHEET_MENU   = "選擇許可證"             # 你新建的分頁（sidebar 名稱來源）


# --------- 文字正規化：避免空白/全形/符號導致配對失敗 ----------
def norm(s) -> str:
    if s is None:
        return ""
    s = str(s).replace("\u3000", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def pick_col(df: pd.DataFrame, contains_any: list[str], fallback_first: bool = False) -> str | None:
    """從欄位中找出包含關鍵字的欄位名（任何一個關鍵字命中即算）"""
    cols = [norm(c) for c in df.columns.tolist()]
    for c in cols:
        for kw in contains_any:
            if kw in c:
                return c
    return cols[0] if (fallback_first and cols) else None


@st.cache_data(show_spinner=False)
def load_sheets():
    all_sheets = pd.read_excel(URL, sheet_name=None)

    if SHEET_MASTER not in all_sheets:
        raise ValueError(f"找不到分頁：{SHEET_MASTER}")
    if SHEET_MENU not in all_sheets:
        raise ValueError(f"找不到分頁：{SHEET_MENU}")

    master = all_sheets[SHEET_MASTER].copy()
    menu = all_sheets[SHEET_MENU].copy()

    # 欄名清理
    master.columns = [norm(c) for c in master.columns]
    menu.columns = [norm(c) for c in menu.columns]

    return master, menu


master_df, menu_df = load_sheets()

# --------- 自動辨識 master（數據總表）欄位 ----------
m_col_name = pick_col(master_df, ["許可證名稱", "名稱"], fallback_first=False)
m_col_id   = pick_col(master_df, ["管制編號", "編號"], fallback_first=False)
m_col_date = pick_col(master_df, ["到期日期", "到期"], fallback_first=False)
m_col_type = pick_col(master_df, ["許可證類型", "類型"], fallback_first=False)

need_master = [m_col_name, m_col_id, m_col_date]
if any(c is None for c in need_master):
    st.error(
        "❌ 數據總表欄位辨識失敗。請確認分頁『大豐既有許可證到期提醒』至少有：許可證名稱 / 管制編號 / 到期日期\n\n"
        f"目前讀到欄位：{master_df.columns.tolist()}"
    )
    st.stop()

# master 清理
master_df[m_col_name] = master_df[m_col_name].map(norm)
master_df[m_col_id]   = master_df[m_col_id].map(norm)
master_df[m_col_date] = pd.to_datetime(master_df[m_col_date], errors="coerce")
if m_col_type:
    master_df[m_col_type] = master_df[m_col_type].map(norm)

# 建 key
master_df["_key_name"] = master_df[m_col_name].map(norm)

# --------- 自動辨識 menu（選擇許可證）欄位 ----------
# sidebar 顯示名稱：優先找「顯示」「標題」「選擇」「名稱」；找不到就用第一欄
menu_display_col = pick_col(menu_df, ["顯示", "標題", "選擇", "名稱"], fallback_first=True)

# 用來對應 master 的欄位：優先找「對應」「許可證名稱」「總表」「key」
menu_match_col = pick_col(menu_df, ["對應", "許可證名稱", "總表", "key"], fallback_first=False)

# 如果 menu_match_col 找不到，就假設「顯示名稱」本身就等於 master 的許可證名稱
if menu_match_col is None:
    menu_match_col = menu_display_col

# menu 清理
menu_df[menu_display_col] = menu_df[menu_display_col].map(norm)
menu_df[menu_match_col]   = menu_df[menu_match_col].map(norm)

# menu 類型欄（如果你有做類型分類就會用到；沒有就整張表當同一類）
menu_type_col = pick_col(menu_df, ["類型", "許可證類型"], fallback_first=False)
if menu_type_col:
    menu_df[menu_type_col] = menu_df[menu_type_col].map(norm)

# 去掉空列
menu_df = menu_df[menu_df[menu_display_col] != ""].copy()

# ================= Sidebar（完全以「選擇許可證」分頁為準） =================
st.sidebar.markdown("## 📂 系統導航")

if menu_type_col:
    sel_type = st.sidebar.selectbox("選擇類型", sorted(menu_df[menu_type_col].dropna().unique().tolist()))
    menu_sub = menu_df[menu_df[menu_type_col] == sel_type].copy()
else:
    sel_type = None
    menu_sub = menu_df

sel_display = st.sidebar.radio("選擇許可證", menu_sub[menu_display_col].dropna().unique().tolist())

# 取出對應 master 的名稱 key
match_name = menu_sub.loc[menu_sub[menu_display_col] == sel_display, menu_match_col].iloc[0]
match_key = norm(match_name)

# ================= 主畫面：標題 + 副標題（你要的呈現） =================
st.title(f"📄 {sel_display}")

# 用 match_key 去 master_df 配對
hit = master_df[master_df["_key_name"] == match_key].copy()

# 找不到就做一次「包含」容錯（避免你 menu 少了分公司/多了括號）
if hit.empty and match_key:
    hit = master_df[master_df["_key_name"].str.contains(re.escape(match_key), na=False)].copy()

if hit.empty:
    # 這裡不讓你看「空白」，而是直接告訴你：配對不到
    st.markdown(
        f"<h4 style='color:#ff6b6b;'>❌ 找不到對應的總表資料：{match_name}</h4>",
        unsafe_allow_html=True
    )
    with st.expander("🔍 除錯：你選到的名稱 vs 總表前 30 筆名稱"):
        st.write("你選到的（用來配對的）名稱：", match_key)
        st.write("總表前 30 筆：", master_df["_key_name"].head(30).tolist())
else:
    # 同名多筆取到期日期最晚（避免抓到空日期或舊資料）
    hit = hit.sort_values(by=m_col_date, ascending=False, na_position="last")
    r = hit.iloc[0]

    permit_no = r[m_col_id] if r[m_col_id] else "—"
    expire_dt = r[m_col_date].strftime("%Y-%m-%d") if pd.notna(r[m_col_date]) else "未設定"

    # ✅ 你要的「副標題一行」
    st.markdown(
        f"<h4>管制編號：{permit_no}　　到期日期：{expire_dt}</h4>",
        unsafe_allow_html=True
    )

st.divider()

# （可留可刪）給你核對：現在 sidebar 對應到哪一筆
with st.expander("📊 對應結果（可收合）"):
    st.write("sidebar 顯示名稱：", sel_display)
    st.write("用來配對總表的名稱：", match_name)
    st.dataframe(hit.drop(columns=["_key_name"], errors="ignore"), use_container_width=True, hide_index=True)
