# ... (前面 AI 比對與數據載入邏輯保持不變) ...

    else:
        # --- 📋 許可證辦理系統 (排版優化版) ---
        st.sidebar.divider()
        sel_type = st.sidebar.selectbox("1. 選擇類型", sorted(main_df.iloc[:, 0].dropna().unique()))
        sub_main = main_df[main_df.iloc[:, 0] == sel_type].copy()
        sel_name = st.sidebar.radio("2. 選擇許可證", sub_main.iloc[:, 2].dropna().unique())
        target_main = sub_main[sub_main.iloc[:, 2] == sel_name].iloc[0]
        
        st.title(f"📄 {sel_name}")

        # 計算到期天數
        expiry_date = target_main.iloc[3]
        days_left = (expiry_date - today).days
        date_str = str(expiry_date)[:10]

        # --- 🟢 第一列：狀態提醒 + AI 建議 (併排) ---
        row1_col1, row1_col2 = st.columns(2)
        
        with row1_col1:
            if days_left < 90:
                st.error(f"🚨 【嚴重警告】剩餘 {days_left} 天")
            elif days_left < 180:
                st.warning(f"⚠️ 【到期預警】剩餘 {days_left} 天")
            else:
                st.success(f"✅ 【狀態正常】剩餘 {days_left} 天")

        with row1_col2:
            # 使用與截圖一致的淺綠背景框，但保持文字深色
            bg_color = "#ffeded" if days_left < 90 else ("#fff9e6" if days_left < 180 else "#e8f5e9")
            text_color = "#333"
            advice = "立即準備附件申報！" if days_left < 90 else ("建議開始核對附件。" if days_left < 180 else "在 180 天前開始蒐集即可。")
            st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 12px; border-radius: 5px; color: {text_color}; border: 1px solid #ccc; height: 50px; line-height: 25px;">
                    <b>🤖 AI 建議：</b>{advice}
                </div>
                """, unsafe_allow_html=True)

        # --- 🔵 第二列：管制編號 + 許可到期日 (併排) ---
        row2_col1, row2_col2 = st.columns(2)
        
        with row2_col1:
            st.info(f"🆔 管制編號：{target_main.iloc[1]}")
            
        with row2_col2:
            st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 12px; border-radius: 5px; color: #333; border: 1px solid #dcdfe6; height: 50px; line-height: 25px;">
                    📅 許可到期日期：<b>{date_str}</b>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # AI 狀態顯示
        pdf_val = target_main.get("PDF連結", "")
        ai_color = "#2E7D32" if pd.notna(pdf_val) and str(pdf_val).strip() != "" else "#d32f2f"
        st.markdown(f'<p style="color:{ai_color}; font-weight:bold;">🔍 AI 背景核對狀態：{"✅ 已同步" if ai_color=="#2E7D32" else "⚠️ 無連結"}</p>', unsafe_allow_html=True)

        display_ai_law_wall(sel_type)
        
        # ... (後續附件上傳邏輯保持不變) ...
