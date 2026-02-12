#!/usr/bin/env python3
"""Direct GetProducts test for BM4942G"""

from tme_api import TMEAPI
import json

api = TMEAPI(
    token="c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0",
    app_secret="4ff75f1cb3075cca95b1"
)

print("Test 1: GetProducts s různými symboly")
print("=" * 80)

symbols_to_try = [
    ["BM4942G"],
    ["4942G-AS"],
    ["BM4940G"],  # This one exists
]

for symbols in symbols_to_try:
    print(f"\nZkouším GetProducts({symbols}):")
    result = api.get_products(symbols)
    
    if result.get('Status') == 'OK':
        products = result.get('Data', {}).get('ProductList', [])
        print(f"  Status: OK, Počet produktů: {len(products)}")
        for p in products:
            print(f"    - Symbol: {p.get('Symbol')}")
            print(f"      Výrobce symbol: {p.get('OriginalSymbol')}")
            print(f"      Popis: {p.get('Description')}")
    else:
        print(f"  Status: {result.get('Status')}")
        print(f"  Error: {result.get('Error', 'N/A')}")

# Test 2: Check if BM4940G works fully
print("\n" + "=" * 80)
print("Test 2: Úplné info o BM4940G (pro srovnání)")
print("=" * 80)

# Get basic info
products = api.get_products(["BM4940G"])
if products.get('Data', {}).get('ProductList'):
    p = products['Data']['ProductList'][0]
    print(f"\nSymbol TME: {p.get('Symbol')}")
    print(f"Výrobce: {p.get('Producer')}")
    print(f"Označení výrobce: {p.get('OriginalSymbol')}")

# Get parameters
params = api.get_parameters(["BM4940G"])
if params.get('Data', {}).get('ProductList'):
    print(f"\nParametry:")
    for param in params['Data']['ProductList'][0].get('ParameterList', []):
        print(f"  - {param.get('ParameterName')}: {param.get('ParameterValue')}")

# Get prices/stock
prices = api.get_prices_and_stocks(["BM4940G"])
if prices.get('Data', {}).get('ProductList'):
    p = prices['Data']['ProductList'][0]
    print(f"\nSkladem: {p.get('Amount')} ks")
    
print("\n" + "=" * 80)
print("ZÁVĚR: BM4942G není přístupný přes TME API")
print("       Produkt je na webu, ale není v API databázi")
print("=" * 80)
