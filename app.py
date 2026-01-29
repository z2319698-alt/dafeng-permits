import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁配置
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 精準法規動作資料庫
DB = {
    "清理計畫": {
        "展延": {
            "msg": "📅 應於期滿前 2-3 個月提出申請。",
            "files": ["清理計畫書(更新版)", "廢棄物合約影本", "負責人身分證影本"]
        },
        "變更": {
            "msg": "⚙️ 產出量、種類或製程變更時提出。",
            "files": ["變更申請表", "差異對照表", "製程說明圖"]
        },
        "異動": {
            "msg": "🔄 基本資料變更，不涉及實質內容。",
            "files": ["異動申請書", "相關證明文件"]
        }
    },
    "清除許可": {
        "展延": {
            "msg": "📅 應於期滿前 6-8 個月提出申請。",
            "files": ["原許可證正本", "車輛照片", "駕駛員證照", "處置同意文件"]
        },
        "變更": {
            "msg": "⚙️ 增加車輛、地址或負責人變更。",
            "files": ["變更申請書", "車輛證明", "有效保險單"]
        },
        "變更暨展延": {
            "msg": "🛠️ 同時辦理變更與展延，節省行政程序。",
            "files": ["合併申請書", "全套更新附件", "清除量統計表"]
        }
    }
}

# 3. 讀取資料
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL, sheet_name='大豐既有許可證到期提醒')
    df['到期日期'] = pd.to_datetime(df['到期日期'], errors='coerce')
    df['許可證類型'] = df['許可證類型'].fillna("未分類")
    return df

try:
    df = load_data()
    today = datetime.now()

    # 4. 跑馬燈 (使用多行字串確保不截斷)
    urgent = df[(df['到期日期'] <= today + pd.Timedelta(days=180)) & (df['到期日期'].notnull())]
    if not urgent.empty:
        items = []
        for _, r in urgent.iterrows():
            diff = (r['到期日期'] - today).days
            items.append(f"🚨 {r['許可證名稱']} (剩 {diff} 天)")
        
        marquee_content = "　　".join(items)
        st.markdown(
            f"""
            <div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;">
                <marquee scrollamount="6">{marquee_content}</marquee>
            </div>
            """, 
            unsafe_allow_html=True
        )

    # 5. 左側導航
    with st.sidebar:
        st.header("📂 系統導航")
        t_list = sorted(df['許可證類型'].unique().tolist())
        sel_t = st.selectbox("1️⃣ 許可證類型", t_list)
        st.divider()
        sub = df[df['許可證類型'] == sel_t]
        sel_p = st.radio("2️⃣ 許可證名稱", sub['許可證名稱'].tolist()) if not sub.empty else None

    # 6. 主畫面
    if sel_p:
        info =
