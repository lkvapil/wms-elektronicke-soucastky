#!/usr/bin/env python3
"""Debug GetProducts request"""

from tme_api import TMEAPI
import requests

# Manual test
token = "c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0"
app_secret = "4ff75f1cb3075cca95b1"

symbol = "1N4007-JGD"

# Test 1: SymbolList jako list
print("Test 1: data={'SymbolList': ['1N4007-JGD']}")
api = TMEAPI(token=token, app_secret=app_secret)

# Modify _make_request temporarily to print debug info
import types

def debug_make_request(self, action, params, response_format='json'):
    params['Token'] = self.token
    uri = f"{self.base_url}/{action}.{response_format}"
    signature = self._generate_signature('POST', uri, params)
    params['ApiSignature'] = signature
    
    print(f"URI: {uri}")
    print(f"Params: {params}")
    
    try:
        response = requests.post(uri, data=params, timeout=10)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text[:500]}")
        response.raise_for_status()
        
        if response_format == 'json':
            return response.json()
        else:
            return response.text
    except requests.exceptions.RequestException as e:
        return {
            'Status': 'ERROR',
            'Error': str(e)
        }

# Replace method
api._make_request = types.MethodType(debug_make_request, api)

# Try get_products
result = api.get_products([symbol])
print(f"\nResult: {result}")
