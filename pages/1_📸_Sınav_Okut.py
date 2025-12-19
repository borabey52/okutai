import streamlit as st
import utils
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
import json
import time
import os
import io

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sınav Okut", page_icon="📸", layout="wide", initial_sidebar_state="collapsed") # Sidebar kapalı başlasın
utils.sayfa_yukle() 

# --- BAŞLIK ---
st.markdown("<h3 style='text-align: center; color: #002D62;'>📸 Sınav Okutma Modülü</h3>", unsafe_allow_html=True)
st.divider()

# Kredi Kontrolü
if st.session_state.credits <= 0:
    st.error("⛔ Krediniz tükenmiştir!")
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

# --- 1. DOSYA YÜKLEME (EN TEPEDE - KOLAY ERİŞİM) ---
st.info("👇 **Mobilden giriyorsan buraya tıkla → Kamera'yı seç.** (İlk seferde yüklemezse lütfen tekrar dene, telefon hafızasından kaynaklanabilir.)")

upl_files = st.file_uploader(
    "Kağıtları Seç veya Çek", 
    type=["jpg","png","jpeg","heic","heif","JPG","PNG","JPEG","HEIC","HEIF"], 
    accept_multiple_files=True,
    key="mobile_uploader",
    label_visibility="collapsed" # Etiketi gizle, yer kaplamasın
)

tum_gorseller = []

if upl_files:
    # Basit ve hızlı işleme döngüsü
    for f in upl_files:
        try:
            img = utils.resim_yukle_ve_isle(f)
            if img: 
                tum_gorseller.append(img)
        except: pass # Hata olursa sessizce geç, arayüzü kilitleme

    if tum_gorseller:
        st.success(f"✅ **{len(tum_gorseller)} Kağıt Hazır!** Aşağıdan ayarları yapıp puanla.")

st.divider()

# --- 2. AYARLAR (SÜTUNLU YAPI BURADA OLABİLİR) ---
col1, col2 = st.columns(2)

with col1:
    # Sınav Seçimi
    mevcut_oturumlar = utils.get_existing_sessions(st.session_state.user_id)
    secim = st.radio("Sınav:", ["Yeni", "Mevcut"], horizontal=True, label_visibility="collapsed")
    
    oturum_adi = ""
    if secim == "Yeni":
        oturum_adi = st.text_input("Sınav Adı", placeholder="Örn: 5/A Matematik")
    else:
        if mevcut_oturumlar:
            oturum_adi = st.selectbox("Mevcut Sınav", mevcut_oturumlar)
        else:
            st.caption("Kayıtlı sınav yok.")
            oturum_adi = st.text_input("Sınav Adı", placeholder="Yeni isim giriniz")

with col2:
    # Sayfa Düzeni
    sayfa_tipi = st.radio("Kağıt Tipi:", ["Tek Sayfa", "Çift Sayfa"], horizontal=True)
    
    # Cevap Anahtarı (Expander içinde gizli)
    with st.expander("🔑 Cevap Anahtarı Yükle"):
        rubrik_files = st.file_uploader("Resim Seç", type=["jpg","png","jpeg","heic"], accept_multiple_files=True, key="rub")
        rub_imgs = []
        if rubrik_files:
            for f in rubrik_files:
                ri = utils.resim_yukle_ve_isle(f)
                if ri: rub_imgs.append(ri)

# Öğretmen Notu (Opsiyonel)
with st.expander("📝 Öğretmen Notu Ekle (Opsiyonel)"):
    ogretmen_promptu = st.text_area("Yapay Zekaya Not:", placeholder="Örn: Gidiş yoluna puan ver...")

# --- 3. BAŞLAT BUTONU ---
if st.button("🚀 PUANLAMAYI BAŞLAT", type="primary", use_container_width=True):
    if not oturum_adi:
        st.error("⚠️ Sınav adı giriniz.")
    elif not tum_gorseller:
        st.error("⚠️ Dosya yüklenmedi.")
    else:
        # --- YAPAY ZEKA İŞLEMİ ---
        genai.configure(api_key=SABIT_API_KEY)
        model = genai.GenerativeModel("gemini-flash-latest")
        
        is_paketleri = []
        adim = 2 if "Çift" in sayfa_tipi and len(tum_gorseller)>1 else 1
        
        for i in range(0, len(tum_gorseller), adim):
            is_paketleri.append(tum_gorseller[i:i+adim])

        prog = st.progress(0); txt = st.empty(); yeni_veriler = []
        
        ANA_KOMUT = """
        Sen bir öğretmen asistanısın. Görevin sınav kağıdını okumak.
        Eğer kağıt BOŞ ise veya sadece soru metni varsa: "cevap": "BOŞ", "puan": 0 döndür.
        Format: {"kimlik":{"ad_soyad":"...","numara":"..."},"degerlendirme":[{"no":"1","soru":"...","cevap":"...","puan":0,"tam_puan":10,"yorum":"..."}]}
        """
        
        for idx, imgs in enumerate(is_paketleri):
            txt.write(f"⏳ Okunuyor: {idx+1}/{len(is_paketleri)}")
            try:
                prompt = [ANA_KOMUT]
                if ogretmen_promptu: prompt.append(f"NOT: {ogretmen_promptu}")
                if rub_imgs: 
                    prompt.append("CEVAP ANAHTARI:")
                    prompt.extend(rub_imgs) 

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
            txt.success("✅ Bitti!"); time.sleep(1); st.rerun()

# --- SONUÇLAR ---
if st.session_state.sinif_verileri:
    st.markdown(f"### 📝 Sonuçlar: {oturum_adi}")
    for ogrenci in reversed(st.session_state.sinif_verileri):
        if ogrenci.get("Oturum") == oturum_adi:
            with st.expander(f"{ogrenci['Ad Soyad']} | {int(ogrenci['Toplam Puan'])} Puan"):
                st.json(ogrenci['Detaylar'])
