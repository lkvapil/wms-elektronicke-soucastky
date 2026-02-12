#!/usr/bin/env python3
"""Test DR384/2.2X6"""

from tme_api import TMEAPI

api = TMEAPI(
    token="c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0",
    app_secret="4ff75f1cb3075cca95b1"
)

symbol = "DR384/2.2X6"

print("=" * 80)
print(f"Získávám informace o {symbol} z TME API")
print("=" * 80)

products = api.get_products([symbol])
if products.get('Status') == 'OK' and products.get('Data', {}).get('ProductList'):
    product = products['Data']['ProductList'][0]
    print(f"\n✓ PRODUKT NALEZEN:")
    print(f"  Symbol TME: {product.get('Symbol')}")
    print(f"  Označení výrobce: {product.get('OriginalSymbol')}")
    print(f"  Výrobce: {product.get('Producer')}")
    print(f"  Popis: {product.get('Description')}")
    print(f"  Kategorie: {product.get('Category')}")
    print(f"  Hmotnost: {product.get('Weight')} {product.get('WeightUnit')}")
    print(f"  Status: {product.get('ProductStatusList')}")
    
    # Get parameters
    params = api.get_parameters([symbol])
    if params.get('Data', {}).get('ProductList'):
        print(f"\n  PARAMETRY:")
        for param in params['Data']['ProductList'][0].get('ParameterList', []):
            print(f"    - {param.get('ParameterName')}: {param.get('ParameterValue')}")
    
    # Get prices and stock
    prices = api.get_prices_and_stocks([symbol])
    if prices.get('Data', {}).get('ProductList'):
        p = prices['Data']['ProductList'][0]
        print(f"\n  DOSTUPNOST:")
        print(f"    Skladem: {p.get('Amount')} ks")
        price_list = p.get('PriceList', [])
        if price_list:
            print(f"    Cenové stupně:")
            for price in price_list[:3]:
                print(f"      {price.get('Amount'):>5} ks -> {price.get('PriceValue'):>8.4f} {prices['Data'].get('Currency')}/ks")
else:
    print("\n✗ Produkt nebyl nalezen")
