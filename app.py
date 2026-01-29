import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁配置
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 定義六大法規動作庫 (這就是你系統的六大核心)
# 這裡你可以根據實際需求，把這六類的 [展延/變更/異動] 寫得更細
ACTION_DATABASE = {
    "廢棄物類": {"展延": "📅 期滿前 2-3 個月提出。", "變更": "⚙️ 產出量/種類變更 15-30 日內提出。", "異動": "🔄 基本資料修正。"},
    "空污類": {"展延": "📅 期滿前 3-6 個月提出。", "變更": "⚙️ 設備變更前需重新申請。", "異動": "🔄 參數微調紀錄。"},
    "水污類": {"展延": "📅 期滿前 4-6 個月提出。", "變更": "⚙️ 負責人變更 30 日內。", "異動": "🔄 系統修正。"},
    "毒化物類": {"展延": "📅 期滿前 1-3 個月提出。", "變更": "⚙️ 種類增減前需申請。", "異動": "🔄 聯絡人變更。"},
    "應回收類": {"展延": "📅 期滿前 1 個月提出。", "變更": "⚙️ 廠址變更需重新登記。"},
    "其他類": {"指引": "請洽環安組確認法規需求。"}
}

# 3. 讀取資料
sheet_url = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(sheet_url, sheet_name='大豐既有許可證到期提醒')
    df['到期日期'] = pd.to_datetime(df['到期日期'], errors='coerce')
    
    # 強制分類邏輯：根據關聯法規字樣歸類到六大類
    def classify(law):
        law = str(law)
        if "廢棄物" in law: return "廢棄物類"
        if "空" in law: return "空污類"
        if "水" in law: return "水污類"
        if "毒" in law: return "毒化物類"
        if "應回收" in law: return "應回收類"
        return "其他類"
    
    df['分類'] = df['關聯法規'].apply(classify)
    return df

df = load_data()
today = datetime.now()

# 4. 頂部警報跑馬燈 (只抓快過期的)
urgent = df[(df['到期日期'] <= today + pd.Timedelta(days=180)) & (df['到期日期'].notnull())]
if not urgent.empty:
    alert_text = "　　".join([f"🚨 {row['許可證名稱']} (剩 {(row['到期日期']-today).days} 天)" for _, row in urgent.iterrows()])
    st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee>{alert_text}</marquee></div>', unsafe_allow_html=True)

# 5. 左側分類導航欄
with st.sidebar:
    st.header("📂 許可證分類導航")
    
    # 這裡就是你要求的六大項
    cat_list = ["廢棄物類", "空污類", "水污類", "毒化物類", "應回收類", "其他類"]
    selected_cat = st.radio("第一層：選擇類別", cat_list)
    
    st.divider()
    
    # 根據第一層篩選出第二層清單
    sub_df = df[df['分類'] == selected_cat]
    if not sub_df.empty:
        selected_permit = st.selectbox("第二層：選擇許可證名稱", sub_df['許可證名稱'].tolist())
    else:
        st.warning("此類別暫無資料")
        selected_permit = None

# 6. 右側主畫面
if selected_permit:
    info = df[df['許可證名稱'] == selected_permit].iloc[0]
    st.title(f"📄 {selected_permit}")
    
    # 狀態面板
    c1, c2, c3 = st.columns(3)
    c1.metric("到期日", info['到期日期'].strftime('%Y-%m-%d') if pd.notnull(info['到期日期']) else "未填寫")
    c2.metric("剩餘天數", (info['到期日期']-today).days if pd.notnull(info['到期日期']) else "N/A")
    c3.metric("管理分類", info['分類'])

    st.markdown("---")
    
    # 動作按鈕區
    st.subheader("💡 辦理項目指引")
    # 直接根據分類抓取 ACTION_DATABASE
    matched_actions = ACTION_DATABASE.get(selected_cat, {"說明": "暫無資料"})
    
    cols = st.columns(len(matched_actions))
    for i, (act_name, act_note) in enumerate(matched_actions.items()):
        if cols[i].button(act_name, use_container_width=True, type="primary"):
            st
