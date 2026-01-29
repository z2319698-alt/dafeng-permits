import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁高級感配置
st.set_page_config(page_title="大豐許可證指引系統", layout="wide")

# 2. 定義詳細的法規動作資料庫
# 格式：{法規關鍵字: {動作名稱: 說明內容}}
ACTION_DATABASE = {
    "廢棄物": {
        "展延": "📅 **展延辦理：** 應於期滿前 2-3 個月提出。\n\n📝 **應備文件：** 更新清理計畫書、檢附廢棄物合約。",
        "變更": "⚙️ **變更辦理：** 產出量、種類或負責人變更時，應於事實發生後 15-30 日內提出。",
        "異動": "🔄 **異動辦理：** 基本資料（如電話、傳真）變更，於系統直接修正即可。"
    },
    "清除許可": {
        "展延": "📅 **展延辦理：** 期滿前 6-8 個月提出。\n\n📝 **應備文件：** 車輛照片、合法的處置場證明。",
        "變更": "⚙️ **變更辦理：** 增加車輛、地址變更需事前申請。",
        "變更暨展延": "🛠️ **合併辦理：** 若剛好遇到到期，可同時提交異動與展延申請，省去兩次審查費。"
    },
    "應回收": {
        "展延": "📅 **展延辦理：** 屆滿前 1 個月辦理換證。\n\n📝 **應備文件：** 工廠登記證、回收處理量紀錄。",
        "變更": "⚙️ **變更辦理：** 負責人或處理項目變更，需檢附相關證明文件。"
    },
    "水污染": {
        "展延": "📅 **展延辦理：** 期滿前 6 個月至 4 個月內。\n\n📝 **應備文件：** 放流水質檢測報告、水措計畫書。",
        "變更": "⚙️ **變更辦理：** 負責人或製程異動應於 30 日內辦理。",
        "異動": "🔄 **異動辦理：** 非重大製程參數微調，可於申報時註記。"
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

# 4. 左側導航欄 (Sidebar)
with st.sidebar:
    st.title("📂 許可證清單")
    # 建立搜尋與清單
    search_query = st.text_input("🔍 搜尋許可證...")
    filtered_list = df[df['許可證名稱'].str.contains(search_query, na=False)]['許可證名稱'].tolist()
    
    # 使用 radio 製作選單，讓使用者選取特定許可證
    selected_permit = st.radio("請選擇許可證：", filtered_list)

# 5. 右側主畫面區
st.title(f"📄 {selected_permit}")
st.markdown("---")

# 抓取該筆資料
info = df[df['許可證名稱'] == selected_permit].iloc[0]
law_name = str(info['關聯法規'])

# 顯示基本狀態卡片
c1, c2, c3 = st.columns(3)
c1.metric("目前狀態", info['狀態'] if '狀態' in df.columns else "監控中")
c2.metric("到期日期", info['到期日期'].strftime('%Y-%m-%d') if pd.notnull(info['到期日期']) else "未填寫")
c3.metric("關聯法規", law_name.split('法')[0] + "法" if '法' in law_name else law_name)

st.write("##")

# 6. 法規動作選擇 (關鍵功能)
st.subheader("💡 請選擇欲辦理的項目：")

# 匹配法規庫
matched_category = None
for key in ACTION_DATABASE:
    if key in law_name:
        matched_category = ACTION_DATABASE[key]
        break

if matched_category:
    # 根據該法規有的項目，動態生成按鈕
    # 使用 columns 橫向排列按鈕
    action_names = list(matched_category.keys())
    cols = st.columns(len(action_names))
    
    # 點擊按鈕後會記錄狀態
    for i, action in enumerate(action_names):
        if cols[i].button(action, use_container_width=True, type="primary"):
            st.session_state.current_action = action
            st.session_state.action_content = matched_category[action]

    # 顯示按鈕點擊後的內容
    if "current_action" in st.session_state:
        st.write("---")
        st.success(f"### 【{st.session_state.current_action}】說明指南")
        st.write(st.session_state.action_content)
else:
    st.warning("⚠️ 此許可證尚未建立法規動作資料庫。")

st.divider()
with st.expander("查看原始數據"):
    st.dataframe(df, use_container_width=True)
