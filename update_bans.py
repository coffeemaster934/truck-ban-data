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

    # --- VÝCHODNÍ EV
