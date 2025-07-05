#!/usr/bin/env python3
# --- test_macrozones.py ---

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the Python path
parent_dir = str(Path(__file__).resolve().parent)
sys.path.append(parent_dir)

from fetch_ads import list_macrozones, COMMON_CITIES

def test_common_cities_json():
    """Test that the common_cities.json file has the expected structure"""
    print("Testing common_cities.json structure...")
    
    # Check that each city has the expected fields
    for city_key, city_info in COMMON_CITIES.items():
        assert "idComune" in city_info, f"Missing idComune for {city_key}"
        assert "name" in city_info, f"Missing name for {city_key}"
        assert "path" in city_info, f"Missing path for {city_key}"
        assert "macrozones" in city_info, f"Missing macrozones for {city_key}"
        
        # Check that macrozones have the expected structure
        for zone_key, zone_info in city_info["macrozones"].items():
            assert "id" in zone_info, f"Missing id for macrozone {zone_key} in {city_key}"
            assert "name" in zone_info, f"Missing name for macrozone {zone_key} in {city_key}"
    
    print("✓ common_cities.json structure is valid")

def test_list_macrozones():
    """Test the list_macrozones function"""
    print("\nTesting list_macrozones function...")
    
    # Test with valid city
    print("\nListing macrozones for 'genova':")
    assert list_macrozones("genova"), "Failed to list macrozones for genova"
    
    # Test with invalid city
    print("\nListing macrozones for 'invalid_city':")
    assert not list_macrozones("invalid_city"), "Should fail for invalid city"
    
    # Test with empty city
    print("\nListing macrozones for empty city:")
    assert not list_macrozones(""), "Should fail for empty city"
    
    print("\n✓ list_macrozones function works correctly")

if __name__ == "__main__":
    print("Running macrozone tests...\n")
    
    test_common_cities_json()
    test_list_macrozones()
    
    print("\nAll tests passed!")
