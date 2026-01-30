import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 資料來源
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=5)
def load_all_data():
    main_df = pd.read_excel(URL, sheet_name="大豐既有許可證到期提醒")
    file_df = pd.read_excel(URL, sheet_name="附件資料庫")
    # 清理欄位空格
    main_df.columns = [str(c).strip() for c in main_df.columns]
    file_df.columns = [str(c).strip() for c in file_df.columns]
    return main_df, file_df

try:
    main_df, file_df = load_all_data()

    # --- 3. 側邊選單 (第一、二層) ---
    st.sidebar.markdown("## 📂 系統導覽")
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
    sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())

    # --- 4. 抓取主表資料 (B欄編號, D欄日期) ---
    target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
    permit_id = str(target_main.iloc[1])
    expiry_date = str(target_main.iloc[3])
    clean_date = expiry_date[:10] if expiry_date != 'nan' else "未設定"

    # --- 5. 主畫面呈現 (你要的標題格式) ---
    # ✅ 標題：純名稱
    st.title(f"📄 {sel_name}")
    # ✅ 副標題：編號 + 日期
    st.info(f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}")
    
    st.divider()

    # --- 6. 🚀 第三層：橫向選單 (點選才觸發) ---
    # 從「附件資料庫」抓取該類型對應的所有「辦理項目」(B欄)
    db_info = file_df[file_df.iloc[:, 0] == sel_type]
    options = db_info.iloc[:, 1].dropna().unique().tolist()

    if options:
        st.markdown("### 🛠️ 請選擇辦理項目")
        # 使用 st.pills 或 st.segmented_control (新版橫向選單)
        # 如果你想要原本最簡單的橫向按鈕，這裡用 toggle 或 selectbox
        sel_action = st.segmented_control("辦理項目", options, selection_mode="single")

        # --- 7. 第四層：顯示附件 ---
        if sel_action:
            st.divider()
            action_data = db_info[db_info.iloc[:, 1] == sel_action].iloc[0]
            
            st.subheader(f"📌 {sel_action} - 檢附資料需求")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write("**辦理步驟說明：**")
                st.info(action_data.iloc[2] if str(action_data.iloc[2]) != 'nan' else "無特別說明")
            
            with col2:
                st.write("**應檢附附件清單：**")
                # 抓取 D 欄之後的所有內容
                attachments = action_data.iloc[3:].dropna().tolist()
                if attachments:
                    for idx, item in enumerate(attachments, 1):
                        st.write(f"{idx}. {item}")
                else:
                    st.write("無需額外附件")
    else:
        st.warning(f"⚠️ 在附件資料庫中找不到『{sel_type}』的辦理項目")

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
