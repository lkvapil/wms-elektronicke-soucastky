#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test TME API - Get all information about BM4942G
"""

from tme_api import TMEAPI
import json

# TME API credentials
APP_SECRET = "4ff75f1cb3075cca95b1"
REAL_TOKEN = "c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0"

print("=" * 80)
print("TME API - Complete Information for BM4942G")
print("=" * 80)

# Initialize API
api = TMEAPI(REAL_TOKEN, APP_SECRET)

# 1. Search for BM4942G
print("\n1. SEARCHING FOR 'BM4942G'...")
print("-" * 80)
search_result = api.search_products("BM4942G")

print(f"Status: {search_result.get('Status')}")
print(f"Full response: {json.dumps(search_result, indent=2, ensure_ascii=False)}")

# Try alternative searches
print("\n\n2. TRYING ALTERNATIVE SEARCHES...")
print("-" * 80)

for search_term in ["BM4942", "BM49", "4942"]:
    print(f"\nSearching for '{search_term}'...")
    alt_result = api.search_products(search_term)
    if alt_result.get('Status') == 'OK':
        products = alt_result.get('Data', {}).get('ProductList', [])
        print(f"Found {len(products)} products")
        for i, p in enumerate(products[:3], 1):
            print(f"  {i}. {p.get('Symbol')} - {p.get('Description', 'N/A')[:60]}")

if search_result.get('Status') == 'OK':
    products = search_result.get('Data', {}).get('ProductList', [])
    print(f"Found {len(products)} products\n")
    
    for i, product in enumerate(products, 1):
        print(f"{i}. {product.get('Symbol')} - {product.get('Description', 'N/A')[:80]}")
        if i >= 5:  # Show max 5 results
            break
    
    if products:
        # Use first result
        symbol = products[0].get('Symbol')
        print(f"\n\nUsing: {symbol}")
        
        # 2. Get product details
        print("\n\n2. PRODUCT DETAILS")
        print("-" * 80)
        details = api.get_products(symbol)
        
        if details.get('Status') == 'OK':
            prod_list = details.get('Data', {}).get('ProductList', [])
            if prod_list:
                product = prod_list[0]
                print(f"Symbol:           {product.get('Symbol', 'N/A')}")
                print(f"Original Symbol:  {product.get('OriginalSymbol', 'N/A')}")
                print(f"Producer:         {product.get('Producer', 'N/A')}")
                print(f"Description:      {product.get('Description', 'N/A')}")
                print(f"Category:         {product.get('CategoryName', 'N/A')}")
                print(f"Category ID:      {product.get('CategoryId', 'N/A')}")
                print(f"Weight:           {product.get('Weight', 'N/A')} g")
                print(f"Photo:            {product.get('Photo', 'N/A')}")
                print(f"Thumbnail:        {product.get('Thumbnail', 'N/A')}")
                print(f"Product URL:      https://www.tme.eu/cz/details/{symbol}/")
                
                # Product status flags
                statuses = product.get('ProductStatusList', [])
                if statuses:
                    print(f"\nStatus Flags:     {', '.join(statuses)}")
        
        # 3. Get prices and stock
        print("\n\n3. PRICES AND STOCK")
        print("-" * 80)
        prices_stocks = api.get_prices_and_stocks(symbol)
        
        if prices_stocks.get('Status') == 'OK':
            data = prices_stocks.get('Data', {})
            prod_list = data.get('ProductList', [])
            
            if prod_list:
                product = prod_list[0]
                print(f"Available Stock:  {product.get('Amount', 'N/A')} pcs")
                print(f"Unit:             {product.get('Unit', 'N/A')}")
                print(f"Min. Order:       {product.get('Multiples', 'N/A')} pcs")
                print(f"Currency:         {data.get('Currency', 'N/A')}")
                print(f"Price Type:       {data.get('PriceType', 'N/A')}")
                
                price_list = product.get('PriceList', [])
                if price_list:
                    print(f"\nPrice Tiers ({data.get('Currency', 'EUR')}):")
                    for price in price_list:
                        print(f"  {price.get('Amount'):>6}+ pcs:  {price.get('PriceValue'):>10} {data.get('Currency')}")
        
        # 4. Get parameters
        print("\n\n4. TECHNICAL PARAMETERS")
        print("-" * 80)
        params_result = api.get_parameters(symbol)
        
        if params_result.get('Status') == 'OK':
            prod_list = params_result.get('Data', {}).get('ProductList', [])
            if prod_list:
                params = prod_list[0].get('ParameterList', [])
                if params:
                    for param in params:
                        name = param.get('ParameterName', 'N/A')
                        value = param.get('ParameterValue', 'N/A')
                        print(f"{name:.<40} {value}")
                else:
                    print("No parameters available")
        
        # 5. Get delivery time
        print("\n\n5. DELIVERY TIME")
        print("-" * 80)
        # Get delivery time needs amount parameter
        # Let's check for different quantities
        for qty in [1, 10, 100]:
            delivery = api._make_request('Products/GetDeliveryTime', {
                'Country': api.default_country,
                'SymbolList': [symbol],
                'AmountList': [qty]
            })
            
            if delivery.get('Status') == 'OK':
                prod_list = delivery.get('Data', {}).get('ProductList', [])
                if prod_list:
                    product = prod_list[0]
                    time_min = product.get('DeliveryTime', {}).get('Min', 'N/A')
                    time_max = product.get('DeliveryTime', {}).get('Max', 'N/A')
                    print(f"For {qty:>3} pcs:  {time_min}-{time_max} days")
        
        # 6. Get product files (datasheets, manuals, etc.)
        print("\n\n6. PRODUCT FILES")
        print("-" * 80)
        files_result = api._make_request('Products/GetProductsFiles', {
            'Country': api.default_country,
            'Language': api.default_language,
            'SymbolList': [symbol]
        })
        
        if files_result.get('Status') == 'OK':
            prod_list = files_result.get('Data', {}).get('ProductList', [])
            if prod_list:
                files = prod_list[0].get('Files', [])
                if files:
                    for file_info in files:
                        file_type = file_info.get('DocumentType', 'N/A')
                        file_url = file_info.get('DocumentUrl', 'N/A')
                        print(f"{file_type:.<20} {file_url}")
                else:
                    print("No files available")
        
        # 7. Raw JSON dump
        print("\n\n7. RAW JSON DATA")
        print("-" * 80)
        print("\nSearch Result:")
        print(json.dumps(products[0], indent=2, ensure_ascii=False))
        
else:
    print(f"Search failed: {search_result}")

print("\n" + "=" * 80)
print("Test completed")
print("=" * 80)
