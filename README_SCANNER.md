# BOM Manager - Scanner

Scanner GUI pro Zebra čtečku čárových kódů

## Funkce

- ✅ Automatické skenování pomocí Zebra čtečky (funguje jako klávesnice)
- ✅ Textové pole pro příjem naskenovaných kódů
- ✅ Seznam všech naskenovaných kódů s časovými razítky
- ✅ Statistiky skenování
- ✅ Export do JSON souboru
- ✅ Ruční přidání kódu
- ✅ Vymazání pole a seznamu

## Jak používat

### Spuštění aplikace

S Pythonem z ordersManager (doporučeno):
```bash
/Users/lukaskvapil/Documents/api-test/production/versionsMain/version1.24/.venv/bin/python /Users/lukaskvapil/Documents/bomManager/bom_scanner.py
```

### Skenování kódu

1. **Klikněte do textového pole** (zelený rámeček s textem "Klikněte sem a naskenujte čárový kód...")
2. **Naskenujte čárový kód Zebra čtečkou**
3. Čtečka automaticky vloží text a stiskne Enter
4. Kód se přidá do seznamu a pole se vymaže
5. Pokračujte skenováním dalšího kódu

### Ovládací tlačítka

- **🗑️ Vymazat pole** - Vymaže aktuální text v poli
- **➕ Přidat manuálně** - Přidá text z pole do seznamu (stejné jako Enter)
- **🗑️ Vymazat seznam** - Vymaže celý seznam naskenovaných kódů (s potvrzením)
- **💾 Exportovat JSON** - Uloží všechny naskenované kódy do JSON souboru

## Jak funguje Zebra čtečka

Zebra čtečka funguje jako **USB klávesnice**:
1. Připojíte ji k počítači přes USB
2. Když naskenujete čárový kód, čtečka "napíše" text jako kdybyste psali na klávesnici
3. Na konci automaticky stiskne Enter
4. Aplikace zpracuje text pomocí PyQt6 události `returnPressed`

**Není potřeba žádný speciální driver ani knihovna pro skenování!**

## Export dat

Naskenované kódy se exportují do JSON formátu:
```json
[
  {
    "code": "1234567890",
    "timestamp": "2026-01-14 12:30:45",
    "length": 10
  },
  {
    "code": "ABCDEFGH",
    "timestamp": "2026-01-14 12:31:12",
    "length": 8
  }
]
```

Soubor se jmenuje podle času: `scanned_codes_20260114_123045.json`

## Technické informace

- **Framework**: PyQt6
- **Python**: 3.10+
- **Závislosti**: Pouze PyQt6
- **Kompatibilita**: macOS, Windows, Linux

## Klávesové zkratky

- **Enter** - Zpracovat kód v poli
- **Esc** - Vymazat pole (můžete přidat, pokud chcete)

## Poznámky

- Aplikace nevaliduje formát kódu - přijímá jakýkoliv text
- Všechny naskenované kódy jsou považovány za úspěšné
- Časová razítka jsou v lokálním čase
- Seznam se uchovává v paměti do zavření aplikace
