import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁配置
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 精準法規動作資料庫 (已補齊您提到的細項)
DETAIL_DATABASE = {
    "廢棄物": {
        "展延": {
            "說明": "📅 應於期滿前 2-3 個月提出申請。",
            "應備附件": ["清理計畫書 (更新版)", "廢棄物合約影本", "工廠登記證明文件", "負責人身分證影本"],
            "範本": "https://example.com/template_waste_extend"
        },
        "變更": {
            "說明": "⚙️ 產出量、種類、負責人或製程變更時提出 (涉及實質改變)。",
            "應備附件": ["變更申請表", "差異對照表", "製程說明圖", "試運轉計畫 (視需要)"],
            "範本": "https://example.com/template_waste_change"
        },
        "異動": {
            "說明": "🔄 基本資料 (如電話、傳真、聯絡人) 變更，不涉及實質變更項目。",
            "應備附件": ["異動申請書", "相關證明文件 (如身分證影本)"],
            "範本": "https://example.com/template_waste_update"
        }
    },
    "清除許可": {
        "展延": {
            "說明": "📅 應於期滿前 6-8 個月提出申請。",
            "應備附件": ["車輛照片", "駕駛員證照", "廢棄物處置同意書", "清運車輛清冊"],
            "範本": "https://example.com/template_clear_extend"
        },
        "變更": {
            "說明": "⚙️ 增加車輛、地址變更或更換負責人時辦理。",
            "應備附件": ["變更申請書", "車輛規格證明", "保險單影本"],
            "範本": "https://example.com/template_clear_change"
        },
        "變更暨展延": {
            "說明": "🛠️ **【合併辦理】** 於到期前需進行變更時，可一併提交展延申請，省去重複審查作業。",
            "應備附件": ["變更暨展延申請書", "全套更新版附件", "歷年清除量統計"],
            "範本": "https://example.com/template_clear_both"
        }
    }
}

# 3. 讀取資料
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
urgent = df[(df['到期日期'] <= today + pd.Timedelta(days=180)) & (df['到::期日期'].notnull())]
if not urgent.empty:
    alert_text = "　　".join([f"🚨 {row['許可證名稱']} (剩 {(row['到期日期']-today).days} 天)" for _, row in urgent.iterrows()])
    st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{alert_text}</marquee></div>', unsafe_allow_html=True)

# 5. 左側導航 (完全遵照 Excel 分類)
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
    
    # 狀態面板
    c1, c2, c3 = st.columns(3)
    c1.metric("到期日", info['到期日期'].strftime('%Y-%m-%d') if pd.notnull(info['到期日期']) else "未填寫")
    days_left = (info['到期日期']-today).days if pd.notnull(info['到::期日期']) else None
    c2.metric("剩餘天數", f"{days_left} 天" if days_left is not None else "N/A")
    c3.metric("管理類型", info['許可證類型'])

    st.markdown("---")
    
    # 7. 辦理項目指引 (核心邏輯：根據關聯法規內容匹配)
    st.subheader("🛠️ 申請辦理指引")
    law_content = str(info['關聯法規'])
    
    # 尋找對應法規分類
    matched_key = None
    if "廢棄物" in law_content: matched_key = "廢棄物"
    elif "清除" in law_content: matched_key = "清除許可"
    
    if matched_key:
        actions = DETAIL_DATABASE[matched_key]
        cols = st.columns(len(actions))
        
        for i, action_name in enumerate(actions.keys()):
            if cols[i].button(action_name, use_container_width=True, type="primary"):
                st.session_state.current_data = actions[action_name]
                st.session_state.current_action_name = action_name

        # 顯示勾選清單
        if "current_data" in st.session_state:
            data = st.session_state.current_data
            st.write(f"### 📍 項目：{st.session_state.current_action_name}")
            st.success(data['說明'])
            
            st.write("📋 **應備附件檢查表：**")
            for item in data['應備附件']:
                st.checkbox(item, key=f"{selected_permit}_{st.session_state.current_action_name}_{item}")
            
            st.link_button(f"📥 下載{st.session_state.current_action_name}相關範本", data['範本'])
    else:
        st.info("💡 此類別目前僅供日期監控。若需辦理指引，請手動確認法規要求。")

else:
    st.info("👈 請先從左側選擇許可證。")
