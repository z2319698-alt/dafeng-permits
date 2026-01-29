import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁高級感配置
st.set_page_config(page_title="大豐許可證法規管理", layout="wide")

# 2. 定義法規大腦 (只要 Excel 裡的字有對到，就會顯示這些內容)
# 這裡建議把 Excel 裡的長字簡化，比如 "水污染防治法第14條..." 簡化為 "水污染防治法"
LAW_DATABASE = {
    "空氣污染防制法": {
        "展延期限": "有效期限屆滿前 3 至 6 個月內",
        "必備動作": "至空污系統提交展延申請，並檢查排放口監測設備是否需校正。",
        "異動規定": "製程設備、操作參數變更前，應重新申請設置許可。"
    },
    "水污染防治法": {
        "展延期限": "有效期限屆滿前 6 個月至 4 個月內",
        "必備動作": "需委託合格檢測公司進行放流水採樣，並上傳水措計畫。",
        "異動規定": "負責人變更於 30 日內辦理；製程異動應於事前申請。"
    },
    "廢棄物清理法": {
        "展延期限": "依各地方環保局規定，通常為屆滿前 2 至 3 個月",
        "必備動作": "重新核算廢棄物產生量，更新清理計畫書 (IWR&MS)。",
        "異動規定": "廢棄物種類增減需提前申請變更。"
    },
    "應回收登記證": {
        "展延期限": "屆滿前 1 個月辦理換證",
        "必備動作": "確認回收處理量與申報數據一致。",
        "異動規定": "廠址或設備變更需重新辦理登記。"
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

# 4. 主視覺區
st.title("🛡️ 許可證辦理指引系統")
st.markdown("---")

# 5. 互動式法規查找 (這就是你要的功能)
st.subheader("🔍 選擇許可證以查看法規需求")
selected_permit = st.selectbox("請選擇要查詢的許可證：", df['許可證名稱'].unique())

# 抓取該筆資料
info = df[df['許可證名稱'] == selected_permit].iloc[0]
law_name = str(info['關聯法規']) # 抓取 Excel 裡的關聯法規文字

# 建立兩個卡片
col1, col2 = st.columns([1, 1.2])

with col1:
    st.info(f"📋 **基本資訊**\n\n**到期日：** {info['到期日期'].strftime('%Y-%m-%d') if pd.notnull(info['到期日期']) else '未填寫'}\n\n**狀態：** {info['狀態'] if '狀態' in df.columns else '監控中'}")

with col2:
    # 這裡做「關鍵字匹配」
    matched_law = None
    for key in LAW_DATABASE:
        if key in law_name: # 只要 Excel 裡的字包含「水污染」等關鍵字就觸發
            matched_law = LAW_DATABASE[key]
            law_title = key
            break
    
    if matched_law:
        st.warning(f"⚖️ **{law_title} 辦理規定**")
        st.write(f"📅 **展延辦理時間：** {matched_law['展延期限']}")
        st.write(f"📝 **應辦事項：** {matched_law['必備動作']}")
        st.write(f"🔄 **異動變更提醒：** {matched_law['異動規定']}")
    else:
        st.write("❓ **法規資料補充中**")
        st.caption(f"Excel 登記法規為：{law_name}，系統暫無對應 SOP。")

st.divider()
st.subheader("📁 完整清單")
st.dataframe(df, use
