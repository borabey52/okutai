# utils.py dosyasının en tepesine ekle:
from PIL import Image, ImageOps
import pillow_heif # <-- Yeni kütüphane
import io

# HEIC formatını sisteme tanıtıyoruz
pillow_heif.register_heif_opener()
import streamlit as st
import sqlite3
import bcrypt
import json
import base64
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# --- VERİTABANI AYARLARI ---
DATABASE_URL = "sqlite:///okutai.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_approved = Column(Integer, default=0)
    credits = Column(Integer, default=0)

class ExamRecord(Base):
    __tablename__ = "exam_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    student_name = Column(String)
    student_number = Column(String)
    session_name = Column(String, default="Genel Sınav")
    total_score = Column(Integer)
    details_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- MERKEZİ YÖNETİM FONKSİYONU ---
def sayfa_yukle():
    """
    Her sayfanın başında çalışır. 
    Güvenlik, Tasarım, MENÜ BUTONLARI ve PROFİL KARTI buradadır.
    """
    # 1. Güvenlik Kontrolü
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.switch_page("main.py")
        st.stop()

    # 2. Session Başlat
    init_session()

    # 3. Tasarım Uygula (CSS)
    apply_design()

    # 4. ŞIK SOL PANEL (SIDEBAR)
    with st.sidebar:
        # Güncel krediyi çek
        user = get_user_data(st.session_state.user_id)
        kredi = user.credits if user else st.session_state.credits
        st.session_state.credits = kredi
        
        # --- PROFİL KARTI ---
        st.markdown(f"""
        <div class="profile-card">
            <div class="profile-icon">👤</div>
            <div class="profile-name">{st.session_state.username}</div>
            <div class="profile-credit-box">
                <span style="font-size: 1.2rem;">🪙</span> 
                <span class="credit-text">Kalan Kredi: <strong>{kredi}</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---") # Çizgi

        # --- MANUEL NAVİGASYON (GÜNCELLENMİŞ VE DÜZELTİLMİŞ LİNKLER) ---
        st.markdown("### 🧭 Menü")
        
        # DİKKAT: Buradaki dosya isimleri, klasördekiyle BİREBİR AYNI olmalı.
        st.page_link("pages/1_📸_Sınav_Okut.py", label="Sınav Okut", icon="📸")
        st.page_link("pages/2_📊_Analiz.py", label="Analiz", icon="📊")
        
        # --- İŞTE DÜZELTİLEN KISIM BURASI ---
        st.page_link("pages/3_Yardim.py", label="Yardım", icon="❓")
        st.page_link("pages/4_Iletisim.py", label="İletişim", icon="📞")
        # ------------------------------------

        st.markdown("---") # Çizgi

        # Çıkış Butonu
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            st.session_state.logged_in = False
            st.switch_page("main.py")
        
        # --- FOOTER ---
        st.markdown("""
        <div style='text-align:center; color:#94a3b8; font-size:10pt; margin-top:30px;'>
            ©OkutAI - Sinan Sayılır
        </div>
        """, unsafe_allow_html=True)

# --- ANA FOOTER ---
def footer_ekle():
    st.markdown("""
    <div style="text-align: center; color: #94a3b8; font-size: 10pt; margin-top: 60px; font-family: sans-serif;">
        OkutAI uygulaması <strong>Sinan Sayılır</strong> tarafından geliştirilmiş ve kodlanmıştır.
    </div>
    """, unsafe_allow_html=True)

# --- DİĞER FONKSİYONLAR ---
def init_session():
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'user_id' not in st.session_state: st.session_state.user_id = None
    if 'username' not in st.session_state: st.session_state.username = ""
    if 'credits' not in st.session_state: st.session_state.credits = 0
    if 'sinif_verileri' not in st.session_state: st.session_state.sinif_verileri = []
    if 'kamera_acik' not in st.session_state: st.session_state.kamera_acik = False

def apply_design():
    st.markdown("""
    <style>
    /* 1. ÜST BOŞLUĞU AYARLA */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    /* 2. TÜM GEREKSİZ STREAMLIT MENÜLERİNİ GİZLE */
    header[data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    #MainMenu { display: none !important; }
    footer { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }

    /* 3. Yan Menü Başlığını (Sayfa Listesini) Gizle */
    [data-testid="stSidebarNav"] { display: none !important; }
    
    /* 4. PROFİL KARTI TASARIMI */
    .profile-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .profile-icon {
        font-size: 40px;
        margin-bottom: 10px;
        background-color: #f1f5f9;
        width: 70px;
        height: 70px;
        line-height: 70px;
        border-radius: 50%;
        margin-left: auto;
        margin-right: auto;
    }
    .profile-name {
        font-size: 20px !important;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 10px;
        font-family: 'Segoe UI', sans-serif;
    }
    .profile-credit-box {
        background-color: #f8fafc;
        border: 1px dashed #cbd5e1;
        border-radius: 10px;
        padding: 10px;
        color: #334155;
    }
    .credit-text {
        font-size: 16px !important;
        font-weight: 500;
    }

    /* 5. Butonlar ve Başlıklar */
    div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; border: 1px solid #d1d5db; }
    div.stButton > button:hover { border-color: #ef4444; color: #ef4444; background-color: #fef2f2; }
    .streamlit-expanderHeader { font-weight: bold; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 5px; }
    h1, h2, h3 { color: #002D62; }
    </style>
    """, unsafe_allow_html=True)

# --- VERİTABANI VE YARDIMCI ARAÇLAR ---
def login_user(username, password):
    db = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    if user and bcrypt.checkpw(password.encode(), user.hashed_password.encode()):
        return user
    return None

def create_user(username, password):
    db = next(get_db())
    if db.query(User).filter(User.username == username).first(): return False
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(username=username, hashed_password=hashed, is_approved=0, credits=0)
    db.add(user); db.commit(); return True

def update_password(username, new_password):
    db = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    if user:
        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        user.hashed_password = hashed
        db.commit()
        return True
    return False

def get_user_data(user_id):
    db = next(get_db())
    return db.query(User).filter(User.id == user_id).first()

def deduct_credit(user_id, amount=1):
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.credits >= amount:
        user.credits -= amount
        db.commit()
        return True
    return False

def save_results(user_id, results_list, oturum_adi):
    db = next(get_db())
    for r in results_list:
        rec = ExamRecord(
            user_id=user_id,
            student_name=r.get("Ad Soyad"),
            student_number=r.get("Numara"),
            session_name=oturum_adi,
            total_score=int(r.get("Toplam Puan", 0)),
            details_json=json.dumps(r.get("Detaylar", []), ensure_ascii=False)
        )
        db.add(rec)
    db.commit()

def load_results(user_id):
    db = next(get_db())
    recs = db.query(ExamRecord).filter(ExamRecord.user_id==user_id).order_by(ExamRecord.created_at.desc()).all()
    data = []
    for r in recs:
        data.append({
            "Ad Soyad": r.student_name, 
            "Numara": r.student_number,
            "Oturum": r.session_name,
            "Tarih": r.created_at,
            "Toplam Puan": r.total_score, 
            "Detaylar": json.loads(r.details_json)
        })
    return data

def get_existing_sessions(user_id):
    db = next(get_db())
    sessions = db.query(ExamRecord.session_name).filter(ExamRecord.user_id == user_id).distinct().all()
    return [s[0] for s in sessions]

def delete_exam(user_id, session_name):
    db = next(get_db())
    try:
        db.query(ExamRecord).filter(
            ExamRecord.user_id == user_id,
            ExamRecord.session_name == session_name
        ).delete()
        db.commit()
        return True
    except Exception as e:
        print(e)
        return False

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: data = f.read()
        return base64.b64encode(data).decode()
    except: return ""

def tablo_olustur(veri_listesi):
    tablo_satirlari = []
    for ogr in veri_listesi:
        satir = {
            "Oturum": ogr.get("Oturum", "-"),
            "Ad Soyad": ogr.get("Ad Soyad"),
            "Numara": ogr.get("Numara"),
            "Toplam Puan": ogr.get("Toplam Puan")
        }
        if "Detaylar" in ogr:
            for soru in ogr["Detaylar"]:
                no = soru.get("no")
                puan = soru.get("puan")
                satir[f"Soru {no}"] = puan
        tablo_satirlari.append(satir)
    return pd.DataFrame(tablo_satirlari)

def extract_json(text):
    text = text.strip()
    try:
        if "```json" in text: text = text.split("```json")[1].split("```")[0]
        elif "```" in text: text = text.split("```")[1].split("```")[0]
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != 0: return text[start:end]
        return text
    except:
        return text
# utils.py dosyasının EN ALTINA ekle:

def resim_yukle_ve_isle(uploaded_file):
    """
    Bu fonksiyon:
    1. HEIC formatındaki (iPhone) fotoları otomatik JPG yapar.
    2. Dev boyuttaki fotoları küçültür (Max 1024px) ki telefon donmasın.
    3. Yan dönmüş fotoları düzeltir (EXIF fix).
    """
    try:
        image = Image.open(uploaded_file)
        
        # 1. Yan dönmüş fotoları düzelt (Telefonla dik çekince yan yatabiliyor)
        image = ImageOps.exif_transpose(image)
        
        # 2. Resmi RGB formatına zorla (Bazı PNG'ler sorun çıkarır)
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        # 3. Boyutlandırma (Devasa fotoları küçültelim, yapay zeka için 1024px yeter de artar)
        max_size = (1024, 1024)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        return image
    except Exception as e:
        print(f"Resim işleme hatası: {e}")
        return None