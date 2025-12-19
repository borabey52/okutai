import streamlit as st
import utils
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="İletişim", page_icon="📞", layout="centered")
utils.sayfa_yukle() 

st.title("📞 İletişim")
st.markdown("Bizimle iletişime geçin, soru ve görüşlerinizi paylaşın.")
st.divider()

col_info, col_form = st.columns([1, 2], gap="large")

with col_info:
    st.markdown("### 📍 Adres")
    st.info("Teknopark İstanbul\nB Blok No:12\nPendik / İstanbul")
    st.markdown("### 📧 E-Posta")
    st.info("destek@okutai.com") 
    st.markdown("### 📱 Telefon")
    st.info("0850 123 45 67")

with col_form:
    st.markdown("### 💬 Mesaj Gönder")
    with st.form("iletisim_formu"):
        gonderen_ad = st.text_input("Adınız Soyadınız", value=st.session_state.username)
        konu = st.selectbox("Konu", ["Teknik Destek", "Kredi İşlemleri", "Öneri / Şikayet", "Diğer"])
        mesaj_icerigi = st.text_area("Mesajınız", height=150, placeholder="Lütfen mesajınızı buraya yazın...")
        
        gonder = st.form_submit_button("Gönder", type="primary", use_container_width=True)
        
        if gonder:
            if not mesaj_icerigi:
                st.error("Lütfen bir mesaj yazın.")
            else:
                try:
                    smtp_server = st.secrets["email"]["smtp_server"]
                    smtp_port = st.secrets["email"]["smtp_port"]
                    sender_email = st.secrets["email"]["sender_email"]
                    sender_password = st.secrets["email"]["sender_password"]
                    receiver_email = st.secrets["email"]["receiver_email"]

                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = receiver_email
                    
                    # --- HATA ÇÖZÜMÜ BURADA ---
                    # Türkçe karakterleri temizle: İ -> I, ş -> s
                    tr_chars = "ğĞüÜşŞİıöÖçÇ"
                    en_chars = "gGuUsSIioOcC"
                    translation_table = str.maketrans(tr_chars, en_chars)
                    
                    safe_subject = f"OkutAI Iletisim: {konu} - {gonderen_ad}"
                    safe_subject = safe_subject.translate(translation_table) # Temizle
                    
                    msg['Subject'] = safe_subject
                    # --------------------------

                    body = f"""
                    YENİ İLETİŞİM FORMU MESAJI
                    --------------------------
                    Gönderen: {gonderen_ad}
                    Konu: {konu}
                    
                    Mesaj:
                    {mesaj_icerigi}
                    """
                    msg.attach(MIMEText(body, 'plain', 'utf-8'))

                    with st.spinner("Mesajınız gönderiliyor..."):
                        server = smtplib.SMTP(smtp_server, smtp_port)
                        server.starttls() 
                        server.login(sender_email, sender_password)
                        server.sendmail(sender_email, receiver_email, msg.as_string())
                        server.quit()

                    st.success("✅ Mesajınız başarıyla bize ulaştı!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Mesaj gönderilemedi. Hata: {e}")
