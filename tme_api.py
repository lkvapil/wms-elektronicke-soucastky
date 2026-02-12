#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TME API Integration
Transfer Multisort Elektronik API for searching and fetching product information
"""

import hashlib
import hmac
import base64
import requests
from urllib.parse import quote, urlencode


class TMEAPI:
    """TME API Client"""
    
    def __init__(self, token, app_secret):
        """
        Initialize TME API client
        
        Args:
            token: Private token (50 characters)
            app_secret: Application secret (20 characters)
        """
        self.token = token
        self.app_secret = app_secret
        self.base_url = "https://api.tme.eu"
        self.default_country = "CZ"  # Czech Republic
        self.default_language = "EN"
        self.default_currency = "EUR"
    
    def _generate_signature(self, method, uri, params):
        """
        Generate HMAC-SHA1 signature for API request
        
        Args:
            method: HTTP method (POST)
            uri: API endpoint URI
            params: Dictionary of parameters
            
        Returns:
            str: Base64 encoded signature
        """
        # Remove ApiSignature from params if exists
        params_copy = {k: v for k, v in params.items() if k != 'ApiSignature'}
        
        # Sort parameters alphabetically
        sorted_params = sorted(params_copy.items())
        
        # URL encode parameters
        encoded_params = []
        for key, value in sorted_params:
            if isinstance(value, list):
                for i, item in enumerate(value):
                    encoded_key = quote(f"{key}[{i}]", safe='')
                    encoded_value = quote(str(item), safe='')
                    encoded_params.append(f"{encoded_key}={encoded_value}")
            else:
                encoded_key = quote(str(key), safe='')
                encoded_value = quote(str(value), safe='')
                encoded_params.append(f"{encoded_key}={encoded_value}")
        
        params_string = '&'.join(encoded_params)
        
        # Create signature base
        signature_base_parts = [
            method.upper(),
            quote(uri, safe=''),
            quote(params_string, safe='')
        ]
        signature_base = '&'.join(signature_base_parts)
        
        # Generate HMAC-SHA1 signature
        key = self.app_secret.encode('utf-8')
        message = signature_base.encode('utf-8')
        signature = hmac.new(key, message, hashlib.sha1).digest()
        
        # Encode with Base64
        return base64.b64encode(signature).decode('utf-8')
    
    def _make_request(self, action, params, response_format='json'):
        """
        Make API request with proper signature
        
        Args:
            action: API action (e.g., 'Products/Search')
            params: Dictionary of parameters
            response_format: 'json' or 'xml'
            
        Returns:
            dict: API response data
        """
        # Add Token to params
        params['Token'] = self.token
        
        # Build URI
        uri = f"{self.base_url}/{action}.{response_format}"
        
        # Generate signature
        signature = self._generate_signature('POST', uri, params)
        params['ApiSignature'] = signature
        
        # Flatten lists in params for requests.post
        # TME API expects SymbolList[0]=value1&SymbolList[1]=value2
        flattened_params = {}
        for key, value in params.items():
            if isinstance(value, list):
                for i, item in enumerate(value):
                    flattened_params[f"{key}[{i}]"] = str(item)
            else:
                flattened_params[key] = value
        
        # Make request
        try:
            response = requests.post(uri, data=flattened_params, timeout=10)
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
    
    def ping(self):
        """Test API connection"""
        params = {}
        return self._make_request('Utils/Ping', params)
    
    def search_products(self, search_text, page=1, with_stock=False, category_id=None):
        """
        Search for products
        
        Args:
            search_text: Search query (e.g., "1N4007", "resistor 100k")
            page: Page number (20 items per page)
            with_stock: Filter only products with stock
            category_id: Category ID to search within
            
        Returns:
            dict: Search results
        """
        params = {
            'Country': self.default_country,
            'Language': self.default_language,
            'SearchPlain': search_text,
            'SearchPage': page,
        }
        
        if with_stock:
            params['SearchWithStock'] = 1
        
        if category_id:
            params['SearchCategory'] = category_id
        
        return self._make_request('Products/Search', params)
    
    def get_products(self, symbol_list):
        """
        Get product details
        
        Args:
            symbol_list: List of product symbols (max 50)
            
        Returns:
            dict: Product details
        """
        if isinstance(symbol_list, str):
            symbol_list = [symbol_list]
        
        params = {
            'Country': self.default_country,
            'Language': self.default_language,
            'SymbolList': symbol_list
        }
        
        return self._make_request('Products/GetProducts', params)
    
    def get_prices_and_stocks(self, symbol_list):
        """
        Get product prices and stock levels
        
        Args:
            symbol_list: List of product symbols (max 50)
            
        Returns:
            dict: Prices and stock data
        """
        if isinstance(symbol_list, str):
            symbol_list = [symbol_list]
        
        params = {
            'Country': self.default_country,
            'Language': self.default_language,
            'Currency': self.default_currency,
            'SymbolList': symbol_list
        }
        
        return self._make_request('Products/GetPricesAndStocks', params)
    
    def get_prices(self, symbol_list):
        """
        Get product prices
        
        Args:
            symbol_list: List of product symbols (max 50)
            
        Returns:
            dict: Price data
        """
        if isinstance(symbol_list, str):
            symbol_list = [symbol_list]
        
        params = {
            'Country': self.default_country,
            'Language': self.default_language,
            'Currency': self.default_currency,
            'SymbolList': symbol_list
        }
        
        return self._make_request('Products/GetPrices', params)
    
    def get_stocks(self, symbol_list):
        """
        Get product stock levels
        
        Args:
            symbol_list: List of product symbols (max 50)
            
        Returns:
            dict: Stock data
        """
        if isinstance(symbol_list, str):
            symbol_list = [symbol_list]
        
        params = {
            'Country': self.default_country,
            'Language': self.default_language,
            'SymbolList': symbol_list
        }
        
        return self._make_request('Products/GetStocks', params)
    
    def get_parameters(self, symbol_list):
        """
        Get product parameters/specifications
        
        Args:
            symbol_list: List of product symbols (max 50)
            
        Returns:
            dict: Product parameters
        """
        if isinstance(symbol_list, str):
            symbol_list = [symbol_list]
        
        params = {
            'Country': self.default_country,
            'Language': self.default_language,
            'SymbolList': symbol_list
        }
        
        return self._make_request('Products/GetParameters', params)
    
    def autocomplete(self, phrase):
        """
        Get product suggestions for autocomplete
        
        Args:
            phrase: Search phrase
            
        Returns:
            dict: Product suggestions
        """
        params = {
            'Country': self.default_country,
            'Language': self.default_language,
            'Phrase': phrase
        }
        
        return self._make_request('Products/Autocomplete', params)
    
    def get_categories(self, category_id=None, tree=True):
        """
        Get product categories
        
        Args:
            category_id: Optional category ID to narrow results
            tree: Return as tree structure
            
        Returns:
            dict: Categories
        """
        params = {
            'Country': self.default_country,
            'Language': self.default_language,
            'Tree': 1 if tree else 0
        }
        
        if category_id:
            params['CategoryId'] = category_id
        
        return self._make_request('Products/GetCategories', params)


# Example usage
if __name__ == '__main__':
    # IMPORTANT: You need to get your own token from https://developers.tme.eu
    # This is just the application secret
    APP_SECRET = "4ff75f1cb3075cca95b1"
    
    # You need to generate a private token (50 characters) at developers.tme.eu
    # and link it with your TME account
    PRIVATE_TOKEN = "your_private_token_here_50_characters_long_string"
    
    # Initialize API
    api = TMEAPI(PRIVATE_TOKEN, APP_SECRET)
    
    # Test connection
    print("Testing API connection...")
    result = api.ping()
    print(f"Ping result: {result}")
    
    # Search for products
    print("\nSearching for '1N4007' diode...")
    search_result = api.search_products("1N4007")
    if search_result.get('Status') == 'OK':
        products = search_result.get('Data', {}).get('ProductList', [])
        print(f"Found {len(products)} products")
        for product in products[:3]:  # Show first 3
            print(f"  - {product.get('Symbol')}: {product.get('Description')}")
    
    # Get product details
    print("\nGetting details for 1N4007...")
    details = api.get_products("1N4007")
    if details.get('Status') == 'OK':
        product_list = details.get('Data', {}).get('ProductList', [])
        if product_list:
            product = product_list[0]
            print(f"  Symbol: {product.get('Symbol')}")
            print(f"  Description: {product.get('Description')}")
            print(f"  Producer: {product.get('Producer')}")
            print(f"  Category: {product.get('CategoryName')}")
    
    # Get prices and stock
    print("\nGetting prices and stock for 1N4007...")
    prices_stocks = api.get_prices_and_stocks("1N4007")
    if prices_stocks.get('Status') == 'OK':
        data = prices_stocks.get('Data', {})
        product_list = data.get('ProductList', [])
        if product_list:
            product = product_list[0]
            print(f"  Available: {product.get('Amount')} pcs")
            price_list = product.get('PriceList', [])
            if price_list:
                print(f"  Prices:")
                for price_item in price_list[:3]:  # Show first 3 price tiers
                    print(f"    {price_item.get('Amount')}+ pcs: {price_item.get('PriceValue')} {data.get('Currency')}")
