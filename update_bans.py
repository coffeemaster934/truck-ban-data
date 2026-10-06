import json
from datetime import datetime
import urllib.request

def fetch_holidays(country_code, year):
    """Stáhne oficiální svátky pro danou zemi a rok z veřejného API."""
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data
    except Exception as e:
        print(f"Chyba při stahování svátků pro {country_code}: {e}")
    return []

def main():
    file_path = 'bans.json'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Soubor bans.json nebyl nalezen, vytvářím nový základ.")
        data = {"version": 1, "countries": {}}

    current_year = datetime.now().year
    countries = ["DE", "AT", "FR", "CZ", "IT", "PL", "SK", "HU"]

    if "countries" not in data:
        data["countries"] = {}

    for code in countries:
        print(f"Aktualizuji svátky pro {code}...")
        holidays = fetch_holidays(code, current_year)
        
        if code not in data["countries"]:
            data["countries"][code] = {"country_name": code, "holiday_bans": []}
            
        # Převedeme stažené svátky do našeho formátu pro aplikaci
        formatted_holidays = []
        for h in holidays:
            formatted_holidays.append({
                "date": h.get("date"),
                "name": h.get("localName") or h.get("name"),
                "time": "00:00 - 22:00" # Standardní celodenní zákaz o svátcích
            })
        
        data["countries"][code]["holiday_bans"] = formatted_holidays

    # Aktualizujeme datum poslední automatické aktualizace
    data['last_updated'] = datetime.now().strftime('%Y-%m-%d')

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Skript úspěšně aktualizoval bans.json k datu: {data['last_updated']}")

if __name__ == '__main__':
    main()import json
from datetime import datetime

def main():
    file_path = 'bans.json'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Soubor bans.json nebyl nalezen.")
        return

    # Aktualizujeme datum poslední kontroly/aktualizace na dnešek
    today_str = datetime.now().strftime('%Y-%m-%d')
    data['last_updated'] = today_str
    
    # Zde můžeme v budoucnu doplnit parsování nebo stahování z webů

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Data byla úspěšně zkontrolována a aktualizována k datu: {today_str}")

if __name__ == '__main__':
    main()
