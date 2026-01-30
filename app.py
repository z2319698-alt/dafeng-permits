import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 資料來源
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=5)
def load_all_data():
    # 同時讀取兩個分頁
    main_df = pd.read_excel(URL, sheet_name="大豐既有許可證到期提醒")
    file_df = pd.read_excel(URL, sheet_name="附件資料庫")
    # 清理欄位空格
    main_df.columns = [str(c).strip() for c in main_df.columns]
    file_df.columns = [str(c).strip() for c in file_df.columns]
    return main_df, file_df

try:
    main_df, file_df = load_all_data()

    # --- 3. 側邊選單 (第一層 & 第二層) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 類型選擇 (A 欄)
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
    sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
    
    # 名稱選擇 (C 欄)
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())

    # --- 4. 抓取主分頁的基本資料 (B 欄與 D 欄) ---
    target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
    permit_id = str(target_main.iloc[1])    # B 欄：管制編號
    expiry_date = str(target_main.iloc[3])  # D 欄：到期日期
    clean_date = expiry_date[:10] if expiry_date != 'nan' else "未設定"

    # --- 5. 🚀 核心：根據「類型」去「附件資料庫」抓取資料 ---
    # 從「附件資料庫」篩選出與目前選擇「類型」相符的所有項目
    db_info = file_df[file_df.iloc[:, 0] == sel_type]

    # --- 6. 主畫面呈現 ---
    st.title(f"📄 {sel_name}")
    # 副標題呈現編號與日期
    st.info(f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}")
    
    st.divider()

    # --- 7. 第三層：呈現「附件資料庫」內容 ---
    st.subheader(f"📋 {sel_type} - 辦理流程與附件需求")
    
    if not db_info.empty:
        # 顯示該類型下的所有辦理項目
        for _, row in db_info.iterrows():
            with st.expander(f"📌 辦理項目：{row.iloc[1]}"): # B 欄：辦理項目
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write("**第一步：**")
                    st.write(row.iloc[2]) # C 欄：第一步
                with col2:
                    st.write("**所需附件清單：**")
                    # 抓取 D 欄以後的所有附件名稱
                    attachments = row.iloc[3:].dropna().tolist()
                    if attachments:
                        for idx, item in enumerate(attachments, 1):
                            st.write(f"{idx}. {item}")
                    else:
                        st.write("無需附件")
    else:
        st.warning(f"⚠️ 在『附件資料庫』中找不到類型「{sel_type}」的資料。")

    st.divider()
    with st.expander("📊 查看完整數據明細"):
        st.dataframe(sub_main, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 讀取失敗：{e}")
