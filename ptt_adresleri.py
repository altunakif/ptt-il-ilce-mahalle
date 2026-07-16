#!/usr/bin/env python3
"""PTT API'sinden il, ilçe, mahalle/köy ve posta kodu verisi indirir."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import unicodedata
from typing import Any

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_URL = "https://www.ptt.gov.tr/api/posta-kodu"
PAGE_URL = "https://www.ptt.gov.tr/posta-kodu"
DEFAULT_OUTPUT = "ptt_il_ilce_mahalle.json"
DEFAULT_DELAY = 0.25

# PTT sertifika zinciri bazı sistemlerde doğrulanamadığı için geçici olarak kapalıdır.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROVINCE_NAMES = [
    "ADANA", "ADIYAMAN", "AFYONKARAHİSAR", "AĞRI", "AMASYA", "ANKARA",
    "ANTALYA", "ARTVİN", "AYDIN", "BALIKESİR", "BİLECİK", "BİNGÖL",
    "BİTLİS", "BOLU", "BURDUR", "BURSA", "ÇANAKKALE", "ÇANKIRI",
    "ÇORUM", "DENİZLİ", "DİYARBAKIR", "EDİRNE", "ELAZIĞ", "ERZİNCAN",
    "ERZURUM", "ESKİŞEHİR", "GAZİANTEP", "GİRESUN", "GÜMÜŞHANE",
    "HAKKARİ", "HATAY", "ISPARTA", "MERSİN", "İSTANBUL", "İZMİR",
    "KARS", "KASTAMONU", "KAYSERİ", "KIRKLARELİ", "KIRŞEHİR", "KOCAELİ",
    "KONYA", "KÜTAHYA", "MALATYA", "MANİSA", "KAHRAMANMARAŞ", "MARDİN",
    "MUĞLA", "MUŞ", "NEVŞEHİR", "NİĞDE", "ORDU", "RİZE", "SAKARYA",
    "SAMSUN", "SİİRT", "SİNOP", "SİVAS", "TEKİRDAĞ", "TOKAT", "TRABZON",
    "TUNCELİ", "ŞANLIURFA", "UŞAK", "VAN", "YOZGAT", "ZONGULDAK",
    "AKSARAY", "BAYBURT", "KARAMAN", "KIRIKKALE", "BATMAN", "ŞIRNAK",
    "BARTIN", "ARDAHAN", "IĞDIR", "YALOVA", "KARABÜK", "KİLİS",
    "OSMANİYE", "DÜZCE",
]
PROVINCES = {index + 1: name for index, name in enumerate(PROVINCE_NAMES)}


def normalize_key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return "".join(ch.lower() for ch in text if ch.isalnum())


def clean_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def first_value(item: dict[str, Any], keys: list[str]) -> Any:
    normalized = {normalize_key(key): value for key, value in item.items()}
    for key in keys:
        value = normalized.get(normalize_key(key))
        if value is not None and (not isinstance(value, str) or value.strip()):
            return value
    return None


def extract_records(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data

    if isinstance(data, str):
        data = data.strip()
        if data.startswith(("[", "{")):
            try:
                return extract_records(json.loads(data))
            except json.JSONDecodeError:
                return []
        return []

    if not isinstance(data, dict):
        return []

    preferred = [
        "data", "result", "results", "items", "liste", "list", "ilceler",
        "ilçeler", "mahalleler", "postakodlari", "posta_kodlari",
    ]
    real_keys = {normalize_key(key): key for key in data}

    for key in preferred:
        real_key = real_keys.get(normalize_key(key))
        if real_key is not None:
            records = extract_records(data[real_key])
            if records:
                return records

    for value in data.values():
        records = extract_records(value)
        if records:
            return records

    return []


def item_to_dict(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return item
    if isinstance(item, (list, tuple)):
        result: dict[str, Any] = {}
        if len(item) > 0:
            result["id"] = item[0]
        if len(item) > 1:
            result["name"] = item[1]
        if len(item) > 2:
            result["posta_kodu"] = item[2]
        return result
    if isinstance(item, str):
        return {"name": item}
    return {"value": item}


def guess_name(item: dict[str, Any]) -> str:
    values = [
        value.strip()
        for value in item.values()
        if isinstance(value, str)
        and value.strip()
        and not value.strip().isdigit()
        and any(ch.isalpha() for ch in value)
    ]
    return max(values, key=len) if values else ""


def guess_code(item: dict[str, Any]) -> Any:
    for value in item.values():
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().isdigit() and len(value.strip()) != 5:
            return value.strip()
    return None


def guess_postal_code(item: dict[str, Any]) -> str | None:
    for value in item.values():
        value = clean_text(value)
        if len(value) == 5 and value.isdigit():
            return value
    return None


def is_placeholder(value: str) -> bool:
    return normalize_key(value) in {
        "", "seciniz", "ilceseciniz", "mahalleseciniz", "tum", "tumu"
    }


def normalize_district(raw: Any) -> dict[str, Any]:
    item = item_to_dict(raw)
    code = first_value(item, [
        "ilce_kodu", "ilçe_kodu", "ilce_id", "ilçe_id", "ilceId",
        "district_id", "district_code", "value", "kod", "code", "id",
    ])
    name = first_value(item, [
        "ilce_adi", "ilçe_adı", "ilce_ad", "ilceAdi", "district_name",
        "text", "label", "isim", "adi", "adı", "ad", "name", "ilce", "ilçe",
    ])
    return {
        "ilce_kodu": code if code is not None else guess_code(item),
        "ilce_adi": clean_text(name if name is not None else guess_name(item)),
    }


def normalize_neighborhood(raw: Any) -> dict[str, Any]:
    item = item_to_dict(raw)
    name = first_value(item, [
        "mahalle_adi", "mahalle_adı", "mahalle_ad", "mahalleAdi",
        "neighborhood_name", "text", "label", "isim", "adi", "adı",
        "ad", "name", "mahalle",
    ])
    postal_code = first_value(item, [
        "posta_kodu", "postaKodu", "postakodu", "postal_code", "postalCode",
        "zip_code", "zipcode", "pk",
    ])

    result: dict[str, Any] = {
        "mahalle_adi": clean_text(name if name is not None else guess_name(item))
    }
    postal_code = postal_code if postal_code is not None else guess_postal_code(item)
    if postal_code is not None:
        result["posta_kodu"] = clean_text(postal_code)
    if not result["mahalle_adi"]:
        result["ptt_ham_verisi"] = item
    return result


def deduplicate(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for record in records:
        identity = (
            normalize_key(record.get("mahalle_adi", "")),
            clean_text(record.get("posta_kodu")),
        )
        if identity not in seen:
            seen.add(identity)
            result.append(record)
    return result


def create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=5, pool_maxsize=5)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.verify = False
    session.headers.update({
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        "Content-Type": "application/json",
        "Origin": "https://www.ptt.gov.tr",
        "Referer": PAGE_URL,
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
        ),
    })
    return session


class PTTClient:
    def __init__(self, delay: float) -> None:
        self.delay = delay
        self.session = create_session()
        try:
            response = self.session.get(PAGE_URL, timeout=30, verify=False)
            print(f"PTT sayfası açıldı: HTTP {response.status_code}", file=sys.stderr)
        except requests.RequestException as error:
            print(f"PTT sayfası ön isteği başarısız: {error}", file=sys.stderr)

    def post(self, payload: dict[str, Any]) -> Any:
        response = self.session.post(API_URL, json=payload, timeout=45, verify=False)
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:1000]}")
        try:
            return response.json()
        except ValueError as error:
            raise RuntimeError(
                f"PTT API JSON olmayan bir cevap döndürdü: {response.text[:1000]}"
            ) from error

    def districts(self, province_code: int) -> list[Any]:
        response = self.post({"action": "ilceler", "il_kodu": str(province_code)})
        records = extract_records(response)
        if not records:
            raise RuntimeError(
                "İlçe listesi boş döndü: "
                + json.dumps(response, ensure_ascii=False)[:1500]
            )
        return records

    def neighborhoods(self, province_code: int, district_code: Any) -> list[Any]:
        response = self.post({
            "action": "postakodu",
            "il_kodu": str(province_code),
            "ilce_kodu": str(district_code),
        })
        return extract_records(response)


def save_json(data: list[dict[str, Any]], output_path: str) -> None:
    temporary_path = f"{output_path}.tmp"
    with open(temporary_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    os.replace(temporary_path, output_path)


def load_json(output_path: str) -> list[dict[str, Any]]:
    if not os.path.exists(output_path):
        return []
    try:
        with open(output_path, encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict) and isinstance(data.get("iller"), list):
            return [item for item in data["iller"] if isinstance(item, dict)]
    except (OSError, json.JSONDecodeError):
        pass
    return []


def scrape_province(client: PTTClient, code: int, name: str) -> dict[str, Any]:
    print(f"\n[{code:02d}] {name} ilçeleri alınıyor...", file=sys.stderr)
    districts = [normalize_district(item) for item in client.districts(code)]
    districts = [item for item in districts if not is_placeholder(item["ilce_adi"])]

    province: dict[str, Any] = {"il_kodu": code, "il_adi": name, "ilceler": []}
    for index, district in enumerate(districts, start=1):
        district_code = district["ilce_kodu"]
        district_name = district["ilce_adi"]
        print(
            f"  {index}/{len(districts)} {district_name or district_code} alınıyor...",
            file=sys.stderr,
        )

        output: dict[str, Any] = {
            "ilce_kodu": district_code,
            "ilce_adi": district_name,
            "mahalleler": [],
        }
        if district_code is None:
            output["hata"] = "İlçe kodu API cevabından tespit edilemedi."
            province["ilceler"].append(output)
            continue

        try:
            neighborhoods = [
                normalize_neighborhood(item)
                for item in client.neighborhoods(code, district_code)
            ]
            neighborhoods = [
                item for item in neighborhoods
                if not is_placeholder(item["mahalle_adi"])
            ]
            output["mahalleler"] = deduplicate(neighborhoods)
            print(f"    {len(output['mahalleler'])} kayıt bulundu.", file=sys.stderr)
        except Exception as error:  # Bir ilçedeki hata diğer ilçeleri durdurmasın.
            output["hata"] = str(error)
            print(f"    Hata: {error}", file=sys.stderr)

        province["ilceler"].append(output)
        time.sleep(client.delay)

    return province


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PTT'den il, ilçe, mahalle/köy ve posta kodu verilerini indirir."
    )
    parser.add_argument("--province", type=int, help="Plaka kodu. Örnek: 28")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="JSON çıktı dosyası")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    if args.province is not None and args.province not in PROVINCES:
        raise SystemExit("Hata: --province değeri 1 ile 81 arasında olmalıdır.")
    if args.delay < 0:
        raise SystemExit("Hata: --delay negatif olamaz.")

    output = load_json(args.output) if args.resume else []
    completed = {
        province.get("il_kodu") for province in output if isinstance(province, dict)
    }
    selected = (
        {args.province: PROVINCES[args.province]}
        if args.province is not None
        else PROVINCES
    )
    client = PTTClient(args.delay)

    try:
        for code, name in selected.items():
            if code in completed:
                print(f"[{code:02d}] {name} daha önce kaydedilmiş, atlanıyor.", file=sys.stderr)
                continue
            try:
                output.append(scrape_province(client, code, name))
            except Exception as error:
                print(f"\n{name} alınamadı: {error}", file=sys.stderr)
                output.append({"il_kodu": code, "il_adi": name, "ilceler": [], "hata": str(error)})
            save_json(output, args.output)
            print(f"  Ara kayıt oluşturuldu: {args.output}", file=sys.stderr)
            time.sleep(args.delay)
    except KeyboardInterrupt:
        print("\nİşlem durduruldu; mevcut veriler kaydediliyor...", file=sys.stderr)
        save_json(output, args.output)
        raise SystemExit(130)

    save_json(output, args.output)
    print(
        f"\nİşlem tamamlandı.\nKaydedilen il sayısı: {len(output)}\n"
        f"Çıktı dosyası: {args.output}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
