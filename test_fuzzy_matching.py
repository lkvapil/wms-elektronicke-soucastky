#!/usr/bin/env python3
"""Test fix_czech_chars and TME fuzzy matching"""

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
print("TEST: Oprava českých znaků a TME fuzzy matching")
print("=" * 80)

# Test 1: Fix Czech chars with underscore instead of slash
test_cases = [
    ("DR384_2.2X6", "DR384/2.2X6"),  # Underscore -> slash
    ("DR384-2.2X6", "DR384/2.2X6"),  # Dash -> slash  
    ("BM4942G", "BM4942G"),  # No change
    ("BM4í4čG", "BM4942G"),  # Czech numbers
]

print("\n1. TEST OPRAVY ZNAKŮ:")
print("-" * 80)
for scanned, expected in test_cases:
    fixed = fix_czech_chars(scanned)
    status = "✓" if fixed == expected else "✗"
    print(f"{status} '{scanned}' -> '{fixed}' (očekáváno: '{expected}')")

# Test 2: TME Fuzzy matching
print("\n2. TEST TME FUZZY MATCHING:")
print("-" * 80)

fuzzy_tests = [
    "DR384_2.2X6",  # Underscore instead of slash
    "DR384-2.2X6",  # Dash instead of slash
    "DR384/2.2X6",  # Correct symbol
    "BM4942G",      # Symbol that exists but not in offer
]

for test_symbol in fuzzy_tests:
    print(f"\nTestuji: '{test_symbol}'")
    fixed = fix_czech_chars(test_symbol)
    print(f"  Po opravě: '{fixed}'")
    
    # Try exact match first
    try:
        products = tme_api.get_products([fixed])
        if products.get('Data', {}).get('ProductList'):
            symbol = products['Data']['ProductList'][0].get('Symbol')
            print(f"  ✓ Přímé nalezení: {symbol}")
            continue
    except:
        pass
    
    # Try fuzzy match
    fuzzy_symbol = find_tme_symbol_fuzzy(fixed, tme_api)
    if fuzzy_symbol:
        print(f"  ✓ Fuzzy match: {fuzzy_symbol}")
        # Get details
        try:
            products = tme_api.get_products([fuzzy_symbol])
            if products.get('Data', {}).get('ProductList'):
                product = products['Data']['ProductList'][0]
                print(f"    Výrobce: {product.get('Producer')}")
                print(f"    Popis: {product.get('Description')[:60]}...")
        except:
            pass
    else:
        print(f"  ✗ Nenalezeno")

print("\n" + "=" * 80)
print("ZÁVĚR:")
print("- Lomítko '/' nelze naskenovat na české klávesnici (vyžaduje AltGr)")
print("- Skener může poslat '_' (underscore) místo '/'")
print("- Funkce fix_czech_chars() opraví '_' na '/'")
print("- Pokud přesný symbol není nalezen, find_tme_symbol_fuzzy() zkusí varianty")
print("=" * 80)
