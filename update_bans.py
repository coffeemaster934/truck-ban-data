import json
from datetime import datetime
import urllib.request
import hashlib

def fetch_holidays(country_code, year):
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Chyba při stahování svátků pro {country_code}: {e}")
    return []

def get_hash(content):
    return hashlib.md5(json.dumps(content, sort_keys=True).encode('utf-8')).hexdigest()

def main():
    file_path = 'bans.json'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    except FileNotFoundError:
        old_data = {"version": 1, "countries": {}}

    current_year = datetime.now().year
    countries = ["DE", "AT", "FR", "CZ", "IT", "PL", "SK", "HU"]

    new_countries_data = {}
    for code in countries:
        holidays = fetch_holidays(code, current_year)
        formatted_holidays = []
        for h in holidays:
            formatted_holidays.append({
                "date": h.get("date"),
                "name": h.get("localName") or h.get("name"),
                "time": "00:00 - 22:00"
            })
        
        new_countries_data[code] = {
            "country_name": code,
            "holiday_bans": formatted_holidays
        }

    new_data = {
        "version": old_data.get("version", 1),
        "last_updated": datetime.now().strftime('%Y-%m-%d'),
        "countries": new_countries_data
    }

    # Porovnáme hash starých a nových dat (bez data posledního update)
    old_check = dict(old_data)
    old_check.pop("last_updated", None)
    new_check = dict(new_data)
    new_check.pop("last_updated", None)

    if get_hash(old_check) == get_hash(new_check):
        print("Žádné změny v datech nebyly detekovány. Soubor se nemění.")
        return

    # Pokud se data liší, uložíme novou verzi
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    print(f"Zjištěny změny! bans.json byl aktualizován k datu: {new_data['last_updated']}")

if __name__ == '__main__':
    main()
