import json
from datetime import datetime
import urllib.request
import hashlib

def fetch_holidays(country_code, year):
    """Stáhne státní svátky z veřejného API pro danou zemi a rok."""
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Chyba při stahování svátků pro {country_code}: {e}")
    return []

def get_country_rules(code, year):
    """Vrací detailní pravidla pro víkendové, noční a prázdninové zákazy pro evropské státy."""
    rules = {}
    
    if code == "DE":
        rules["standard_weekend_ban"] = {
            "active": True, "days": ["Sunday"], "time": "00:00 - 22:00", "vehicles": "nad 7.5t a přívěsy"
        }
        rules["summer_ban"] = {
            "active": True, "period": f"{year}-07-01 to {year}-08-31", "days": ["Saturday"], "time": "07:00 - 20:00", "note": "Prázdninový zákaz na vybraných dálnicích (nařízení BAG)"
        }
    elif code == "AT":
        rules["standard_weekend_ban"] = {
            "active": True, "days": ["Saturday", "Sunday"], "time": "So 15:00 - Ne 22:00", "vehicles": "nad 7.5t"
        }
        rules["night_ban"] = {
            "active": True, "time": "22:00 - 05:00", "vehicles": "nad 7.5t (Inntalautobahn A12 a vybrané úseky)"
        }
    elif code == "FR":
        rules["standard_weekend_ban"] = {
            "active": True, "days": ["Saturday", "Sunday"], "time": "So 22:00 - Ne 22:00", "vehicles": "nad 7.5t"
        }
        rules["summer_ban"] = {
            "active": True, "period": f"{year}-07-01 to {year}-08-31", "days": ["Saturday"], "time": "07:00 - 19:00", "note": "Celostátní prázdninové zákazy (černé/červené soboty Bison Futé)"
        }
    elif code == "IT":
        rules["standard_weekend_ban"] = {
            "active": True, "days": ["Sunday"], "time": "09:00 - 22:00", "vehicles": "nad 7.5t"
        }
        rules["summer_ban"] = {
            "active": True, "period": f"{year}-06-01 to {year}-09-01", "days": ["Sunday", "vybrané sobory"], "time": "Různé (často 07:00 - 22:00)", "note": "Rozšířené letní zákazy pro tranzit k moři"
        }
    elif code == "CZ":
        rules["standard_weekend_ban"] = {
            "active": True, "days": ["Sunday"], "time": "13:00 - 22:00", "vehicles": "nad 7.5t"
        }
        rules["summer_ban"] = {
            "active": True, "period": f{year}-07-01 to {year}-08-31", "days": ["Friday", "Saturday", "Sunday"], "time": "Pá 17:00-21:00, So 07:00-13:00, Ne 13:00-22:00", "note": "Prázdninový provoz (vybrané silnice I. třídy a dálnice)"
        }
    elif code == "SK":
        rules["standard_weekend_ban"] = {
            "active": True, "days": ["Sunday"], "time": "00:00 - 22:00", "vehicles": "nad 7.5t s přívěsem"
        }
    elif code == "PL":
        rules["standard_weekend_ban"] = {
            "active": True, "days": ["Sunday"], "time": "08:00 - 22:00", "vehicles": "nad 12t"
        }
        rules["summer_ban"] = {
            "active": True, "period": f"{year}-06-25 to {year}-08-31", "days": ["Friday", "Saturday", "Sunday"], "time": "Pá 18-22, So 08-14, Ne 08-22", "note": "Letní prázdninová omezení pro nákladní vozidla nad 12t"
        }
    elif code == "HU":
        rules["standard_weekend_ban"] = {
            "active": True, "days": ["Saturday", "Sunday"], "time": "So 22:00 - Ne 22:00", "vehicles": "nad 7.5t"
        }
        rules["summer_ban"] = {
            "active": True, "period": f"{year}-07-01 to {year}-08-31", "days": ["Saturday - Sunday"], "time": "So 15:00 - Ne 22:00", "note": "Letní rozšířený zákaz v Maďarsku (často i před svátky)"
        }
    else:
        rules["standard_weekend_ban"] = {
            "active": False, "note": "Standardní celoplošné víkendové zákazy neuplatněny nebo lokálního charakteru."
        }
        
    return rules

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
    eu_countries = [
        "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", 
        "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", 
        "PL", "PT", "RO", "SK", "SI", "ES", "SE"
    ]

    new_countries_data = {}
    for code in eu_countries:
        print(f"Zpracovávám stát EU: {code}...")
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
        country_obj.update(get_country_rules(code, current_year))
        new_countries_data[code] = country_obj

    new_data = {
        "version": old_data.get("version", 1),
        "last_updated": datetime.now().strftime('%Y-%m-%d'),
        "countries": new_countries_data
    }

    old_check = dict(old_data)
    old_check.pop("last_updated", None)
    new_check = dict(new_data)
    new_check.pop("last_updated", None)

    if get_hash(old_check) == get_hash(new_check):
        print("Žádné změny v datech nebyly detekovány.")
        return

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    print(f"Data pro 27 zemí EU včetně prázdninových zákazů aktualizována k: {new_data['last_updated']}")

if __name__ == '__main__':
    main()
