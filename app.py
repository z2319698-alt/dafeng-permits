import streamlit as st
import pandas as pd
from datetime import date
import smtplib
import time
from email.mime.text import MIMEText
from email.header import Header
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. 系統設定
# ==========================================
st.set_page_config(page_title="大豐環保許可證管理系統", layout="wide")

# ==========================================
# 2. 數據層 - 自動容錯欄位定位
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_get_col(df, target_name, default_index):
    """
    AI 自動定位邏輯：
    1. 嘗試完全匹配標題名稱
    2. 嘗試模糊匹配（去除空格後）
    3. 若都失敗，則使用預設的列索引 (Index)
    """
    # 移除標題空格
    cols = [str(c).strip() for c in df.columns]
    if target_name in cols:
        return target_name
    
    # 嘗試索引退回
    if len(df.columns) > default_index:
        return df.columns[default_index]
    
    return None

@st.cache_data(ttl=600) # 先設 10 分鐘，測試穩了再拉長
def load_data():
    try:
        m_df = conn.read(worksheet="大豐既有許可證到期提醒")
        f_df = conn.read(worksheet="附件資料庫")
        l_df = conn.read(worksheet="申請紀錄")
        
        # 清除所有 DataFrame 的欄位前後空格
        m_df.columns = [str(c).strip() for c in m_df.columns]
        f_df.columns = [str(c).strip() for c in f_df.columns]
        l_df = l_df.dropna(how='all')
        
        return m_df, f_df, l_df
    except Exception as e:
        st.error(f"連線失敗：{e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# ==========================================
# 3. 核心邏輯
# ==========================================
def get_real_status(row_date, today):
    if pd.isna(row_date): return "未設定"
    if row_date < today: return "❌ 已過期"
    elif row_date <= today + pd.Timedelta(days=180): return "⚠️ 準備辦理"
    else: return "✅ 有效"

def get_dynamic_status(permit_name, logs_df, today):
    # 自動尋找申請紀錄中的「許可證名稱」、「狀態」、「核准日期」
    c_name = safe_get_col(logs_df, "許可證名稱", 0)
    c_status = safe_get_col(logs_df, "狀態", 3)
    c_approve = safe_get_col(logs_df, "核准日期", 4)

    if logs_df.empty or not c_name: return "未提送"
    
    my_logs = logs_df[logs_df[c_name] == permit_name]
    if my_logs.empty: return "未提送"
    
    last_log = my_logs.iloc[-1]
    status = str(last_log.get(c_status, "未提送")).strip()
    
    if status == "已核准":
        try:
            app_d = pd.to_datetime(last_log.get(c_approve))
            if (today - app_d).days > 5: return "未提送"
        except: pass
    return status

# ==========================================
# 4. 主程式 UI
# ==========================================
def main():
    main_df, file_df, logs_df = load_data()
    today = pd.Timestamp(date.today())

    if main_df.empty:
        st.error("❌ 無法載入 Google Sheets 資料，請確認網路與權限。")
        return

    # 定義主表欄位
    col_type = safe_get_col(main_df, "類型", 0)
    col_id = safe_get_col(main_df, "管制編號", 1)
    col_name = safe_get_col(main_df, "許可證名稱", 2)
    col_expiry = safe_get_col(main_df, "到期日期", 3)

    # 計算狀態
    main_df['判斷日期'] = pd.to_datetime(main_df[col_expiry], errors='coerce')
    main_df['最新狀態'] = main_df['判斷日期'].apply(lambda x: get_real_status(x, today))

    # --- 📢 跑馬燈 ---
    upcoming = main_df[main_df['最新狀態'].isin(["❌ 已過期", "⚠️ 準備辦理"])]
    if not upcoming.empty:
        marquee_items = [f"{row['最新狀態']}：{row[col_name]} ({str(row[col_expiry])[:10]})" for _, row in upcoming.iterrows()]
        marquee_text = " | ".join(marquee_items)
        st.markdown(f'<div style="background-color: #FFF3E0; padding: 10px; border-radius: 5px; border-left: 5px solid #FF9800; overflow: hidden; white-space: nowrap;"><marquee scrollamount="5" style="color: #E65100; font-weight: bold;">{marquee_text}</marquee></div>', unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🌱 大豐環保許可證管理系統</h1>", unsafe_allow_html=True)
    st.write("---")

    # --- 📂 側邊選單 ---
    if st.sidebar.button("🔄 刷新雲端資料", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.sidebar.button("🏠 回到系統首頁", use_container_width=True):
        st.session_state.selected_actions = set()
        st.rerun()
    
    st.sidebar.divider()
    
    types = sorted(main_df[col_type].dropna().unique())
    sel_type = st.sidebar.selectbox("1. 選擇類型", types)
    
    sub_main = main_df[main_df[col_type] == sel_type].copy()
    permits = sub_main[col_name].dropna().unique()
    sel_name = st.sidebar.radio("2. 選擇許可證", permits)

    # 獲取目標資訊
    target_main = sub_main[sub_main[col_name] == sel_name].iloc[0]
    dynamic_s = get_dynamic_status(sel_name, logs_df, today)

    # 顯示狀態資訊卡
    st.title(f"📄 {sel_name}")
    status_msg = f"🆔 管制編號：{target_main[col_id]}　|　📅 到期日期：{str(target_main[col_expiry])[:10]}　|　📢 流程進度：【{dynamic_s}】"
    if "已過期" in target_main['最新狀態']: st.error(status_msg)
    elif "準備辦理" in target_main['最新狀態']: st.warning(status_msg)
    else: st.info(status_msg)

    # --- 🛠️ 申請流程 ---
    st.divider()
    db_info = file_df[file_df[safe_get_col(file_df, "類型", 0)] == sel_type]
    options = db_info.iloc[:, 1].dropna().unique().tolist()

    if options:
        st.subheader("🛠️ 第一步：選擇辦理項目 (可多選)")
        if "selected_actions" not in st.session_state: st.session_state.selected_actions = set()
        
        cols = st.columns(len(options))
        for i, option in enumerate(options):
            is_active = option in st.session_state.selected_actions
            if cols[i].button(option, key=f"btn_{option}", use_container_width=True, type="primary" if is_active else "secondary"):
                if is_active: st.session_state.selected_actions.remove(option)
                else: st.session_state.selected_actions.add(option)
                st.rerun()

        if st.session_state.selected_actions:
            st.divider()
            st.markdown("### 📝 第二步：填寫申請資訊")
            c1, c2 = st.columns(2)
            with c1: user_name = st.text_input("👤 申請人姓名", placeholder="請輸入姓名")
            with c2: apply_date = st.date_input("📅 提出申請日期", value=date.today())

            # 附件處理
            final_attachments = set()
            for action in st.session_state.selected_actions:
                action_row = db_info[db_info.iloc[:, 1] == action]
                if not action_row.empty:
                    atts = action_row.iloc[0, 3:].dropna().tolist()
                    for item in atts: final_attachments.add(str(item).strip())

            st.write("**📋 必備附件清單：**")
            for item in sorted(list(final_attachments)):
                with st.expander(f"📁 {item}", expanded=True):
                    st.file_uploader(f"請上傳檔案 - {item}", key=f"up_{item}")

            if st.button("🚀 確認提交申請", type="primary", use_container_width=True):
                if not user_name:
                    st.warning("⚠️ 請填寫姓名！")
                else:
                    submit_request(sel_name, user_name, apply_date, list(st.session_state.selected_actions), logs_df)

    st.write("---")
    with st.expander("📊 查看所有許可證狀態清單"):
        st.dataframe(main_df[[col_type, col_id, col_name, col_expiry, '最新狀態']], use_container_width=True, hide_index=True)

def submit_request(permit_name, user_name, apply_date, actions, current_logs):
    try:
        with st.spinner("正在同步至 Google Sheets..."):
            # 獲取欄位名稱避免寫錯位
            c_name = safe_get_col(current_logs, "許可證名稱", 0)
            c_user = safe_get_col(current_logs, "申請人", 1)
            c_date = safe_get_col(current_logs, "申請日期", 2)
            c_stat = safe_get_col(current_logs, "狀態", 3)

            new_row = pd.DataFrame([{
                c_name: permit_name,
                c_user: user_name,
                c_date: apply_date.strftime("%Y-%m-%d"),
                c_stat: "已提送需求"
            }])
            updated_logs = pd.concat([current_logs, new_row], ignore_index=True)
            conn.update(worksheet="申請紀錄", data=updated_logs)
            
            # 發送郵件 (帶入 secrets)
            send_email(permit_name, user_name, apply_date, actions)
            
            st.balloons()
            st.success("✅ 申請成功！")
            st.session_state.selected_actions = set()
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
    except Exception as e:
        st.error(f"寫入失敗：{e}")

def send_email(permit_name, user_name, apply_date, actions):
    try:
        msg = MIMEText(f"申請人：{user_name}\n許可證：{permit_name}\n項目：{', '.join(actions)}", 'plain', 'utf-8')
        msg['Subject'] = Header(f"【新申請】{permit_name}", 'utf-8')
        msg['From'] = st.secrets["email"]["sender"]
        msg['To'] = st.secrets["email"]["receiver"]
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(st.secrets["email"]["sender"], st.secrets["email"]["password"])
            server.sendmail(st.secrets["email"]["sender"], [st.secrets["email"]["receiver"]], msg.as_string())
    except: pass # 郵件失敗不影響系統

if __name__ == "__main__":
    main()
