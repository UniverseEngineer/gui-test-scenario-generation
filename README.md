---Mobil Uygulama Arayüzündeki Componentlerin Tespiti---

Bu projede herhangi bir mobil uygulamaya ait arayüzdeki Componentlerin tespit edilmesi amaçlanmıştır. Proje ileride otomatik test senaryoları oluşturmak adına bir ön adımdır.

Komponentlerin tespiti 2 bölümden oluşur:

1. Metin için algılama gerçekleştirmek üzere OCR'den yararlanır .

2. Grafik öğeleri bulmak için CV yaklaşımlarını ve sınıflandırma için CNN sınıflandırıcısını kullanır.

BAĞIMLILIKLAR:

1. Python 3.9
2. Opencv 3.4.2
3. Pandas

KULLANIM:

Kendi mobil uygulama arayüzü görüntünüzü test etmek için "run_single.py" içerisindeki "input_path_img" değerini değiştiriniz.
Test edilecek görüntü "data" klasöründeki input klasörü içerisine eklenmelidir. 

MODEL:

Eğitilmiş modeli [bu linkten](https://drive.google.com/drive/folders/1ecB127vE_VKMygf9mHcvU_gfA0-XgKKi?usp=drive_link) indirebilirsiniz.

