# PO Generator - Purchase Order Automation

Tedarikçi tekliflerinden otomatik olarak Purchase Order (PO) belgesi oluşturan Python scripti.

## Ne Yapar?

1. Klasördeki teklif dosyasını (PDF/Word/Excel) okur
2. Claude API ile tedarikçi adı, fiyat, ödeme koşulları gibi bilgileri çıkarır
3. `PO_TEMPLATE.docx` şablonunu doldurarak Word PO belgesi oluşturur
4. Word'ü PDF'e çevirir ve teklif ile birleştirip tek bir PDF yapar

## Kurulum

### 1. Python Bağımlılıkları

```bash
pip install anthropic python-docx pypdf pdfplumber openpyxl pandas docx2pdf
```

### 2. ANTHROPIC_API_KEY

Script, Claude API kullanır. API key'inizi ortam değişkeni olarak tanımlayın:

```bash
# Windows (kalıcı):
setx ANTHROPIC_API_KEY "sk-ant-api03-..."

# Windows (geçici, sadece bu terminal):
set ANTHROPIC_API_KEY=sk-ant-api03-...
```

API key almak için: https://console.anthropic.com/

### 3. Microsoft Word

PDF dönüşümü için Microsoft Word yüklü olmalıdır (`docx2pdf` Word COM automation kullanır).

## Kullanım

1. Klasöre tek bir teklif dosyası (PDF, DOCX, XLSX) koyun — dosya adında **"PO" geçmemeli**
2. Scripti çalıştırın:

```bash
python po_generator.py
```

3. Klasörde iki yeni dosya oluşur:
   - `547_08022026 PO for Ring Joint Gaskets.docx` — Word PO belgesi
   - `547_08022026 PO for Ring Joint Gaskets.pdf` — PO + teklif birleşik PDF

## Klasör Yapısı

```
PO Oluşturma/
├── PO_TEMPLATE.docx          ← Şablon (değiştirmeyin)
├── po_generator.py            ← Script
├── 545_30012026 PO for ...    ← Eski PO'lar (numaralama için kullanılır)
└── yeni_teklif.pdf            ← İşlenecek teklif dosyası
```

## PO Numaralama

Script klasördeki mevcut PO dosyalarının numaralarını tarar ve en yüksek numaraya +1 ekler. İlk çalıştırmada `001`'den başlar.

## Şablon Placeholder'ları

| Placeholder | Açıklama |
|---|---|
| `{{DATE}}` | Tarih (DD.MM.YYYY) |
| `{{SUPPLIER}}` | Tedarikçi firma adı |
| `{{ATTN}}` | İlgili kişi |
| `{{PO_NO}}` | PO numarası |
| `{{SUBJECT}}` | Konu (3-5 kelime) |
| `{{DELIVERY_TIME}}` | Teslimat süresi |
| `{{PAYMENT_TERM}}` | Ödeme koşulları |
| `{{DELIVERY_TERM}}` | Teslimat koşulları |
| `{{TOTAL_PRICE}}` | Toplam fiyat |
