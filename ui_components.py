import streamlit as st

def display_penalty_cases():
    """專門處理裁處案例顯示。改顏色、改文字都在這裡改。"""
    st.markdown("## ⚖️ 近一年重大環保事件 (深度解析)")
    cases = [
        {"t": "2025/09 屏東非法棄置案", "c": "清運包商非法直排強酸液，產源工廠重罰 600 萬。"},
        {"t": "2026/02 GPS 軌跡稽查案", "c": "環境部透過 GPS 鎖定產源單位，沒收獲利 2.4 億。"},
        {"t": "2025/11 數據造假案", "c": "特定場區更動 CWMS 監測參數，沒入相關許可證。"}
    ]
    for case in cases:
        st.markdown(f"""<div style="background-color: #2D0D0D; border-left: 5px solid #e53935; padding: 15px; border-radius: 8px; margin-bottom: 15px;"><b style="color: #ff4d4d;">🚨 {case['t']}</b><p style="color: white; margin-top: 5px;">{case['c']}</p></div>""", unsafe_allow_html=True)
