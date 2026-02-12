#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skript pro čtení QR kódů z českých součastek (platebních dokladů)
"""

import cv2
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
    # Načtení obrázku
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"Chyba: Nelze načíst obrázek '{image_path}'")
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
        
        # Vykreslení obdélníku kolem QR kódu
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    return results, image


def parse_czech_payment_qr(qr_data):
    """
    Parsuje QR kód české současky (SPD formát)
    
    Args:
        qr_data: Textová data z QR kódu
        
    Returns:
        dict: Strukturovaná platební data
    """
    payment_info = {}
    
    # QR platba - formát SPD (Short Payment Descriptor)
    if qr_data.startswith('SPD*'):
        parts = qr_data.split('*')
        
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                key = parts[i]
                value = parts[i + 1]
                
                # Mapování klíčů
                key_mapping = {
                    'ACC': 'Číslo účtu',
                    'AM': 'Částka',
                    'CC': 'Měna',
                    'RF': 'Reference platby',
                    'RN': 'Jméno příjemce',
                    'MSG': 'Zpráva pro příjemce',
                    'VS': 'Variabilní symbol',
                    'SS': 'Specifický symbol',
                    'KS': 'Konstantní symbol',
                    'DT': 'Datum splatnosti',
                    'PT': 'Typ platby',
                    'X-PER': 'Periodicita',
                    'X-ID': 'Identifikátor platby'
                }
                
                readable_key = key_mapping.get(key, key)
                payment_info[readable_key] = value
    
    return payment_info


def main():
    """Hlavní funkce"""
    if len(sys.argv) < 2:
        print("Použití: python qr_reader.py <cesta_k_obrázku>")
        print("Příklad: python qr_reader.py sousenka.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    print(f"Načítání obrázku: {image_path}")
    print("-" * 60)
    
    result = read_qr_from_image(image_path)
    
    if result:
        qr_results, marked_image = result
        
        for idx, qr_info in enumerate(qr_results, 1):
            print(f"\nQR kód #{idx}:")
            print(f"Typ: {qr_info['type']}")
            print(f"Pozice: {qr_info['position']}")
            print(f"\nSurová data:")
            print(qr_info['data'])
            
            # Pokus o parsování platebních dat
            payment_data = parse_czech_payment_qr(qr_info['data'])
            
            if payment_data:
                print(f"\nPlatební informace:")
                for key, value in payment_data.items():
                    print(f"  {key}: {value}")
            
            print("-" * 60)
        
        # Uložení obrázku s vyznačenými QR kódy
        output_path = image_path.rsplit('.', 1)[0] + '_detected.jpg'
        cv2.imwrite(output_path, marked_image)
        print(f"\nObrázek s vyznačenými QR kódy uložen: {output_path}")


if __name__ == "__main__":
    main()
