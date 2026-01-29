import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁配置
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 定義法規動作庫 (根據關鍵字匹配，供按鈕顯示使用)
ACTION_DATABASE = {
    "廢棄物": {"展延": "📅 期滿前 2-3 個月提出。", "變更": "⚙️ 產出量/種類變更 15-30 日內提出。", "異動": "🔄 基本資料修正。"},
    "空污": {"展延": "📅 期滿前 3-6 個月提出。", "變更": "⚙️ 設備變更前需重新申請。", "異動": "🔄 參數微調紀錄。"},
    "水污": {"展延": "📅 期滿前 4-6 個月提出。", "變更": "⚙️ 負責人變更 30 日內。", "異動": "🔄 系統修正。"},
    "毒化物": {"展延": "📅 期滿前 1-3 個月提出。", "變更": "⚙️ 種類增減前需申請。", "異動": "🔄 聯絡人變更。"},
    "應回收": {"展延": "📅 期滿前 1 個月提出。", "變更": "⚙️ 廠址變更需重新辦理登記。"}
}

# 3. 讀取資料
sheet_url = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    # 讀取 Excel
    df = pd.read_excel(sheet_url, sheet_name='大豐既有許可證到期提醒')
    df['到期日期'] = pd.to_datetime(df['到期日期'], errors='coerce')
    # 確保「許可證類型」沒有空值，方便分類
    df['許可證類型'] = df['許可證類型'].fillna("未分類")
    return df

df = load_data()
today = datetime.now()

# 4. 頂部警報跑馬燈
urgent = df[(df['到期日期'] <= today + pd.Timedelta(days=180)) & (df['到期日期'].notnull())]
if not urgent.empty:
    alert_text = "　　".join([f"🚨 {row['許可證名稱']} (剩 {(row['到期日期']-today).days} 天)" for _, row in urgent.iterrows()])
    st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{alert_text}</marquee></div>', unsafe_allow_html=True)

# 5. 左側分類導航欄
with st.sidebar:
    st.header("📂 系統導航")
    
    # 第一層：直接抓 Excel 裡的「許可證類型」
    type_list = sorted(df['許可證類型'].unique().tolist())
    selected_type = st.selectbox("許可證類型", type_list)
    
    st.divider()
    
    # 第二層：根據所選類型，抓取對應的「許可證名稱」
    sub_df = df[df['許可證類型'] == selected_type]
    selected_permit = st.radio("大豐許可證", sub_df['許可證名稱'].tolist())

# 6. 右側主畫面
if selected_permit:
    info = df[df['許可證名稱'] == selected_permit].iloc[0]
    st.title(f"📄 {selected_permit}")
    
    # 指標看板
    c1, c2, c3 = st.columns(3)
    c1.metric("到期日", info['到期日期'].strftime('%Y-%m-%d') if pd.notnull(info['到期日期']) else "未填寫")
    days_left = (info['到期日期']-today).days if pd.notnull(info['到期日期']) else None
    c2.metric("剩餘天數", f"{days_left} 天" if days_left is not None else "N/A")
    c3.metric("目前狀態", info['狀態'] if '狀態' in df.columns else "監控中")

    st.markdown("---")
    
    # 動作按鈕區 (根據關聯法規內容匹配指引)
    st.subheader("💡 辦理項目指引")
    law_content = str(info['關聯法規'])
    
    # 尋找匹配的法規指引
    matched_actions = None
    for key, actions in ACTION_DATABASE.items():
        if key in law_content:
            matched_actions = actions
            break
            
    if matched_actions:
        cols = st.columns(len(matched_actions))
        for i, (act_name, act_note) in enumerate(matched_actions.items()):
            if cols[i].button(act_name, use_container_width=True, type="primary"):
                st.info(f"### 【{act_name}】辦理重點\n\n{act_note}")
    else:
        st.info("此類別暫無預設指引，請依個案法規辦理。")

else:
    st.title("🛡️ 大豐環境許可證監控系統")
    st.info("👈 請從左側選擇許可證類型開始。")

# 7. 底部數據總表
with st.expander("📊 查看原始數據總表"):
    st.dataframe(df, use_container_width=True)
