# Veritabanı Tasarımı

Bu veri kümesi için üç seviyeli bir yapı kullanılır:

```text
Province 1 ─── N District 1 ─── N Neighborhood
```

## Tablolar

### `provinces`

| Alan | Tip | Açıklama |
|---|---|---|
| `code` | `SMALLINT` | Plaka kodu, birincil anahtar |
| `name` | `VARCHAR(100)` | İl adı |
| `created_at` | `TIMESTAMPTZ` | Oluşturulma zamanı |
| `updated_at` | `TIMESTAMPTZ` | Güncellenme zamanı |

### `districts`

| Alan | Tip | Açıklama |
|---|---|---|
| `id` | `BIGSERIAL` | Uygulama içi birincil anahtar |
| `ptt_code` | `INTEGER` | PTT'nin döndürdüğü ilçe kodu |
| `province_code` | `SMALLINT` | İl ilişkisi |
| `name` | `VARCHAR(100)` | İlçe adı |
| `created_at` | `TIMESTAMPTZ` | Oluşturulma zamanı |
| `updated_at` | `TIMESTAMPTZ` | Güncellenme zamanı |

### `neighborhoods`

| Alan | Tip | Açıklama |
|---|---|---|
| `id` | `BIGSERIAL` | Uygulama içi birincil anahtar |
| `district_id` | `BIGINT` | İlçe ilişkisi |
| `name` | `VARCHAR(180)` | Mahalle veya köy adı |
| `postal_code` | `CHAR(5)` | Beş haneli posta kodu |
| `created_at` | `TIMESTAMPTZ` | Oluşturulma zamanı |
| `updated_at` | `TIMESTAMPTZ` | Güncellenme zamanı |

## JSON alanlarının eşlenmesi

| JSON | Veritabanı |
|---|---|
| `il_kodu` | `provinces.code` |
| `il_adi` | `provinces.name` |
| `ilce_kodu` | `districts.ptt_code` |
| `ilce_adi` | `districts.name` |
| `mahalle_adi` | `neighborhoods.name` |
| `posta_kodu` | `neighborhoods.postal_code` |

## Güncelleme stratejisi

Veriler toplu olarak alınmalı ve tek transaction içinde `upsert` edilmelidir:

1. İl, `code` üzerinden eklenir veya güncellenir.
2. İlçe, `ptt_code` üzerinden eklenir veya güncellenir.
3. Mahalle/köy, `district_id + name + postal_code` bileşimi üzerinden eklenir veya güncellenir.
4. İçe aktarım tamamlandıktan sonra kaynakta artık bulunmayan kayıtlar doğrudan silinmek yerine önce pasif duruma alınabilir.

## Doğrulama kuralları

- İl kodu 1–81 arasında olmalıdır.
- İlçe kodu sayısal olmalıdır.
- İl, ilçe ve mahalle adları boş olmamalıdır.
- Posta kodu tam olarak beş rakamdan oluşmalıdır.
- Aynı ilçe içinde aynı ad ve posta koduna sahip kayıt tekrar eklenmemelidir.

## Uygulama entegrasyonu

Bir kullanıcının veya kuruluşun konumu mahalle seviyesinde tutulacaksa konum tablosunda `neighborhood_id` kullanılabilir. Yalnızca il/ilçe seçimi yeterliyse `district_id` zorunlu, `neighborhood_id` isteğe bağlı tutulmalıdır.

Örnek ilişki:

```text
Location
- owner_id
- district_id
- neighborhood_id (nullable)
- address_line
- latitude
- longitude
```

PTT'ye her kullanıcı formu açılışında istek göndermek yerine veriler PostgreSQL'e alınmalı ve kullanıcı arayüzü uygulamanın kendi API'sinden beslenmelidir.
