# Projekt UML - BOM Manager

**Autor:** Lukáš Kvapil  
**Datum:** 10. února 2026  
**Předmět:** Objektově orientovaná analýza a návrh  
**Téma:** Systém pro správu BOM (Bill of Materials) s QR skenováním

---

## Obsah projektu

📄 **Hlavní dokumenty:**
- [`README.md`](README.md) - Tento soubor, hlavní dokumentace projektu
- [`datovy_slovnik.md`](datovy_slovnik.md) - Kompletní datový slovník (19 tříd)
- [`scenare.md`](scenare.md) - Detailní scénáře use cases (7 UC)

🔷 **PlantUML diagramy:**
- [`class_diagram.puml`](class_diagram.puml) - Objektový model (Class Diagram)
- [`state_diagram_part.puml`](state_diagram_part.puml) - Stavový diagram třídy Part
- [`state_diagram_scanner.puml`](state_diagram_scanner.puml) - Stavový diagram třídy BOMScanner
- [`use_case_diagram.puml`](use_case_diagram.puml) - Use Case diagram (31 UC)
- [`sequence_diagram.puml`](sequence_diagram.puml) - Sekvenční diagram workflow
- [`activity_diagram.puml`](activity_diagram.puml) - Diagram aktivit kompletního procesu

---

## Rychlý přehled struktury

1. [Formulace problému](#1-formulace-problému)
2. [Datový slovník](#2-datový-slovník)
3. [Objektový model](#3-objektový-model)
4. [Stavový model](#4-stavový-model)
5. [Model interakcí](#5-model-interakcí)
6. [Závěr](#6-závěr)

---

# 1. Formulace problému

## 1.1 Popis problémové domény

Při výrobě elektronických zařízení je nezbytné efektivně spravovat **BOM (Bill of Materials)** - seznam všech použitých součástek. Tradiční metody (ruční zápis, Excel tabulky) jsou náchylné k chybám, pomalé a neumožňují snadné sledování součástek napříč projekty.

## 1.2 Cíl systému

Vytvořit desktopovou aplikaci pro:
- **Rychlé skenování** QR kódů součástek pomocí Zebra čtečky
- **Automatickou extrakci** dat z QR kódů (Part Number, Manufacturer, Quantity, atd.)
- **Integraci s TME API** pro obohacení dat o kategorie a popisy
- **Správu projektů** - přiřazování součástek k jednotlivým projektům
- **Správu skladových míst** - fyzická lokace součástek
- **Tisk štítků** pomocí Zebra tiskárny (ZPL formát)
- **Export dat** do CSV/JSON pro další zpracování

## 1.3 Klíčové požadavky

**Funkční požadavky:**
1. Automatické skenování QR kódů (čtečka funguje jako klávesnice)
2. Parsování QR kódů ve formátu `PN=hodnota,MPN=hodnota,QTY=hodnota,...`
3. Detekce duplicitních součástek a automatické sčítání množství
4. Ukládání scan historie pro každou součástku
5. Přiřazování součástek k projektům (M:N vztah)
6. Přiřazování součástek na skladová místa (M:1 vztah)
7. Generování ZPL kódu pro tisk 2x1 palcových štítků
8. Export BOM do CSV s timestampem
9. Perzistence dat v JSON formátu

**Nefunkční požadavky:**
- Rychlá odezva (< 1s pro zpracování QR kódu)
- Intuitivní GUI (PyQt6)
- Offline funkčnost (TME API volitelné)
- Multiplatformní (macOS, Windows, Linux)

## 1.4 Aktéři systému

- **Uživatel** - technik/skladník skenující součástky
- **Zebra Čtečka** - čtečka QR kódů (externí HW, funguje jako klávesnice)
- **TME API** - externí API pro informace o součástkách
- **Zebra Tiskárna** - tiskárna štítků (externí HW)

## 1.5 Rozsah projektu

Tento projekt pokrývá **kompletní workflow** od skenování součástek po tisk štítků skladových míst. Systém je plně funkční a používaný v produkci.

---

# 2. Datový slovník

**→ Viz samostatný soubor:** [`datovy_slovnik.md`](datovy_slovnik.md)

Obsahuje:
- Detailní popis všech tříd (19 tříd)
- Atributy s datovými typy a významem
- Metody se signaturami
- Kardinalita vazeb
- Kvalifikované asociace
- Invarianty systému

---

# 3. Objektový model

## 3.1 Class Diagram

**→ Viz soubor:** [`class_diagram.puml`](class_diagram.puml)

### Klíčové vlastnosti objektového modelu:

#### Zobecnění (Generalization)
Nepoužito v tomto projektu - všechny třídy jsou samostatné bez dědičnosti. Systém preferuje kompozici nad dědičností.

#### Agregace a Kompozice

**Agregace (◇):**
- `BOMManager (1) o-- (0..*) Part`
- `ProjectManager (1) o-- (0..*) Project`
- `StorageManager (1) o-- (0..*) StorageLocation`

Části (Part, Project, StorageLocation) mohou existovat nezávisle na kontejneru.

**Kompozice (◆):**
- `Part (1) *-- (1..*) ScanRecord`
- `BOMScannerMainWindow (1) *-- (1) ZPLGeneratorTab`

Části (ScanRecord, ZPLGeneratorTab) nemohou existovat bez vlastníka.

#### Kvalifikované vazby

1. **BOMManager -> Part** kvalifikováno pomocí `pn: str`
   ```
   BOMManager[pn: str] -> Part
   ```
   Umožňuje rychlý O(1) přístup k součástce podle Part Number.

2. **ProjectManager -> Project** kvalifikováno pomocí `name: str`
   ```
   ProjectManager[name: str] -> Project
   ```

3. **StorageManager -> StorageLocation** kvalifikováno pomocí `code: str`
   ```
   StorageManager[code: str] -> StorageLocation
   ```

#### Kardinalita vazeb

- `Part (0..*) -- (0..*) Project` - Many-to-Many (součástka může být ve více projektech)
- `Part (0..*) -- (0..1) StorageLocation` - Many-to-One (součástka max. na jednom místě)
- `Part (1) *-- (1..*) ScanRecord` - One-to-Many kompozice (součástka má historii skenování)

#### Atributy spojení

Pro M:N vztah `Part -- Project` nejsou potřeba atributy spojení, protože obě strany si udržují seznamy:
- `Part.projects: List[str]` - seznam názvů projektů
- `Project.parts: List[str]` - seznam Part Numbers

#### Vrstevnatá architektura

```
UI Layer (BOMScannerMainWindow, Dialogy)
    ↓
Business Logic (Managers)
    ↓
Domain Model (Entity třídy)
    ↓
External Integration (API, Drivers)
```

---

# 4. Stavový model

## 4.1 State Machine Diagram - Part

**→ Viz soubor:** [`state_diagram_part.puml`](state_diagram_part.puml)

### Stavy součástky:
1. **New** - Právě naskenováno, parsování dat
2. **InBOM** - Složený stav s vnořenými stavy:
   - **Unallocated** - Bez přiřazení
   - **PartiallyAllocated** - Má lokaci nebo projekty
   - **FullyAllocated** - Kompletně alokováno
3. **QuantityChanged** - Přechodný stav po re-skenování
4. **LowStock** - Nízký stav zásob
5. **OutOfStock** - Vyprodáno
6. **Archived** - Archivováno

### Klíčové přechody:
- `scan_again() / add_quantity()` - Re-skenování existující součástky
- `assign_location()` - Přiřazení skladového místa
- `assign_to_project()` - Přiřazení k projektu
- `[quantity < threshold]` - Guard pro low stock
- `delete()` - Finální stav

---

## 4.2 State Machine Diagram - BOMScanner

**→ Viz soubor:** [`state_diagram_scanner.puml`](state_diagram_scanner.puml)

### Stavy aplikace:
1. **Initializing** - Inicializace (načítání dat, UI, API)
2. **Ready** - Složený stav připravenosti:
   - **Idle** - Čeká na skenování
   - **Processing** - Zpracování QR kódu (fork/join)
   - **ManagingData** - Uživatelské akce (choice pseudostate)
3. **Saving** - Ukládání před zavřením

### Dynamické vlastnosti:

**Fork/Join:**
```
CheckingExistence
    ↓ fork
    ├─> UpdatingExisting
    └─> CreatingNew
    ↓ join
SavingData
```

**Choice pseudostate:**
```
choice_action
    ├─> ViewingDetails
    ├─> EditingProjects
    ├─> AllocatingStorage
    ├─> PrintingLabels
    └─> ExportingData
```

**Entry/Exit/Do actions:**
- `entry / load_qsettings()` - Akce při vstupu do stavu
- `exit / clear_input_field()` - Akce při opuštění
- `do / search_in_bom()` - Aktivita během stavu

---

# 5. Model interakcí

## 5.1 Use Case Diagram

**→ Viz soubor:** [`use_case_diagram.puml`](use_case_diagram.puml)

### Přehled Use Cases (31 UC):

**Skenování a Správa Součástek (6 UC):**
- UC1: Naskenovat QR kód
- UC2: Parsovat data z QR kódu (<<include>> z UC1)
- UC3: Zobrazit detail součástky
- UC4: Upravit množství
- UC5: Smazat součástku
- UC15: Načíst QR z obrázku

**Správa Projektů (4 UC):**
- UC6: Vytvořit projekt
- UC7: Přiřadit součástku k projektu (<<extend>> z UC3)
- UC8: Zobrazit součástky projektu
- UC9: Upravit projekt

**Správa Skladových Míst (3 UC):**
- UC10: Vytvořit skladové místo
- UC11: Přiřadit součástku na místo (<<extend>> z UC3)
- UC12: Vytisknout štítek skladového místa

**Export a Import (3 UC):**
- UC13: Exportovat BOM do CSV
- UC14: Exportovat do JSON
- UC16: Importovat BOM

**TME Integrace (3 UC):**
- UC17: Vyhledat součástku v TME
- UC18: Získat informace o součástce (<<include>> z UC17, <<extend>> z UC2)
- UC19: Aktualizovat cenu (<<extend>> z UC18)

### Vztahy mezi aktéry a UC:
- **Uživatel** - iniciuje všechny hlavní UC
- **Zebra Čtečka** - poskytuje vstup pro UC1
- **TME API** - poskytuje data pro UC18
- **Zebra Tiskárna** - tiskne štítky v UC12

---

## 5.2 Scénáře Use Cases

**→ Viz soubor:** [`scenare.md`](scenare.md)

Obsahuje detailní scénáře pro 7 klíčových use cases:

### UC1: Naskenovat QR kód
- **Hlavní scénář:** 13 kroků od spuštění po uložení
- **Alt. A1:** Součástka již existuje (přičtení množství)
- **Alt. A2:** TME API nedostupné (použití pouze QR dat)
- **Výj. E1:** Nevalidní QR kód

### UC7: Přiřadit součástku k projektu
- **Hlavní scénář:** Checkboxy pro výběr projektů
- **Alt. A1:** Žádné projekty neexistují
- **Alt. A2:** Zrušení změn

### UC11: Přiřadit součástku na skladové místo
- **Hlavní scénář:** Výběr lokace z dropdown
- **Alt. A1:** Součástka již má místo (přepsání)
- **Alt. A2:** Skladové místo neexistuje (vytvoření)

### UC12: Vytisknout štítek skladového místa
- **Hlavní scénář:** Generování ZPL → Copy to clipboard → Tisk
- **Alt. A1:** Uložení do .zpl souboru
- **Alt. A2:** Přímý tisk (pokud Zebra lib dostupná)
- **Výj. E1:** Prázdný kód lokace

### UC13: Exportovat BOM do CSV
- **Hlavní scénář:** Export s timestampem
- **Alt. A1:** Vlastní umístění souboru
- **Alt. A2:** BOM je prázdný
- **Výj. E1:** Chyba zápisu (oprávnění)

### UC17: Vyhledat součástku v TME
- **Hlavní scénář:** API request → HMAC-SHA1 autentizace → Odpověď
- **Alt. A1:** Více výsledků (výběr prvního)
- **Alt. A2:** Fuzzy matching (varianty MPN)
- **Výj. E1:** Součástka nenalezena
- **Výj. E2:** API timeout
- **Výj. E3:** Neplatné credentials

---

## 5.3 Sekvenční Diagram

**→ Viz soubor:** [`sequence_diagram.puml`](sequence_diagram.puml)

### Zobrazené interakce:

**1. Inicializace aplikace:**
```
Uživatel -> GUI -> DB (load_bom, load_projects, load_storage_locations)
```

**2. Skenování QR kódu:**
```
Scanner -> GUI -> Parser -> TME API
         ↓
    BOMManager (add/update)
         ↓
    DB (save)
```

**3. Přiřazení skladového místa:**
```
Uživatel -> GUI -> StorageManager -> DB
```

**4. Přiřazení k projektu:**
```
Uživatel -> GUI -> ProjectManager -> DB
```

### Klíčové vlastnosti:
- **Životnost objektů:** Aktivační bloky ukazují dobu zpracování
- **Synchronní zprávy:** Plné šipky (např. parse_qr_code())
- **Návratové hodnoty:** Přerušované šipky
- **Alt fragment:** Podmíněné chování (existuje/neexistuje)

---

## 5.4 Diagram Aktivit

**→ Viz soubor:** [`activity_diagram.puml`](activity_diagram.puml)

### Workflow aplikace:

**1. Start → Inicializace**
- Načtení dat z JSON
- Init TME API
- Zobrazení GUI

**2. Cyklus skenování (repeat loop)**
- Skenovat QR kód
- Parsovat data
- **Decision:** Součástka existuje?
  - ANO: Přičíst množství + timestamp
  - NE: Fork → Vytvořit záznam + Vyhledat v TME → Join
- Aktualizovat UI
- Auto-save

**3. Volitelné kroky:**
- **Decision:** Přiřadit skladová místa?
  - Repeat: Vybrat součástku → Vybrat lokaci → Assign
- **Decision:** Tisknout štítky?
  - Repeat: Zadat kód → Generate ZPL → Choice (clipboard/soubor) → Tisk
- **Decision:** Přiřadit k projektům?
  - Repeat: Vybrat součástku → Zaškrtnout projekty → Save

**4. Export (volitelný)**
- **Decision:** Formát? CSV/JSON
- Vytvořit soubor
- Uložit

**5. Ukončení**
- Auto-save všech dat
- Uložit settings
- Stop

### Použité elementy:
- **Swimlanes:** Uživatel, Systém, Zebra Čtečka, Zebra Tiskárna
- **Decision nodes:** Diamanty pro podmínky
- **Fork/Join:** Paralelní zpracování
- **Loop nodes:** Repeat cykly
- **Note elements:** Vysvětlivky k aktivitám

---

# 6. Závěr

## 6.1 Zhodnocení projektu

### Splnění požadavků zadání:

✅ **Objektový model (Class Diagram)**
- 19 tříd organizovaných do 4 vrstev (UI, Business Logic, Domain, External)
- Agregace (`BOMManager o-- Part`)
- Kompozice (`Part *-- ScanRecord`)
- Kvalifikované vazby (slovníky s PN, name, code jako kvalifikátory)
- Kardinalita (1, 0..1, 0..*, M:N vztahy)
- Atributy vazeb (implicitně přes seznamy v obou směrech)

✅ **Stavový model (State Machine Diagrams)**
- **Part:** 6 hlavních stavů + 3 složené stavy s vnořenými substates
- **BOMScanner:** Inicializace → Ready (složený) → Saving
- Použity: composite states, fork/join, choice pseudostate
- Entry/exit/do actions, guards

✅ **Model interakcí**
- Use Case diagram: 31 use cases, 4 aktéři, include/extend vztahy
- Scénáře: 7 detailních scénářů s alternativami a výjimkami
- Sekvenční diagram: Kompletní workflow od inicializace po uložení
- Diagram aktivit: Celý životní cyklus aplikace s decision points, loops, fork/join

✅ **Datový slovník**
- Všechny třídy s detailními popisy
- Atributy s datovými typy a významem
- Metody se signaturami a účelem
- Kardinalita všech vazeb
- Invarianty systému

## 6.2 Propojení modelů

### Objektový ↔ Stavový
- Třídy `Part` a `BOMScannerMainWindow` mají stavové diagramy
- Stavy odpovídají hodnotám atributů (např. `quantity == 0` → OutOfStock)
- Metody tříd odpovídají přechodům (např. `add_quantity()` → QuantityChanged)

### Objektový ↔ Use Case
- Každý use case je realizován metodami tříd:
  - UC1 (Naskenovat) → `BOMScannerMainWindow.on_scan_received()`
  - UC7 (Přiřadit k projektu) → `PartDetailDialog.manage_projects()`
  - UC12 (Tisk štítku) → `ZPLGenerator.generate_label()`

### Stavový ↔ Sekvenční
- Stavy v State Diagram odpovídají fázím v Sequence Diagram:
  - Part.New → Sekvenční: Parser.parse()
  - Part.InBOM → Sekvenční: BOMManager.add_or_update()
  - BOMScanner.Processing → Celá sekvence zpracování QR

### Use Case ↔ Sekvenční ↔ Aktivit
- UC1 (Naskenovat) je detailně rozpracován v:
  - Sequence Diagram: Interakce mezi objekty
  - Activity Diagram: Tok aktivit s rozhodovacími body
- Všechny tři pohledy popisují stejný proces z jiných úhlů

## 6.3 Výhody objektového přístupu

1. **Modularita:** Třídy jsou nezávislé, změna jedné neovlivní ostatní
2. **Znovupoužitelnost:** Manager třídy lze použít i v jiných projektech
3. **Rozšiřitelnost:** Snadné přidání nových funkcí (např. další API)
4. **Údržba:** Jasná struktura usnadňuje hledání a opravu chyb
5. **Testovatelnost:** Každá třída/metoda testovatelná samostatně

## 6.4 Použité výrazové prostředky UML

### Class Diagram:
- Agregace (◇), Kompozice (◆), Asociace (—)
- Kvalifikované vazby [kvalifikátor]
- Kardinalita (1, 0..1, 0..*, *)
- Stereotypy (<<Entity>>, <<UI>>, <<API>>, <<Manager>>)
- Notes pro dokumentaci

### State Machine:
- Simple states, Composite states
- Initial/Final pseudostates
- Fork/Join, Choice
- Entry/Exit/Do actions
- Guards [condition]
- Transitions with events/actions

### Interaction Diagrams:
- Actors, Use cases
- Include/Extend vztahy
- Lifelines, Activation boxes
- Synchronní/asynchronní zprávy
- Alt/Opt/Loop fragments (sequence)
- Swimlanes, Decision/Merge nodes (activity)
- Fork/Join nodes (activity)

## 6.5 Možná rozšíření

1. **Multi-user:** Přidat server pro sdílení BOM mezi uživateli
2. **Historie změn:** Audit log všech operací
3. **Alerting:** Notifikace při low stock
4. **Barcode generování:** QR kódy pro vlastní součástky
5. **Statistiky:** Dashboardy s grafy spotřeby

## 6.6 Závěrečné shrnutí

Tento projekt demonstruje komplexní aplikaci objektové metodologie UML na reálný problém správy BOM. Všechny modely jsou navzájem konzistentní a doplňují se:

- **Objektový model** definuje strukturu systému
- **Stavový model** popisuje dynamické chování klíčových tříd
- **Model interakcí** zachycuje scénáře použití a komunikaci mezi objekty

Systém je navržen s důrazem na:
- Jasnou separaci vrstev (UI, Business, Domain, External)
- Vysokou kohezi a nízké párování (loose coupling)
- Snadnou rozšiřitelnost a údržbu
- Intuitivní použití pro koncového uživatele

Aplikace je funkční, otestovaná a v produkčním nasazení.

---

## Jak zobrazit diagramy

### Online
1. Otevřete [PlantUML Online Server](http://www.plantuml.com/plantuml/uml/)
2. Zkopírujte obsah .puml souboru
3. Vložte do editoru

### VS Code
1. Nainstalujte rozšíření "PlantUML"
2. Otevřete .puml soubor
3. Stiskněte `Alt+D` pro náhled

### Generování obrázků
```bash
# Instalace PlantUML
brew install plantuml  # macOS
# nebo
sudo apt-get install plantuml  # Linux

# Generování PNG
plantuml *.puml

# Generování SVG
plantuml -tsvg *.puml
```

## Obsah

### 1. Use Case Diagram (`use_case_diagram.puml`)
**Use Case diagram** zobrazuje hlavní funkcionality systému a jejich vztahy k aktérům:

**Aktéři:**
- **Uživatel** - hlavní uživatel systému
- **Zebra Čtečka** - čtečka čárových kódů (externí systém)
- **TME API** - externí API pro informace o součástkách
- **Zebra Tiskárna** - tiskárna štítků (externí systém)

**Hlavní use cases:**
- Skenování a správa součástek (17 use cases)
- Správa projektů (4 use cases)
- Správa skladových míst (3 use cases)
- Export a import dat (4 use cases)
- TME integrace (3 use cases)

### 2. Sequence Diagram (`sequence_diagram.puml`)
**Sekvenční diagram** zobrazuje tok komunikace mezi objekty při skenování součástky a jejím přiřazení:

**Hlavní flow:**
1. **Inicializace** - načtení BOM, projektů a skladových míst z JSON
2. **Skenování QR kódu** - zpracování naskenovaných dat, parsování, dotaz na TME API
3. **Přiřazení skladového místa** - výběr a přiřazení lokace
4. **Přiřazení k projektu** - výběr projektů přes checkboxy

**Účastníci:**
- Uživatel, GUI, Scanner Input, QR Parser, TME API Client, BOM Manager, Storage Manager, Project Manager, Database (JSON)

### 3. Activity Diagram (`activity_diagram.puml`)
**Diagram aktivit** zobrazuje kompletní pracovní tok při používání aplikace:

**Hlavní aktivity:**
1. Spuštění aplikace a načtení dat
2. Cyklus skenování součástek pomocí Zebra čtečky
3. Parsování QR kódů a extrakce dat (PN, MPN, QTY, atd.)
4. Kontrola existence součástky a aktualizace/přidání
5. Volitelné přiřazení skladových míst
6. Volitelný tisk štítků pomocí ZPL
7. Volitelné přiřazení k projektům
8. Export dat (CSV/JSON)
9. Automatické ukládání při zavření

**Rozhodovací body:**
- Existuje součástka v BOM?
- Nalezena v TME API?
- Potřeba přiřadit skladová místa?
- Potřeba tisknout štítky?
- Formát exportu?

## Jak zobrazit diagramy

### Online
1. Otevřete [PlantUML Online Server](http://www.plantuml.com/plantuml/uml/)
2. Zkopírujte obsah .puml souboru
3. Vložte do editoru

### VS Code
1. Nainstalujte rozšíření "PlantUML"
2. Otevřete .puml soubor
3. Stiskněte `Alt+D` pro náhled

### Generování obrázků
```bash
# Instalace PlantUML
brew install plantuml  # macOS
# nebo
sudo apt-get install plantuml  # Linux

# Generování PNG
plantuml use_case_diagram.puml
plantuml sequence_diagram.puml
plantuml activity_diagram.puml

# Generování SVG
plantuml -tsvg use_case_diagram.puml
plantuml -tsvg sequence_diagram.puml
plantuml -tsvg activity_diagram.puml
```

## Popis systému

**BOM Manager** je desktopová aplikace pro správu BOM (Bill of Materials) s těmito hlavními funkcemi:

- ✅ Automatické skenování QR kódů pomocí Zebra čtečky
- ✅ Parsování dat z QR kódů (PN, MPN, QTY, manufacturer, atd.)
- ✅ Integrace s TME API pro získání dodatečných informací
- ✅ Správa projektů a přiřazování součástek
- ✅ Správa skladových míst
- ✅ Tisk štítků pomocí ZPL (Zebra Programming Language)
- ✅ Export do CSV a JSON
- ✅ Persistentní ukládání dat

## Technologie

- **Framework**: PyQt6
- **Python**: 3.10+
- **API**: TME (Transfer Multisort Elektronik)
- **Hardware**: Zebra čtečka čárových kódů, Zebra tiskárna
- **Formát dat**: JSON (persistence), CSV (export)

---

**Datum vytvoření:** 10. února 2026  
**Verze:** 1.0
