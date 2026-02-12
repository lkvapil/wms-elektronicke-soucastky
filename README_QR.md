# QR Reader pro české současky

Tento skript umožňuje načítat QR kódy z obrázků českých součastek a extrahovat platební informace.

## Instalace

1. Nainstalujte potřebné knihovny:
```bash
pip install -r requirements.txt
```

2. Na macOS může být potřeba nainstalovat zbar:
```bash
brew install zbar
```

## Použití

```bash
python qr_reader.py cesta/k/obrazku/sousenky.jpg
```

## Podporovaný formát

Skript podporuje české QR platby ve formátu SPD (Short Payment Descriptor), který obsahuje:
- Číslo účtu příjemce
- Částku
- Měnu
- Variabilní, specifický a konstantní symbol
- Zprávu pro příjemce
- Další platební údaje

## Výstup

Skript vytvoří nový obrázek s příponou `_detected.jpg`, kde budou QR kódy vyznačeny zeleným rámečkem.
