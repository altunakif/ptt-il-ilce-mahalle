# PTT İl–İlçe–Mahalle Veri Çekici

PTT'nin posta kodu sayfasında kullanılan API üzerinden Türkiye'nin il, ilçe, mahalle/köy ve posta kodu verilerini JSON olarak indirir.

> Bu servis PTT tarafından herkese açık biçimde belgelenmiş bir API değildir. İstek yapısı veya cevap alanları ileride değişebilir.

## Özellikler

- 81 ili veya yalnızca seçilen bir ili çeker.
- İlçeleri ve her ilçenin mahalle/posta kodu kayıtlarını indirir.
- Sonucu sade, hiyerarşik JSON olarak kaydeder.
- `mahalle_kodu` üretmez.
- Her il tamamlandığında ara kayıt alır.
- `--resume` ile tamamlanan illeri atlayarak devam eder.
- Geçici ağ hatalarında otomatik yeniden dener.

## Gereksinimler

- Python 3.10 veya üzeri
- `requests`
- `urllib3`

## Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Kullanım

### Yalnızca Giresun

```bash
python ptt_adresleri.py \
  --province 28 \
  --output giresun.json
```

### Tüm Türkiye

```bash
python ptt_adresleri.py \
  --output turkiye_il_ilce_mahalle.json
```

### Yarıda kalan işleme devam etme

```bash
python ptt_adresleri.py \
  --output turkiye_il_ilce_mahalle.json \
  --resume
```

### İstekler arasındaki bekleme süresini değiştirme

```bash
python ptt_adresleri.py \
  --output turkiye_il_ilce_mahalle.json \
  --delay 0.5
```

## JSON çıktısı

Çıktının kökünde doğrudan il listesi bulunur. Kaynak, tarih veya SSL açıklaması gibi üst seviye metadata eklenmez.

```json
[
  {
    "il_kodu": 28,
    "il_adi": "GİRESUN",
    "ilceler": [
      {
        "ilce_kodu": "1133",
        "ilce_adi": "ALUCRA",
        "mahalleler": [
          {
            "mahalle_adi": "AKÇİÇEK KÖYÜ",
            "posta_kodu": "28700"
          }
        ]
      }
    ]
  }
]
```

Çıktının biçimsel tanımı [`schemas/output.schema.json`](schemas/output.schema.json) dosyasındadır.

## Kullanılan PTT istekleri

İlçeler:

```json
{
  "action": "ilceler",
  "il_kodu": "28"
}
```

Mahalle ve posta kodları:

```json
{
  "action": "postakodu",
  "il_kodu": "28",
  "ilce_kodu": "1133"
}
```

Ayrıntılar için [`docs/PTT_API.md`](docs/PTT_API.md) dosyasına bakın.

## Veritabanı

PostgreSQL şeması:

- [`database/schema.sql`](database/schema.sql)

Prisma şeması:

- [`database/schema.prisma`](database/schema.prisma)

Veri eşlemesi ve içe aktarma notları:

- [`docs/DATABASE.md`](docs/DATABASE.md)

## SSL uyarısı

PTT'nin sunduğu sertifika zinciri bazı Ubuntu/Python kurulumlarında `unable to get local issuer certificate` hatasına yol açtığı için bu scriptte SSL sertifika doğrulaması geçici olarak kapatılmıştır.

Bu kullanım yalnızca tek seferlik veri indirme işlemi içindir. `verify=False` yaklaşımı üretim backend'ine taşınmamalıdır. Üretimde veri bir kez doğrulanıp veritabanına alınmalı ve uygulama PTT'ye her kullanıcı isteğinde doğrudan bağlanmamalıdır.
