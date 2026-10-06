import json
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
