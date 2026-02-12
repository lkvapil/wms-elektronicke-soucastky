#!/usr/bin/env python3
"""Test script to retrieve information about DR38472.2X6 from TME API"""

from tme_api import TMEAPI

# Initialize API
api = TMEAPI(
    token="c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0",
    app_secret="4ff75f1cb3075cca95b1"
)

print("=" * 80)
print("Získávám informace o DR38472.2X6 z TME API")
print("=" * 80)

# Try different variants
variants = ["DR38472.2X6", "DR38472", "DR 38472.2X6", "DR-38472.2X6"]

for variant in variants:
    print(f"\nHledám: '{variant}'")
    search = api.search_products(variant)
    amount = search.get('Data', {}).get('Amount', 0)
    print(f"  Search výsledků: {amount}")
    
    if amount > 0:
        products = search.get('Data', {}).get('ProductList', [])
        for p in products[:3]:
            print(f"    - {p.get('Symbol')}: {p.get('Description')}")

# Try GetProducts directly
print("\n" + "=" * 80)
print("Zkouším GetProducts přímo s DR38472.2X6")
print("=" * 80)

products = api.get_products(["DR38472.2X6"])
if products.get('Status') == 'OK' and products.get('Data', {}).get('ProductList'):
    product = products['Data']['ProductList'][0]
    print(f"\n✓ PRODUKT NALEZEN:")
    print(f"  Symbol TME: {product.get('Symbol')}")
    print(f"  Označení výrobce: {product.get('OriginalSymbol')}")
    print(f"  Výrobce: {product.get('Producer')}")
    print(f"  Popis: {product.get('Description')}")
    print(f"  Kategorie: {product.get('Category')}")
    print(f"  Status: {product.get('ProductStatusList')}")
    
    # Get parameters
    params = api.get_parameters(["DR38472.2X6"])
    if params.get('Data', {}).get('ProductList'):
        print(f"\n  PARAMETRY:")
        for param in params['Data']['ProductList'][0].get('ParameterList', []):
            print(f"    - {param.get('ParameterName')}: {param.get('ParameterValue')}")
    
    # Get prices and stock
    prices = api.get_prices_and_stocks(["DR38472.2X6"])
    if prices.get('Data', {}).get('ProductList'):
        p = prices['Data']['ProductList'][0]
        print(f"\n  DOSTUPNOST:")
        print(f"    Skladem: {p.get('Amount')} ks")
        price_list = p.get('PriceList', [])
        if price_list:
            print(f"    Cena: {price_list[0].get('PriceValue')} {prices['Data'].get('Currency')}/ks")
else:
    print("\n✗ Produkt nebyl nalezen")
    print(f"  Status: {products.get('Status')}")
