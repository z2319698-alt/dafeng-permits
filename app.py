import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁配置
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 定義「辦理細項與附件資料庫」
# 這裡可以根據你提供的 AppSheet 邏輯，把需要填寫或準備的附件放進去
DETAIL_DATABASE = {
    "廢棄物": {
        "展延": {
            "說明": "📅 應於期滿前 2-3 個月提出申請。",
            "應備附件": ["清理計畫書 (更新版)", "廢棄物合約影本", "工廠登記證明文件", "負責人身分證影本"],
            "範本連結": "https://example.com/template_waste_extend"
        },
        "變更": {
            "說明": "⚙️ 產出量、種類或負責人變更時提出。",
            "應備附件": ["變更申請表", "差異對照表", "製程說明圖"],
            "範本連結": "https://example.com/template_waste_change"
        }
    },
    "清除許可": {
        "展延": {
            "說明": "📅 期滿前 6-8 個月提出申請。",
            "應備附件": ["車輛照片", "駕駛員證照", "廢棄物處置同意書", "清運車輛清冊"],
            "範本連結": "https://example.com/template_clear_extend"
        }
    }
}

# 3. 讀取資料 (保持與 Excel 同步)
sheet_url = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(sheet_url, sheet_name='大豐既有許可證到期提醒')
    df['到期日期'] = pd.to_datetime(df['到期日期'], errors='coerce')
    df['許可證類型'] = df['許可證類型'].fillna("未分類")
    return df

df = load_data()
today = datetime.now()

# 4. 頂部警報跑馬燈
urgent = df[(df['到期日期'] <= today + pd.Timedelta(days=180)) & (df['到期日期'].notnull())]
if not urgent.empty:
    alert_text = "　　".join([f"🚨 {row['許可證名稱']} (剩 {(row['到期日期']-today).days} 天)" for _, row in urgent.iterrows()])
    st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{alert_text}</marquee></div>', unsafe_allow_html=True)

# 5. 左側導航
with st.sidebar:
    st.header("📂 系統導航")
    type_list = sorted(df['許可證類型'].unique().tolist())
    selected_type = st.selectbox("許可證類型", type_list)
    st.divider()
    sub_df = df[df['許可證類型'] == selected_type]
    selected_permit = st.radio("大豐許可證", sub_df['許可證名稱'].tolist())

# 6. 右側主畫面
if selected_permit:
    info = df[df['許可證名稱'] == selected_permit].iloc[0]
    st.title(f"📄 {selected_permit}")
    
    # 狀態看板
    c1, c2, c3 = st.columns(3)
    c1.metric("到期日", info['到期日期'].strftime('%Y-%m-%d') if pd.notnull(info['到期日期']) else "未填寫")
    days_left = (info['到期日期']-today).days if pd.notnull(info['到期日期']) else None
    c2.metric("剩餘天數", f"{days_left} 天" if days_left is not None else "N/A")
    c3.metric("管理分類", info['許可證類型'])

    st.markdown("---")
    
    # 7. 辦理項目與附件連動區
    st.subheader("🛠️ 辦理申請指引")
    
    # 匹配資料庫關鍵字 (例如 "廢棄物")
    law_content = str(info['關聯法規'])
    matched_key = next((k for k in DETAIL_DATABASE.keys() if k in law_content), None)
    
    if matched_key:
        # 顯示該法規可辦理的項目按鈕
        actions = DETAIL_DATABASE[matched_key]
        cols = st.columns(len(actions))
        
        for i, action_name in enumerate(actions.keys()):
            if cols[i].button(action_name, use_container_width=True, type="primary"):
                st.session_state.action_data = actions[action_name]
                st.session_state.action_name = action_name

        # 顯示點擊後的細節
        if "action_data" in st.session_state:
            data = st.session_state.action_data
            st.markdown(f"### 📍 正在查看：{st.session_state.action_name}")
            st.warning(data['說明'])
            
            # 附件清單 (Checklist)
            st.write("📋 **應備附件清單：**")
            for item in data['應備附件']:
                st.checkbox(item, key=f"{selected_permit}_{item}")
            
            # 提供範本下載按鈕
            st.link_button(f"📥 下載 {st.session_state.action_name} 範本文件", data['範本連結'])
    else:
        st.info("此項目暫無預設辦理指引，請參考法規公告或洽環安單位。")

else:
    st.info("👈 請從左側選擇許可證類型。")

# 8. 數據備查
with st.expander("📊 查看原始數據總表"):
    st.dataframe(df, use_container_width=True)
