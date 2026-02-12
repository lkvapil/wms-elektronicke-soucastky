#!/usr/bin/env python3
"""Try to find BM4942G using category browsing"""

from tme_api import TMEAPI
import json

api = TMEAPI(
    token="c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0",
    app_secret="4ff75f1cb3075cca95b1"
)

# According to webpage URL: /tesneni/ = gaskets category
# Try to find category ID for gaskets

# 1. Search for similar products and check their categories
print("Zjišťuji kategorii těsnění (gaskets):")
print("=" * 80)

search = api.search_products("BM4940G")  # This one exists
if search.get('Data', {}).get('ProductList'):
    product = search['Data']['ProductList'][0]
    print(f"\nProdukt BM4940G:")
    print(f"  Symbol: {product.get('Symbol')}")
    print(f"  Kategorie ID: {product.get('CategoryId')}")
    print(f"  Kategorie: {product.get('Category')}")
    
    # Now search within this category for BM49*G gaskets
    category_id = product.get('CategoryId')
    if category_id:
        print(f"\nHledám všechny BM49xxG v kategorii {category_id}:")
        
        for variant in ["BM4941G", "BM4942G", "BM4943G", "BM4944G", "BM4945G", "BM4946G"]:
            search_cat = api.search_products(variant, category_id=category_id)
            amount = search_cat.get('Data', {}).get('Amount', 0)
            print(f"  {variant}: {amount} výsledků")
            if amount > 0:
                prod = search_cat['Data']['ProductList'][0]
                print(f"    -> {prod.get('Symbol')}: {prod.get('Description')}")

# 2. Try searching for exact manufacturer symbol
print("\n" + "=" * 80)
print("Zkouším přesný symbol výrobce '4942G-AS':")
search2 = api.search_products("4942G-AS")
amount2 = search2.get('Data', {}).get('Amount', 0)
print(f"Výsledků: {amount2}")
if amount2 > 0:
    for p in search2['Data']['ProductList'][:5]:
        print(f"  - {p.get('Symbol')}: {p.get('OriginalSymbol')} | {p.get('Description')}")

# 3. Try variations
print("\n" + "=" * 80)
print("Zkouším varianty:")
for var in ["4942G AS", "4942GAS", "4942-G-AS", "4942 G AS"]:
    s = api.search_products(var)
    a = s.get('Data', {}).get('Amount', 0)
    print(f"  '{var}': {a} výsledků")
    if a > 0:
        print(f"    -> {s['Data']['ProductList'][0].get('Symbol')}")
