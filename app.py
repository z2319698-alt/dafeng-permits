# --- 新增：員工登入頁面邏輯 (中間集中版) ---
if not st.session_state.logged_in:
    # 建立三欄位，比例為 1:1.5:1 (中間那欄就是登入框)
    empty_l, login_col, empty_r = st.columns([1, 1.5, 1])
    
    with login_col:
        st.write("#") # 增加上方間距
        st.write("#")
        # 使用 st.container 並加上 border (Streamlit 1.29+ 版本支援)
        with st.container(border=True):
            st.title("🔐 員工登入")
            st.markdown("請輸入您的認證資訊以進入系統")
            
            # 使用普通的輸入框而非 form，體驗更直覺
            emp_id = st.text_input("👤 員工編號", placeholder="例如: DF001")
            emp_pwd = st.text_input("🔑 登入密碼", type="password", placeholder="****")
            
            st.write("#") # 增加按鈕上方的間距
            if st.button("登入系統", use_container_width=True, type="primary"):
                # 驗證邏輯
                if emp_id == "DF001" and emp_pwd == "1234":
                    st.session_state.logged_in = True
                    st.success("✅ 登入成功！")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ 員編或密碼錯誤")
            
            st.caption("💡 忘記密碼請洽系統管理員 Andy")
            
    st.stop() # 未登入前，強制停止執行後續程式碼
