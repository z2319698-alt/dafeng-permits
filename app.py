import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁配置
st.set_page_config(page_title="大豐許可證監控系統", layout="wide")

# 2. 定義動作資料庫 (保留原本的)
ACTION_DATABASE = {
    "廢棄物": {
        "展延": "📅 應於期滿前 2-3 個月提出。",
        "變更": "⚙️ 事實發生後 15-30 日內提出。",
        "異動": "🔄 系統直接修正即可。"
    },
    "清除許可": {
        "展延": "📅 期滿前 6-8 個月提出。",
        "變更暨展延": "🛠️ 可同時提交，省去重複審查。"
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
today = datetime.now()

# 4. 核心邏輯：計算哪些「現在」該辦理？
# 這裡設定：距離到期日剩不到 180 天就開始跑馬燈提醒
urgent_items = df[
    (df['到期日期'] <= today + pd.Timedelta(days=180)) & 
    (df['到期日期'].notnull())
].copy()
urgent_items = urgent_items.sort_values('到期日期')

# 5. 製作跑馬燈 (使用 HTML/CSS)
if not urgent_items.empty:
    # 串接所有警報訊息
    msg_list = []
    for _, row in urgent_items.iterrows():
        days_left = (row['到期日期'] - today).days
        status_text = "🚨 已逾期" if days_left < 0 else f"⏳ 剩餘 {days_left} 天"
        msg_list.append(f"【{row['許可證名稱']}】{status_text}，請儘速辦理！")
    
    alert_text = "　　　　".join(msg_list) # 間隔符號
    
    st.markdown(f"""
        <div style="background-color: #ff4b4b; color: white; padding: 10px; border-radius: 5px; font-weight: bold;">
            <marquee scrollamount="6">{alert_text}</marquee>
        </div>
    """, unsafe_allow_html=True)

st.write("#")

# 6. 視覺化預警區塊 (三格看板)
col1, col2, col3 = st.columns(3)

# 已逾期
overdue = df[df['到期日期'] < today]
col1.metric("🚨 已逾期 (需立即補辦)", len(overdue), delta_color="inverse")

# 6個月內到期 (法規展延高峰期)
upcoming = df[(df['到期日期'] >= today) & (df['到期日期'] <= today + pd.Timedelta(days=180))]
col2.metric("⚠️ 180天內到期 (應準備展延)", len(upcoming))

# 系統狀態
col3.metric("✅ 正常監控中", len(df) - len(overdue) - len(upcoming))

st.markdown("---")

# 7. 左側導航與右側功能按鈕 (承襲之前的設計)
with st.sidebar:
    st.title("📂 許可證清單")
    search_query = st.text_input("🔍 搜尋許可證...")
    filtered_df = df[df['許可證名稱'].str.contains(search_query, na=False)]
    selected_permit = st.radio("請選擇：", filtered_df['許可證名稱'].tolist())

# 主內容區
st.subheader(f"📄 {selected_permit}")
info = df[df['許可證名稱'] == selected_permit].iloc[0]
law_name = str(info['關聯法規'])

# 顯示該法規按鈕
matched_category = None
for key in ACTION_DATABASE:
    if key in law_name:
        matched_category = ACTION_DATABASE[key]
        break

if matched_category:
    action_names = list(matched_category.keys())
    cols = st.columns(len(action_names))
    for i, action in enumerate(action_names):
        if cols[i].button(action, use_container_width=True):
            st.warning(f"💡 **{action} 辦理指引：**\n\n{matched_category[action]}")
else:
    st.info("此項目僅供到期日監控，若需法規指引請洽環安組。")

st.divider()
st.caption(f"數據最後更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
