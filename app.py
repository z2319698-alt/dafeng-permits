import streamlit as st
import pandas as pd

# 1. 頁面設定
st.set_page_config(page_title="環保證照管理系統", layout="wide")

# 2. 資料連結
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

@st.cache_data(ttl=5) # 快取縮短到 5 秒，確保你改 Excel 後幾乎是秒同步
def load_data():
    # 讀取 Excel
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    # 強制清理所有欄位名稱的隱形空白
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df = load_data()

    # --- 3. 側邊選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 這裡用第 0 欄（A 欄：許可證類型）
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(df.iloc[:, 0].dropna().unique()))
    
    # 過濾資料
    sub_df = df[df.iloc[:, 0] == sel_type].copy()
    
    # 這裡用第 2 欄（C 欄：許可證名稱）
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_df.iloc[:, 2].dropna().unique())

    # --- 🚀 4. 核心修正：用「位置」強行抓取日期 ---
    # 找到選中名稱的那一列
    target_row = sub_df[sub_df.iloc[:, 2] == sel_name].iloc[0]
    
    # 【最暴力解法】直接抓這列的第 5 個格子 (Index 4，即 E 欄)
    # 不管欄位名稱對不對，程式只認位置！
    raw_date_val = target_row.iloc[4] 
    
    # 強制轉字串並只取前 10 位 (YYYY-MM-DD)
    date_display = str(raw_date_val)[:10] if str(raw_date_val) != 'nan' else "未設定"

    # ✅ 呈現標題：名稱 (日期)
    # 我們換一個寫法，用 st.header 試試，有時候 title 會被系統樣式干擾
    st.header(f"📄 {sel_name} ({date_display})")

    # 呈現管制編號（第 2 欄，B 欄）
    st.markdown(f"### 管制編號：{target_row.iloc[1]}")
    
    st.divider()

    # --- 5. 數據總表 ---
    with st.expander("📊 查看詳細數據內容"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"系統發生預期外的錯誤：{e}")
