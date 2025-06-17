"""Скрипт для сбора объявлений с сайта Encar по всем маркам, моделям и комплектациям.
Полученные данные за указанный период выгружаются в Google Sheets."""

import os
import re
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
from googletrans import Translator
import gspread
from google.oauth2.service_account import Credentials


def get_api_base() -> str:
    """Определить базовый адрес API, анализируя стартовую страницу."""
    global _API_BASE
    if _API_BASE:
        return _API_BASE
    try:
        resp = requests.get(BASE_URL, timeout=30)
        resp.raise_for_status()
        m = re.search(r"RYVUSS_BASE_END_POINT\s*=\s*'([^']+)'", resp.text)
        if m:
            _API_BASE = m.group(1)
        else:
            _API_BASE = "https://api.encar.com"
    except Exception:
        _API_BASE = "https://api.encar.com"
    return _API_BASE

# Базовый URL поиска (будет получен автоматически из первой страницы)
BASE_URL = "https://www.encar.com/fc/fc_carsearchlist.do"
_API_BASE: str | None = None

# Константы периода выбора машин
START_YEAR = 2020
START_MONTH = 8
END_YEAR = 2022
END_MONTH = 8


def fetch_brands() -> List[Dict[str, str]]:
    """Получить список марок автомобилей."""
    base = get_api_base()
    resp = requests.get(f"{base}/api/public/car/maker")
    resp.raise_for_status()
    return resp.json().get("makerList", [])


def fetch_models(maker_code: str) -> List[Dict[str, str]]:
    """Получить список моделей для указанной марки."""
    base = get_api_base()
    resp = requests.get(
        f"{base}/api/public/car/model",
        params={"makerCode": maker_code},
    )
    resp.raise_for_status()
    return resp.json().get("modelList", [])


def fetch_trims(model_code: str) -> List[Dict[str, str]]:
    """Получить список комплектаций для выбранной модели."""
    base = get_api_base()
    resp = requests.get(
        f"{base}/api/public/car/trim",
        params={"modelCode": model_code},
    )
    resp.raise_for_status()
    return resp.json().get("trimList", [])


def fetch_listings(maker: str, model: str, trim: str, page: int = 1) -> List[Dict[str, str]]:
    """Загрузить список объявлений для конкретной комплектации."""
    params = {
        "carType": "for",
        "searchType": "manufacturer",
        "page": page,
        "limit": 20,
        "makerCode": maker,
        "modelCode": model,
        "trimCode": trim,
        "yearFrom": START_YEAR,
        "yearTo": END_YEAR,
        "loginCheck": "false",
        "sort": "ModifiedDate",
    }
    base = get_api_base()
    search_url = f"{base}/search/car/list"  # API поиска объявлений
    resp = requests.get(search_url, params=params, timeout=30)
    resp.raise_for_status()
    # Предполагается, что сервер возвращает JSON
    try:
        data = resp.json()
    except ValueError:
        # Если пришёл HTML, разбираем его парсером
        data = parse_listings(resp.text)
        return data
    return data.get("searchResult", {}).get("list", [])


def within_range(year: int, month: int) -> bool:
    """Проверяет, попадает ли дата выпуска в указанный период."""
    start = START_YEAR * 100 + START_MONTH
    end = END_YEAR * 100 + END_MONTH
    current = year * 100 + month
    return start <= current <= end


def parse_listings(html: str) -> List[Dict[str, str]]:
    """Резервный парсер HTML на случай отсутствия JSON."""
    soup = BeautifulSoup(html, "html.parser")
    listings = []
    for item in soup.select("ul.list li"):
        title_elem = item.select_one("span.model")
        price_elem = item.select_one("span.price")
        year_elem = item.select_one("span.year")
        if not (title_elem and price_elem and year_elem):
            continue
        listings.append(
            {
                "title": title_elem.get_text(strip=True),
                "price": price_elem.get_text(strip=True),
                "year": year_elem.get_text(strip=True),
            }
        )
    return listings


def translate_listings(listings: List[Dict[str, str]]) -> None:
    """Перевод текстовых полей на английский язык."""
    translator = Translator()
    for listing in listings:
        listing["title_en"] = translator.translate(listing["title"], src="ko", dest="en").text


def append_to_sheet(creds_file: str, spreadsheet: str, listings: List[Dict[str, str]]) -> None:
    """Добавить строки с объявлениями в таблицу Google."""
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open(spreadsheet).sheet1

    if sheet.row_count == 0:
        sheet.append_row(["Title", "Year", "Price", "Title (EN)"])

    for listing in listings:
        sheet.append_row([
            listing.get("title"),
            listing.get("year"),
            listing.get("price"),
            listing.get("title_en"),
        ])


def gather_all_listings() -> List[Dict[str, str]]:
    """Проходит по всем комбинациям марка/модель/комплектация и собирает данные."""
    result: List[Dict[str, str]] = []
    for brand in fetch_brands():
        maker_code = brand.get("code")
        for model in fetch_models(maker_code):
            model_code = model.get("code")
            for trim in fetch_trims(model_code):
                trim_code = trim.get("code")
                page = 1
                while True:
                    items = fetch_listings(maker_code, model_code, trim_code, page)
                    if not items:
                        break
                    for item in items:
                        year = int(item.get("year", 0))
                        month = int(item.get("month", 1))
                        if within_range(year, month):
                            result.append(item)
                    page += 1
    return result


def main() -> None:
    # Получение всех объявлений за период и выгрузка в Google Sheets
    listings = gather_all_listings()
    translate_listings(listings)
    creds_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
    spreadsheet = os.environ.get("SPREADSHEET_NAME", "Encar Listings")
    append_to_sheet(creds_file, spreadsheet, listings)


if __name__ == "__main__":
    main()
