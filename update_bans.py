import json
from datetime import datetime
import urllib.request
import hashlib
import time
import os
from urllib.parse import urlparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart 

VERIFIED_HOLIDAY_BANS = {}
VERIFIED_POLISH_SUMMER_BANS = {}

def fetch_holidays(country_code, year, retries=3, delay=2):
    """Stáhne státní svátky z veřejného API pro danou zemi a rok s opakovanými pokusy při výpadku."""
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"Pokus {attempt + 1}/{retries} – Chyba při stahování svátků pro {country_code}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    print(f"Nepodařilo se stáhnout svátky pro {country_code} ani po {retries} pokusech.")
    return None

def format_public_holidays(holidays):
    """Formats calendar data only; public holidays are not truck-ban evidence."""
    return [
        {
            "date": holiday.get("date"),
            "name": holiday.get("localName") or holiday.get("name"),
        }
        for holiday in holidays
    ]

def build_country_data(code, year, holidays):
    metadata = get_country_metadata(code, year)
    country_data = {
        "country_name": code,
        "timezone": metadata["timezone"],
        "official_portal_url": metadata["official_portal_url"],
        "public_holidays": format_public_holidays(holidays),
        "holiday_bans": get_verified_holiday_bans(code, year),
    }

    if "regional_note" in metadata:
        country_data["regional_note"] = metadata["regional_note"]

    country_data.update(metadata["rules"])
    return country_data

def get_verified_holiday_bans(code, year):
    records = VERIFIED_HOLIDAY_BANS.get((code, year), [])
    for record in records:
        if (
            not isinstance(record, dict)
            or not isinstance(record.get("date"), str)
            or not isinstance(record.get("name"), str)
            or not record["name"].strip()
            or not isinstance(record.get("time"), str)
            or not record["time"].strip()
            or record.get("ban") is not True
            or not _has_verified_national_source(record)
        ):
            raise ValueError(
                f"Invalid verified holiday-ban record for {code} in {year}."
            )
        try:
            datetime.strptime(record["date"], "%Y-%m-%d")
        except ValueError as error:
            raise ValueError(
                f"Invalid date in holiday-ban record for {code} in {year}."
            ) from error
    return records

def _has_verified_national_source(record):
    source_url = record.get("source_url")
    parsed_source = urlparse(source_url) if isinstance(source_url, str) else None
    return (
        record.get("verified") is True
        and record.get("scope") == "national"
        and parsed_source is not None
        and parsed_source.scheme == "https"
        and bool(parsed_source.netloc)
    )

def get_country_metadata(code, year):
    """Return display metadata without treating legacy schedules as legal rules."""
    countries = {
        "AT": ("Europe/Vienna", "https://www.asfinag.at/"),
        "BE": ("Europe/Brussels", "https://mobilite.belgium.be/"),
        "BG": ("Europe/Sofia", "https://www.api.bg/"),
        "HR": ("Europe/Zagreb", "https://mup.gov.hr/"),
        "CY": ("Asia/Nicosia", "https://www.mcw.gov.cy/"),
        "CZ": ("Europe/Prague", "https://www.mdcr.cz/"),
        "DK": ("Europe/Copenhagen", "https://vd.dk/"),
        "EE": ("Europe/Tallinn", "https://transpordiamet.ee/"),
        "FI": ("Europe/Helsinki", "https://vayla.fi/"),
        "FR": ("Europe/Paris", "https://www.bison-fute.gouv.fr/"),
        "DE": ("Europe/Berlin", "https://www.bag.bund.de/"),
        "GR": ("Europe/Athens", "https://www.astynomia.gr/"),
        "HU": ("Europe/Budapest", "https://www.utinform.hu/"),
        "IE": (
            "Europe/Dublin",
            "https://www.gov.ie/en/organisation/department-of-transport/",
        ),
        "IT": ("Europe/Rome", "https://www.mit.gov.it/"),
        "LV": ("Europe/Riga", "https://www.lvceli.lv/"),
        "LT": ("Europe/Vilnius", "https://lakd.lrv.lt/"),
        "LU": ("Europe/Luxembourg", "https://transports.gouv.lu/"),
        "MT": ("Europe/Malta", "https://www.transport.gov.mt/"),
        "NL": ("Europe/Amsterdam", "https://www.rijkswaterstaat.nl/"),
        "PL": ("Europe/Warsaw", "https://www.gov.pl/web/infrastruktura"),
        "PT": ("Europe/Lisbon", "https://www.imt-ip.pt/"),
        "RO": ("Europe/Bucharest", "https://www.cnadnr.ro/"),
        "SK": ("Europe/Bratislava", "https://www.mindop.sk/"),
        "SI": ("Europe/Ljubljana", "https://www.gov.si/"),
        "ES": ("Europe/Madrid", "https://www.dgt.es/"),
        "SE": ("Europe/Stockholm", "https://www.trafikverket.se/"),
    }
    if code not in countries:
        raise ValueError(f"Unsupported country code: {code}")

    timezone, official_portal_url = countries[code]
    rules = {}
    polish_summer_ban = VERIFIED_POLISH_SUMMER_BANS.get(year) if code == "PL" else None
    if polish_summer_ban is not None:
        if (
            polish_summer_ban.get("active") is not True
            or not isinstance(polish_summer_ban.get("period"), str)
            or not isinstance(polish_summer_ban.get("days"), list)
            or not isinstance(polish_summer_ban.get("time"), str)
            or not _has_verified_national_source(polish_summer_ban)
        ):
            raise ValueError(f"Invalid verified Polish summer schedule for {year}.")
        rules["summer_ban"] = polish_summer_ban

    return {
        "timezone": timezone,
        "official_portal_url": official_portal_url,
        "rules": rules,
    }

def get_hash(content):
    return hashlib.md5(json.dumps(content, sort_keys=True).encode('utf-8')).hexdigest()

def send_email_notification(new_version):
    sender_email = "coffeemaster934@gmail.com"
    receiver_email = "coffeemaster934@gmail.com"
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    
    if not app_password:
        print("Chybí GMAIL_APP_PASSWORD v proměnných prostředí, e-mail nebyl odeslán.")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"Aktualizace kalendáře svátků - Verze {new_version}"

    body = (
        f"Ahoj,\n\nKalendář státních svátků byl aktualizován na verzi "
        f"{new_version}. Veřejné svátky se v tomto feedu nepovažují za "
        "důkaz zákazu jízdy.\n\nŠťastnou cestu!"
    )
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("E-mailové upozornění bylo úspěšně odesláno na coffeemaster934@gmail.com.")
    except Exception as e:
        print(f"Chyba při odesílání e-mailu: {e}")

def main():
    file_path = 'bans.json'
    tmp_file_path = 'bans.json.tmp'
    old_data = {"version": 1, "countries": {}}
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    old_data = json.loads(content)
        except Exception as e:
            print(f"Varování: Existující bans.json je poškozený ({e}), bude nahrazen novou verzí.")

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
        if holidays is None:
            print(
                f"CHYBA: Chybí kalendář pro {code}. "
                "Stávající data ponechána beze změny."
            )
            return
        new_countries_data[code] = build_country_data(
            code,
            current_year,
            holidays,
        )

    if len(new_countries_data) != len(eu_countries):
        print("CHYBA: Nejsou dostupná data pro všech 27 zemí. Stávající data ponechána beze změny.")
        return

    # Zjištění, zda se data reálně změnila
    old_check = dict(old_data)
    old_check.pop("last_updated", None)
    old_check.pop("version", None)
    
    current_version = old_data.get("version", 1)

    new_data_temp = {
        "countries": new_countries_data
    }

    if get_hash(old_check) == get_hash(new_data_temp):
        print("Žádné změny v datech nebyly detekovány.")
        return

    # Pokud se data změnila, navýšíme verzi o 1
    new_version = current_version + 1

    new_data = {
        "version": new_version,
        "last_updated": datetime.now().strftime('%Y-%m-%d'),
        "countries": new_countries_data
    }

    # ATOMICKÝ ZÁPIS: Zápis do dočasného souboru a ověření jeho formátu před přepsáním ostrého souboru
    try:
        with open(tmp_file_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        
        with open(tmp_file_path, 'r', encoding='utf-8') as f:
            json.load(f)

        if os.path.exists(file_path):
            os.remove(file_path)
        os.rename(tmp_file_path, file_path)

    except Exception as e:
        print(f"CHYBA při atomickém zápisu souboru: {e}")
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
        return
    
    print(
        f"Kalendář svátků pro všech 27 zemí EU byl aktualizován na verzi "
        f"{new_version} k: {new_data['last_updated']}. "
        "Z kalendáře se neodvozují zákazy jízdy."
    )

    # Odeslání e-mailového upozornění po úspěšné aktualizaci
    send_email_notification(new_version)

if __name__ == '__main__':
    main()
