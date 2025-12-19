import streamlit as st
import utils
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
import json
import time
import os
import io

# --- SAYFA VE MERKEZİ YÖNETİM ---
st.set_page_config(page_title="Sınav Okut", page_icon="📸", layout="wide", initial_sidebar_state="expanded")
utils.sayfa_yukle() 
# --------------------------------

# --- BAŞLIK ---
# Logoyu ve başlığı eski güzel haline getirdik
try:
    img_base64 = utils.get_img_as_base64("okutai_logo.png") 
    if img_base64:
        st.markdown(f"""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <img src="data:image/png;base64,{img_base64}" width="220" style="margin-bottom: 5px;">
                <h3 style='color: #002D62; margin: 0; font-size: 1.5rem; font-weight: 800;'>Sen Okut, O Puanlasın.</h3>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #002D62;'>OkutAİ</h1>", unsafe_allow_html=True)
except:
    st.markdown("<h1 style='text-align: center; color: #002D62;'>OkutAİ</h1>", unsafe_allow_html=True)

st.divider()

# Kredi Kontrolü
if st.session_state.credits <= 0:
    st.error("⛔ Krediniz tükenmiştir! Lütfen yöneticinizle görüşün.")
    st.stop()

# API KEY
SABIT_API_KEY = ""
try:
    if "GOOGLE_API_KEY" in st.secrets: SABIT_API_KEY = st.secrets["GOOGLE_API_KEY"]
except: pass
if not SABIT_API_KEY: SABIT_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Güvenlik Ayarları
guvenlik_ayarlari = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# --- ARAYÜZ (ESKİ SÜTUNLU YAPIYA DÖNÜŞ) ---
col_sol, col_sag = st.columns([1, 1], gap="large")

with col_sol:
    st.header("1. Sınav Bilgileri")
    
    # Sınav Seçimi
    mevcut_oturumlar = utils.get_existing_sessions(st.session_state.user_id)
    secim_tipi = st.radio("İşlem Türü:", ["🆕 Yeni Sınav Oluştur", "➕ Mevcut Sınava Ekle"], horizontal=True)
    
    oturum_adi = ""
    if secim_tipi == "🆕 Yeni Sınav Oluştur":
        oturum_adi = st.text_input("Yeni Sınav Adı:", placeholder="Örn: 5/C Matematik 1. Yazılı")
    else:
        if not mevcut_oturumlar:
            st.warning("⚠️ Henüz kayıtlı sınavınız yok.")
        else:
            oturum_adi = st.selectbox("Hangi Sınava Eklensin?", mevcut_oturumlar)

    ogretmen_promptu = st.text_area("Öğretmen Notu / Kriter:", height=100, placeholder="Ör: Yazım hataları -1 puan...")
    sayfa_tipi = st.radio("Sayfa Düzeni", ["Tek Sayfa", "Çift Sayfa"], horizontal=True)
    
    # Cevap Anahtarı
    with st.expander("🔑 Cevap Anahtarı (Opsiyonel)"):
        rubrik_files = st.file_uploader("Yükle", type=["jpg","png","jpeg","heic"], accept_multiple_files=True, key="rub")
        rub_imgs = []
        if rubrik_files:
            for f in rubrik_files:
                ri = utils.resim_yukle_ve_isle(f)
                if ri: rub_imgs.append(ri)
            st.caption(f"✅ {len(rub_imgs)} sayfa cevap anahtarı.")

with col_sag:
    st.header("2. Kağıt Yükleme")
    st.info("💡 **Bilgi:** Mobilden giriyorsanız alttaki alana tıklayıp **Kamera** veya **Galeri** seçeneğini kullanabilirsiniz.")
    
    # --- KRİTİK NOKTA: HAFIZA SİSTEMİ ---
    # Dosya yükleyiciye sabit bir key veriyoruz.
    upl_files = st.file_uploader(
        "Sınav Kağıtlarını Seç veya Çek", 
        type=["jpg","png","jpeg","heic","heif","JPG","PNG","JPEG","HEIC","HEIF"], 
        accept_multiple_files=True,
        key="mobil_uyumlu_uploader" 
    )
    
    tum_gorseller = []
    
    # Dosyalar seçildiği an işlemeye başlıyoruz
    if upl_files:
        # Şık bir durum çubuğu ile listeyi gizliyoruz (UI temiz kalıyor)
        with st.status("📂 Dosyalar işleniyor...", expanded=True) as status:
            toplam_boyut = 0
            for f in upl_files:
                try:
                    # utils içindeki fonksiyonumuz dosyayı küçültüp hafızaya alıyor
                    img = utils.resim_yukle_ve_isle(f)
                    if img: 
                        tum_gorseller.append(img)
                        toplam_boyut += (f.size / (1024*1024))
                except: pass
            
            status.update(label=f"✅ {len(tum_gorseller)} Kağıt Hazır! ({toplam_boyut:.1f} MB işlendi)", state="complete", expanded=False)

    # Başarı Mesajı
    if len(tum_gorseller) > 0:
        st.success(f"🚀 **{len(tum_gorseller)} adet kağıt yüklendi.** Puanlamaya hazır.")

st.divider()

# --- PUANLAMA BUTONU (ARTIK EN ALTTA VE GENİŞ) ---
if st.button("🚀 PUANLAMAYI BAŞLAT", type="primary", use_container_width=True):
    if not oturum_adi:
        st.error("⚠️ Lütfen bir Sınav Adı belirleyin!")
    elif not SABIT_API_KEY:
        st.error("API Key eksik.")
    elif not tum_gorseller:
        st.warning("⚠️ Lütfen önce yukarıdan dosya yükleyin.")
    else:
        genai.configure(api_key=SABIT_API_KEY)
        model = genai.GenerativeModel("gemini-flash-latest")
        
        is_paketleri = []
        adim = 2 if "Çift" in sayfa_tipi and len(tum_gorseller)>1 else 1
        
        for i in range(0, len(tum_gorseller), adim):
            is_paketleri.append(tum_gorseller[i:i+adim])

        prog = st.progress(0); txt = st.empty(); yeni_veriler = []
        
        # ... PROMPT AYNI KALIYOR ...
        ANA_KOMUT = """
        Sen bir öğretmen asistanısın. Görevin sınav kağıdını okumak.
        Eğer kağıt üzerinde sadece soru metni varsa ve öğrenci HİÇBİR ŞEY yazmamışsa: "cevap": "BOŞ", "puan": 0.
        Format: {"kimlik":{"ad_soyad":"...","numara":"..."},"degerlendirme":[{"no":"1","soru":"...","cevap":"...","puan":0,"tam_puan":10,"yorum":"..."}]}
        """
        
        for idx, imgs in enumerate(is_paketleri):
            txt.write(f"⏳ Okunuyor: {idx+1}/{len(is_paketleri)} - {oturum_adi}")
            try:
                prompt = [ANA_KOMUT]
                if ogretmen_promptu: prompt.append(f"NOT: {ogretmen_promptu}")
                if rub_imgs: 
                    prompt.append("CEVAP ANAHTARI:"); prompt.extend(rub_imgs) 

                prompt.append("ÖĞRENCİ KAĞIDI:"); prompt.extend(imgs)

                res = model.generate_content(prompt, safety_settings=guvenlik_ayarlari)
                try: 
                    cevap_metni = res.text
                    d = json.loads(utils.extract_json(cevap_metni))
                    k = d.get("kimlik",{})
                    s = d.get("degerlendirme",[])
                    tp = sum([float(x.get('puan',0)) for x in s])
                    
                    kayit = {"Ad Soyad": k.get("ad_soyad","?"), "Numara": k.get("numara","?"), "Oturum": oturum_adi, "Toplam Puan": tp, "Detaylar": s}
                    st.session_state.sinif_verileri.append(kayit)
                    yeni_veriler.append(kayit)
                except: pass
            except: pass
            prog.progress((idx+1)/len(is_paketleri))
        
        if yeni_veriler:
            utils.save_results(st.session_state.user_id, yeni_veriler, oturum_adi)
            if utils.deduct_credit(st.session_state.user_id, len(yeni_veriler)):
                st.session_state.credits -= len(yeni_veriler)
            txt.success("✅ İşlem Tamamlandı!"); time.sleep(1); st.rerun()

# --- SONUÇLAR (AKILLI GÖRÜNÜM) ---
if st.session_state.sinif_verileri:
    st.markdown(f"### 📝 Sonuçlar: {oturum_adi}")
    for ogrenci in reversed(st.session_state.sinif_verileri):
        # Sadece mevcut oturuma ait sonuçları göster
        if ogrenci.get("Oturum") == oturum_adi:
            renk = "green" if ogrenci['Toplam Puan'] >= 50 else "red"
            with st.expander(f"📄 {ogrenci['Ad Soyad']} | {int(ogrenci['Toplam Puan'])} Puan"):
                # Detayları JSON yerine tablo gibi göstermek istersen burayı özelleştirebiliriz
                # Şimdilik JSON bırakıyorum ki hızlı çalışsın
                st.json(ogrenci['Detaylar'])
