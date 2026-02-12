#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test TME API connection
"""

from tme_api import TMEAPI

# Application secret (20 characters)
APP_SECRET = "4ff75f1cb3075cca95b1"

# Real token (50 characters)
REAL_TOKEN = "c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0"

print("=" * 60)
print("TME API Connection Test")
print("=" * 60)

# Initialize API with real credentials
api = TMEAPI(REAL_TOKEN, APP_SECRET)

print("\n1. Testing Ping endpoint...")
result = api.ping()
print(f"Status: {result.get('Status')}")
if result.get('Status') != 'OK':
    print(f"Error: {result}")
else:
    print(f"Response: {result}")

print("\n2. Testing product search (1N4007)...")
search_result = api.search_products("1N4007")
print(f"Status: {search_result.get('Status')}")
if search_result.get('Status') != 'OK':
    print(f"Error: {search_result}")
else:
    data = search_result.get('Data', {})
    products = data.get('ProductList', [])
    print(f"Found {len(products)} products")
    if products:
        for i, product in enumerate(products[:3], 1):
            print(f"  {i}. {product.get('Symbol')}: {product.get('Description', 'N/A')[:60]}")

print("\n" + "=" * 60)
print("Test completed.")
print("\nTo use TME API properly, you need to:")
print("1. Register at https://developers.tme.eu/signup")
print("2. Generate a Private Token (50 characters)")
print("3. Link the token with your TME account")
print("4. Replace DUMMY_TOKEN in this script with your real token")
print("=" * 60)
