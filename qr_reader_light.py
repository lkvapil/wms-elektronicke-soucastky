#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skript pro čtení QR kódů z českých součastek (platebních dokladů)
Lightweight verze bez opencv - pouze PIL + pyzbar
"""

from PIL import Image
from pyzbar import pyzbar
import sys


def read_qr_from_image(image_path):
    """
    Načte a dekóduje QR kód z obrázku současky
    
    Args:
        image_path: Cesta k obrázku současky
        
    Returns:
        dict: Dekódovaná data z QR kódu
    """
    try:
        # Načtení obrázku pomocí PIL
        image = Image.open(image_path)
    except Exception as e:
        print(f"Chyba: Nelze načíst obrázek '{image_path}': {e}")
        return None
    
    # Detekce a dekódování QR kódů
    qr_codes = pyzbar.decode(image)
    
    if not qr_codes:
        print("Nebyl nalezen žádný QR kód na obrázku")
        return None
    
    results = []
    for qr_code in qr_codes:
        # Dekódování dat
        qr_data = qr_code.data.decode('utf-8')
        qr_type = qr_code.type
        
        # Získání souřadnic QR kódu
        (x, y, w, h) = qr_code.rect
        
        result = {
            'data': qr_data,
            'type': qr_type,
            'position': (x, y, w, h)
        }
        results.append(result)
    
    return results


def parse_spayd(spayd_data):
    """
    Parsuje SPAYD formát (Short Payment Descriptor) používaný na českých současkách
    
    Args:
        spayd_data: String ve formátu SPAYD
        
    Returns:
        dict: Naparsovaná data platby
    """
    if not spayd_data.startswith('SPD*'):
        return {'error': 'Neplatný SPAYD formát'}
    
    # Odstranění prefixu SPD*verze*
    parts = spayd_data.split('*')
    version = parts[1] if len(parts) > 1 else 'unknown'
    
    # Parsování klíč-hodnota párů
    payment_data = {'version': version}
    
    # Najdeme všechny páry klíč:hodnota
    data_part = spayd_data[len(f'SPD*{version}*'):]
    pairs = data_part.split('*')
    
    for pair in pairs:
        if ':' in pair:
            key, value = pair.split(':', 1)
            payment_data[key] = value
    
    # Překlad klíčů do čitelných názvů
    readable = {}
    key_mapping = {
        'ACC': 'číslo_účtu',
        'AM': 'částka',
        'CC': 'měna',
        'MSG': 'zpráva',
        'VS': 'variabilní_symbol',
        'SS': 'specifický_symbol',
        'KS': 'konstantní_symbol',
        'DT': 'datum_splatnosti',
        'X-PER': 'počet_dní',
        'RF': 'reference'
    }
    
    for key, value in payment_data.items():
        readable_key = key_mapping.get(key, key)
        readable[readable_key] = value
    
    return readable


def main():
    if len(sys.argv) < 2:
        print("Použití: python qr_reader_light.py <cesta_k_obrazku>")
        print("Příklad: python qr_reader_light.py soucenka.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    print(f"Čtení QR kódu z obrázku: {image_path}")
    print("-" * 50)
    
    # Načtení QR kódu
    results = read_qr_from_image(image_path)
    
    if not results:
        sys.exit(1)
    
    # Zobrazení výsledků
    for i, result in enumerate(results, 1):
        print(f"\nQR kód #{i}:")
        print(f"Typ: {result['type']}")
        print(f"Pozice: x={result['position'][0]}, y={result['position'][1]}, " + 
              f"šířka={result['position'][2]}, výška={result['position'][3]}")
        print(f"\nData:")
        print(result['data'])
        
        # Pokusit se naparsovat jako SPAYD
        if result['data'].startswith('SPD*'):
            print("\nNaparsovaná platební data (SPAYD):")
            payment_info = parse_spayd(result['data'])
            for key, value in payment_info.items():
                print(f"  {key}: {value}")


if __name__ == '__main__':
    main()
