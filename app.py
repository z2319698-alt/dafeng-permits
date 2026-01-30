import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 資料來源
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

try:
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    df.columns = [str(c).strip() for c in df.columns]

    # --- 3. 側邊選單 ---
    st.sidebar.markdown("## 📂 系統導覽")
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(df.iloc[:, 0].dropna().unique()))
    sub_df = df[df.iloc[:, 0] == sel_type].copy()
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_df.iloc[:, 2].dropna().unique())

    # --- 4. 抓取該筆資料的所有內容 ---
    target = sub_df[sub_df.iloc[:, 2] == sel_name].iloc[0]
    
    # 定義欄位 (根據截圖位置)
    permit_id = str(target.iloc[1])    # B: 管制編號
    expiry_date = str(target.iloc[3])  # D: 到期日期
    regulation = str(target.iloc[4])   # E: 關聯法規
    email = str(target.iloc[6])        # G: 負責人信箱
    status = str(target.iloc[7])       # H: 狀態
    reg_link = str(target.iloc[8])     # I: 法規連結

    clean_date = expiry_date[:10] if expiry_date != 'nan' else "未設定"

    # --- 5. 主畫面呈現 ---
    st.title(f"📄 {sel_name}") # 標題純名稱
    st.info(f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}") # 副標題含日期
    
    st.divider()

    # --- 6. 分類顯示所有資訊 ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 關聯法規與狀態")
        st.write(f"**目前狀態：** {status}")
        st.write(f"**法規依據：** {regulation}")
        if reg_link.startswith("http"):
            st.markdown(f"🔗 [點我查看法規詳情]({reg_link})")

    with col2:
        st.subheader("📧 管理資訊與附件")
        st.write(f"**負責人信箱：** {email}")
        # 如果你後續有附件欄位，可以繼續在這邊增加 iloc 索引
        st.write("**附件狀態：** 尚未上傳附件")

    st.divider()

    # 7. 底部保留完整表格，確保你什麼都看得到
    with st.expander("📊 查看完整數據明細"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 讀取失敗：{e}")
