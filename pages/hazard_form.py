import streamlit as st
from streamlit_drawable_canvas import st_canvas
from datetime import datetime

# 頁面配置
st.set_page_config(page_title="大豐環保-危害告知書", layout="centered")

# --- 1. 模擬資料庫與自動帶入 ---
# 未來你可以把這部分改為讀取 Google Sheets
def get_user_info(face_id):
    db = {
        "001": {"name": "王小明", "company": "大豐環保", "dept": "粉碎課"},
        "002": {"name": "張大龍", "company": "承攬廠商A", "dept": "造粒課"}
    }
    return db.get(face_id, {"name": "", "company": "", "dept": "粉碎課"})

# 取得網址參數 fid
fid = st.query_params.get("fid", None)
user = get_user_info(fid)

# --- 2. 介面標題 ---
st.title("大豐環保科技股份有限公司")
st.subheader("危害告知書 (版本：114.01)")

# --- 3. 填寫欄位 (自動帶入) ---
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("入場人員姓名", value=user["name"])
        company = st.text_input("公司名稱", value=user["company"])
    with col2:
        dept = st.selectbox("施工單位", 
                            ["粉碎課", "造粒課", "玻璃屋", "地磅室", "廠內周邊工程"],
                            index=["粉碎課", "造粒課", "玻璃屋", "地磅室", "廠內周邊工程"].index(user["dept"]))
        today = st.date_input("日期", value=datetime.now())

# --- 4. 安全衛生規定 ---
st.markdown("""
### 安全衛生規定
一、為防止尖銳物(玻璃、鐵釘、廢棄針頭)切割危害，應佩戴安全手套、安全鞋及防護具。  
二、設備維修需經主管同意並掛「維修中/保養中」牌。  
三、場內限速 15 公里/小時，嚴禁超速。  
... (中間省略，請自行補齊 15 條) ...  
**以上事項願承諾確實遵行，若有疏失願自行負責。**
""")

# --- 5. 簽名區域 ---
st.write("人員手寫簽署：")
canvas_result = st_canvas(
    fill_color="rgba(255, 255, 255, 1)",
    stroke_width=3,
    stroke_color="#000000",
    background_color="#ffffff",
    height=150,
    key="canvas",
)

# --- 6. 送出按鈕 ---
if st.button("確認簽署並送出", type="primary", use_container_width=True):
    if canvas_result.image_data is not None and name:
        st.success(f"✅ 簽署成功！資料已紀錄（人員：{name}）")
        # 這裡未來會接 PDF 生成與上傳 Google Drive 的代碼
    else:
        st.error("❌ 請輸入姓名並完成簽名！")
