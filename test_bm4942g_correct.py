#!/usr/bin/env python3
"""Test script to retrieve ALL information about BM4942G from TME API"""

from tme_api import TMEAPI

# Initialize API
api = TMEAPI(
    token="c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0",
    app_secret="4ff75f1cb3075cca95b1"
)

print("=" * 80)
print("Získávám všechny informace o BM4942G z TME API")
print("=" * 80)

# 0. First try to search
print("\n0. VYHLEDÁVÁNÍ")
print("-" * 80)
search = api.search_products("BM4942G")
print(f"Search results: Found {search.get('Data', {}).get('Amount', 0)} products")
if search.get('Data', {}).get('ProductList'):
    for p in search['Data']['ProductList'][:3]:
        print(f"  - {p.get('Symbol')}: {p.get('Description')}")

# 1. Get basic product information
print("\n1. ZÁKLADNÍ INFORMACE O PRODUKTU")
print("-" * 80)
products = api.get_products(["BM4942G"])
print(f"GetProducts response: {products}")
if products and products.get('Data', {}).get('ProductList'):
    product = products['Data']['ProductList'][0]
    print(f"Symbol TME: {product.get('Symbol')}")
    print(f"Označení výrobce: {product.get('OriginalSymbol')}")
    print(f"Výrobce: {product.get('Producer')}")
    print(f"Popis: {product.get('Description')}")
    print(f"Kategorie: {product.get('Category')}")
    print(f"EAN: {product.get('EAN')}")
    print(f"WarehouseStatus: {product.get('WarehouseStatus')}")
    
# 2. Get parameters (specifications)
print("\n2. PARAMETRY A SPECIFIKACE")
print("-" * 80)
params = api.get_parameters(["BM4942G"])
if params and params.get('Data', {}).get('ProductList'):
    product_params = params['Data']['ProductList'][0]
    print(f"\nParametry pro {product_params.get('Symbol')}:")
    for param in product_params.get('ParameterList', []):
        print(f"  - {param.get('ParameterName')}: {param.get('ParameterValue')}")

# 3. Get prices and stock availability
print("\n3. CENY A DOSTUPNOST")
print("-" * 80)
prices = api.get_prices_and_stocks(["BM4942G"])
if prices and prices.get('Data', {}).get('ProductList'):
    product_price = prices['Data']['ProductList'][0]
    print(f"\nSklad a ceny pro {product_price.get('Symbol')}:")
    print(f"  Skladem: {product_price.get('Amount')} ks")
    print(f"  Dodací lhůta: {product_price.get('DeliveryDate')}")
    print(f"\n  Cenové stupně:")
    for price_break in product_price.get('PriceList', []):
        print(f"    {price_break.get('Amount'):>5} ks -> {price_break.get('PriceValue'):>8.4f} CZK/ks")

# 4. Get product files (documentation)
print("\n4. DOKUMENTACE")
print("-" * 80)
if products and products.get('Data', {}).get('ProductList'):
    product = products['Data']['ProductList'][0]
    files = product.get('Files', [])
    if files:
        print(f"\nDostupné dokumenty:")
        for file in files:
            print(f"  - {file.get('DocumentType')}: {file.get('DocumentUrl')}")
    else:
        print("  Žádné dokumenty nejsou dostupné")

# 5. Get photos
print("\n5. OBRÁZKY")
print("-" * 80)
if products and products.get('Data', {}).get('ProductList'):
    product = products['Data']['ProductList'][0]
    photo = product.get('Photo')
    if photo:
        print(f"  Hlavní obrázek: {photo}")
    photos = product.get('Photos', [])
    if photos:
        print(f"  Počet obrázků: {len(photos)}")
        for i, photo_url in enumerate(photos, 1):
            print(f"    {i}. {photo_url}")

print("\n" + "=" * 80)
print("KONEC - Všechny dostupné informace zobrazeny")
print("=" * 80)
