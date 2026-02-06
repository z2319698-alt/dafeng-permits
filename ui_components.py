import streamlit as st

def display_penalty_cases():
    """
    專門負責顯示裁處案例與社會熱點。
    將複雜的 HTML/CSS 抽離主程式，保持 app.py 乾淨。
    """
    st.markdown("## ⚖️ 近一年重大環保事件 (深度解析)")
    
    # 定義案例資料
    cases = [
        {"t": "2025/09 屏東非法棄置與有害廢液直排案", "c": "清運包商非法直排強酸液，產源工廠因未落實監督被重罰 600 萬並承擔 1,500 萬生態復育費。"},
        {"t": "2026/02 農地盜採回填與 GPS 軌跡回溯稽查", "c": "跨縣市犯罪集團回填 14 萬噸廢棄物。環境部透過 GPS 鎖定多家產源單位，沒收獲利 2.4 億元。"},
        {"t": "2025/11 高雄工業區廢水監測數據造假案", "c": "特定場區更動 CWMS 監測參數。環境部認定人工造假，沒入相關許可證。"}
    ]
    
    # 渲染案例
    for i, case in enumerate(cases):
        st.markdown(f"""
            <div style="background-color: #2D0D0D; border-left: 5px solid #e53935; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <b style="color: #ff4d4d;">🚨 {case['t']}</b>
                <p style="color: white; margin-top: 5px;">{case['c']}</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("### 🌐 社會重大事件與監控熱點")
    
    news = [
        {"topic": "南投焚化爐修繕抗爭", "desc": "設施修繕導致量縮，居民異味抗爭造成清運受阻。", "advice": "落實巡檢與除臭紀錄。"},
        {"topic": "環境部科技監控", "desc": "AI 影像與軌跡比對，偏離路線 1 公里即自動觸發稽查。", "advice": "要求廠商按申報路線行駛。"},
        {"topic": "社群爆料檢舉趨勢", "desc": "Dcard/FB 即時爆料模式增加，引發媒體跟進與頻繁查訪。", "advice": "強化邊界防治並保留作業紀錄。"},
        {"topic": "許可代碼誤植連罰", "desc": "營建與一般廢棄物代碼混用為近期查核重點。", "advice": "執行內部代碼複核確保一致。"}
    ]
    
    cols = st.columns(2)
    for i, m in enumerate(news):
        with cols[i % 2]:
            st.markdown(f"""
                <div style="background-color: #1A1C23; border-left: 5px solid #0288d1; padding: 15px; border-radius: 8px; border: 1px solid #333; min-height: 160px; margin-bottom: 15px;">
                    <b style="color: #4fc3f7;">{m['topic']}</b>
                    <p style="color: white; font-size: 0.85rem;">{m['desc']}</p>
                    <p style="color: #81d4fa; font-size: 0.85rem;"><b>📢 建議：</b>{m['advice']}</p>
                </div>
            """, unsafe_allow_html=True)
