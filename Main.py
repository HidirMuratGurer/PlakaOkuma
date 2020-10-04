# Main.py
import locale
import cv2 #Goruntu işleme kütüphanesi
import numpy as np
import os
import sys
import Database
import PlakaYerTespit
import datetime
import pytesseract
from PlakaOkuma import Ui_MainWindow
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt, QRegExp #PyQT5 kütüphanesi tanımlanmasi
from PyQt5.QtGui import QImage, QPixmap, QRegExpValidator, QIcon #PyQT5 kütüphanesi tanımlanmasi
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox, QTableWidgetItem,QTableWidgetItem, QFileDialog, QWidget #PyQT5 kütüphanesi tanımlanmasi
from PyQt5 import QtCore, QtGui, QtWidgets
import sqlite3

#pytesseract kütüphanesi için bilgisayar yolunu tanıttık.
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

#Local veritabanı için gerekli tanımlamalar
locale.setlocale(locale.LC_ALL, '')

#Veritabanı bağlantı tanımlaması
conn = sqlite3.connect('PlakaTespit.db', check_same_thread=False)
curs = conn.cursor()

cap=cv2.VideoCapture(0) #Kamera görüntüsünü almak için kullanılan fonksiyon.Bu değişkeni global olarak tanımlamamızın nedeni thread'ı durduduğumuzda tekrar çalıştırırken sorun yaşamamak.

class Thread(QThread):
    changePixmap = pyqtSignal(QImage)
    def run(self):
        # Thread çalıştığı sürece bu fonksiyon sürekli olarak çalışır.
        while True:
            ret, frame = cap.read()
            main(frame)
            if ret:
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) #Griton Dönüşüm yapılıyor.
                h, w, ch = rgbImage.shape #Yukseklik genişlik değerleri alınıyor.
                bytesPerLine = ch * w
                convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888) #Pyqt5 için uygun format dönüşümü yapılıyor.
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p) #Pixeldeki değişim oldukca p değeri yani ekran görüntüsü gönderiliyor.

    def stop(self):
        self.terminate() #threadı durdurmak için kullanıyoruz.
        self.exec()
        self.quit()
        self.exit()


class MainClass(QMainWindow,Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainClass, self).__init__(parent)
        self.setupUi(self)
        self.InitUi()
    def InitUi(self):
        self.show() #Arayüzün açıldığı yer
        Database.setDatabase() #Veritabanının ayarladığı komut
        self.LoadDatabase() #Verilerin Tabloya yüklenmesi
        self.pushButton.clicked.connect(self.Baslat)        #Kamerayı Başlatan button için click event veriliyor.
        self.pushButton_2.clicked.connect(self.Durdur)      #Kamerayı Durduran button için click event veriliyor.
        self.PlakaAra.clicked.connect(self.PlakaArama)      #Plaka Araması Yapmak için click event veriliyor.
        self.TarihAra.clicked.connect(self.TarihArama)      #Tarih Araması Yapmak için click event veriliyor.
        self.YontemAra.clicked.connect(self.YontemArama)    #Yontem Araması Yapmak için click event veriliyor.
        self.th = Thread(self)
        self.th.changePixmap.connect(self.setImage)


    def setImage(self, image):
        self.ResimLabel.setPixmap(QPixmap.fromImage(image))
        self.LoadDatabase()


    def LoadDatabase(self):
        while self.tableWidget.rowCount() > 0:
            self.tableWidget.removeRow(0) #Eğer tabloda veri varsa siliyor.
        while True:
            res = conn.execute('SELECT Plaka,Tarih,Saat,Yontem FROM Plaka') #Veritabanındaki kayıtlı tüm plakaları alıyoruz.
            for row_index, row_data in enumerate(res): #Her bir satırı geziyoruz.
                self.tableWidget.insertRow(row_index) #Bulunan satır sayısı kadar tabloya ekleme yapıyor.
                for colm_index, colm_data in enumerate(row_data): #Her bir sutunu geziyoruz.
                    self.tableWidget.setItem(row_index, colm_index, QTableWidgetItem(str(colm_data))) #Veriyi tabloya ekliyoruz.
            return
    def PlakaArama(self):
        while self.AramaTable.rowCount() > 0:
            self.AramaTable.removeRow(0) #Eğer tabloda veri varsa siliyor.
        while True:
            Aranan =self.textEdit.toPlainText()
            res = conn.execute("SELECT Plaka,Tarih,Saat,Yontem FROM Plaka WHERE Plaka =? ", (Aranan,))
            for row_index, row_data in enumerate(res): #Her bir satırı geziyoruz.
                self.AramaTable.insertRow(row_index) #Bulunan satır sayısı kadar tabloya ekleme yapıyor.
                for colm_index, colm_data in enumerate(row_data): #Her bir sutunu geziyoruz.
                    self.AramaTable.setItem(row_index, colm_index, QTableWidgetItem(str(colm_data))) #Veriyi tabloya ekliyoruz.

            return
    def TarihArama(self):
        while self.AramaTable.rowCount() > 0:
            self.AramaTable.removeRow(0) #Eğer tabloda veri varsa siliyor.
        while True:
            Aranan =self.textEdit_2.toPlainText()
            res = conn.execute("SELECT Plaka,Tarih,Saat,Yontem FROM Plaka WHERE Tarih =? ", (Aranan,))
            for row_index, row_data in enumerate(res): #Her bir satırı geziyoruz.
                self.AramaTable.insertRow(row_index)  #Bulunan satır sayısı kadar tabloya ekleme yapıyor.
                for colm_index, colm_data in enumerate(row_data): #Her bir sutunu geziyoruz.
                    self.AramaTable.setItem(row_index, colm_index, QTableWidgetItem(str(colm_data))) #Veriyi tabloya ekliyoruz.

            return
    def YontemArama(self):
        while self.AramaTable.rowCount() > 0:
            self.AramaTable.removeRow(0) #Eğer tabloda veri varsa siliyor.
        while True:
            Aranan =self.textEdit_3.toPlainText()
            res = conn.execute("SELECT Plaka,Tarih,Saat,Yontem FROM Plaka WHERE Yontem =? ", (Aranan,))
            for row_index, row_data in enumerate(res): #Her bir satırı geziyoruz.
                self.AramaTable.insertRow(row_index)  #Bulunan satır sayısı kadar tabloya ekleme yapıyor.
                for colm_index, colm_data in enumerate(row_data): #Her bir sutunu geziyoruz.
                    self.AramaTable.setItem(row_index, colm_index, QTableWidgetItem(str(colm_data))) #Veriyi tabloya ekliyoruz.

            return
    def Baslat(self):
        #Thread run fonksiyonunu çalıştırıyoruz.
        self.th.start()

    def Durdur(self):
        # Thread stop fonksiyonunu çalıştırıyoruz threadı durdurmak için.
        self.th.stop()




def main(Goruntu):
    KNNYukle = PlakaYerTespit.KNNVerileriniYukle()   #KNN verilerini yüklüyoruz.

    if KNNYukle == False:
        print("\nKNN Algoritması Yuklenirken Hata Olustu\n")
        return  #main fonksiyonundan çıkıyoruz.
    #if bitimi

    if Goruntu is None:  #Goruntu Bulunamadıysa
        print("\nHata Goruntu Bulunamadı \n\n")
        return
    #if bitimi

    Plakalar = PlakaYerTespit.PlakaYeriBul(Goruntu)    #Goruntudeki plakaları bulacak fonksiyonu çağırıyoruz.

    Plakalar = PlakaYerTespit.PlakadakiKarakterleriBul(Plakalar)       # Plakadaki karakterleri bulacak fonksiyonu çağırıyoruz.

    # Eğer Plaka Bulunamadıysa
    if len(Plakalar) == 0:
        return
    # En az 1 tane plaka bulunduysa
    else:

        #Plakaları Sıralıyoruz.
        Plakalar.sort(key = lambda karakter: len(karakter.textPlaka), reverse = True)

        #En olası plakayı değişkene alıyoruz.
        mevcutPlaka = Plakalar[0]

        #Plaka resminden tesseract ile yazıyı okuyoruz.
        yazitesseract=pytesseract.image_to_string(mevcutPlaka.PlakaResmi)
        #Gün ve Saati fonksiyon ile alıyoruz veritabanına kayıt ederken kullanacağız.
        date, time = getDateAndTime()

        #Eğer Mevcut Plakada 5 den fazla karakter varsa veritabanına kayıt ediyoruz.
        if len(mevcutPlaka.textPlaka)>5:
            curs.execute("INSERT INTO Plaka (Plaka,Tarih,Saat,Yontem) VALUES(?,?,?,?)",
                         (mevcutPlaka.textPlaka, date, time, "KNN"))
            conn.commit()
        #Eğer tesseract ile okunan yazının uzunluğu 5 den fazla ise veritabanına kayıt ediyoruz.
        if len(yazitesseract)>5:
            curs.execute("INSERT INTO Plaka (Plaka,Tarih,Saat,Yontem) VALUES(?,?,?,?)",
                         (yazitesseract, date, time, "Tesseract"))
            conn.commit()
        #Plakada hiç karakter yoksa yani yanlış bir plaka okuması yapıldıysa veya Algoritma harfleri tanıyamadıysa
        if len(mevcutPlaka.textPlaka) == 0:
            return
        #if bitimi

        #Plakanın çevresini dikdörtgen içerisine alan fonksiyon
        PlakayiCiz(Goruntu, mevcutPlaka)

        #Okunan plakayı görüntü üzerine yazan fonksiyon
        PlakaYaz(Goruntu, mevcutPlaka)

    #if bitimi

    return
#main bitimi
def getDateAndTime():
    an = datetime.datetime.now()
    second = int(an.second)
    hour = int(an.hour)
    date = str(an.day) + "." + str(an.month) + "." + str(an.year)
    time = str(an.hour) + ":" + str(an.minute) + ":" + str(an.second)
    return date, time

def PlakayiCiz(Goruntu, mevcutPlaka):
    Kirmizi = (0.0, 0.0, 255.0)
    #Plakanın 4 köşesininin kordinatlarını aldık
    PlakaYerleri = cv2.boxPoints(mevcutPlaka.PlakaninSahnedekiYeri)

    #Her bir köşe için çizim yapıyoruz.
    cv2.line(Goruntu, tuple(PlakaYerleri[0]), tuple(PlakaYerleri[1]), Kirmizi, 2)
    cv2.line(Goruntu, tuple(PlakaYerleri[1]), tuple(PlakaYerleri[2]), Kirmizi, 2)
    cv2.line(Goruntu, tuple(PlakaYerleri[2]), tuple(PlakaYerleri[3]), Kirmizi, 2)
    cv2.line(Goruntu, tuple(PlakaYerleri[3]), tuple(PlakaYerleri[0]), Kirmizi, 2)
#fonksiyon bitimi


def PlakaYaz(Goruntu, mevcutPlaka):
    Sari = (0.0, 255.0, 255.0)
    #Plakanın ortasını bulmak için tanımlamalar
    YazininXEksenininOrtasi = 0
    YazininYEksenininOrtasi = 0

    #Metinin yazılacağa yerin sol alt kısmı için tanımlamalar
    EnSoldakiXKordinati = 0
    EnSoldakiYKordinati = 0

    #Genel goruntunun ve plakanın bulunduğu yerin genişlik ve yükseklik değerlerini hesaplıyoruz.
    goruntuYuksekligi, goruntuGenisligi, sceneNumChannels = Goruntu.shape
    plakaYuksekligi, plakaGenisligi, plateNumChannels = mevcutPlaka.PlakaResmi.shape

    #Font Ayarlaması
    FontGorunumu = cv2.FONT_HERSHEY_SIMPLEX

    #Fontun büyüklügü Plakaya göre ayarlanıyor.
    FontBoyutu = float(plakaYuksekligi) / 30.0

    #Fontun boyutuna göre font kalınlıgını ayarladık.
    FontKalinligi = int(round(FontBoyutu * 1.5))

    #Yazının boyutunu istediğimiz font değerlerine göre aldık
    yaziBoyutu, baseline = cv2.getTextSize(mevcutPlaka.textPlaka, FontGorunumu, FontBoyutu, FontKalinligi)

    #Plakanın yerini bulmak için sınıftan plaka değerlerini alıyoruz.
    ( (PlakaninXeksenininOrtasi, PlakaninYeksenininOrtasi), (PlakaGenisligi, PlakaYuksekligi), PlakanınAlanHesabi ) = mevcutPlaka.PlakaninSahnedekiYeri

    #Yazının ortasını tespit edip goruntuya yazmak için orta noktalarının int değerlerini alıyoruz çünkü fonksiyon int değerler ile çalışıyor.
    PlakaninXeksenininOrtasi = int(PlakaninXeksenininOrtasi)
    PlakaninYeksenininOrtasi = int(PlakaninYeksenininOrtasi)

    #X Ekseni plaka ile aynı olacağı için direk alıyoruz.
    YazininXEksenininOrtasi = int(PlakaninXeksenininOrtasi)

    #Plaka boyutuna göre yazının yazılacağı yeri ayarlıyoruz. Eğer plaka görüntüsü normal görüntünün %75 inden az ise altına değilse üstüne yazacağız.
    if PlakaninYeksenininOrtasi < (goruntuYuksekligi * 0.75):
        YazininYEksenininOrtasi = int(round(PlakaninYeksenininOrtasi)) + int(round(plakaYuksekligi * 1.6))   #Alt tarafa yazmak için kordinat ayarlanıyor.
    else:
        YazininYEksenininOrtasi = int(round(PlakaninYeksenininOrtasi)) - int(round(plakaYuksekligi * 1.6))   #Ust tarafa yazmak için kordinat ayarlanıyor.
    #if bitimi

    yaziGenisligi, yaziYuksekligi = yaziBoyutu

    #Yazının başlangıcı için en sol tarafın hesabı yapılıyor.
    EnSoldakiXKordinati = int(YazininXEksenininOrtasi - (yaziGenisligi / 2))
    EnSoldakiYKordinati = int(YazininYEksenininOrtasi + (yaziYuksekligi / 2))

    #Yazının goruntu üzerine yazılması
    cv2.putText(Goruntu, mevcutPlaka.textPlaka, (EnSoldakiXKordinati, EnSoldakiYKordinati), FontGorunumu, FontBoyutu, Sari, FontKalinligi)
#fonksiyon bitimi



if __name__ == "__main__":
    app = QApplication([])
    win = MainClass()

    sys.exit(app.exec_())























