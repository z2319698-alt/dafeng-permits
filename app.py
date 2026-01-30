import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 資料來源
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

try:
    # 讀取 Excel
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    df.columns = [str(c).strip() for c in df.columns]

    # --- 3. 側邊選單 (Sidebar) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # A 欄：類型
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(df.iloc[:, 0].dropna().unique()))
    sub_df = df[df.iloc[:, 0] == sel_type].copy()
    
    # C 欄：名稱
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_df.iloc[:, 2].dropna().unique())

    # --- 4. 抓取該筆資料的所有欄位內容 ---
    target_row = sub_df[sub_df.iloc[:, 2] == sel_name].iloc[0]
    
    # 欄位定義 (根據你的 Excel 順序)
    permit_id = str(target_row.iloc[1])    # B 欄：管制編號
    expiry_date = str(target_row.iloc[3])  # D 欄：到期日期
    extension = str(target_row.iloc[4])    # E 欄：展延/變更 (假設位置)
    attachment = str(target_row.iloc[5])   # F 欄：附件位置 (假設位置)

    clean_date = expiry_date[:10] if expiry_date != 'nan' else "未設定"

    # --- 5. 主畫面呈現 ---
    # ✅ 標題：許可證名稱 (C 欄)
    st.title(f"📄 {sel_name}")

    # ✅ 副標題：管制編號 + 到期日期 (B 欄 + D 欄)
    st.info(f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}")
    
    st.divider()

    # --- 🚀 6. 顯示 展延 與 附件 資訊 ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 展延 / 變更狀態")
        if extension != "nan":
            st.write(extension)
        else:
            st.write("目前無紀錄")

    with col2:
        st.subheader("🔗 附件連結 / 位置")
        if attachment != "nan":
            # 如果是網址，可以點擊
            if attachment.startswith("http"):
                st.markdown(f"[點我打開附件檔案]({attachment})")
            else:
                st.write(attachment)
        else:
            st.write("尚未上傳附件")

    st.divider()

    # 7. 原始數據總表 (保留原本功能)
    with st.expander("📊 查看完整數據明細"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 讀取失敗，請確認 Excel 欄位位置。")
    st.info(f"錯誤原因：{e}")
