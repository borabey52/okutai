# admin_panel.py
import streamlit as st
import utils

def calistir():
    st.set_page_config(page_title="Yönetici", page_icon="🔐")
    
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False

    ADMIN_PASS = "admin123" # Şifreyi buradan değiştir

    st.markdown("## 🔐 Gizli Yönetici Girişi")

    if not st.session_state.admin_logged_in:
        with st.form("admin_login"):
            pwd = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş"):
                if pwd == ADMIN_PASS:
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("Yanlış şifre.")
    else:
        st.success("Yönetici Paneli Aktif")
        db = next(utils.get_db())
        users = db.query(utils.User).all()

        st.info("Kullanıcıları onaylayabilir veya kredi ekleyebilirsiniz.")

        for u in users:
            with st.expander(f"👤 {u.username} | Kredi: {u.credits}"):
                c1, c2 = st.columns(2)
                is_approved = c1.checkbox("Onaylı Hesap", value=(u.is_approved==1), key=f"app_{u.id}")
                new_credit = c2.number_input("Kredi", value=u.credits, step=10, key=f"cred_{u.id}")
                
                if st.button("Kaydet", key=f"btn_{u.id}"):
                    u.is_approved = 1 if is_approved else 0
                    u.credits = new_credit
                    db.commit()
                    st.toast(f"{u.username} güncellendi!", icon="✅")
                    st.rerun()
        db.close()
        
        st.divider()
        if st.button("Çıkış Yap"):
            st.session_state.admin_logged_in = False
            st.query_params.clear()
            st.rerun()