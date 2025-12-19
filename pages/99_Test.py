import streamlit as st
import time

st.set_page_config(page_title="Efekt Testi")

st.title("🎭 Efekt Test Alanı")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🎈 Balonlar", use_container_width=True):
        st.balloons()

with col2:
    if st.button("❄️ Kar Yağışı", use_container_width=True):
        st.snow()

with col3:
    if st.button("🍞 Toast Mesaj", use_container_width=True):
        st.toast("Bu bir bildirim mesajıdır!", icon="🔔")
        time.sleep(0.5)
        st.toast("Hatta arka arkaya gelebilirler!", icon="😎")

st.divider()

if st.button("Dönen Çember (Spinner)"):
    with st.spinner("İşlem yapılıyor..."):
        time.sleep(2)
    st.success("Bitti!")