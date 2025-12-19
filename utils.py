import streamlit as st
import utils
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
import json
import time
import os
import io # Boyut ölçümü için gerekli

# --- SAYFA VE MERKEZİ YÖNETİM ---
st.set_page_config(page_title="Sınav Okut", page_icon="📸", layout="wide", initial_sidebar_state="expanded")
utils.sayfa_yukle() 
# --------------------------------

# --- LOGO VE BAŞLIK ---
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

# --- ARAYÜZ ---
col_sol, col_sag = st.columns([1, 1], gap="large")

with col_sol:
    st.header("1. Sınav Bilgileri")
    
    # --- AKILLI SINAV SEÇİMİ ---
    mevcut_oturumlar = utils.get_existing_sessions(st.session_state.user_id)
    secim_tipi = st.radio("İşlem Türü:", ["🆕 Yeni Sınav Oluştur", "➕ Mevcut Sınava Ekle"], horizontal=True)
    
    oturum_adi = ""
    if secim_tipi == "🆕 Yeni Sınav Oluştur":
        oturum_adi = st.text_input("Yeni Sınav Adı:", placeholder="Örn: 5/C Matematik 1. Yazılı")
    else:
        if not mevcut_oturumlar:
            st.warning("⚠️ Henüz kayıtlı sınavınız yok. 'Yeni Sınav Oluştur' seçeneğini kullanın.")
        else:
            oturum_adi = st.selectbox("Hangi Sınava Eklensin?", mevcut_oturumlar)
            st.info(f"💡 Okutacağınız kağıtlar **'{oturum_adi}'** grubuna dahil edilecektir.")
    # ---------------------------

    ogretmen_promptu = st.text_area("Öğretmen Notu / Kriter:", height=100, placeholder="Ör: Yazım hataları -1 puan...")
    sayfa_tipi = st.radio("Sayfa Düzeni", ["Tek Sayfa", "Çift Sayfa"], horizontal=True)
    
    # --- CEVAP ANAHTARI ---
    with st.expander("Cevap Anahtarı (Opsiyonel)"):
        rubrik_files = st.file_uploader("Yükle (Ön ve Arka Yüz)", type=["jpg","png","jpeg","heic","heif","JPG","PNG","JPEG","HEIC"], accept_multiple_files=True, key="rub")
        rub_imgs = []
        if rubrik_files:
            for f in rubrik_files:
                processed_img = utils.resim_yukle_ve_isle(f)
                if processed_img:
                    rub_imgs.append(processed_img)
            st.caption(f"✅ {len(rub_imgs)} sayfa cevap anahtarı işlendi.")
    # ----------------------------

with col_sag:
    st.header("2. Kağıt Yükleme")
    
    st.info("💡 **Bilgi:** Mobilden giriyorsanız aşağıdaki alana tıklayıp **Kamera** veya **Galeri** seçeneğini kullanabilirsiniz.")
    
    # DÜZELTME 1: 'key' parametresi ekledik. Bu, sayfa yenilenirse dosyanın kaybolmamasını sağlar.
    upl_files = st.file_uploader(
        "Sınav Kağıtlarını Seç veya Çek", 
        type=["jpg","png","jpeg","heic","heif","JPG","PNG","JPEG","HEIC","HEIF"], 
        accept_multiple_files=True,
        key="sinav_kagidi_uploader" 
    )
    
    tum_gorseller = []
    
    if upl_files:
        st.write(f"📥 {len(upl_files)} dosya alındı, işleniyor...")
        
        for f in upl_files:
            try:
                img = utils.resim_yukle_ve_isle(f)
                if img: 
                    tum_gorseller.append(img)
                    
                    # DÜZELTME 2: KANIT SİSTEMİ (BOYUT HESAPLAMA)
                    # İşlenmiş resmin RAM'deki boyutunu hesaplayıp gösterelim
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG', quality=85)
                    size_kb = len(img_byte_arr.getvalue()) / 1024
                    orig_mb = f.size / (1024 * 1024)
                    
                    st.caption(f"✅ **{f.name}** hazır! (📉 {orig_mb:.1f} MB -> **{size_kb:.0f} KB**'a düşürüldü)")
                    
                else:
                    st.error(f"❌ '{f.name}' dosyası okunamadı!")
            except Exception as e:
                st.error(f"❌ Hata: {f.name} işlenirken sorun oluştu: {e}")
        
        if len(tum_gorseller) > 0:
            st.success(f"🚀 {len(tum_gorseller)} kağıt puanlamaya hazır!")

st.divider()

if st.button("🚀 KAĞITLARI OKUT VE PUANLA", type="primary", use_container_width=True):
    if not oturum_adi:
        st.error("⚠️ Lütfen bir Sınav Adı belirleyin veya listeden seçin!")
    elif not SABIT_API_KEY:
        st.error("API Key eksik.")
    else:
        if not tum_gorseller:
            st.warning("⚠️ Henüz geçerli bir dosya yüklenmedi.")
        else:
            genai.configure(api_key=SABIT_API_KEY)
            model = genai.GenerativeModel("gemini-flash-latest")
            
            is_paketleri = []
            adim = 2 if "Çift" in sayfa_tipi and len(tum_gorseller)>1 else 1
            
            for i in range(0, len(tum_gorseller), adim):
                p = tum_gorseller[i:i+adim]
                if p: is_paketleri.append(p)

            prog = st.progress(0); txt = st.empty(); yeni_veriler = []
            
            # --- PROMPT ---
            ANA_KOMUT = """
            Sen bir öğretmen asistanısın. Görevin sınav kağıdını okumak.
            
            ÇOK ÖNEMLİ KURAL - BOŞ KAĞIT KONTROLÜ:
            1. Önce kağıda dikkatlice bak. Öğrenci tarafından yazılmış bir cevap, işaretlenmiş bir şık veya karalama var mı?
            2. Eğer kağıt üzerinde sadece soru metni varsa ve öğrenci HİÇBİR ŞEY yazmamışsa, o soru için "cevap": "BOŞ", "puan": 0, "yorum": "Öğrenci cevap vermemiş." olarak döndür.
            3. ASLA soruyu kendin çözüp öğrenci çözmüş gibi puan verme. Sadece öğrencinin yazdıklarını değerlendir.
            
            ÇIKTI FORMATI:
            Sadece geçerli bir JSON döndür. Başka hiçbir metin yazma.
            Format: {"kimlik":{"ad_soyad":"...","numara":"..."},"degerlendirme":[{"no":"1","soru":"...","cevap":"...","puan":0,"tam_puan":10,"yorum":"..."}]}
            
            PUANLAMA:
            - Cevap doğruysa tam puan ver.
            - Kısmen doğruysa puan kır.
            - Yanlışsa veya BOŞ ise 0 ver.
            """
            
            for idx, imgs in enumerate(is_paketleri):
                txt.write(f"⏳ Okunuyor: {idx+1}/{len(is_paketleri)} - {oturum_adi}")
                try:
                    prompt = [ANA_KOMUT]
                    if ogretmen_promptu: prompt.append(f"ÖĞRETMEN EK NOTU: {ogretmen_promptu}")
                    if rub_imgs: 
                        prompt.append("CEVAP ANAHTARI (RUBRİK):")
                        prompt.extend(rub_imgs) 

                    prompt.append("DEĞERLENDİRİLECEK ÖĞRENCİ KAĞIDI:"); prompt.extend(imgs)

                    res = model.generate_content(prompt, safety_settings=guvenlik_ayarlari)
                    try: cevap_metni = res.text
                    except: continue

                    d = json.loads(utils.extract_json(cevap_metni))
                    k = d.get("kimlik",{})
                    s = d.get("degerlendirme",[])
                    tp = sum([float(x.get('puan',0)) for x in s])
                    
                    kayit = {
                        "Ad Soyad": k.get("ad_soyad","?"), 
                        "Numara": k.get("numara","?"), 
                        "Oturum": oturum_adi,     
                        "Toplam Puan": tp, 
                        "Detaylar": s
                    }
                    st.session_state.sinif_verileri.append(kayit)
                    yeni_veriler.append(kayit)
                    
                except Exception as e: st.error(f"Hata: {e}")
                prog.progress((idx+1)/len(is_paketleri))
            
            if yeni_veriler:
                utils.save_results(st.session_state.user_id, yeni_veriler, oturum_adi)
                if utils.deduct_credit(st.session_state.user_id, 1):
                    st.session_state.credits -= 1
                txt.success("✅ Tamamlandı ve Kaydedildi!"); st.balloons(); time.sleep(1); st.rerun()

# --- ANLIK SONUÇLAR ---
if len(st.session_state.sinif_verileri) > 0:
    st.markdown(f"### 📝 {oturum_adi} - Sonuçlar")
    for i, ogrenci in enumerate(reversed(st.session_state.sinif_verileri)):
        if ogrenci.get("Oturum") == oturum_adi:
            baslik = f"📄 {ogrenci['Ad Soyad']} | {int(ogrenci['Toplam Puan'])}"
            with st.expander(baslik, expanded=False):
                if "Detaylar" in ogrenci:
                    for soru in ogrenci["Detaylar"]:
                        p_val = float(soru.get('puan', 0))
                        t_val = float(soru.get('tam_puan', 0))
                        
                        renk_kod = "green" if p_val == t_val and t_val > 0 else "red" if p_val == 0 else "orange"
                        ikon = "✅" if p_val == t_val and t_val > 0 else "❌" if p_val == 0 else "⚠️"
                        
                        cevap_text = soru.get('cevap', '')
                        if "BOŞ" in str(cevap_text).upper():
                            ikon = "⛔"
                            renk_kod = "gray"
                            cevap_text = "⚠️ ÖĞRENCİ CEVABI BULUNAMADI"

                        p_text = f"{int(p_val)}" if p_val == int(p_val) else f"{p_val}"
                        t_text = f"{int(t_val)}" if t_val == int(t_val) else f"{t_val}"

                        st.markdown(f"""
                        <div style="font-size:18px; margin-bottom:5px;">
                            <strong>Soru {soru.get('no')}</strong> {ikon} <span style="color:{renk_kod}; font-weight:bold;">[{p_text} / {t_text}]</span>
                        </div>
                        <div style="font-size:16px; margin-bottom:10px; color:#333;">
                            <strong>Cevap:</strong> {cevap_text}
                        </div>
                        <div style="background-color:#f0f8ff; padding:15px; border-radius:8px; border-left:6px solid #002D62; font-size:16px;">
                            <span style="font-weight:bold; color:#002D62;">🤖 Yorum:</span> {soru.get('yorum')}
                        </div>
                        <hr style="margin: 10px 0;">
                        """, unsafe_allow_html=True)

utils.footer_ekle()
