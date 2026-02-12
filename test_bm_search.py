#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test - what is BM4942G?
"""

from tme_api import TMEAPI

APP_SECRET = "4ff75f1cb3075cca95b1"
REAL_TOKEN = "c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0"

api = TMEAPI(REAL_TOKEN, APP_SECRET)

print("=" * 80)
print("Analyzing BM4942G - trying to find similar products")
print("=" * 80)

# The BM prefix suggests it might be from a specific manufacturer
# Let's search for products starting with BM
searches = [
    "BM4940",
    "BM4941", 
    "BM4942",
    "BM4943",
    "BM4944",
    "BM4945",
]

for search in searches:
    print(f"\n{search}:")
    result = api.search_products(search)
    if result.get('Status') == 'OK':
        products = result.get('Data', {}).get('ProductList', [])
        if products:
            for p in products[:2]:
                print(f"  ✓ {p.get('Symbol')}: {p.get('Description', 'N/A')[:70]}")
        else:
            print(f"  ✗ Not found")

print("\n" + "=" * 80)
print("\nBM4942G je pravděpodobně:")
print("1. Součástka, která není v TME katalogu")
print("2. Nebo má jiný symbol (možná originální výrobce má jiné označení)")
print("3. Zkontroluj datasheet nebo originální označení výrobce")
print("=" * 80)
