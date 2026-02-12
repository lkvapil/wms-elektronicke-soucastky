#!/usr/bin/env python3
"""Broader search for DR38472"""

from tme_api import TMEAPI

api = TMEAPI(
    token="c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0",
    app_secret="4ff75f1cb3075cca95b1"
)

print("Širší vyhledávání:")
print("=" * 80)

# Try partial searches
searches = ["DR384", "DR38", "38472", "DR"]

for term in searches:
    print(f"\nHledám: '{term}'")
    search = api.search_products(term)
    amount = search.get('Data', {}).get('Amount', 0)
    print(f"  Výsledků: {amount}")
    
    if amount > 0 and amount < 10:
        products = search.get('Data', {}).get('ProductList', [])
        for p in products:
            symbol = p.get('Symbol')
            if '38472' in symbol or 'DR' in symbol:
                print(f"    ✓ {symbol}: {p.get('Description')}")

# Try autocomplete
print("\n" + "=" * 80)
print("Autocomplete pro 'DR38':")
autocomplete = api.autocomplete("DR38")
if autocomplete.get('Data', {}).get('Result'):
    for item in autocomplete['Data']['Result'][:10]:
        prod = item.get('Product', {})
        symbol = prod.get('Symbol')
        if '384' in symbol or '38' in symbol:
            print(f"  {symbol}: {prod.get('Description')}")
