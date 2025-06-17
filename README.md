# Encar Listings Parser

This repository provides a simple script to collect car listings from [Encar](https://www.encar.com/) and store them in a Google Sheet. The text values are automatically translated from Korean to English.

## Prerequisites

- Python 3.8+
- A Google service account JSON credentials file (set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable or place the file at `credentials.json`).
- An existing Google Spreadsheet (set the `SPREADSHEET_NAME` environment variable with its name).

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the parser:

```bash
python encar_parser.py
```

The script automatically iterates over all available brands, models and trims, collecting listings for vehicles produced between **August 2020** and **August 2022**. It first reads the Encar start page to determine the API base URL (`RYVUSS_BASE_END_POINT`). Parsed data are appended to the first worksheet of the specified spreadsheet.

## Notes

- Network restrictions may block access to `encar.com`. Ensure that the environment has permission to reach the site before running the script.
- CSS selectors in `encar_parser.py` may require adjustments if the website structure changes.

## Инструкция на русском

1. Установите зависимости командой `pip install -r requirements.txt`.
2. Сохраните JSON-файл учетных данных сервисного аккаунта Google и укажите путь к нему в переменной окружения `GOOGLE_APPLICATION_CREDENTIALS` (или поместите файл как `credentials.json`).
3. Задайте имя целевой таблицы в переменной окружения `SPREADSHEET_NAME`.
4. Запустите скрипт `python encar_parser.py`. Скрипт автоматически проходит по всем маркам, моделям и комплектациям, собирая объявления за период с августа 2020 года по август 2022 года и добавляя данные в таблицу. Перед началом работы скрипт считывает со стартовой страницы значение `RYVUSS_BASE_END_POINT`, чтобы узнать адрес API.
