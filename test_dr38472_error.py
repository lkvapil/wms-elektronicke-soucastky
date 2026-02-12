#!/usr/bin/env python3
"""Test scanning error DR38472.2X6 -> DR384/2.2X6"""

import sys
sys.path.insert(0, '/Users/lukaskvapil/Documents/bomManager')

from bom_scanner import fix_czech_chars, find_tme_symbol_fuzzy
from tme_api import TMEAPI

# Initialize TME API
tme_api = TMEAPI(
    token="c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0",
    app_secret="4ff75f1cb3075cca95b1"
)

print("=" * 80)
print("TEST: Oprava chyby skenování DR38472.2X6 -> DR384/2.2X6")
print("=" * 80)

scanned = "DR38472.2X6"
expected = "DR384/2.2X6"

print(f"\nNaskenováno: '{scanned}'")
print(f"Očekáváno:   '{expected}'")

# Step 1: Fix Czech chars
fixed = fix_czech_chars(scanned)
print(f"\n1. Po fix_czech_chars: '{fixed}'")

# Step 2: TME fuzzy matching
print(f"\n2. TME fuzzy matching:")
tme_symbol = find_tme_symbol_fuzzy(fixed, tme_api)

if tme_symbol:
    print(f"   ✓ Nalezeno: {tme_symbol}")
    
    # Get product details
    try:
        products = tme_api.get_products([tme_symbol])
        if products.get('Data', {}).get('ProductList'):
            product = products['Data']['ProductList'][0]
            print(f"\n   📦 Informace o produktu:")
            print(f"   - Symbol TME: {product.get('Symbol')}")
            print(f"   - Výrobce: {product.get('Producer')}")
            print(f"   - Popis: {product.get('Description')}")
            
            # Check stock
            prices = tme_api.get_prices_and_stocks([tme_symbol])
            if prices.get('Data', {}).get('ProductList'):
                stock = prices['Data']['ProductList'][0]
                print(f"   - Skladem: {stock.get('Amount')} ks")
    except Exception as e:
        print(f"   Chyba při získávání detailů: {e}")
else:
    print(f"   ✗ Produkt nenalezen")

print("\n" + "=" * 80)
if tme_symbol == expected:
    print("✓ ÚSPĚCH: Správný produkt nalezen!")
else:
    print(f"✗ PROBLÉM: Nalezeno '{tme_symbol}', očekáváno '{expected}'")
print("=" * 80)
