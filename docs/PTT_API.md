# PTT API Notları

## Uç nokta

```text
POST https://www.ptt.gov.tr/api/posta-kodu
```

İstekler JSON gövdesiyle gönderilir.

## İlçe sorgusu

```json
{
  "action": "ilceler",
  "il_kodu": "28"
}
```

- `il_kodu`: 1–81 arasındaki plaka kodudur.
- Cevapta seçim alanı için kullanılan `Seçiniz` kaydı bulunabilir; script bu kaydı dışarıda bırakır.
- PTT'nin döndürdüğü ilçe kodu sonraki sorguda `ilce_kodu` olarak kullanılır.

## Mahalle ve posta kodu sorgusu

```json
{
  "action": "postakodu",
  "il_kodu": "28",
  "ilce_kodu": "1133"
}
```

Cevap, mahalle veya köy adıyla birlikte posta kodunu içerir. Script cevap alanlarının farklı yazım biçimlerini desteklemek için alan adlarını normalize eder.

## HTTP başlıkları

Script tarayıcı isteğine yakın aşağıdaki başlıkları gönderir:

- `Accept: application/json, text/plain, */*`
- `Content-Type: application/json`
- `Origin: https://www.ptt.gov.tr`
- `Referer: https://www.ptt.gov.tr/posta-kodu`
- `X-Requested-With: XMLHttpRequest`

API çağrılarından önce posta kodu sayfası açılarak varsa oturum çerezleri alınır.

## Dayanıklılık

- 429, 500, 502, 503 ve 504 cevaplarında yeniden deneme yapılır.
- Her il tamamlandığında JSON dosyası atomik olarak güncellenir.
- `--resume`, JSON dosyasında bulunan `il_kodu` değerlerini tamamlanmış kabul eder.

## Bilinen sınırlamalar

1. API resmî olarak belgelenmediği için `action` adları veya cevap alanları değişebilir.
2. PTT sertifika zinciri bazı istemcilerde doğrulanamadığından scriptte geçici olarak `verify=False` kullanılır.
3. Çıktıdaki `ilce_kodu`, PTT'nin iç kodudur; plaka kodu değildir.
4. PTT cevabında köy kayıtları da mahalle listesi içinde yer alabilir.
5. Veriler kullanılmadan önce posta kodu biçimi ve boş alanlar doğrulanmalıdır.
