#!/usr/bin/env python3
"""Test different symbol variants for BM4942G"""

from tme_api import TMEAPI
import json

api = TMEAPI(
    token="c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0",
    app_secret="4ff75f1cb3075cca95b1"
)

variants = [
    "BM4942G",
    "4942G-AS",
    "4942G AS",
    "4942G",
    "BM 4942G",
    "bm4942g",  # lowercase
]

print("Testování různých variant symbolu:")
print("=" * 80)

for variant in variants:
    print(f"\nHledám: '{variant}'")
    search = api.search_products(variant)
    amount = search.get('Data', {}).get('Amount', 0)
    print(f"  Výsledků: {amount}")
    
    if amount > 0:
        products = search.get('Data', {}).get('ProductList', [])
        for p in products[:3]:
            print(f"    - TME: {p.get('Symbol')} | Výrobce: {p.get('OriginalSymbol')} | {p.get('Description')}")

# Try autocomplete
print("\n" + "=" * 80)
print("Zkoušíme autocomplete:")
autocomplete = api.autocomplete("bm4942")
print(json.dumps(autocomplete, indent=2, ensure_ascii=False))
