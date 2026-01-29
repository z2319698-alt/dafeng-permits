import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁配置
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 精準法規動作資料庫 - 嚴格對照您的需求
DETAIL_DATABASE = {
    "清理計畫": { # 對應 廢棄物清理計畫書
        "展延": {
            "說明": "📅 應於期滿前 2-3 個月提出申請。",
            "應備附件": ["清理計畫書 (更新版)", "廢棄物合約影本", "負責人身分證影本"]
        },
        "變更": {
            "說明": "⚙️ 產出量、種類或製程變更時提出。",
            "應備附件": ["變更申請表", "差異對照表", "製程說明圖"]
        },
        "異動": {
            "說明": "🔄 基本資料 (如電話、聯絡人) 變更，不涉及實質內容。",
            "應備附件": ["異動申請書", "相關證明文件"]
        }
    },
    "清除許可": { # 對應 廢棄物清除許可證
        "展延": {
            "說明": "📅 應於期滿前 6-8 個月提出申請。",
            "應備附件": ["車輛照片", "駕駛員證照", "處置同意書"]
        },
        "變更": {
            "說明": "⚙️ 增加車輛、地址變更或更換負責人時辦理。",
            "應備附件": ["變更申請表", "車輛證明文件", "保險單影本"]
        },
        "變更暨展延": {
            "說明": "🛠️ 於到期前進行變更時，可一併提交展延申請，省去重複作業。",
            "應備附件": ["變更暨展延申請書", "全套更新版附件", "歷年清除量統計表"]
        }
    }
}

# 3. 讀取資料
sheet_url = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(sheet_url, sheet_name='大豐既有許可證到期提醒')
    df['到期日期'] = pd.to_datetime(df['到期日期'], errors='coerce')
    if '許可證類型' not in df.columns:
        df['許可證類型'] = "未分類"
    return df

try:
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
        selected_type = st.selectbox("1️⃣ 許可證類型", type_list)
        st.divider()
        sub_df = df[df['許可證類型'] == selected_type]
        if not sub_df.empty:
            selected_permit = st.radio("2️⃣ 大豐許可證名稱", sub_df['許可證名稱'].tolist())
        else:
            selected_permit = None

    # 6. 右側主畫面
    if selected_permit:
        info = df[df['許可證名稱'] == selected_permit].iloc[0]
        st.title(f"📄 {selected_permit}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("到期日", info['到期日期'].strftime('%Y-%m-%d') if pd.notnull(info['到期日期']) else "未填寫")
        days_left = (info['到期日期']-today).days if pd.notnull(info['到期日期']) else None
        c2.metric("剩餘天數", f"{days_left} 天" if days_left is not None else "N/A")
        c3.metric("管理類型", info['許可證類型'])

        st.markdown("---")
        
        # 7. 辦理項目指引 - 精準匹配邏輯
        st.subheader("🛠️ 申請辦理指引與附件檢查")
        law_content = str(info['許可證名稱']) + str(info['關聯法規'])
        
        matched_key = None
        # 優先判定清除許可
        if "清除" in law_content and "許可" in law_content:
            matched_key = "清除許可"
        elif "清理" in law_content and "計畫" in law_content:
            matched_key = "清理計畫"
        
        if matched_key:
            actions = DETAIL_DATABASE[matched_key]
            cols = st.columns(len(actions))
            for i, action_name in enumerate(actions.keys()):
                # 使用 unique key 避免衝突
                if cols[i].button(action_name, key=f"btn_{selected_permit}_{action_name}", use_container_width=True, type="primary"):
                    st.session_state.current_data = actions[action_name]
                    st.session_state.current_action_name = action_name

            if "current_data" in st.session_state and matched_key in law_content:
                st.write(f"### 📍 項目：{st.session_state.current_action_name}")
                st.success(st.session_state.current_data['說明'])
                st.write("📋 **應備附件檢查表：**")
                for item in st.session_state.current_data['應備附件']:
                    st.checkbox(item, key=f"chk_{selected_permit}_{st.session_state.current_action_name}_{item}")
        else:
            st.info("💡 此類別目前僅供監控。若有辦理需求請洽環安組。")
    
    st.divider()
    with st.expander("📊 查看原始數據總表"):
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ 程式發生錯誤: {e}")
