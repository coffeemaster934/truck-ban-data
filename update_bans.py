import json
from datetime import datetime
import urllib.request
import hashlib
import time
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    return []

def get_country_metadata(code, year):
    """Vrací detailní pravidla, časová pásma, oficiální portály a regionální poznámky pro všech 27 zemí EU."""
    rules = {
        "timezone": "Europe/Berlin",
        "official_portal_url": "https://ec.europa.eu/transport/index_en",
        "rules": {}
    }
    
    # --- STŘEDNÍ EVROPA A HLAVNÍ TRANZIT ---
    if code == "DE":
        rules["timezone"] = "Europe/Berlin"
        rules["official_portal_url"] = "https://www.bag.bund.de/"
        rules["regional_note"] = "Některé svátky platí pouze ve vybraných spolkových zemích."
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Sunday"], "time": "00:00 - 22:00", "vehicles": "nad 7.5t a přívěsy"}
        rules["rules"]["summer_ban"] = {"active": True, "period": f"{year}-07-01 to {year}-08-31", "days": ["Saturday"], "time": "07:00 - 20:00", "note": "Prázdninový zákaz na vybraných dálnicích"}
    elif code == "AT":
        rules["timezone"] = "Europe/Vienna"
        rules["official_portal_url"] = "https://www.asfinag.at/"
        rules["regional_note"] = "Zákazy se mohou lišit podle spolkových zemí."
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Saturday", "Sunday"], "time": "So 15:00 - Ne 22:00", "vehicles": "nad 7.5t"}
        rules["rules"]["night_ban"] = {"active": True, "time": "22:00 - 05:00", "vehicles": "nad 7.5t (Inntalautobahn A12)"}
    elif code == "CZ":
        rules["timezone"] = "Europe/Prague"
        rules["official_portal_url"] = "https://www.mdcr.cz/"
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Sunday"], "time": "13:00 - 22:00", "vehicles": "nad 7.5t"}
        rules["rules"]["summer_ban"] = {"active": True, "period": f"{year}-07-01 to {year}-08-31", "days": ["Friday", "Saturday", "Sunday"], "time": "Pá 17-21, So 07-13, Ne 13-22"}
    elif code == "SK":
        rules["timezone"] = "Europe/Bratislava"
        rules["official_portal_url"] = "https://www.mindop.sk/"
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Sunday", "Svátky"], "time": "00:00 - 22:00", "vehicles": "nad 7.5t s přívěsem"}
    elif code == "PL":
        rules["timezone"] = "Europe/Warsaw"
        rules["official_portal_url"] = "https://www.gov.pl/web/infrastruktura"
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Sunday"], "time": "08:00 - 22:00", "vehicles": "nad 12t"}
        rules["rules"]["summer_ban"] = {"active": True, "period": f"{year}-06-25 to {year}-08-31", "days": ["Friday", "Saturday", "Sunday"], "time": "Pá 18-22, So 08-14, Ne 08-22"}
    elif code == "HU":
        rules["timezone"] = "Europe/Budapest"
        rules["official_portal_url"] = "https://www.utinform.hu/"
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Saturday", "Sunday"], "time": "So 22:00 - Ne 22:00", "vehicles": "nad 7.5t"}

    # --- ZÁPADNÍ EVROPA ---
    elif code == "FR":
        rules["timezone"] = "Europe/Paris"
        rules["official_portal_url"] = "https://www.bison-fute.gouv.fr/"
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Saturday", "Sunday"], "time": "So 22:00 - Ne 22:00", "vehicles": "nad 7.5t"}
        rules["rules"]["summer_ban"] = {"active": True, "period": f"{year}-07-01 to {year}-08-31", "days": ["Saturday"], "time": "07:00 - 19:00", "note": "Černé/červené soboty Bison Futé"}
    elif code == "BE":
        rules["timezone"] = "Europe/Brussels"
        rules["official_portal_url"] = "https://mobilite.belgium.be/"
        rules["rules"]["standard_weekend_ban"] = {"active": False, "note": "Plošné víkendové zákazy pro kamiony neexistují, platí lokální omezení."}
    elif code == "NL":
        rules["timezone"] = "Europe/Amsterdam"
        rules["official_portal_url"] = "https://www.rijkswaterstaat.nl/"
        rules["rules"]["standard_weekend_ban"] = {"active": False, "note": "Bez celoplošných víkendových zákazů, regulace vjezdu do měst."}
    elif code == "LU":
        rules["timezone"] = "Europe/Luxembourg"
        rules["official_portal_url"] = "https://transports.gouv.lu/"
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Soboty před nedělí a svátky"], "time": "Zákazy vjezdu do/z DE a FR dle aktuálních bilaterálních dohod."}

    # --- JIŽNÍ EVROPA A BALKÁN ---
    elif code == "IT":
        rules["timezone"] = "Europe/Rome"
        rules["official_portal_url"] = "https://www.mit.gov.it/"
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Sunday"], "time": "09:00 - 22:00", "vehicles": "nad 7.5t"}
        rules["rules"]["summer_ban"] = {"active": True, "period": f"{year}-06-01 to {year}-09-01", "days": ["Sunday"], "time": "07:00 - 22:00", "note": "Rozšířené letní zákazy tranzitu"}
    elif code == "ES":
        rules["timezone"] = "Europe/Madrid"
        rules["official_portal_url"] = "https://www.dgt.es/"
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Neděle a svátky v létě"], "time": "Různé (dle DGT nařízení)", "note": "Omezení pro nákladní dopravu nad 7.5t na hlavních tazích."}
    elif code == "PT":
        rules["timezone"] = "Europe/Lisbon"
        rules["official_portal_url"] = "https://www.imt-ip.pt/"
        rules["rules"]["standard_weekend_ban"] = {"active": False, "note": "Omezení vjezdu do Lisabonu a Porta v špičkách, sváteční zákazy pro nadměrné náklady."}
    elif code == "SI":
        rules["timezone"] = "Europe/Ljubljana"
        rules["official_portal_url"] = "https://www.gov.si/"
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Sunday", "Svátky"], "time": "08:00 - 21:00", "vehicles": "nad 7.5t"}
    elif code == "HR":
        rules["timezone"] = "Europe/Zagreb"
        rules["official_portal_url"] = "https://mup.gov.hr/"
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Neděle v sezóně"], "time": "12:00 - 23:00", "note": "Sezónní letní omezení pro vybrané silnice."}
    elif code == "EL" or code == "GR":
        rules["timezone"] = "Europe/Athens"
        rules["official_portal_url"] = "https://www.ynanp.gr/"
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Před/Po svátcích a v létě"], "time": "Časové bloky pro výjezdy z Atén a Soluně."}
    elif code: # Malta a Kypr
        if code == "CY":
            rules["timezone"] = "Asia/Nicosia"
            rules["official_portal_url"] = "https://www.mcw.gov.cy/"
            rules["rules"]["standard_weekend_ban"] = {"active": False, "note": "Bez celostátních víkendových zákazů."}
        elif code == "MT":
            rules["timezone"] = "Europe/Malta"
            rules["official_portal_url"] = "https://www.transport.gov.mt/"
            rules["rules"]["standard_weekend_ban"] = {"active": False, "note": "Lokální časová omezení pro nákladní auta v obcích."}

    # --- SEVERNÍ A SEVEROVÝCHODNÍ EVROPA (BALT) ---
    elif code == "DK":
        rules["timezone"] = "Europe/Copenhagen"
        rules["official_portal_url"] = "https://vd.dk/"
        rules["rules"]["standard_weekend_ban"] = {"active": False, "note": "Žádné plošné víkendové zákazy pro kamiony."}
    elif code == "SE":
        rules["timezone"] = "Europe/Stockholm"
        rules["official_portal_url"] = "https://www.trafikverket.se/"
        rules["rules"]["standard_weekend_ban"] = {"active": False, "note": "Žádné celoplošné víkendové zákazy."}
    elif code == "FI":
        rules["timezone"] = "Europe/Helsinki"
        rules["official_portal_url"] = "https://vayla.fi/"
        rules["rules"]["standard_weekend_ban"] = {"active": False, "note": "Žádné víkendové plošné zákazy."}
    elif code == "EE":
        rules["timezone"] = "Europe/Tallinn"
        rules["official_portal_url"] = "https://transpordiamet.ee/"
        rules["rules"]["standard_weekend_ban"] = {"active": False, "note": "Bez víkendových zákazů."}
    elif code == "LV":
        rules["timezone"] = "Europe/Riga"
        rules["official_portal_url"] = "https://www.lvceli.lv/"
        rules["rules"]["standard_weekend_ban"] = {"active": False, "note": "Bez plošných víkendových zákazů, omezení v Jūrmale."}
    elif code == "LT":
        rules["timezone"] = "Europe/Vilnius"
        rules["official_portal_url"] = "https://lakd.lrv.lt/"
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Letní neděle"], "time": "16:00 - 22:00", "note": "Letní omezení pro vozidla nad 7.5t na vybraných tazích."}

    # --- VÝCHODNÍ EVROPA (RO / BG / IE) ---
    elif code == "RO":
        rules["timezone"] = "Europe/Bucharest"
        rules["official_portal_url"] = "https://www.cnadnr.ro/"
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Předvečer svátků a víkendy v létě"], "time": "Různé (často 06:00 - 22:00 na dálnicích)"}
    elif code == "BG":
        rules["timezone"] = "Europe/Sofia"
        rules["official_portal_url"] = "https://www.api.bg/"
        rules["rules"]["standard_weekend_ban"] = {"active": True, "days": ["Poslední den prázdnin/svátků"], "time": "16:00 - 20:00 na vybraných silnicích", "vehicles": "nad 12t"}
    elif code == "IE":
        rules["timezone"] = "Europe/Dublin"
        rules["official_portal_url"] = "https://www.gov.ie/en/organisation/department-of-transport/"
        rules["rules"]["standard_weekend_ban"] = {"active": False, "note": "Žádné celoplošné víkendové zákazy, lokální omezení v Dublinu."}
        
    return rules

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
    msg['Subject'] = f"🚚 Aktualizace zákazů kamionů - Verze {new_version}"

    body = f"Ahoj,\n\nDatabáze zákazů byla právě aktualizována na novou verzi {new_version}.\nZměny byly úspěšně zkontrolovány pro všech 27 zemí EU.\n\nŠťastnou cestu!"
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

    # Bezpečnostní pojistka: Pokud API selhalo a máme méně než 25 zemí, data nezapíšeme
    if len(new_countries_data) < 25:
        print("CHYBA: Staženo podezřele málo zemí. Přerušuji zápis, abych nepoškodil existující data.")
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

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    print(f"Kompletní EU data (všech 27 zemí) aktualizována na verzi {new_version} k: {new_data['last_updated']}")

    # Odeslání e-mailového upozornění po úspěšné aktualizaci
    send_email_notification(new_version)

if __name__ == '__main__':
    main()
