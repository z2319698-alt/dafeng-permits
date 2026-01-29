import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁配置
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 定義法規知識庫 (你可以根據實際需求修改這裡的文字)
LAW_DATABASE = {
    "水污染防治法": {
        "展延需求": "應於期滿前 6 個月至 4 個月內申請展延。",
        "異動需求": "負責人、基本資料變更應於 30 日內辦理；製程異動應於事前申請。",
        "法條連結": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=O0040001"
    },
    "空氣污染防制法": {
        "展延需求": "應於有效期間屆滿前 3 至 6 個月內申請展延。",
        "異動需求": "製程設備或規模變更，應重新申請核發設置許可證。",
        "法條連結": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=O0020001"
    },
    "廢棄物清理法": {
        "展延需求": "依各地方環保局規定，通常為屆滿前 3 個月。",
        "異動需求": "清理計畫書變更需於事實發生後 15-30 日內提出。",
        "法條連結": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=O0050001"
    }
}

# 3. 讀取資料
sheet_url = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(sheet_url, sheet_name='大豐既有許可證到期提醒')
    df['到期日期'] = pd.to_datetime(df['到期日期'], errors='coerce')
    return df

df = load_data()

# 4. 主介面
st.title("🛡️ 許可證管理與法規指引")

# 5. 互動選擇區
st.info("💡 請從下方下拉選單選擇一個許可證，查看其法規辦理需求：")

# 讓使用者選一個許可證
selected_permit = st.selectbox("請選擇許可證名稱：", df['許可證名稱'].unique())

# 抓取該許可證的詳細資料
permit_info = df[df['許可證名稱'] == selected_permit].iloc[0]

# 顯示法規需求卡片
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"📋 證照基本資料")
    st.write(f"**到期日期：** {permit_info['到期日期'].strftime('%Y-%m-%d') if pd.notnull(permit_info['到期日期']) else '未填寫'}")
    st.write(f"**目前狀態：** {permit_info['備註'] if '備註' in df.columns else '監控中'}")
    st.write(f"**負責人：** {permit_info['負責人信箱']}")

with col2:
    st.subheader(f"⚖️ 法規辦理指引")
    # 根據 Excel 裡的「關聯法規」欄位來對應知識庫
    law_category = permit_info['關聯法規']
    
    if law_category in LAW_DATABASE:
        law = LAW_DATABASE[law_category]
        st.warning(f"**【{law_category}】相關規定：**")
        st.write(f"📌 **展延：** {law['展延需求']}")
        st.write(f"⚙️ **異動/變更：** {law['異動需求']}")
        st.link_button("查看完整法規連結", law['法規連結'])
    else:
        st.write("⚠️ 尚未建立此法規的詳細指引，請洽環安室。")

st.divider()

# 6. 原有的清單顯示
st.subheader("📁 全量清單總覽")
st.dataframe(df, use_container_width=True)
