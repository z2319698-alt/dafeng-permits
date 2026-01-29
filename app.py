import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁配置
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 精準法規動作資料庫
DETAIL_DATABASE = {
    "清理計畫": {
        "展延": {
            "說明": "📅 應於期滿前 2-3 個月提出申請。",
            "附件": ["清理計畫書(更新版)", "廢棄物合約影本", "負責人身分證影本"]
        },
        "變更": {
            "說明": "⚙️ 產出量、種類或製程變更時提出。",
            "附件": ["變更申請表", "差異對照表", "製程說明圖"]
        },
        "異動": {
            "說明": "🔄 基本資料變更，不涉及實質內容。",
            "附件": ["異動申請書", "相關證明文件"]
        }
    },
    "清除許可": {
        "展延": {
            "說明": "📅 應於期滿前 6-8 個月提出申請。",
            "附件": ["原許可證正本", "車輛照片", "駕駛員證照", "處置同意文件"]
        },
        "變更": {
            "說明": "⚙️ 增加車輛、地址或負責人變更。",
            "附件": ["變更申請書", "車輛證明", "有效保險單"]
        },
        "變更暨展延": {
            "說明": "🛠️ 同時辦理變更與展延，節省行政程序。",
            "附件": ["合併申請書", "全套更新附件", "清除量統計表"]
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

try:
    df = load_data()
    today = datetime.now()

    # 4. 跑馬燈
    urgent = df[(df['到期日期'] <= today + pd.Timedelta(days=180)) & (df['到期日期'].notnull())]
    if not urgent.empty:
        alert_text = "　　".join([f"🚨 {r['許可證名稱']} (剩 {(r['到期日期']-today).days} 天)" for _, r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5
