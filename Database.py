#Database.py
import sqlite3


#Veritabanı tablosunun oluşturulduğu yer
def setDatabase():
    conn = sqlite3.connect('PlakaTespit.db')
    curs = conn.cursor()
    curs.execute("""
                CREATE TABLE IF NOT EXISTS Plaka(
                PlakaId INTEGER PRIMARY KEY,
                Plaka TEXT,
                Tarih TEXT,
                Saat TEXT,
                Yontem TEXT)
                """)

