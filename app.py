import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁配置
st.set_page_config(page_title="大豐許可證分類管理系統", layout="wide")

# 2. 法規動作資料庫 (可視需求持續擴充)
ACTION_DATABASE = {
    "廢棄物": {"展延": "📅 期滿前 2-3 個月提出。", "變更": "⚙️ 事實發生後 15-30 日內提出。", "異動": "🔄 系統直接修正。"},
    "清除許可": {"展延": "📅 期滿前 6-8 個月提出。", "變更暨展延": "🛠️ 可同時提交。"},
    "水污染": {"展延": "📅 期滿前 6-4 個月提出。", "變更": "⚙️ 30 日內辦理。"}
}

# 3. 讀取與處理資料
sheet_url = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(sheet_url, sheet_name='大豐既有許可證到期提醒')
    df['到期日期'] = pd.to_datetime(df['到期日期'], errors='coerce')
    # 建立一個簡單的「大類別」欄位供導航使用
    df['法規大類'] = df['關聯法規'].apply(lambda x: str(x).split('法')[0] + "法" if '法' in str(x) else "其他類")
    return df

df = load_data()
today = datetime.now()

# 4. 頂部警報跑馬燈
urgent_items = df[(df['到期日期'] <= today + pd.Timedelta(days=180)) & (df['到期日期'].notnull())]
if not urgent_items.empty:
    alert_text = "　　".join([f"🚨 {row['許可證名稱']} (剩 {(row['到期日期']-today).days} 天)" for _, row in urgent_items.iterrows()])
    st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee>{alert_text}</marquee></div>', unsafe_allow_html=True)

# 5. 左側分類導航欄
with st.sidebar:
    st.header("📂 許可證分類")
    
    # 第一層：選擇類型
    all_categories = sorted(df['法規大類'].unique())
    selected_cat = st.selectbox("1️⃣ 選擇法規類型：", ["請選擇"] + all_categories)
    
    # 第二層：根據第一層篩選名稱
    if selected_cat != "請選擇":
        sub_list = df[df['法規大類'] == selected_cat]['許可證名稱'].tolist()
        selected_permit = st.radio("2️⃣ 選擇特定許可證：", sub_list)
    else:
        st.write("請先選擇上方類型")
        selected_permit = None

# 6. 右側主畫面
if selected_permit:
    st.title(f"📄 {selected_permit}")
    info = df[df['許可證名稱'] == selected_permit].iloc[0]
    
    # 指標看板
    c1, c2 = st.columns(2)
    c1.metric("到期日", info['到期日期'].strftime('%Y-%m-%d') if pd.notnull(info['到期日期']) else "未填寫")
    c2.metric("關聯法規", info['關聯法規'])

    st.markdown("---")
    
    # 動作按鈕區
    st.subheader("💡 辦理項目指引")
    matched_category = next((v for k, v in ACTION_DATABASE.items() if k in str(info['關聯法規'])), None)
    
    if matched_category:
        cols = st.columns(len(matched_category))
        for i, (act_name, act_note) in enumerate(matched_category.items()):
            if cols[i].button(act_name, use_container_width=True, type="secondary"):
                st.warning(f"**{act_name} 說明：**\n\n{act_note}")
    else:
        st.info("此項目暫無預設 SOP，請依個案辦理。")
else:
    # 初始歡迎畫面
    st.title("🛡️ 大豐許可證管理系統")
    st.info("請從左側選單選擇「法規類型」開始作業。")
    st.image("https://via.placeholder.com/800x200.png?text=Select+a+Category+to+Begin", use_container_width=True)
