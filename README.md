# PO Generator - Evrensel Satın Alma Otomasyonu (V2)

Tedarikçi tekliflerinden (PDF/Word/Excel) otomatik olarak Purchase Order (PO) belgesi oluşturan, yapay zeka destekli masaüstü uygulaması.

## Özellikler

- **Evrensel Şablon Desteği:** Herhangi bir şirketin PO formatını tek bir örnek PDF'ten öğrenir ve birebir taklit eder.
- **Yüksek Sadakatli PDF:** HTML/CSS tablo düzeni kullanarak milimetrik hassasiyette, kayma yapmayan PDF'ler üretir.
- **Çoklu AI Desteği:** Claude (Anthropic), GPT-4 (OpenAI) veya Gemini (Google) modelleri ile çalışabilir.
- **Kompakt Tasarım:** Orijinal belgenin sayfa yapısını ve yoğunluğunu korur, gereksiz sayfa taşmalarını engeller.
- **Otomatik Birleştirme:** Oluşturulan PO'nun sonuna orijinal tedarikçi teklifini otomatik olarak ekler.

## Kurulum

### 1. Bağımlılıklar
Aşağıdaki kütüphanelerin yüklü olduğundan emin olun:
```bash
pip install anthropic openai google-generativeai python-dotenv pdfplumber pillow python-docx openpyxl jinja2 pypdf
```

### 2. Microsoft Edge
PDF üretimi için sisteminizde Microsoft Edge yüklü olmalıdır (Windows 10/11'de varsayılan olarak gelir).

## Kullanım

1. **Uygulamayı Başlatın:**
   ```bash
   python main.py
   ```
2. **İlk Kurulum (Setup):** Program ilk açılışta sizden bir örnek PO PDF'i ve API anahtarınızı isteyecektir. Bu aşamada AI, şirket formatınızı öğrenir.
3. **PO Oluşturma:** Ana ekrana teklif dosyasını sürükleyin veya seçin, "Analiz Et" butonuna basın. Gelen verileri kontrol edip onayladığınızda PO'nuz hazır!

## Dosya Yapısı

- `main.py`: Uygulama giriş noktası.
- `core/`: Analiz, çıkarma ve PDF üretim motorları.
- `gui/`: Kullanıcı arayüzü ekranları.
- `po_template.html`: AI tarafından oluşturulan görsel şablonunuz.
- `po_fields.json`: Şablonunuzdaki değişken alanların manifestosu.
- `.env`: API anahtarlarınız ve model ayarlarınız (Gizli tutulmalıdır).
