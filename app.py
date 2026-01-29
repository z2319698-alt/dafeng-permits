import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. 網頁配置
st.set_page_config(page_title="WorkGuard 許可證監控", layout="wide")

# 2. 讀取資料
sheet_url = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(sheet_url, sheet_name='大豐既有許可證到期提醒')
    df['到期日期'] = pd.to_datetime(df['到期日期'], errors='coerce')
    return df

df = load_data()
today = datetime.now()

# 3. 狀態計算邏輯
df_valid = df.copy()
def get_status(date):
    if pd.isnull(date): return '⚪ 未填寫'
    if date < today: return '🚨 已逾期'
    elif date <= today + pd.Timedelta(days=180): return '🟡 展延預警'
    else: return '✅ 正常'

df_valid['狀態'] = df_valid['到期日期'].apply(get_status)

# 4. 頂部 KPI
st.title("🛡️ WorkGuard 許可證智能監測中心")
st.markdown("---")

c1, c2, c3, c4 = st.columns(4)
c1.metric("監控總數", len(df))
c2.metric("嚴重警告 (已逾期)", len(df_valid[df_valid['狀態'] == '🚨 已逾期']))
c3.metric("展延預警", len(df_valid[df_valid['狀態'] == '🟡 展延預警']))
c4.metric("系統狀態", "線上運行中")

# 5. 重點：互動篩選功能
st.write("##")
left_col, right_col = st.columns([1, 2.5])

with left_col:
    st.write("#### ⚖️ 狀態統計")
    # 畫圖
    fig = px.pie(df_valid, names='狀態', hole=0.6, color='狀態',
                 color_discrete_map={'✅ 正常': '#00cc96', '🟡 展延預警': '#f39c12', '🚨 已逾期': '#ef553b', '⚪ 未填寫': '#808080'})
    st.plotly_chart(fig, use_container_width=True)
    
    # 這裡就是你要的「點選」功能：下拉選單篩選
    status_filter = st.multiselect(
        "🔍 篩選特定狀態的證照：",
        options=['🚨 已逾期', '🟡 展延預警', '✅ 正常', '⚪ 未填寫'],
        default=['🚨 已逾期', '🟡 展延預警'] # 預設直接幫你挑出有問題的
    )

with right_col:
    st.write("#### 📋 許可證詳細清單")
    
    # 根據篩選器過濾資料
    df_filtered = df_valid[df_valid['狀態'].isin(status_filter)]
    
    # 格式化顯示
    df_display = df_filtered.copy()
    df_display['到期日期'] = df_display['到期日期'].dt.strftime('%Y-%m-%d').fillna("未填寫")
    
    # 使用表格顯示，並加上顏色標註
    st.dataframe(
        df_display.style.map(
            lambda x: 'color: #ef553b; font-weight: bold;' if x == '🚨 已逾期' else '', subset=['狀態']
        ).map(
            lambda x: 'color: #f39c12;' if x == '🟡 展延預警' else '', subset=['狀態']
        ),
        use_container_width=True,
        height=500
    )

st.success("✅ 數據已即時同步。您可以透過左側選單切換要查看的證照類別。")
