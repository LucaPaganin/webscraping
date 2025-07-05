# Immobiliare.it Zone Data Utilities

This directory contains scripts to fetch real estate ads from Immobiliare.it API and utilities to populate zone/macrozone data for cities.

## Zone Population Scripts

### populate_zones.py

Populates zone data for specific search queries:

```bash
python populate_zones.py "Pegli, Multedo" "Castelletto" "Marassi"
```

Optional arguments:
- `--max-level`: Maximum level of detail (default: 3, which is for zones/neighborhoods)
- `--min-delay`, `--max-delay`: Control delay between API requests (default: 1.0-2.0 seconds)
- `--file`: Path to common_cities.json file

### populate_all_zones.py

Populates zone data for all cities in common_cities.json or for specific cities:

```bash
# Populate for all cities
python populate_all_zones.py --all

# Populate for specific cities
python populate_all_zones.py --cities "Genova" "Savona"
```

Optional arguments:
- `--max-level`: Maximum level of detail (default: 3)
- `--min-delay`, `--max-delay`: Control delay between API requests (default: 1.0-2.0 seconds)
- `--file`: Path to common_cities.json file

## Zone Data Structure in common_cities.json

The zone data is structured as follows:

```json
{
    "genova": {
        "idComune": "6846",
        "name": "Genova",
        "path": "/genova/",
        "macrozones": {
            "pegli_multedo": {
                "id": "10301",
                "name": "Pegli, Multedo"
            },
            "castelletto": {
                "id": "10003",
                "name": "Castelletto"
            }
        }
    }
}
```

## Using Macrozones in fetch_ads.py

You can use macrozones to filter ads by specific neighborhoods:

```bash
# Filter by macrozone IDs
python fetch_ads.py --city genova --macrozones 10301 10003

# Filter by macrozone names
python fetch_ads.py --city genova --macrozone-names pegli_multedo castelletto

# List available macrozones for a city
python fetch_ads.py --city genova --list-macrozones
```

The macrozone parameter is correctly passed to the API as:
```
idMacrozona[0]=10301&idMacrozona[1]=10003
```

This enables you to filter ads by specific neighborhoods within a city.
