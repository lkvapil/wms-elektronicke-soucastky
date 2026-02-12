# Scénáře Use Cases - BOM Manager

## UC1: Naskenovat QR kód

### Hlavní scénář (Success scenario)
1. Uživatel spustí aplikaci BOM Manager
2. Systém zobrazí hlavní okno s aktivním vstupním polem
3. Uživatel klikne do vstupního pole pro skenování
4. Uživatel naskenuje QR kód pomocí Zebra čtečky
5. Čtečka odošle data do vstupního pole a automaticky stiskne Enter
6. Systém parsuje QR kód a extrahuje data (PN, MPN, QTY, MFR, atd.)
7. Systém kontroluje, zda součástka již existuje v BOM
8. Součástka neexistuje - systém vytvoří nový záznam
9. Systém dotazuje TME API pro získání dodatečných informací
10. Systém přidá součástku do BOM tabulky
11. Systém automaticky uloží BOM do JSON souboru
12. Systém vymaže vstupní pole a zobrazí potvrzení
13. **Use case končí úspěchem**

### Alternativní scénář A1: Součástka již existuje
- Začíná v kroku 7
- A1.1: Systém najde existující součástku
- A1.2: Systém přičte naskenované množství k existujícímu
- A1.3: Systém přidá timestamp do scan historie
- A1.4: Systém aktualizuje zobrazení v tabulce
- A1.5: Pokračuje krokem 11

### Alternativní scénář A2: TME API nedostupné
- Začíná v kroku 9
- A2.1: TME API neodpovídá nebo vrací chybu
- A2.2: Systém použije pouze data z QR kódu
- A2.3: Systém nastaví kategorii na "Unknown"
- A2.4: Pokračuje krokem 10

### Výjimečný scénář E1: Nevalidní QR kód
- Začíná v kroku 6
- E1.1: Parsování selže, data nejsou ve správném formátu
- E1.2: Systém zobrazí chybovou hlášku
- E1.3: Systém vymaže vstupní pole
- E1.4: **Use case končí neúspěchem**

### Preconditions (Předpoklady)
- Aplikace je spuštěna
- Zebra čtečka je připojena k počítači
- Vstupní pole je aktivní (focused)

### Postconditions (Výsledky)
- **Success:** Součástka je přidána/aktualizována v BOM a uložena do JSON
- **Failure:** Vstupní pole je vymazáno, chyba zobrazena uživateli

---

## UC7: Přiřadit součástku k projektu

### Hlavní scénář
1. Uživatel vybere součástku v BOM tabulce
2. Uživatel dvojklikem otevře detail součástky
3. Systém zobrazí PartDetailDialog s informacemi o součástce
4. Uživatel klikne na tlačítko "Manage Projects"
5. Systém načte seznam všech dostupných projektů
6. Systém zobrazí dialog s checkboxy pro všechny projekty
7. Systém označí projekty, ke kterým je součástka již přiřazena
8. Uživatel zaškrtne/odškrtne požadované projekty
9. Uživatel klikne "Save"
10. Systém aktualizuje přiřazení projektů pro součástku
11. Systém uloží změny do BOM JSON
12. Systém obnoví ProjectsTable pro aktualizaci počtu součástek
13. Systém zavře dialog a obnoví PartDetailDialog
14. **Use case končí úspěchem**

### Alternativní scénář A1: Žádné projekty neexistují
- Začíná v kroku 5
- A1.1: Seznam projektů je prázdný
- A1.2: Systém zobrazí zprávu "No projects available. Create a project first."
- A1.3: Uživatel může zavřít dialog nebo vytvořit nový projekt
- A1.4: **Use case končí**

### Alternativní scénář A2: Zrušení změn
- Začíná v kroku 9
- A2.1: Uživatel klikne "Cancel"
- A2.2: Systém zahodí všechny změny
- A2.3: Systém zavře dialog bez uložení
- A2.4: **Use case končí bez změn**

### Preconditions
- Alespoň jedna součástka existuje v BOM
- Uživatel má otevřený detail součástky

### Postconditions
- **Success:** Součástka je přiřazena k vybraným projektům
- **Cancel:** Žádné změny neprovedeny

---

## UC11: Přiřadit součástku na skladové místo

### Hlavní scénář
1. Uživatel otevře záložku "Allocating Storage Locations"
2. Systém zobrazí seznam všech součástek a skladových míst
3. Uživatel vybere součástku ze seznamu
4. Uživatel vybere skladové místo z dropdown menu
5. Uživatel klikne "Assign Location"
6. Systém ověří, že součástka ještě nemá přiřazené místo
7. Systém přiřadí součástku na vybrané skladové místo
8. Systém aktualizuje sloupec "Storage Location" v BOM tabulce
9. Systém uloží změny do storage_locations.json a BOM_current.csv
10. Systém zobrazí potvrzovací zprávu
11. Systém aktualizuje počet součástek na skladovém místě
12. **Use case končí úspěchem**

### Alternativní scénář A1: Součástka již má místo
- Začíná v kroku 6
- A1.1: Systém detekuje existující přiřazení
- A1.2: Systém zobrazí dialog s varováním
- A1.3: Uživatel potvrdí přepsání nebo zruší
- A1.4: Pokud potvrzeno, pokračuje krokem 7
- A1.5: Pokud zrušeno, use case končí

### Alternativní scénář A2: Skladové místo neexistuje
- Začíná v kroku 4
- A2.1: Seznam skladových míst je prázdný
- A2.2: Systém nabídne vytvoření nového místa
- A2.3: Uživatel zadá kód a popis nového místa
- A2.4: Systém vytvoří nové skladové místo
- A2.5: Pokračuje krokem 5

### Preconditions
- Alespoň jedna součástka existuje v BOM
- Alespoň jedno skladové místo existuje

### Postconditions
- **Success:** Součástka má přiřazené skladové místo
- **Cancel:** Přiřazení nezměněno

---

## UC12: Vytisknout štítek skladového místa

### Hlavní scénář
1. Uživatel otevře záložku "Print Labels"
2. Systém zobrazí formulář pro generování štítků
3. Uživatel zadá kód skladového místa (např. "A1", "B23")
4. Systém automaticky generuje ZPL kód při psaní
5. Systém zobrazí náhled ZPL kódu v textovém poli
6. Uživatel klikne "Copy to Clipboard"
7. Systém zkopíruje ZPL kód do schránky
8. Systém zobrazí potvrzení "ZPL copied to clipboard"
9. Uživatel otevře Zebra Setup Utilities
10. Uživatel vloží ZPL kód do aplikace tiskárny
11. Uživatel odešle příkaz k tisku
12. Zebra tiskárna vytiskne štítek 2x1 palec s čárovým kódem
13. **Use case končí úspěchem**

### Alternativní scénář A1: Uložení do souboru
- Začíná v kroku 6
- A1.1: Uživatel klikne "Save to File"
- A1.2: Systém zobrazí dialog pro výběr umístění
- A1.3: Uživatel zadá název souboru
- A1.4: Systém uloží ZPL kód jako .zpl soubor
- A1.5: Systém zobrazí potvrzení
- A1.6: **Use case končí úspěchem**

### Alternativní scénář A2: Přímý tisk (pokud dostupný)
- Začíná v kroku 6
- A2.1: Zebra knihovna je dostupná (ZEBRA_AVAILABLE)
- A2.2: Uživatel klikne "Print Directly"
- A2.3: Systém odešle ZPL přímo na tiskárnu přes USB/síť
- A2.4: Tiskárna vytiskne štítek okamžitě
- A2.5: **Use case končí úspěchem**

### Výjimečný scénář E1: Prázdný kód
- Začíná v kroku 4
- E1.1: Vstupní pole je prázdné
- E1.2: Systém zobrazí placeholder text
- E1.3: Tlačítka jsou neaktivní
- E1.4: **Use case čeká na vstup**

### Preconditions
- Aplikace je spuštěna
- Uživatel zná kód skladového místa
- (Volitelně) Zebra tiskárna je připojena

### Postconditions
- **Success:** Štítek je vytištěn nebo ZPL kód exportován
- **Partial:** ZPL kód vygenerován, ale netištěn

---

## UC13: Exportovat BOM do CSV

### Hlavní scénář
1. Uživatel klikne na tlačítko "Export CSV" na hlavní obrazovce
2. Systém zobrazí dialog pro potvrzení exportu
3. Uživatel potvrdí export
4. Systém generuje název souboru s aktuálním timestampem (BOM_YYYYMMDD_HHMMSS.csv)
5. Systém prochází všechny součástky v BOM tabulce
6. Systém vytváří CSV záznamy s hlavičkou:
   - PN, MPN, Manufacturer, Quantity, Value, Category, Projects, Storage Location, atd.
7. Systém zapisuje data do CSV souboru v pracovním adresáři
8. Systém zobrazí potvrzovací dialog s cestou k souboru
9. **Use case končí úspěchem**

### Alternativní scénář A1: Vlastní umístění
- Začíná v kroku 3
- A1.1: Uživatel klikne "Choose Location"
- A1.2: Systém zobrazí file dialog
- A1.3: Uživatel vybere adresář a název
- A1.4: Pokračuje krokem 5

### Alternativní scénář A2: BOM je prázdný
- Začíná v kroku 2
- A2.1: Systém detekuje prázdný BOM
- A2.2: Systém zobrazí varování "BOM is empty. Nothing to export."
- A2.3: **Use case končí bez akce**

### Výjimečný scénář E1: Chyba zápisu
- Začíná v kroku 7
- E1.1: Soubor nelze zapsat (oprávnění, disk plný)
- E1.2: Systém zachytí výjimku
- E1.3: Systém zobrazí chybovou hlášku s detailem
- E1.4: **Use case končí neúspěchem**

### Preconditions
- BOM obsahuje alespoň jednu součástku

### Postconditions
- **Success:** CSV soubor vytvořen s aktuálními daty BOM
- **Failure:** Žádný soubor nevytvořen, error zobrazena

---

## UC17: Vyhledat součástku v TME

### Hlavní scénář
1. Systém přijme MPN (Manufacturer Part Number) součástky
2. Systém inicializuje TME API klienta s credentials
3. Systém sestaví API request s parametry:
   - SearchPlain = MPN
   - Country = "CZ"
   - Language = "EN"
4. Systém generuje HMAC-SHA1 signaturu pro autentizaci
5. Systém odešle POST request na TME API endpoint
6. TME API zpracuje požadavek
7. TME API vrací JSON odpověď s výsledky vyhledávání
8. Systém parsuje odpověď a extrahuje:
   - Symbol (TME kód)
   - Description (popis)
   - Category (kategorie)
   - Producer (výrobce)
9. Systém ukládá nalezené informace do Part objektu
10. **Use case končí úspěchem**

### Alternativní scénář A1: Více výsledků
- Začíná v kroku 7
- A1.1: API vrací více než jeden výsledek
- A1.2: Systém použije první nejrelevantnější výsledek
- A1.3: Systém zaloguje počet nalezených variant
- A1.4: Pokračuje krokem 8

### Alternativní scénář A2: Fuzzy matching
- Začíná v kroku 7
- A2.1: Přesná shoda nenalezena
- A2.2: Systém zkouší varianty MPN (bez pomlček, mezer)
- A2.3: Pokud nalezeno, pokračuje krokem 8
- A2.4: Pokud ne, přechází na E1

### Výjimečný scénář E1: Součástka nenalezena
- Začíná v kroku 7
- E1.1: API vrací prázdný výsledek
- E1.2: Systém nastaví Category = "Unknown"
- E1.3: Systém použije pouze QR data
- E1.4: Systém loguje nedostupnost TME dat
- E1.5: **Use case končí částečným úspěchem**

### Výjimečný scénář E2: API timeout
- Začíná v kroku 5
- E2.1: TME API neodpovídá do 10 sekund
- E2.2: Systém zachytí timeout výjimku
- E2.3: Systém pokračuje bez TME dat
- E2.4: **Use case končí částečným úspěchem**

### Výjimečný scénář E3: Neplatné credentials
- Začíná v kroku 5
- E3.1: API vrací chybu autentizace (401)
- E3.2: Systém loguje chybu credentials
- E3.3: Systém deaktivuje TME integraci pro session
- E3.4: **Use case končí neúspěchem**

### Preconditions
- TME API credentials jsou nakonfigurovány
- Internetové připojení je dostupné
- MPN je platný řetězec

### Postconditions
- **Success:** Součástka obohacena o TME data
- **Partial:** Součástka má pouze QR data
- **Failure:** TME integrace dočasně vypnuta

---

## Popis formátu QR kódu

Aplikace očekává QR kód v následujícím formátu (klíč=hodnota, oddělené čárkami):

```
PN=R0805-100R,MPN=RC0805FR-07100RL,QTY=100,MFR=YAGEO,CoO=CN,PO=PO12345,URL=https://example.com,RoHS=Y
```

**Povinné položky:**
- **PN** - Part Number (interní číslo součástky)
- **MPN** - Manufacturer Part Number
- **QTY** - Quantity (množství)

**Volitelné položky:**
- **MFR** - Manufacturer (výrobce)
- **CoO** - Country of Origin (země původu)
- **PO** - Purchase Order (číslo objednávky)
- **URL** - Odkaz na datasheet
- **RoHS** - RoHS compliance (Y/N)
- **VALUE** - Hodnota součástky (např. "100R", "10uF")

Parser automaticky rozpozná formát a extrahuje jednotlivé položky do slovníku.
