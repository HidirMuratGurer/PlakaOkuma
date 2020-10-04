#PlakaYerTespit.py
import cv2 #opencv kütüphanesinin yüklenmesi
import numpy as np #KNN verilerinin karşılaştırılabilmesi için tanımlandı.
import math
import os
import random
import sqlite3 #Veritabanı için kütüphane

conn = sqlite3.connect('PlakaTespit.db', check_same_thread=False)
curs = conn.cursor()
KNNAlgoritmasi = cv2.ml.KNearest_create()

class ContoursOzellikleri:
    def __init__(self, _contour):
        self.contour = _contour
        self.CevreBulma = cv2.boundingRect(self.contour)
        # Bulduğumuz Contourun dikdörtgen boyutlarını alıyoruz
        [Xdegeri, Ydegeri, Genislik, Yukseklik] = self.CevreBulma
        self.DikdortgeninXdegeri = Xdegeri
        self.DikdortgeninYdegeri = Ydegeri
        self.DikdortgeninGenisligi = Genislik
        self.DikdortgeninYuksekligi = Yukseklik
        # Dikdörtgenin alan hesabı
        self.DikdortgenAlani = self.DikdortgeninGenisligi * self.DikdortgeninYuksekligi
        self.XeksenininOrtasi = (self.DikdortgeninXdegeri + self.DikdortgeninXdegeri + self.DikdortgeninGenisligi) / 2
        self.YeksenininOrtasi = (self.DikdortgeninYdegeri + self.DikdortgeninYdegeri + self.DikdortgeninYuksekligi) / 2
        self.DikdortgenCevreHesabi = math.sqrt((self.DikdortgeninGenisligi ** 2) + (self.DikdortgeninYuksekligi ** 2))
        self.EnBoyHesabi = float(self.DikdortgeninGenisligi) / float(self.DikdortgeninYuksekligi)


# class bitimi


class Plaka:
    def __init__(self):
        self.PlakaResmi = None
        self.PlakaGriton = None
        self.PlakaTreshold = None
        self.PlakaninSahnedekiYeri = None
        self.textPlaka = ""
# class Bitimi

def PlakaYeriBul(Goruntu):
    Plakalar = [] # Bulunan plakaların atılacağı liste
    #Goruntunun boyutlarını almamız gerekiyor

    genislik,yukseklik,kanallar=Goruntu.shape

    #Griton,Treshold,Conturslar için 0 lanmış numpy tanımlamaları yapıyoruz.

    GritonGoruntu =np.zeros((yukseklik, genislik, 1), np.uint8)
    Treshold = np.zeros((yukseklik, genislik, 1), np.uint8)
    Contours = np.zeros((yukseklik, genislik, 3), np.uint8)

    GritonGoruntu, Treshold = GritonVeTreshold(Goruntu)     #Griton ve Treshold Goruntu elde ediyoruz.

    #Plaka aramasını treshold resim üzerinden yapacağız.
    Contourslar =GoruntudekiContourlariBul(Treshold)

    #Bulunan Contours üzerinde harf aramasi yapacağız.
    GruplanmisKarakterler =GruplanmisKarakterleriBul(Contourslar)

    for karakterGrubu in GruplanmisKarakterler:

        #Plakayı tespit etmek için fonksiyonu çalıştırıyoruz.
        Plaka=PlakayıTespitEt(Goruntu,karakterGrubu)
        #Eğer PlakaResmine herhangi bir plaka girişi yapıldıysa en az 1 adet plaka bulmuşuz demektir.
        #Bulunan plakayı plakalar listemize ekliyoruz.
        if Plaka.PlakaResmi is not None:
            Plakalar.append(Plaka) #Eğer program buraya geldiyse plakayı bulduk demektir.

    return Plakalar
#fonksiyon bitimi

def GritonVeTreshold(Goruntu):
    yukseklik, genislik, numChannels = Goruntu.shape

    Gecici = np.zeros((yukseklik, genislik, 3), np.uint8)

    Gecici = cv2.cvtColor(Goruntu, cv2.COLOR_BGR2HSV)

    renk, grilikMiktarı, Griton = cv2.split(Gecici)

    gritonYukseklik, gritonGenislik = Griton.shape

    #İyi bir görüntü elde etmek için constrast ayarlaması yaomak gerekiyor.
    #Bunun için blackhat ve tophat bulup maximum constrast elde edeceğiz. 3x3 lük

    TophatGoruntu = np.zeros((gritonYukseklik, gritonGenislik, 1), np.uint8)
    BlackhatGoruntu = np.zeros((gritonYukseklik, gritonGenislik, 1), np.uint8)
    BlurBulma = np.zeros((gritonYukseklik, gritonGenislik, 1), np.uint8)

    Yapilandirma = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))    #3x3 ayarladık

    TophatGoruntu = cv2.morphologyEx(Griton, cv2.MORPH_TOPHAT, Yapilandirma) #3x3 'lük tophat değeri alındı
    BlackhatGoruntu = cv2.morphologyEx(Griton, cv2.MORPH_BLACKHAT, Yapilandirma) #3x3 'lük blackhat değeri alındı

    TopHatTopla = cv2.add(Griton, TophatGoruntu) #Tophat değeri Griton resimle birleştirildi.
    GritonConstrast = cv2.subtract(TopHatTopla, BlackhatGoruntu) #Griton için maksimum contrast elde ettik

    BlurBulma = cv2.GaussianBlur(GritonConstrast, (5,5), 0)  #5x5 lik Gauss Filtresi Uyguladık

    # Treshold için piksek eşik değerini 19 olarak tanımladık.
    Treshold = cv2.adaptiveThreshold(BlurBulma, 255.0, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,19, 9)


    return Griton,Treshold
#fonksiyon bitimi

def GoruntudekiContourlariBul(TresholdGoruntu):
    Contourslar =[]
    Minimum_Piksel_Alani = 80
    Minimum_Piksek_Genisligi = 2
    Minimum_Piksel_Yuksekligi = 8
    Minimum_EnboyOrani = 0.25
    Maksimum_EnboyOrani = 1.0
    #FindCotours fonksiyonu ile görüntü üzerindeki tüm countoursları buluyoruz.
    contours, buyukluk = cv2.findContours(TresholdGoruntu.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    for i in range(0, len(contours)):
        Contour = ContoursOzellikleri(contours[i])
        if (Contour.DikdortgenAlani > Minimum_Piksel_Alani and Contour.DikdortgeninGenisligi > Minimum_Piksek_Genisligi
            and Contour.DikdortgeninYuksekligi > Minimum_Piksel_Yuksekligi and Minimum_EnboyOrani < Contour.EnBoyHesabi and Contour.EnBoyHesabi < Maksimum_EnboyOrani):
            Contourslar.append(Contour)
        #if bitimi
    #for bitimi

    return Contourslar
#fonksiyon bitimi


def GruplanmisKarakterleriBul(Contourslar):
    #Bu fonksiyonda olası bütün countsları gezerek içerisindeki karakter gruplarını tespit etmek.
    #Karakter Grupları tespit edildikten sonra uygunsuz olanlar listeden silinir.
    #Yeni oluşan listede elimizde sadece bizim istediğimiz sayıda ve yakınlıktaki karakter grupları oluşturan contourslar kalır.
    #Yani bu fonksiyonun sonunda olası plaka olabilecek countourslar kalır.

    GruplanmisKarakterler =[]
    Gruplanacak_Karakter_Sayisi=3

    for karakter in Contourslar:
        karakterGrubu = YakinKarakteriBulma(karakter,Contourslar)    #Mevcut listedeki bütün yakın karakterleri bulmak için kullanılır.
        karakterGrubu.append(karakter)      #Bulunan olası karakterleri mevcut listeye ekledik.

        if len(karakterGrubu) < Gruplanacak_Karakter_Sayisi:    #Birbirine yakın olan karakterlerin sayısı 3 den az ise
            continue    #Bulunan bu karakter grubu plaka olamayacağı için atlanır.
        #if bitimi
        GruplanmisKarakterler.append(karakterGrubu)     #Fonksiyon buraya kadar geldiyse 3 den fazla grublanmış karakterleri bulduk demektir.

        SilinecekKarakterlerListesi =[]

        #Eğer gruplanmış karakter bulduksak listeden çıkarmamız lazım diğerlerini ararken 2 kez bulunmaması için
        SilinecekKarakterlerListesi = list(set(Contourslar) - set(karakterGrubu))

        #Fonksiyon 2 Contours arasında karşılaştırma yaptıgı için silindikten sonra listeyi tekrar tekrar çağırarak tüm countourlar arası karşılaştırma yapılacak
        recursiveGruplanmisKarakter = GruplanmisKarakterleriBul(SilinecekKarakterlerListesi)

        # Tüm bulunan gruplanmış karakterler listeye eklenir.
        for tekrarBulma in recursiveGruplanmisKarakter:
            GruplanmisKarakterler.append(tekrarBulma)
        #for bitimi

        break


    return GruplanmisKarakterler
#fonksiyon bitimi


def YakinKarakteriBulma(karakter,Contourslar):
    Maksimum_diagram_uzakligi=5.0
    Maksimum_karakterlerarasi_aci=12.0
    Maksimum_degisim_alani=0.5
    Maksimum_degisim_genisligi=0.8
    Maksimum_degisim_yuksekligi=0.2

    Karakterler =[]
    #Bu fonksiyonun amacı karakterler arası mesafe,açı,alanı,genişliği ve yüksekliğini hesaplayarak.
    #Hesaplanan karakter bilgileri bizim olası olarak hesapladığımız değişkenler ile karşılaştırılarak
    #Karakter gruplarının olası plakayı içerip içermediğini bulabilmek.

    for olasiGruplanmisKarakterler in Contourslar:
        if olasiGruplanmisKarakterler == karakter:

            continue

        #İki contours arasındaki mesafe hesaplanır.
        MesafeHesabi = KarakterlerArasiUzaklikHesaplama(karakter,olasiGruplanmisKarakterler)

        #Karakterin arasındaki açı hesaplaması yaptıyoruz.
        #Açı hesabı yaparken karakterler arası X ve Y arasındaki mesafeyi hesaplıyoruz.
        #Bulunan mesafenin radyanı arctanjant ile bulunuyor
        #Bulunan radyan ile açı hesaplaması yapıyoruz.
        KarakterAcisi = AciHesapla(karakter,olasiGruplanmisKarakterler)

        #Alan Genislik ve Yukseklik Değerlerinin iki karakter arasındaki değişimi hesaplanıyor.
        #Hesaplanan değerler Tanımlanmış olan değerler ile karşılaştırılıp olası gruplanmış karakterler listeye alınarak olası plaka tespit ediliyor.
        AlandakiDegisim = float(abs(olasiGruplanmisKarakterler.DikdortgenAlani - karakter.DikdortgenAlani)) / float(karakter.DikdortgenAlani)
        GenislikdekiDegisim = float(abs(olasiGruplanmisKarakterler.DikdortgeninGenisligi - karakter.DikdortgeninGenisligi)) / float(karakter.DikdortgeninGenisligi)
        YukseklikdekiDegisim = float(abs(olasiGruplanmisKarakterler.DikdortgeninYuksekligi - karakter.DikdortgeninYuksekligi)) / float(karakter.DikdortgeninYuksekligi)

        #Hesaplanan değerlerin kontrolü yapılıyor.
        if (MesafeHesabi < (karakter.DikdortgenCevreHesabi * Maksimum_diagram_uzakligi) and
            KarakterAcisi < Maksimum_karakterlerarasi_aci and
            AlandakiDegisim < Maksimum_degisim_alani and
            GenislikdekiDegisim < Maksimum_degisim_genisligi and
            YukseklikdekiDegisim < Maksimum_degisim_yuksekligi):

            Karakterler.append(olasiGruplanmisKarakterler)  # Eğer Mesafe,açı ve değişim değerleri uyumluysa listeye ekleniyor.

        #if bitimi
    #for bitimi

    return Karakterler
#fonksiyon bitimi

def KarakterlerArasiUzaklikHesaplama(ilkKarakter,ikinciKarakter):
    #İki nokta arasındaki uzaklık hespalanırken pisagor bağlantısını kullanıyoruz.
    #(X2-X1)^2+(Y2-Y1)^2 formülü kullanılarak hesaplanır bulunan sonuc karakök içerisine alınarak karakterler arası mesafe hesaplanır
    intX = abs(ilkKarakter.XeksenininOrtasi - ikinciKarakter.XeksenininOrtasi)
    intY = abs(ilkKarakter.YeksenininOrtasi - ikinciKarakter.YeksenininOrtasi)

    return math.sqrt((intX ** 2) + (intY ** 2))
#fonksiyon bitimi

def AciHesapla(ilkKarakter,ikinciKarakter):
    Xnoktasi = float(abs(ilkKarakter.XeksenininOrtasi - ikinciKarakter.XeksenininOrtasi))
    Ynoktasi = float(abs(ilkKarakter.YeksenininOrtasi - ikinciKarakter.YeksenininOrtasi))

    # 0/0 belirsizliği oluşursa varsayılan olarak arctan 1,5708 olarak tanımlanıyor
    if Xnoktasi != 0.0:
        arcTanHesabi = math.atan(Ynoktasi / Xnoktasi)
    else:
        arcTanHesabi = 1.5708
    # if bitimi

    KarakterAcisi = arcTanHesabi * (180.0 / math.pi)  # Karakterler arası açı hesaplandı.

    return KarakterAcisi
#fonksiyon bitimi

def PlakayıTespitEt(Goruntu,karakterGrubu):
    PlakaGenisligiBoslugu = 1.3
    PlakaYuksekligiBoslugu = 1.5
    #Bu fonksiyonda gruplanmış karakterler listesindeki contoursların her birinin yerini tespit ediyoruz.
    #Tespit edilen contoursların karakter açıları hesaplanarak düzeltme işlemi yapılıyor.
    plaka=Plaka()

    karakterGrubu.sort(key = lambda karakterGrubu: karakterGrubu.XeksenininOrtasi)
    PlakaXEkseniOrtasi = (karakterGrubu[0].XeksenininOrtasi + karakterGrubu[len(karakterGrubu) - 1].XeksenininOrtasi) / 2.0
    PlakaYEkseniOrtasi = (karakterGrubu[0].YeksenininOrtasi + karakterGrubu[len(karakterGrubu) - 1].YeksenininOrtasi) / 2.0

    PlakaninOrtasi = PlakaXEkseniOrtasi, PlakaYEkseniOrtasi
    #Plakanın ortasını bulduk şimdi genişliğini ve yüksekliğini bulacağız.

    #Genişlik Bulmak için iki farklı method uygulanabilir
    #1)Toplam genişliğin bulunup karakter sayısına bölünmesi
    #2)Son elemanın x değeri-ilk elemanın x degeri+son elemanın genişliği
    PlakaGenisligi = int((karakterGrubu[len(karakterGrubu) - 1].DikdortgeninXdegeri + karakterGrubu[len(karakterGrubu) - 1].DikdortgeninGenisligi - karakterGrubu[0].DikdortgeninXdegeri) * PlakaGenisligiBoslugu)-25

    #Yukseklik Hesaplaması yapıyoruz.Tüm elemanların yükseklik değerlerinin toplamı ve eleman sayısına bölünmesi
    ToplamYukseklik = 0
    for karakter in karakterGrubu: #Tüm karakterleri geziyoruz
        ToplamYukseklik = ToplamYukseklik + karakter.DikdortgeninYuksekligi

    Gecici=ToplamYukseklik/len(karakterGrubu)
    PlakaYuksekligi= int(Gecici*PlakaYuksekligiBoslugu)-10

    #Karşı Kenarı ve Hipotenus hesaplamarı yapıyoruz.
    #Ve Sinus hesaplaması yaparak plakadaki açı kaymasını düzeltilecek açıyı buluyoruz.
    Karsi = karakterGrubu[len(karakterGrubu) - 1].YeksenininOrtasi - karakterGrubu[0].YeksenininOrtasi
    Hipotenus = KarakterlerArasiUzaklikHesaplama(karakterGrubu[0],karakterGrubu[len(karakterGrubu) - 1])
    DuzeltilecekAci = (math.asin(Karsi / Hipotenus)) * (180.0 / math.pi)

    #Plakanın sahnedeki yerini kayıt ediyoruz.
    plaka.PlakaninSahnedekiYeri = ( tuple(PlakaninOrtasi),(PlakaGenisligi,PlakaYuksekligi),DuzeltilecekAci)

    yukseklik, genislik, numChannels = Goruntu.shape  # Orjinal görüntü genişliğini ve yüksekliğini alıyoruz
    #Plakayı bulduğumuz düzeltilecek açıya göre dönderiyoruz
    PlakaDonder = cv2.warpAffine(Goruntu, (cv2.getRotationMatrix2D(tuple(PlakaninOrtasi), DuzeltilecekAci, 1.0)), (genislik, yukseklik))
    #Tüm görüntünün içerisinden sadece plakanın olduğu yeri alıyoruz.
    PlakaYeri = cv2.getRectSubPix(PlakaDonder, (PlakaGenisligi, PlakaYuksekligi), tuple(PlakaninOrtasi))
    #Bulduğumuz plakayı plaka resmine atıyoruz.
    plaka.PlakaResmi = PlakaYeri
    return plaka
#fonksiyon bitimi

def PlakadakiKarakterleriBul(PlakaListesi):
    #Plakanın yerini bulurken uyguladığımız methodları bulunan plaka üzerine uyguladığımızda
    #Plakada bulunan her bir karakteri tespit edebileceğiz.
    #Tespit ettiğimiz karakterin ne olduğunu KNN algoritması yardımıyla bulacağız.
    Contourslar=[]

    #Eğer Mevcut bit plaka yoksa üzerinde karakter arayamayacağımız için boş listeyi geri dönderiyoruz.
    if len(PlakaListesi) ==0:
        return PlakaListesi

    #Plakanın Treshold ve Griton Görüntüsünü buluyoruz.
    for plaka in PlakaListesi:
        plaka.PlakaGriton,plaka.PlakaTreshold = GritonVeTreshold(plaka.PlakaResmi)

        #Treshold resim yeniden boyutlanıyor
        plaka.PlakaTreshold = cv2.resize(plaka.PlakaTreshold, (0, 0), fx=1.6, fy=1.6)

        #Plaka dışındaki gri alanları yok etmek için tekrar treshold yapıyoruz.
        tresholddegeri, plaka.PlakaTreshold = cv2.threshold(plaka.PlakaTreshold, 0.0, 255.0,cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        #Daha öncedende kullandığımız counturları bulma fonksiyonu ile plakadaki countourları yani her bir karakteri buluyoruz.
        plakadakiKarakterler = GoruntudekiContourlariBul(plaka.PlakaTreshold)

        #Plakadaki gruplanmış karakterleri buluyoruz.
        gruplanmisKarakterler = GruplanmisKarakterleriBul(plakadakiKarakterler)

        #Eğer plakada gruplanmış karakter yoksa yazılacak bir yazı olmayacağından texti boş bırakıyoruz.
        if (len(gruplanmisKarakterler) == 0):
            plaka.textPlaka=""
            continue
        #if bitimi

        #Gruplanmış karakterler arasında iç içe geçmiş olanları bulup siliyoruz.
        for i in range(0, len(gruplanmisKarakterler)):
            gruplanmisKarakterler[i].sort(key = lambda karakterler: karakterler.XeksenininOrtasi)        # Karakterler soldan sağa sıralanıyor.
            gruplanmisKarakterler[i] = icicegecmisKarakterleriSil(gruplanmisKarakterler[i])              # İç içe geçmiş karakterler bulunup siliniyor.
        #for bitimi

        ListeUuzunlugu = 0
        ListeIndex = 0

        #Listeyi tek tek gezerek en uzun listeyi ve listenin genel listedeki indexini buluyoruz.
        for i in range(0, len(gruplanmisKarakterler)):
            if len(gruplanmisKarakterler[i]) > ListeUuzunlugu:
                ListeUuzunlugu = len(gruplanmisKarakterler[i])
                ListeIndex = i
            #if bitimi
        #for bitimi


        EnUzunGruplanmisKarakterler = gruplanmisKarakterler[ListeIndex]


        plaka.textPlaka = KarakterleriYaziOlarakBul(plaka.PlakaTreshold, EnUzunGruplanmisKarakterler)

    return PlakaListesi


def icicegecmisKarakterleriSil(gruplanmisKarakterler):
    #Bu fonksiyonun amacı iç içe geçmiş karakterleri temizlemek.
    #Örneğin D harfinin bir iç tarafındaki boşluk ve birde dış tarafı var
    #Bu harfin sadece bir tarafının contours olarak alınması lazım.
    Minumum_diagram_uzakligi = 0.3
    icicegemisleriSil=list(gruplanmisKarakterler)

    for mevcutKarakter in gruplanmisKarakterler:
        for digerKarakter in gruplanmisKarakterler:
            #Karakterler Aynı değilse
            if mevcutKarakter != digerKarakter:
                #Eğer Mevcut karakterin merkez noktası diğer karakterle nerdeyse aynıysa
                if KarakterlerArasiUzaklikHesaplama(mevcutKarakter, digerKarakter) < (mevcutKarakter.DikdortgenCevreHesabi * Minumum_diagram_uzakligi):
                    #İç içe geçmiş contoursların alanlarının karşılaştırmasını yapıp küçük olan contoursun silinmesi gerekiyor.
                    if mevcutKarakter.DikdortgenAlani < digerKarakter.DikdortgenAlani:
                        if mevcutKarakter in icicegemisleriSil:
                            icicegemisleriSil.remove(mevcutKarakter) #Mecvut karakterin alanı daha küçük olduğundan siliniyor.
                        #if bitimi
                    else:
                        if digerKarakter in icicegemisleriSil:
                            icicegemisleriSil.remove(digerKarakter)  #Diğer karakterin alanı daha küçük olduğundan siliniyor.
                        #if bitimi
                    #if bitimi
                #if bitimi
            #if bitimi
        #for bitimi
    #for bitimi

    return icicegemisleriSil
#fonksiyon bitimi

def KarakterleriYaziOlarakBul(Treshold, GruplanmisKarakterler):
    Karakter_Genisligi = 20
    Karakter_Yuksekligi = 30
    Yesil = (0.0, 255.0, 0.0)
    textKarakter = ""
    #Treshold resmin içerisindeki karakterlerin bulunduğu yerleri buluyoruz.
    height, width = Treshold.shape
    TresholdRengi = np.zeros((height, width, 3), np.uint8)
    #Karakterleri soldan sağa sıralıyoruz.
    GruplanmisKarakterler.sort(key = lambda karakter: karakter.XeksenininOrtasi)
    #Renk Ayarlaması yapıyoruz.
    cv2.cvtColor(Treshold, cv2.COLOR_GRAY2BGR, TresholdRengi)

    for mevcutKarakter in GruplanmisKarakterler:
        pt1 = (mevcutKarakter.DikdortgeninXdegeri, mevcutKarakter.DikdortgeninYdegeri)
        pt2 = ((mevcutKarakter.DikdortgeninXdegeri + mevcutKarakter.DikdortgeninGenisligi), (mevcutKarakter.DikdortgeninYdegeri + mevcutKarakter.DikdortgeninYuksekligi))

        cv2.rectangle(TresholdRengi, pt1, pt2, Yesil, 2)

        #Treshold Görüntü içerisinden karakterlerin olduğu kısmı buluyoruz.
        Kırp = Treshold[mevcutKarakter.DikdortgeninYdegeri : mevcutKarakter.DikdortgeninYdegeri + mevcutKarakter.DikdortgeninYuksekligi,
                           mevcutKarakter.DikdortgeninXdegeri : mevcutKarakter.DikdortgeninXdegeri + mevcutKarakter.DikdortgeninGenisligi]

        #Karakterleri tanıyabilmek için knn algoritmasının trainin datasında kullandığımız boyutlara göre karakterleri yeniden boyutlandırıyoruz.
        YenidenBoyutlandir = cv2.resize(Kırp, (Karakter_Genisligi, Karakter_Yuksekligi))

        #Numpy dizisine dönüştürebilmek için boyutlarını alıyoruz.
        DüzeltilmisGoruntu = YenidenBoyutlandir.reshape((1, Karakter_Genisligi * Karakter_Yuksekligi))

        #Numpy dizisine dönüştürüyoruz çünkü bizim training datamız numpy dizisi şeklinde.
        DüzeltilmisGoruntu = np.float32(DüzeltilmisGoruntu)

        #KNN algoritmasını çağırıyoruz.
        donusdegeri, yazi, komsu, mesafe = KNNAlgoritmasi.findNearest(DüzeltilmisGoruntu, k = 1)

        #KNN algoritmasıyla bulduğumuz karakterin string ifadesini alıyoruz.
        KarakterdekiMecvutYazi = str(chr(int(yazi[0][0])))

        #Soldan sağa tüm karakterleri değişkene ekliyoruz ve olası plakayı elde ettik.
        textKarakter = textKarakter + KarakterdekiMecvutYazi

    #for bitimi

    return textKarakter
#fonksiyon bitimi

def KNNVerileriniYukle():
    allContoursWithData = []
    validContoursWithData = []
    #Daha önce Oluşturduğumuz training dataları yüklüyoruz.
    try:
        YaziSinifi = np.loadtxt("siniflandirma.txt", np.float32)
        GoruntuDizisi = np.loadtxt("goruntudizisi.txt", np.float32)
    except:
        #Eğer Dosya okumada herhangi bir hata oluştuysa hata mesajı verip sistemi durduruyoruz.
        print("KNN algoritmasi yüklenirken sorun olustu lutfen dosyalari kontrol ediniz.\n")
        os.system("pause")
        return False
    #try cach bitimi

    #Daha önce numpy dizisine çevirdiğimiz plakayı train edebilmek için knn sınıflandırması ayarlıyoruz.
    YaziSinifi = YaziSinifi.reshape((YaziSinifi.size, 1))

    #Varsayılan K değerini ayarlıyoruz
    KNNAlgoritmasi.setDefaultK(3)

    #Verileri işliyoruz.
    KNNAlgoritmasi.train(GoruntuDizisi, cv2.ml.ROW_SAMPLE, YaziSinifi)

    #Eğer buraya geldiysek knn algoritması başarıyla tamamlanmış demektir.
    return True
#fonksiyon bitimi