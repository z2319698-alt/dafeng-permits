import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. 強制設定深色主題與網頁配置
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

# 3. 數據清理與狀態判斷
df_valid = df.dropna(subset=['到期日期']).copy()

def get_status(date):
    if date < today:
        return '🚨 已逾期'
    elif date <= today + pd.Timedelta(days=180):
        return '🟡 展延預警'
    else:
        return '✅ 正常'

df_valid['狀態'] = df_valid['到期日期'].apply(get_status)

# 4. 頂部標題
st.title("🛡️ WorkGuard 許可證智能監測中心")
st.markdown("---")

# 5. KPI 卡片
c1, c2, c3, c4 = st.columns(4)
c1.metric("監控總數", len(df))
c2.metric("嚴重警告", len(df_valid[df_valid['狀態'] == '🚨 已逾期']))
c3.metric("近期需辦理", len(df_valid[df_valid['狀態'] == '🟡 展延預警']))
c4.metric("系統狀態", "線上運行中")

# 6. 中間區塊：圖表與清單
st.write("##")
left_col, right_col = st.columns([1, 2])

with left_col:
    st.write("#### ⚖️ 證照狀態分佈")
    # 修正後的繪圖代碼
    fig = px.pie(
        df_valid, 
        names='狀態', 
        hole=0.6,
        color='狀態',
        color_discrete_map={'✅ 正常': '#00cc96', '🟡 展延預警': '#f39c12', '🚨 已逾期': '#ef553b'}
    )
    fig.update_layout(
        showlegend=True, 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font_color="white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig, use_container_width=True)

with right_col:
    st.write("#### 📋 許可證詳細清單")
    df_show = df.copy()
    df_show['到期日期'] = df_show['到期日期'].dt.strftime('%Y-%m-%d').fillna("未填寫")
    st.dataframe(df_show, use_container_width=True, height=400)

st.success("✅ 數據已與 Google Sheets 同步更新")