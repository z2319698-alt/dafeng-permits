import streamlit as st
from streamlit_drawable_canvas import st_canvas
from streamlit_gsheets import GSheetsConnection
from PIL import Image
from fpdf import FPDF
import pandas as pd
from datetime import datetime
import io

# 1. 頁面基礎設定
st.set_page_config(page_title="大豐環保-危害告知書", layout="centered")

# 2. 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取人員主檔 (假設你的試算表有一頁分頁叫 "人員主檔")
# 如果分頁名稱不同，請修改下面的 worksheet 名稱
try:
    user_df = conn.read(worksheet="人員主檔")
except:
    st.error("找不到 '人員主檔' 分頁，請確認 Google Sheets 內容。")
    user_df = pd.DataFrame(columns=["FaceID", "姓名", "公司名稱", "施工單位"])

# 3. 抓取網址參數 (FaceID)
fid = st.query_params.get("fid", None)

# 自動填寫邏輯：比對 FaceID
user_info = {"姓名": "", "公司名稱": "", "施工單位": "粉碎課"}
if fid and not user_df.empty:
    target = user_df[user_df["FaceID"].astype(str) == str(fid)]
    if not target.empty:
        user_info["姓名"] = target.iloc[0]["姓名"]
        user_info["公司名稱"] = target.iloc[0]["公司名稱"]
        user_info["施工單位"] = target.iloc[0]["施工單位"]

# --- 介面開始 ---
st.title("大豐環保科技股份有限公司")
st.subheader("危害告知書 (版本：114.01)")

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("人員姓名", value=user_info["姓名"])
        company = st.text_input("公司名稱", value=user_info["公司名稱"])
    with col2:
        # 下拉選單自動對應
        unit_list = ["粉碎課", "造粒課", "玻璃屋", "地磅室", "廠內周邊工程"]
        default_idx = unit_list.index(user_info["施工單位"]) if user_info["施工單位"] in unit_list else 0
        dept = st.selectbox("施工單位", unit_list, index=default_idx)
        today_str = datetime.now().strftime("%Y-%m-%d")
        st.write(f"簽署日期：{today_str}")

# 15 條工安規範 (簡約顯示)
with st.expander("📝 點擊閱讀：15 條安全衛生規定", expanded=True):
    st.markdown("""
    1. 預防尖銳物切割危害，應佩戴安全手套。
    2. 維修需經主管同意並掛牌。
    3. 場內限速 15 公里。
    4. 工作場所禁止吸菸飲酒。
    *(請在此自行補齊 15 條完整內容)*
    """)
    st.warning("⚠️ 以上事項願承諾確實遵行，若有疏失願自行負責。")

# 4. 手寫簽名板
st.write("人員簽章：")
canvas_result = st_canvas(
    fill_color="rgba(255, 255, 255, 1)",
    stroke_width=3,
    stroke_color="#000000",
    background_color="#ffffff",
    height=150,
    key="canvas",
)

# 5. 送出按鈕與後續動作
if st.button("確認簽署並送出", type="primary", use_container_width=True):
    if canvas_result.image_data is not None and name != "":
        # A. 顯示成功訊息
        st.success(f"✅ {name} 簽署成功！")
        
        # B. 生成 PDF (暫存在記憶體)
        pdf = FPDF()
        pdf.add_page()
        # 解決中文亂碼問題需載入字體，這裡先用英文示意邏輯
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Dafeng Hazard Notification Form", ln=1, align='C')
        pdf.cell(200, 10, txt=f"Name: {name} / Company: {company}", ln=2)
        
        # C. 這裡可以串接將資料寫回 Google Sheets 的「簽署紀錄」
        # new_record = pd.DataFrame([{"姓名": name, "日期": today_str, "單位": dept}])
        # conn.create(worksheet="簽署紀錄", data=new_record)
        
        st.balloons()
    else:
        st.error("請確認姓名已填寫且已完成手寫簽名！")
