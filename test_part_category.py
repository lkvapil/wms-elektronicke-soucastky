from tme_api import TMEAPI

api = TMEAPI('c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0', '4ff75f1cb3075cca95b1')

# Import funkce z bom_scanner
import sys
sys.path.insert(0, '/Users/lukaskvapil/Documents/bomManager')
from bom_scanner import get_part_category, map_tme_category_to_general

# Test kategorizace
test_parts = ['AO3401A', '2N7002', '1N5408', '100nF']

for part in test_parts:
    category = get_part_category(part, None, api)
    print(f"{part:15} → {category}")
