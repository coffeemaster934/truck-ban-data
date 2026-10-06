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

def get_country_metadata(code, year):
    """Vrací detailní pravidla, časová pásma, oficiální portály a regionální poznámky."""
    rules = {
        "timezone": "Europe/Berlin", # Výchozí středoevropský
        "official_portal_url": "https://ec.europa.eu/transport/index_en",
        "rules": {}
    }
    
    if code == "DE":
        rules["timezone"] = "Europe/Berlin"
        rules["official_portal_url"] = "https://www.bag.bund.de/"
        rules["regional_note"] = "Některé svátky (např. Den reformace, Všichni svatí) platí pouze ve vybraných spolkových zemích (např. BY, BW, NW, RP, SL)."
        rules["rules"]["standard_weekend_ban"] = {
            "active": True, "days": ["Sunday"], "time": "00:00 - 22:00", "vehicles": "nad 7.5t a přívěsy"
        }
        rules["rules"]["summer_ban"] = {
            "active": True, "period": f"{year}-07-01 to {year}-08-31", "days": ["Saturday"], "time": "07:00 - 20:00", "note": "Prázdninový zákaz na vybraných dálnicích (nařízení BAG)"
        }
    elif code == "AT":
        rules["timezone"] = "Europe/Vienna"
        rules["official_portal_url"] = "https://www.asfinag.at/"
        rules["regional_note"] = "Některé svátky a zákazy se mohou lišit podle spolkových zemí."
        rules["rules"]["standard_weekend_ban"] = {
            "active": True, "days": ["Saturday", "Sunday"], "time": "So 15:00 - Ne 22:00", "vehicles": "nad 7.5t"
        }
        rules["rules"]["night_ban"] = {
            "active": True, "time": "22:00 - 05:00", "vehicles": "nad 7.5t (Inntalautobahn A12 a vybrané úseky)"
        }
    elif code == "FR":
        rules["timezone"] = "Europe/Paris"
        rules["official_portal_url"] = "https://www.bison-fute.gouv.fr/"
        rules["rules"]["standard_weekend_ban"] = {
            "active": True, "days": ["Saturday", "Sunday"], "time": "So 22:00 - Ne 22:00", "vehicles": "nad 7.5t"
        }
        rules["rules"]["summer_ban"] = {
            "active": True, "period": f"{year}-07-01 to {year}-08-31", "days": ["Saturday"], "time": "07:00 - 19:00", "note": "Celostátní prázdninové zákazy (černé/červené soboty Bison Futé)"
        }
    elif code == "IT":
        rules["timezone"] = "Europe/Rome"
        rules["official_portal_url"] = "https://www.mit.gov.it/"
        rules["rules"]["standard_weekend_ban"] = {
            "active": True, "days": ["Sunday"], "time": "09:00 - 22:00", "vehicles": "nad 7.5t"
        }
        rules["rules"]["summer_ban"] = {
            "active": True, "period": f"{year}-06-01 to {year}-09-01", "days": ["Sunday", "vybrané sobory"], "time": "Různé (často 07:00 - 22:00)", "note": "Rozšířené letní zákazy pro tranzit k moři"
        }
    elif code == "CZ":
        rules["timezone"] = "Europe/Prague"
        rules["official_portal_url"] = "https://www.mdcr.cz/"
        rules["rules"]["standard_weekend_ban"] = {
            "active": True, "days": ["Sunday"], "time": "13:00 - 22:00", "vehicles": "nad 7.5t"
        }
        rules["rules"]["summer_ban"] = {
            "active": True, "period": f"{year}-07-01 to {year}-08-31", "days": ["Friday", "Saturday", "Sunday"], "time": "Pá 17:00-21:00, So 07:00-13:00, Ne 13:00-22:00", "note": "Prázdninový provoz (silnice I. třídy a dálnice)"
        }
    elif code == "SK":
        rules["timezone"] = "Europe/Bratislava"
        rules["official_portal_url"] = "https://www.mindop.sk/"
        rules["rules"]["standard_weekend_ban"] = {
            "active": True, "days": ["Sunday"], "time": "00:00 - 22:00", "vehicles": "nad 7.5t s přívěsem"
        }
    elif code == "PL":
        rules["timezone"] = "Europe/Warsaw"
        rules["official_portal_url"] = "https://www.gov.pl/web/infrastruktura"
        rules["rules"]["standard_weekend_ban"] = {
            "active": True, "days": ["Sunday"], "time": "08:00 - 22:00", "vehicles": "nad 12t"
        }
        rules["rules"]["summer_ban"] = {
            "active": True, "period": f"{year}-06-25 to {year}-08-31", "days": ["Friday", "Saturday", "Sunday"], "time": "Pá 18-22, So 08-14, Ne 08-22", "note": "Letní prázdninová omezení nad 12t"
        }
    elif code == "HU":
        rules["timezone"] = "Europe/Budapest"
        rules["official_portal_url"] = "https://www.utinform.hu/"
        rules["rules"]["standard_weekend_ban"] = {
            "active": True, "days": ["Saturday", "Sunday"], "time": "So 22:00 - Ne 22:00", "vehicles": "nad 7.5t"
        }
        rules["rules"]["summer_ban"] = {
            "active": True, "period": f"{year}-07-01 to {year}-08-31", "days": ["Saturday - Sunday"], "time": "So 15:00 - Ne 22:00", "note": "Letní rozšířený zákaz v Maďarsku"
        }
    else:
        # Základní profil pro ostatní země EU
        rules["rules"]["standard_weekend_ban"] = {
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
        print(f"Stahuji a kompletuji data pro: {code}...")
        holidays = fetch_holidays(code, current_year)
        formatted_holidays = []
        for h in holidays:
            formatted_holidays.append({
                "date": h.get("date"),
                "name": h.get("localName") or h.get("name"),
                "time": "00:00 - 22:00"
            })
        
        metadata = get_country_metadata(code, current_year)
        
        country_obj = {
            "country_name": code,
            "timezone": metadata["timezone"],
            "official_portal_url": metadata["official_portal_url"],
            "holiday_bans": formatted_holidays
        }
        
        if "regional_note" in metadata:
            country_obj["regional_note"] = metadata["regional_note"]
            
        country_obj.update(metadata["rules"])
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
    
    print(f"Kompletní EU data (vč. časových pásem a odkazů) aktualizována k: {new_data['last_updated']}")

if __name__ == '__main__':
    main()
