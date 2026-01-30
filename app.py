import streamlit as st
import pandas as pd
from datetime import datetime as dt

# 1. 配置網頁
st.set_page_config(page_title="大豐許可管理系統", layout="wide")

# 2. 定義核心資料庫
# 確保「清除許可」對應的是你指定的：展延 / 變更 / 變更暨展延
DB = {
    "P": {
        "展延": ["清理計畫書(更新版)", "廢棄物合約影本", "負責人身分證影本"],
        "變更": ["變更申請表", "差異對照表", "製程說明圖"],
        "異動": ["異動申請書", "相關證明文件"]
    },
    "C": {
        "展延": ["原許可證正本", "車輛照片 (含排氣檢驗)", "駕駛員證照及勞保卡", "廢棄物處置同意文件"],
        "變更": ["變更申請表", "變更事項證明文件", "新車輛規格證明 (如行照)", "有效保險單影本"],
        "變更暨展延": ["變更暨展延申請表", "全套更新版附件", "歷年清除量統計表", "相關切結書"]
    }
}

# 3. 讀取資料
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    data = pd.read_excel(URL, sheet_name=0)
    # 強制對齊你的 Excel 欄位名稱
    data['D'] = pd.to_datetime(data["許可證期日"], errors='coerce')
    data['T'] = data["變更項目"].fillna("廢棄物類")
    data['N'] = data["清除許可證名稱"]
    return data

df = load_data()
now = dt.now()

# 4. 側邊選單邏輯
st.sidebar.header("📂 系統選單")
type_list = sorted(df['T'].unique().tolist())
sel_type = st.sidebar.selectbox("1. 選擇類型", type_list)

# 篩選子集並重設索引
sub_df = df[df['T'] == sel_type].reset_index(drop=True)

if sub_df.empty:
    st.warning("此分類下目前沒有資料。")
    st.stop()

sel_name = st.sidebar.radio("2. 選擇許可證", sub_df['N'].tolist())

# 5. 主畫面顯示
# 透過名稱精準抓取該列資料
current_row = sub_df[sub_df['N'] == sel_name]

if not current_row.empty:
    row = current_row.iloc[0]
    st.title(f"📄 {sel_name}")
    
    # 顯示基礎資訊
    c1, c2, c3 = st.columns(3)
    d_val = row['D']
    c1.metric("到期日期", d_val.strftime('%Y-%m-%d') if pd.notnull(d_val) else "未填寫")
    days_left = (d_val - now).days if pd.notnull(d_val) else None
    c2.metric("剩餘天數", f"{days_left} 天" if days_left is not None else "N/A")
    c3.metric("目前類型", row['T'])

    st.markdown("---")
    st.subheader("🛠️ 辦理項目指引")

    # 判斷是「清除許可」還是「清理計畫」
    acts = None
    if "清除" in str(sel_name):
        acts = DB["C"]
    elif "清理" in str(sel_name) or "計畫" in str(sel_name):
        acts = DB["P"]

    if acts:
        # 顯示動作按鈕
        btn_cols = st.columns(len(acts))
        for i, act_name in enumerate(acts.keys()):
            # 點擊按鈕後將選取的動作存入 Session State
            if btn_cols[i].button(act_name, key=f"btn_{sel_name}_{act_name}", use_container_width=True):
                st.session_state["active_act"] = act_name
                st.session_state["active_permit"] = sel_name

        # 檢查當前顯示的附件是否屬於「目前選中的許可證」
        if st.session_state.get("active_permit") == sel_name:
            current_act = st.session_state.get("active_act")
            
            if current_act and current_act in acts:
                st.success(f"📍 正在辦理：{current_act}")
                st.write("📋 **應備附件檢查清單：**")
                
                # 顯示附件勾選清單
                for item in acts[current_act]:
                    st.checkbox(item, key=f"chk_{sel_name}_{current_act}_{item}")
            else:
                st.info("👆 請點擊上方按鈕，查看不同辦理項目的指引與清單。")
        else:
            # 如果換了許可證，提示使用者重新點選
            st.info("👆 請選擇上方辦理項目。")
    else:
        st.info("💡 此項目目前僅供到期監控，暫無預設辦理指引。")

# 6. 底部資料備查
st.divider()
with st.expander("📊 查看 Excel 原始數據清單"):
    st.dataframe(df[["清除許可證名稱", "許可證期日", "變更項目"]], use_container_width=True)
