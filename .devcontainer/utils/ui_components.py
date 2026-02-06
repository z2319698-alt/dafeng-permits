import streamlit as st

def display_penalty_cases():
    st.markdown("## ⚖️ 近一年重大環保事件 (深度解析)")
    
    cases = [
        {"t": "2025/09 屏東非法棄置案", "c": "清運包商非法直排強酸液，產源工廠重罰 600 萬。"},
        {"t": "2026/02 GPS 軌跡稽查案", "c": "跨縣市非法回填，沒收獲利 2.4 億元。"},
        {"t": "2025/11 數據造假案", "c": "監測參數人工造假，沒入相關許可證。"}
    ]
    
    for case in cases:
        st.warning(f"🚨 {case['t']}\n\n{case['c']}")

    st.markdown("---")
    st.markdown("### 🌐 社會重大事件與監控熱點")
    
    news = [
        {"topic": "科技監控", "desc": "AI 影像與軌跡比對，偏離路線即觸發稽查。"},
        {"topic": "社群爆料", "desc": "Dcard/FB 爆料模式增加，引發查訪頻率。"},
        {"topic": "代碼誤植", "desc": "營建與一般廢棄物代碼混用為近期查核重點。"}
    ]
    
    for m in news:
        with st.expander(m['topic']):
            st.write(m['desc'])
