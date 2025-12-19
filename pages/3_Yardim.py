import streamlit as st
import utils

# --- AYARLAR ---
st.set_page_config(page_title="Yardım Merkezi", page_icon="❓", layout="wide")
utils.sayfa_yukle() # Sol menü ve güvenlik
# ---------------

st.title("❓ Yardım Merkezi")
st.markdown("OkutAI kullanım rehberi ve sıkça sorulan sorular.")
st.divider()

# --- SIKÇA SORULAN SORULAR (Accordion) ---
st.subheader("Sıkça Sorulan Sorular")

with st.expander("📄 Sınav Kağıdı Nasıl Yüklenir?"):
    st.markdown("""
    1. **Sınav Okut** sayfasına gidin.
    2. **Yeni Sınav Oluştur** diyerek bir isim verin.
    3. Sağ taraftan **Dosya** sekmesini seçin ve kağıtların fotoğraflarını topluca yükleyin.
    4. "Kağıtları Okut" butonuna basın.
    """)

with st.expander("📸 Kamera ile Okuma Nasıl Yapılır?"):
    st.markdown("""
    1. Bilgisayarınızın veya telefonunuzun kamerasını kullanabilirsiniz.
    2. **Kamera** sekmesine gelin ve **Başlat** butonuna basın.
    3. Kağıdı kadraja alıp fotoğrafı çekin.
    4. Her öğrenci için bu işlemi tekrarlayın.
    """)

with st.expander("📝 Puanlama Mantığı Nedir?"):
    st.markdown("""
    Sistem, yüklediğiniz cevap anahtarına (veya öğretmen notuna) göre yapay zeka ile değerlendirme yapar.
    * Tam doğru cevaplara tam puan verir.
    * Eksik cevaplara kısmi puan verebilir.
    * Yanlış cevaplara 0 puan verir.
    """)

with st.expander("💰 Kredim Biterse Ne Olur?"):
    st.markdown("""
    Krediniz bittiğinde sınav okuma işlemi yapamazsınız. 
    Kredi yüklemek için **Yönetici** ile iletişime geçmeniz gerekir.
    İletişim sayfasından bize mesaj atabilirsiniz.
    """)

st.divider()

# --- VİDEOLU ANLATIM (Temsili) ---
col1, col2 = st.columns([1, 1])
with col1:
    st.info("💡 **İpucu:** Fotoğrafların net olması ve el yazısının okunabilir olması başarı oranını artırır.")

with col2:
    st.warning("⚠️ **Uyarı:** Sistemin hata yapma payı vardır. Sonuçları kontrol etmeniz önerilir.")

# Alt İmza
utils.footer_ekle()