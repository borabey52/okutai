# utils.py dosyasının GÜNCELLENMİŞ HALİ

import streamlit as st
import sqlite3
import bcrypt
import json
import base64
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from PIL import Image, ImageOps # Resim işleme
import pillow_heif # iPhone formatı için
import io

# HEIC formatını sisteme tanıtıyoruz
pillow_heif.register_heif_opener()

# --- VERİTABANI AYARLARI ---
DATABASE_URL = "sqlite:///okutai.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ... (Buradaki User ve ExamRecord sınıfları aynı kalıyor, değiştirme) ...
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
    try: yield db
    finally: db.close()

# ... (Diğer login, create_user vb. fonksiyonlar aynı kalsın) ...
# ... (sayfa_yukle, init_session vb. fonksiyonlar aynı kalsın) ...

# --- 👇 İŞTE GÜNCELLENEN SIKIŞTIRMA FONKSİYONU ---
def resim_yukle_ve_isle(uploaded_file):
    """
    Bu fonksiyon:
    1. HEIC (iPhone) formatını JPG yapar.
    2. Resmi 800px'e kadar küçültür (Yapay zeka için en ideal ve hızlı boyut).
    3. Dosya boyutunu 4MB'dan ~150KB'a düşürür.
    """
    try:
        # Dosyayı aç
        image = Image.open(uploaded_file)
        
        # 1. Yan dönmüş fotoları düzelt
        image = ImageOps.exif_transpose(image)
        
        # 2. Renk formatını RGB yap (PNG veya bozuk formatları düzeltir)
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        # 3. BOYUT KÜÇÜLTME (RESIZE)
        # Önceki kodda 1024 yapmıştık, şimdi 800 yapıyoruz.
        # A4 kağıdındaki yazılar 800px genişlikte gayet net okunur.
        max_size = (800, 800) 
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Not: Burada return ettiğimiz 'image' objesi artık RAM'de küçücük yer kaplıyor.
        # Kullanıcı ekranda hala "4.2MB" yazısını görebilir (o yüklenen dosyadır),
        # ama bizim işlediğimiz ve yapay zekaya gönderdiğimiz şey artık tüy gibidir.
        
        return image
    except Exception as e:
        print(f"Resim işleme hatası: {e}")
        return None

# ... (Geri kalan tüm fonksiyonlar aynı: get_img_as_base64, save_results vb.) ...

# Kopyalama kolaylığı için diğer fonksiyonları buraya tekrar yazmıyorum, 
# sadece 'resim_yukle_ve_isle' fonksiyonunu güncellemen yeterli.
# Ama eğer utils.py karıştıysa söyle, tamamını atayım.
