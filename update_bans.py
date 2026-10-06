import json
from datetime import datetime
import urllib.request
import hashlib

def fetch_holidays(country_code, year):
    """Stáhne státní svátky z veřejného API."""
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Chyba při stahování svátků pro {country_code}: {e}")
    return []

def get_german_summer_bans(year):
    """Vrací oficiální sobotní letní prázdninové zákazy v Německu (dle předpisů BAG)."""
    # Německé letní zákazy platí pro soboty v červenci a srpnu od 7:00 do 20:00 na vybraných tazích
    return {
        "active": True,
        "period": f"{year}-07-01 to {year}-08-31",
        "days": ["Saturday"],
        "time": "07:00 - 20:00",
        "note": "Platí na dálnicích a vybraných silnicích 1. třídy dle nařízení BAG (nad 7.5t a přívěsy)."
    }

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
        
        country_obj = {
            "country_name": code,
            "holiday_bans": formatted_holidays
        }

        # Pokud jde o Německo, přihodíme rovnou i speciální letní prázdninové zákazy BAG
        if code == "DE":
            country_obj["special_summer_ban"] = get_german_summer_bans(current_year)

        new_countries_data[code] = country_obj

    new_data = {
        "version": old_data.get("version", 1),
        "last_updated": datetime.now().strftime('%Y-%m-%d'),
        "countries": new_countries_data
    }

    # Porovnání hashů, zda se něco změnilo
    old_check = dict(old_data)
    old_check.pop("last_updated", None)
    new_check = dict(new_data)
    new_check.pop("last_updated", None)

    if get_hash(old_check) == get_hash(new_check):
        print("Žádné změny v datech nebyly detekovány.")
        return

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    print(f"Data byla úspěšně aktualizována včetně mimořádných zákazů k datu: {new_data['last_updated']}")

if __name__ == '__main__':
    main()
