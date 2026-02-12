# Datový slovník - BOM Manager

## Třídy (Classes)

### BOMScannerMainWindow
**Typ:** UI třída (hlavní okno aplikace)  
**Účel:** Hlavní řídící třída aplikace zodpovědná za UI a koordinaci všech operací

**Atributy:**
- `settings: QSettings` - Perzistentní nastavení aplikace (Qt framework)
- `scanned_codes: List[Dict]` - Kolekce všech naskenovaných součástek
- `projects_data: List[Dict]` - Kolekce všech projektů
- `storage_locations_data: List[Dict]` - Kolekce skladových míst
- `bom_table: QTableWidget` - Qt widget pro zobrazení BOM tabulky
- `projects_table: QTableWidget` - Qt widget pro zobrazení projektů
- `storage_table: QTableWidget` - Qt widget pro zobrazení skladových míst
- `tme_api: TMEAPI` - Instance TME API klienta

**Metody:**
- `init_ui()` - Inicializuje uživatelské rozhraní
- `on_scan_received(code: str)` - Event handler pro příjem naskenovaného kódu
- `add_code_to_list(code: str)` - Přidá kód do seznamu
- `export_to_json()` - Exportuje BOM do JSON formátu
- `export_to_csv()` - Exportuje BOM do CSV formátu
- `save_bom()` - Uloží BOM do JSON souboru
- `load_bom()` - Načte BOM z JSON souboru

---

### Part
**Typ:** Entita (doménová třída)  
**Účel:** Reprezentuje elektronickou součástku s jejími atributy a vztahy

**Atributy:**
- `pn: str` - Part Number (primární identifikátor, např. "R0805-100R")
- `mpn: str` - Manufacturer Part Number (např. "RC0805FR-07100RL")
- `manufacturer: str` - Výrobce součástky (např. "YAGEO", "Vishay")
- `quantity: int` - Aktuální množství kusů na skladě (≥ 0)
- `location: str` - Kód skladového místa (např. "A1", "SHELF-12")
- `value: str` - Hodnota součástky (např. "100R", "10uF", "BC547")
- `category: str` - Kategorie součástky (např. "Resistors", "Capacitors")
- `coo: str` - Country of Origin - země původu (ISO kód, např. "CN", "US")
- `po: str` - Purchase Order - číslo nákupní objednávky
- `url: str` - URL odkaz na datasheet nebo produktovou stránku
- `rohs: bool` - RoHS compliance (True = splňuje, False = nesplňuje)
- `projects: List[str]` - Seznam názvů projektů, ke kterým je součástka přiřazena
- `scan_history: List[str]` - Časová razítka všech skenování (ISO formát)

**Metody:**
- `add_quantity(qty: int)` - Přičte množství k existujícímu stavu
- `update_location(location: str)` - Aktualizuje skladové místo
- `add_to_project(project_name: str)` - Přiřadí součástku k projektu
- `remove_from_project(project_name: str)` - Odebere součástku z projektu
- `add_scan_timestamp()` - Přidá aktuální čas do historie
- `get_category(): str` - Vrací kategorii součástky
- `to_dict(): Dict` - Serializuje objekt do slovníku

**Kardinalita vazeb:**
- Part `0..*` --- `0..*` Project (many-to-many)
- Part `0..*` --- `0..1` StorageLocation (many-to-one)
- Part `1` --- `1..*` ScanRecord (one-to-many, composition)

---

### Project
**Typ:** Entita  
**Účel:** Reprezentuje projekt, ke kterému lze přiřazovat součástky

**Atributy:**
- `name: str` - Název projektu (jedinečný identifikátor)
- `description: str` - Popis projektu
- `created_date: str` - Datum vytvoření (ISO formát YYYY-MM-DD)
- `parts: List[str]` - Seznam Part Numbers přiřazených součástek

**Metody:**
- `add_part(pn: str)` - Přidá součástku do projektu
- `remove_part(pn: str)` - Odebere součástku z projektu
- `get_parts_count(): int` - Vrací počet součástek v projektu
- `to_dict(): Dict` - Serializace
- `from_dict(data: Dict): Project` - Deserializace (class method)

**Vztahy:**
- Agregace: Project obsahuje odkazy na Parts (ale Part může existovat bez Project)

---

### StorageLocation
**Typ:** Entita  
**Účel:** Reprezentuje fyzické skladové místo (police, box, zásuvka)

**Atributy:**
- `code: str` - Kód skladového místa (např. "A1", "B23", jedinečný)
- `description: str` - Popis umístění (např. "Levá police, horní řada")
- `created_date: str` - Datum vytvoření (ISO formát)
- `parts: List[str]` - Seznam Part Numbers uložených součástek

**Metody:**
- `assign_part(pn: str)` - Přiřadí součástku na toto místo
- `remove_part(pn: str)` - Odebere součástku z místa
- `is_empty(): bool` - Vrací True pokud žádné součástky
- `to_dict(): Dict` - Serializace
- `from_dict(data: Dict): StorageLocation` - Deserializace

---

### ScanRecord
**Typ:** Entita  
**Účel:** Záznam o jednom skenování QR kódu

**Atributy:**
- `code: str` - Surový text z QR kódu
- `timestamp: str` - Čas skenování (ISO formát YYYY-MM-DD HH:MM:SS)
- `parsed_data: Dict` - Parsovaná data ze skenování
- `length: int` - Délka kódu v znacích

**Metody:**
- `parse(): Dict` - Parsuje surový kód do struktury
- `to_dict(): Dict` - Serializace záznamu

---

### BOMManager
**Typ:** Manager (business logika)  
**Účel:** Centrální správce všech součástek v BOM

**Atributy:**
- `parts: Dict[str, Part]` - Slovník součástek indexovaný podle PN (kvalifikovaná asociace)
- `filename: str` - Cesta k JSON souboru s BOM daty

**Metody:**
- `add_or_update_part(parsed_data: Dict): Part` - Přidá novou nebo aktualizuje existující
- `get_part(pn: str): Part` - Získá součástku podle PN
- `remove_part(pn: str)` - Odstraní součástku z BOM
- `get_all_parts(): List[Part]` - Vrací všechny součástky
- `save(): bool` - Uloží BOM do JSON
- `load(): bool` - Načte BOM z JSON
- `export_to_csv(filename: str)` - Export do CSV
- `get_parts_by_project(project: str): List[Part]` - Filtr podle projektu
- `get_parts_by_location(location: str): List[Part]` - Filtr podle lokace

**Vztah k Part:**
- Agregace: BOMManager `1` o-- `0..*` Part
- Kvalifikátor: PN (Part Number) pro rychlý přístup

---

### ProjectManager
**Typ:** Manager  
**Účel:** Správa projektů

**Atributy:**
- `projects: Dict[str, Project]` - Slovník projektů indexovaný podle name
- `filename: str` - Cesta k projects.json

**Metody:**
- `create_project(name: str, desc: str): Project` - Vytvoří nový projekt
- `get_project(name: str): Project` - Získá projekt podle jména
- `delete_project(name: str)` - Smaže projekt
- `get_all_projects(): List[Project]` - Vrací všechny projekty
- `save(): bool` - Uloží do JSON
- `load(): bool` - Načte z JSON

---

### StorageManager
**Typ:** Manager  
**Účel:** Správa skladových míst

**Atributy:**
- `locations: Dict[str, StorageLocation]` - Slovník lokací indexovaný podle code
- `filename: str` - Cesta k storage_locations.json

**Metody:**
- `create_location(code: str, desc: str): StorageLocation`
- `get_location(code: str): StorageLocation`
- `delete_location(code: str)`
- `get_all_locations(): List[StorageLocation]`
- `save(): bool`
- `load(): bool`

---

### QRParser
**Typ:** Utility (statická třída)  
**Účel:** Parsování QR kódů do strukturovaných dat

**Konstanty:**
- Žádné instance atributy (všechny metody statické)

**Metody:**
- `parse_qr_code(code: str): Dict` - Hlavní parsovací metoda
- `extract_field(code: str, field: str): str` - Extrahuje konkrétní pole
- `parse_quantity(qty_str: str): int` - Parsuje množství
- `validate_format(code: str): bool` - Validuje formát QR kódu

**Formát vstupu:**
```
PN=hodnota,MPN=hodnota,QTY=hodnota,...
```

---

### TMEAPI
**Typ:** External API Client  
**Účel:** Integrace s TME (Transfer Multisort Elektronik) API

**Atributy:**
- `token: str` - Private token (50 znaků, autentizace)
- `app_secret: str` - Application secret (20 znaků, pro signaturu)
- `base_url: str` - "https://api.tme.eu"
- `default_country: str` - "CZ" (Czech Republic)
- `default_language: str` - "EN"
- `default_currency: str` - "EUR"

**Metody:**
- `search_products(symbol: str): Dict` - Vyhledá součástku podle symbolu/MPN
- `get_product_details(symbol: str): Dict` - Získá detailní informace
- `get_prices(symbol: str): List` - Získá cenové informace
- `_generate_signature(method: str, uri: str, params: Dict): str` - HMAC-SHA1
- `_make_request(action: str, params: Dict): Dict` - HTTP POST request

**Návratové hodnoty (search_products):**
```json
{
  "Symbol": "RC0805FR-07100RL",
  "Description": "Resistor 100R 0805 1%",
  "Category": "Resistors > SMD > 0805",
  "Producer": "YAGEO",
  "OriginalSymbol": "RC0805FR-07100RL"
}
```

---

### ZPLGenerator
**Typ:** Utility (statická třída)  
**Účel:** Generování ZPL (Zebra Programming Language) kódu pro tisk štítků

**Konstanty:**
- `DPI: int = 203` - Rozlišení tiskárny (dots per inch)
- `LABEL_WIDTH: int = 2` - Šířka štítku v palcích
- `LABEL_HEIGHT: int = 1` - Výška štítku v palcích

**Metody:**
- `generate_label(location: str): str` - Generuje ZPL kód pro lokaci
- `save_to_file(zpl: str, filename: str)` - Uloží ZPL do .zpl souboru
- `send_to_printer(zpl: str, printer_name: str)` - Odešle ZPL na tiskárnu

**Příklad výstupu:**
```zpl
^XA
^FO50,20^BY2^BCN,100,Y,N,N^FDA1^FS
^FO50,140^A0N,30,30^FDStorage: A1^FS
^XZ
```

---

### ZebraPrinterDriver
**Typ:** External Device Driver  
**Účel:** Komunikace se Zebra tiskárnou

**Atributy:**
- `printer_name: str` - Název tiskárny v systému
- `connection_type: str` - Typ připojení ("USB", "Network", "Bluetooth")

**Metody:**
- `print_zpl(zpl_code: str): bool` - Pošle ZPL příkaz k tisku
- `get_status(): str` - Vrací stav tiskárny ("Ready", "Error", "Offline")
- `is_connected(): bool` - Kontroluje připojení

---

### CategoryMapper
**Typ:** Utility  
**Účel:** Mapování součástek na kategorie

**Metody:**
- `get_category(pn: str, value: str, tme_api: TMEAPI): str` - Určí kategorii
- `categorize_by_prefix(pn: str): str` - Kategorizace podle prefixu PN
- `categorize_by_tme(mpn: str, tme_api: TMEAPI): str` - Kategorizace přes TME

**Pravidla kategorizace:**
| Prefix | Kategorie |
|--------|-----------|
| 1xx | Electronic Components |
| 2xx | Screws |
| 3xx | Nuts |
| 4xx | Bearings |
| 5xx | Cables |

---

### FileExporter
**Typ:** Utility  
**Účel:** Export a import dat do různých formátů

**Metody:**
- `export_to_csv(data: List[Dict], filename: str)` - CSV export
- `export_to_json(data: List[Dict], filename: str)` - JSON export
- `import_from_csv(filename: str): List[Dict]` - CSV import

---

## Datové typy

### Dict (Slovník)
Struktura klíč-hodnota používaná pro:
- Parsovaná QR data
- JSON serializace/deserializace
- Konfigurace

### List (Seznam)
Kolekce prvků používaná pro:
- Seznam součástek (`List[Part]`)
- Historie skenování (`List[str]`)
- Projekty součástky (`List[str]`)

### str (Řetězec)
Textové hodnoty:
- Identifikátory (PN, MPN, code)
- Popisy
- URL
- Timestamp v ISO formátu

### int (Celé číslo)
Numerické hodnoty:
- Množství součástek
- Počet záznamů
- Délka kódu

### bool (Boolean)
Logické hodnoty:
- RoHS compliance
- Stavové příznaky
- Výsledky validace

---

## Soubory a formáty

### BOM_current.csv
**Formát:** CSV (Comma-Separated Values)  
**Účel:** Exportovaný BOM pro další zpracování  
**Struktura:**
```csv
PN,MPN,Manufacturer,Quantity,Value,Category,Projects,Storage Location,CoO,PO,URL,RoHS
R0805-100R,RC0805FR-07100RL,YAGEO,100,100R,Resistors,"Project1;Project2",A1,CN,PO12345,https://...,Y
```

### projects.json
**Formát:** JSON  
**Účel:** Perzistence projektů  
**Struktura:**
```json
[
  {
    "name": "LED Controller v2",
    "description": "RGB LED controller board",
    "created_date": "2026-01-15",
    "parts": ["R0805-100R", "C0805-10uF"]
  }
]
```

### storage_locations.json
**Formát:** JSON  
**Účel:** Perzistence skladových míst  
**Struktura:**
```json
[
  {
    "code": "A1",
    "description": "Top shelf, left side",
    "created_date": "2026-01-10",
    "parts": ["R0805-100R"]
  }
]
```

### label.zpl
**Formát:** ZPL (Zebra Programming Language)  
**Účel:** Příkazy pro tisk štítků  
**Obsah:** Textové příkazy pro Zebra tiskárnu

---

## Kvalifikované vazby

### BOMManager -> Part
**Kvalifikátor:** `pn: str` (Part Number)  
**Vztah:** `Dict[str, Part]`  
**Význam:** Rychlé vyhledání součástky podle Part Number

### ProjectManager -> Project
**Kvalifikátor:** `name: str`  
**Vztah:** `Dict[str, Project]`  
**Význam:** Rychlé vyhledání projektu podle jména

### StorageManager -> StorageLocation
**Kvalifikátor:** `code: str`  
**Vztah:** `Dict[str, StorageLocation]`  
**Význam:** Rychlé vyhledání lokace podle kódu

---

## Kardinalita vazeb

- `BOMManager (1) o-- (0..*) Part` - Agregace
- `Part (0..*) -- (0..*) Project` - Asociace many-to-many
- `Part (0..*) -- (0..1) StorageLocation` - Asociace many-to-one
- `Part (1) *-- (1..*) ScanRecord` - Kompozice one-to-many
- `BOMScannerMainWindow (1) --> (1) BOMManager` - Závislost
- `BOMScannerMainWindow (1) --> (0..1) TMEAPI` - Volitelná závislost

---

## Stavy objektů

### Part
- **New** - Právě naskenováno
- **InBOM** - V BOM tabulce
- **Allocated** - Má přiřazené místo
- **LowStock** - Nízký stav
- **OutOfStock** - Vyprodáno
- **Archived** - Archivováno

### BOMScanner
- **Initializing** - Načítání dat
- **Ready** - Připraven na skenování
- **Processing** - Zpracování kódu
- **Saving** - Ukládání dat

---

## Invarianty

1. `Part.quantity >= 0` - Množství nemůže být záporné
2. `Part.pn` je jedinečný v rámci BOMManager
3. `Project.name` je jedinečný v rámci ProjectManager
4. `StorageLocation.code` je jedinečný v rámci StorageManager
5. Součástka může být přiřazena max. k jednomu skladovému místu
6. Součástka může být přiřazena k více projektům
7. Všechny timestamp jsou v ISO formátu "YYYY-MM-DD HH:MM:SS"
