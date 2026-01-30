import streamlit as st
import pandas as pd
from datetime import datetime as dt
import urllib.parse

st.set_page_config(page_title="大豐管理系統", layout="wide")

# 1. 精確法規資料庫 (修正先前截圖中的錯誤)
LAW_REQUIREMENTS = {
    "廢棄物清理計畫書": {
        "變更": ["涉及主體、類別、產能擴增達 10% 以上 (廢清法第 31 條)", "廢棄物項目增加或數量異動逾 10%"],
        "異動": ["基本資料更動 (負責人、聯絡人等)", "不涉及製程改變之行政異動"],
        "展延": ["依規於期滿前提出展延申請"]
    },
    "廢棄物清除許可證": {
        "變更": ["清除車輛增加、減少或規格異動", "清除廢棄物種類增加"],
        "變更暨展延": ["同時涉及證照到期與車輛/種類變更"],
        "展延": ["許可證效期屆滿前 6-8 個月申請"]
    },
    "水污染防治措施": {
        "事前變更": ["廢(污)水處理程序改變 (水污法第 14 條)", "每日最大廢水產生量增加 10%"],
        "事後變更": ["不涉及程序改變之微幅異動備查"],
        "展延": ["水污染防治許可效期展延"]
    }
}

# 2. 資料讀取 (包含主表與附件資料庫分頁)
URL = "https://docs.google.com/spreadsheets/d/1BA427GfGw41UWen083KSWxbdRwbe3a1SEF_H89MyBZE/export?format=xlsx"

@st.cache_data(ttl=60)
def load_full_data():
    all_sh = pd.read_excel(URL, sheet_name=None)
    main_df = None
    # 根據 GID 846283148 對應的分頁名稱，這裡假設分頁名為 "附件資料庫"
    # 如果您的分頁名稱不同，請修改下方的字串
    attach_df = all_sh.get("附件資料庫") 
    
    for n, df in all_sh.items():
        df.columns = [str(c).strip() for c in df.columns]
        if "許可證名稱" in df.columns:
            main_df = df
            break
    return main_df, attach_df

try:
    df, attach_db = load_full_data()
    C_NAME, C_DATE, C_TYPE = "許可證名稱", "到期日期", "許可證類型"
    df['D'] = pd.to_datetime(df[C_DATE], errors='coerce')
    now = dt.now()

    # 3. 跑馬燈
    urgent = df[(df['D'] <= now + pd.Timedelta(days=180)) & (df['D'].notnull())]
    if not urgent.empty:
        m_txt = "　　".join([f"🚨 {r[C_NAME]}(剩{(r['D']-now).days}天)" for _,r in urgent.iterrows()])
        st.markdown(f'<div style="background:#ff4b4b;color:white;padding:10px;border-radius:5px;"><marquee scrollamount="6">{m_txt}</marquee></div>', unsafe_allow_html=True)

    # 4. 側邊選單
    st.sidebar.markdown("## 📂 系統導航")
    t_list = sorted(df[C_TYPE].unique().tolist())
    sel_t = st.sidebar.selectbox("1. 選擇類型", t_list)
    sub = df[df[C_TYPE] == sel_t].reset_index(drop=True)
    sel_n = st.sidebar.radio("2. 選擇許可證", sub[C_NAME].tolist())

    # 5. 主畫面
    row = sub[sub[C_NAME] == sel_n].iloc[0]
    st.title(f"📄 {sel_n}")
    
    st.divider()
    raw_type = str(row[C_TYPE])
    
    # 決定按鈕選項
    acts = {}
    if "清除" in raw_type: acts = {"變更":None, "變更暨展延":None, "展延":None}
    elif "清理" in raw_type: acts = {"變更":None, "展延":None, "異動":None}
    elif "水污染" in raw_type: acts = {"事前變更":None, "事後變更":None, "展延":None}

    st.subheader("🛠️ 第三層：辦理項目選擇")
    btn_cols = st.columns(len(acts))
    for i, a_name in enumerate(acts.keys()):
        if btn_cols[i].button(a_name, key=f"b_{sel_n}_{a_name}", use_container_width=True):
            st.session_state["cur_a"] = a_name
            st.session_state["last_p"] = sel_n

    # 流程執行
    if st.session_state.get("last_p") == sel_n:
        curr_act = st.session_state.get("cur_a")
        st.markdown(f"### 📍 目前選擇項目：{curr_act}")
        
        # --- 第一步：法規確認 ---
        with st.expander("⚖️ 第一步：法規依據條件確認", expanded=True):
            match_key = next((k for k in LAW_REQUIREMENTS if k in raw_type), None)
            conditions = LAW_REQUIREMENTS[match_key].get(curr_act, ["參考縣市規範"]) if match_key else ["參考規範"]
            selected_laws = []
            for cond in conditions:
                if st.checkbox(cond, key=f"law_{sel_n}_{curr_act}_{cond}"):
                    selected_laws.append(cond)
        
        # --- 第二步：人員登錄 ---
        with st.expander("👤 第二步：人員登錄", expanded=True):
            c1, c2 = st.columns(2)
            u_name = c1.text_input("辦理人姓名", key=f"name_{sel_n}")
            u_date = c2.date_input("辦理日期", value=now, key=f"date_{sel_n}")
            
            if u_name:
                # --- 第三步：附件清單 (連動 Excel 分頁) ---
                st.markdown("---")
                st.subheader(f"📂 第三步：應檢附附件清單")
                
                final_items = []
                # 優先從 Excel 分頁讀取
                if attach_db is not None:
                    try:
                        mask = (attach_db["許可證類型"] == sel_t) & (attach_db["辦理項目"] == curr_act)
                        final_items = attach_db[mask]["附件名稱"].tolist()
                    except:
                        pass
                
                # 若分頁沒提到，則使用保底清單
                if not final_items:
                    final_items = ["申請書正本", "差異對照表", "各縣市要求證明文件"]
                
                checked_items = []
                for item in final_items:
                    col_a, col_b = st.columns([0.4, 0.6])
                    if col_a.checkbox(item, key=f"ck_{sel_n}_{item}"):
                        checked_items.append(item)
                    col_b.file_uploader("上傳", key=f"up_{sel_n}_{item}", label_visibility="collapsed")
                
                # --- 第四步：提出申請按鈕 ---
                st.divider()
                if st.button("🚀 提出申請並發信", use_container_width=True):
                    # 彙整內容
                    mail_body = f"大豐許可管理系統 - 自動申請單\n"
                    mail_body += f"--------------------------\n"
                    mail_body += f"申請單位：{sel_n}\n"
                    mail_body += f"辦理項目：{curr_act}\n"
                    mail_body += f"辦理人員：{u_name}\n"
                    mail_body += f"辦理日期：{u_date}\n"
                    mail_body += f"符合法規：{', '.join(selected_laws)}\n"
                    mail_body += f"已勾選附件：{', '.join(checked_items)}\n"
                    
                    subject = urllib.parse.quote(f"許可辦理申請：{sel_n}-{curr_act}")
                    body = urllib.parse.quote(mail_body)
                    
                    # 生成 Mailto 連結
                    mailto_link = f"mailto:andy.chen@df-recycle.com?subject={subject}&body={body}"
                    st.success("申請資料已彙整！請點擊下方連結啟動郵件系統寄送：")
                    st.markdown(f'<a href="{mailto_link}" style="background-color:#4CAF50; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">📧 按此寄送電子郵件</a>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ 請輸入姓名以解鎖後續功能。")

except Exception as e:
    st.error(f"系統錯誤: {e}")

# 8. 全數據呈現 (最下方)
st.divider()
with st.expander("📊 原始數據總表"):
    st.dataframe(df, use_container_width=True)
