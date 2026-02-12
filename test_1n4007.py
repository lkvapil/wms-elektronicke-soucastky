#!/usr/bin/env python3
"""Test s produktem který určitě existuje"""

from tme_api import TMEAPI

api = TMEAPI(
    token="c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0",
    app_secret="4ff75f1cb3075cca95b1"
)

print("Test 1: Search pro 1N4007")
search = api.search_products("1N4007")
if search.get('Data', {}).get('ProductList'):
    symbol = search['Data']['ProductList'][0].get('Symbol')
    print(f"  Našel jsem: {symbol}")
    
    print(f"\nTest 2: GetProducts pro {symbol}")
    products = api.get_products([symbol])
    print(f"  Status: {products.get('Status')}")
    
    if products.get('Status') == 'OK':
        p = products['Data']['ProductList'][0]
        print(f"  Symbol: {p.get('Symbol')}")
        print(f"  Výrobce: {p.get('Producer')}")
        print(f"  Popis: {p.get('Description')}")
        
        print(f"\nTest 3: GetParameters pro {symbol}")
        params = api.get_parameters([symbol])
        if params.get('Data', {}).get('ProductList'):
            print("  Parametry:")
            for param in params['Data']['ProductList'][0].get('ParameterList', [])[:5]:
                print(f"    - {param.get('ParameterName')}: {param.get('ParameterValue')}")
        
        print(f"\nTest 4: GetPricesAndStocks pro {symbol}")
        prices = api.get_prices_and_stocks([symbol])
        if prices.get('Data', {}).get('ProductList'):
            stock = prices['Data']['ProductList'][0]
            print(f"  Skladem: {stock.get('Amount')} ks")
            print(f"  První cena: {stock.get('PriceList', [{}])[0].get('PriceValue')} CZK/ks")
    else:
        print(f"  Error: {products.get('Error')}")
