# main.py
import streamlit as st
import utils
import admin_panel 

# Sayfa Ayarları (Sidebar kapalı başlasın)
st.set_page_config(page_title="OkutAİ", page_icon="🎓", layout="centered", initial_sidebar_state="collapsed")

# 1. YÖNETİCİ KONTROLÜ
if st.query_params.get("mod") == "yonetici":
    admin_panel.calistir()
    st.stop() 

# 2. OTURUM BAŞLAT
utils.init_session()

# 3. KESİN YÖNLENDİRME (Giriş yapıldıysa HİÇBİR ŞEY GÖSTERME, direkt ışınla)
if st.session_state.logged_in:
    st.switch_page("pages/1_📸_Sınav_Okut.py")
    st.stop() # Kodun geri kalanını okuma bile!

# 4. GİRİŞ EKRANI TASARIMI (Sadece giriş yapmamışlar görür)
# Buraya kadar geldiyse giriş yapmamış demektir.
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    /* Yan Menüyü Kökten Gizle */
    [data-testid="stSidebar"] { display: none !important; }
    
    .hero-container { text-align: center; margin-bottom: 20px; padding-top: 30px; }
    .logo-img { width: 350px; max-width: 100%; height: auto; margin-bottom: 10px; }
    .hero-title { color: #002D62 !important; font-size: 40px !important; font-weight: 800; margin: 0; }
    .hero-subtitle { color: #475569 !important; font-size: 1.2rem; margin-top: 5px; font-weight: 500; }
    .footer-text { text-align: center; color: #94a3b8; font-size: 10pt; margin-top: 60px; font-family: sans-serif; }
</style>
""", unsafe_allow_html=True)

img_base64 = utils.get_img_as_base64("okutai_logo.png")
if img_base64:
    header_html = f"""
    <div class="hero-container">
        <img src="data:image/png;base64,{img_base64}" class="logo-img">
        <div class="hero-subtitle">Sen Okut, O Puanlasın.</div>
    </div>
    """
else:
    header_html = """
    <div class="hero-container">
        <div class="hero-title">OkutAI</div>
        <div class="hero-subtitle">Sen Okut, O Puanlasın.</div>
    </div>
    """
st.markdown(header_html, unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Giriş Yap", "Kayıt Ol", "Şifremi Unuttum"])

with tab1: 
    st.markdown("<br>", unsafe_allow_html=True)
    u = st.text_input("Kullanıcı Adı", key="l_u")
    p = st.text_input("Şifre", type="password", key="l_p")
    if st.button("Giriş Yap", type="primary", use_container_width=True):
        user = utils.login_user(u, p)
        if user:
            if user.is_approved == 0: st.warning("Hesabınız henüz onaylanmadı.")
            else:
                st.session_state.logged_in = True
                st.session_state.user_id = user.id
                st.session_state.username = user.username
                st.session_state.credits = user.credits
                st.session_state.sinif_verileri = utils.load_results(user.id)
                st.switch_page("pages/1_📸_Sınav_Okut.py") 
        else: st.error("Hatalı kullanıcı adı veya şifre.")

with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    nu = st.text_input("Kullanıcı Adı", key="r_u")
    np = st.text_input("Şifre", type="password", key="r_p")
    if st.button("Kayıt Ol", use_container_width=True):
        if utils.create_user(nu, np): st.success("Kayıt alındı! Yönetici onayı bekleniyor.")
        else: st.error("Bu kullanıcı adı zaten alınmış.")

with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    ru = st.text_input("Kullanıcı Adı", key="f_u")
    rn = st.text_input("Yeni Şifre", type="password", key="f_p")
    if st.button("Şifreyi Güncelle", use_container_width=True):
        if utils.update_password(ru, rn): st.success("Şifreniz güncellendi! Giriş yapabilirsiniz.")
        else: st.error("Kullanıcı bulunamadı.")

utils.footer_ekle()