import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁配置
st.set_page_config(page_title="大豐許可證管理系統", layout="wide")

# 2. 精準法規動作資料庫
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
