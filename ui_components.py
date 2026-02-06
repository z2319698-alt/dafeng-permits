import streamlit as st

def display_penalty_cases():
    st.markdown("## ⚖️ 近一年重大環保事件 (深度解析)")
    cases = [
        {"t": "2025/09 屏東非法棄置案", "c": "產源工廠未落實監督被重罰 600 萬並承擔 1,500 萬復育費。"},
        {"t": "2026/02 GPS 軌跡稽查", "c": "環境部透過 GPS 鎖定多家產源單位，沒收獲利 2.4 億元。"},
        {"t": "2025/11 監測數據造假", "c": "特定場區更動 CWMS 參數。認定造假，沒入許可證。"}
    ]
    for case in cases:
        st.markdown(f"""
            <div style="background-color: #2D0D0D; border-left: 5px solid #e53935; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <b style="color: #ff4d4d;">🚨 {case['t']}</b>
                <p style="color: white; margin-top: 5px;">{case['c']}</p>
            </div>
        """, unsafe_allow_html=True)
