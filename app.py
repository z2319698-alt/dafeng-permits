import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 資料來源
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=5)
def load_all_data():
    # 同時讀取兩個關鍵分頁
    main_df = pd.read_excel(URL, sheet_name="大豐既有許可證到期提醒")
    file_df = pd.read_excel(URL, sheet_name="附件資料庫")
    # 清理空格
    main_df.columns = [str(c).strip() for c in main_df.columns]
    file_df.columns = [str(c).strip() for c in file_df.columns]
    return main_df, file_df

try:
    main_df, file_df = load_all_data()

    # --- 3. 側邊選單 (從主分頁抓取) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # 類型選擇 (A 欄)
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
    sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
    
    # 名稱選擇 (C 欄)
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())

    # --- 4. 抓取主分頁的基本資料 (管制編號、日期) ---
    target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
    permit_id = str(target_main.iloc[1])    # B 欄：管制編號
    expiry_date = str(target_main.iloc[3])  # D 欄：到期日期
    clean_date = expiry_date[:10] if expiry_date != 'nan' else "未設定"

    # --- 5. 🚀 關鍵核心：去「附件資料庫」分頁找資料 ---
    # 假設「附件資料庫」的 A 欄是許可證名稱，B 欄是展延紀錄，C 欄是附件連結
    # 這裡會根據 sel_name 去比對「附件資料庫」的內容
    file_info = file_df[file_df.iloc[:, 0] == sel_name]

    # --- 6. 主畫面呈現 ---
    st.title(f"📄 {sel_name}")
    st.info(f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}")
    
    st.divider()

    # --- 7. 第三層：呈現來自「附件資料庫」的內容 ---
    if not file_info.empty:
        f_target = file_info.iloc[0]
        ext_status = str(f_target.iloc[1]) # 假設附件資料庫 B 欄是展延狀態
        file_link = str(f_target.iloc[2])  # 假設附件資料庫 C 欄是連結

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📝 展延 / 變更狀態")
            st.success(ext_status if ext_status != 'nan' else "無紀錄")

        with col2:
            st.markdown("### 🔗 附件連結 / 位置")
            if file_link.startswith("http"):
                st.link_button("👉 點擊開啟附件檔案", file_link)
            else:
                st.warning(file_link if file_link != 'nan' else "尚未上傳連結")
    else:
        st.warning(f"⚠️ 在『附件資料庫』中找不到關於「{sel_name}」的紀錄。")

    st.divider()
    with st.expander("📊 查看『附件資料庫』原始清單"):
        st.dataframe(file_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 讀取失敗，請確認分頁名稱是否正確。")
    st.info(f"錯誤訊息：{e}")
