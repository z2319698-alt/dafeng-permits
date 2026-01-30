import streamlit as st
import pandas as pd

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 資料來源
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"
SHEET_NAME = "大豐既有許可證到期提醒"

try:
    # 讀取 Excel 並清理欄位名稱
    df = pd.read_excel(URL, sheet_name=SHEET_NAME)
    df.columns = [str(c).strip() for c in df.columns]

    # --- 3. 側邊選單 (第一層 & 第二層) ---
    st.sidebar.markdown("## 📂 系統導覽")
    
    # A 欄：類型 (第一層)
    sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(df.iloc[:, 0].dropna().unique()))
    sub_df = df[df.iloc[:, 0] == sel_type].copy()
    
    # C 欄：名稱 (第二層)
    sel_name = st.sidebar.radio("2. 選擇許可證", sub_df.iloc[:, 2].dropna().unique())

    # --- 4. 第三層：主畫面詳細資訊呈現 ---
    # 定義該筆資料列
    target = sub_df[sub_df.iloc[:, 2] == sel_name].iloc[0]
    
    # 精確抓取 Excel 欄位 [根據你最新調整的順序]
    permit_id = str(target.iloc[1])    # B 欄：管制編號
    expiry_date = str(target.iloc[3])  # D 欄：到期日期
    status_info = str(target.iloc[4])  # E 欄：展延/變更狀態 (請確認是否為這格)
    attachment = str(target.iloc[5])   # F 欄：附件位置 (請確認是否為這格)

    clean_date = expiry_date[:10] if expiry_date != 'nan' else "未設定"

    # --- 5. 畫面呈現 ---
    # ✅ 標題：純名稱 (C 欄)
    st.title(f"📄 {sel_name}")

    # ✅ 副標題：管制編號 + 到期日期 (B 欄 + D 欄)
    st.info(f"🆔 管制編號：{permit_id}　|　📅 到期日期：{clean_date}")
    
    st.divider()

    # ✅ 下方呈現你要的「展延」與「附件」區塊
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 展延 / 變更狀態")
        st.info(status_info if status_info != 'nan' else "無紀錄")

    with col2:
        st.markdown("### 🔗 附件連結 / 位置")
        if attachment.startswith("http"):
            st.link_button("👉 點擊開啟附件檔案", attachment)
        else:
            st.warning(attachment if attachment != 'nan' else "尚未上傳附件")

    st.divider()

    # 底部保留總表供參考
    with st.expander("📊 查看該分類原始數據明細"):
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 讀取失敗，可能是 Excel 欄位位置不對。")
    st.info(f"錯誤訊息：{e}")
