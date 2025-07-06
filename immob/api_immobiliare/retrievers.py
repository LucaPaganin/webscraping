#!/usr/bin/env python3
"""
Real Estate Ad Retrievers
========================

Abstract base class and concrete implementations for retrieving real estate data from various websites.

Author: Lucas P
Date: July 6, 2025
"""

import json
import logging
import random
import time
import requests
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from real_estate_models import RealEstateAd


class RealEstateAdRetriever(ABC):
    """
    Abstract base class for real estate ad retrievers.
    
    This class defines the interface for retrieving real estate data from various sources.
    Each website implementation should inherit from this class and implement the abstract methods.
    """
    
    @classmethod
    def create_mock_retriever(cls, config: Dict[str, Any] = None) -> 'RealEstateAdRetriever':
        """
        Create a mock retriever for use with data_manager when only storage functionality is needed.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            A concrete RealEstateAdRetriever instance
        """
        from retrievers import ImmobiliareAdRetriever
        config = config or {}
        return ImmobiliareAdRetriever(config)
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the retriever with configuration.
        
        Args:
            config: Configuration dictionary containing API settings, headers, etc.
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup the requests session with headers and other configurations."""
        headers = self.config.get('headers', {})
        if headers:
            self.session.headers.update(headers)
        
        cookies = self.config.get('cookies', {})
        if cookies:
            self.session.cookies.update(cookies)
    
    @abstractmethod
    def get_city_zones(self, city: str) -> Dict[str, Any]:
        """
        Get available zones for a city.
        
        Args:
            city: City name
            
        Returns:
            Dictionary containing zone information
        """
        pass
    
    @abstractmethod
    def build_search_params(self, **kwargs) -> Dict[str, Any]:
        """
        Build search parameters for the API.
        
        Args:
            **kwargs: Search parameters (city, contract_type, zone_id, etc.)
            
        Returns:
            Dictionary of API parameters
        """
        pass
    
    @abstractmethod
    def fetch_page(self, params: Dict[str, Any], page: int) -> Tuple[List[Dict], bool]:
        """
        Fetch a single page of results.
        
        Args:
            params: API parameters
            page: Page number
            
        Returns:
            Tuple of (raw_ads_list, has_more_pages)
        """
        pass
    
    @abstractmethod
    def parse_ad(self, raw_ad: Dict[str, Any]) -> RealEstateAd:
        """
        Parse raw ad data into standardized RealEstateAd model.
        
        Args:
            raw_ad: Raw ad data from the API
            
        Returns:
            Standardized RealEstateAd instance
        """
        pass
    
    def fetch_ads(self, **search_params) -> List[RealEstateAd]:
        """
        Fetch all ads matching the search criteria.
        
        Args:
            **search_params: Search parameters
            
        Returns:
            List of RealEstateAd instances
        """
        params = self.build_search_params(**search_params)
        all_ads = []
        page = search_params.get('start_page', 1)
        max_pages = search_params.get('max_pages')
        delay_range = search_params.get('delay_range', (2.5, 5.0))
        
        self.logger.info(f"Starting to fetch ads with parameters: {params}")
        
        while True:
            try:
                # Add delay between requests
                if page > search_params.get('start_page', 1):
                    delay = random.uniform(*delay_range)
                    time.sleep(delay)
                
                raw_ads, has_more = self.fetch_page(params, page)
                
                # Parse raw ads to standardized format
                for raw_ad in raw_ads:
                    try:
                        ad = self.parse_ad(raw_ad)
                        all_ads.append(ad)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse ad: {e}")
                        continue
                
                self.logger.info(f"Page {page}: Found {len(raw_ads)} ads")
                
                # Check if we should continue
                if not has_more or (max_pages and page >= max_pages):
                    break
                
                page += 1
                
            except Exception as e:
                self.logger.error(f"Error fetching page {page}: {e}")
                break
        
        self.logger.info(f"Total ads retrieved: {len(all_ads)}")
        return all_ads
    
    @abstractmethod
    def get_ad_details(self, ad_url: str) -> Dict[str, Any]:
        """
        Fetch detailed information for a specific ad URL.
        
        Args:
            ad_url: The URL of the specific real estate advertisement
            
        Returns:
            Dictionary containing detailed information about the advertisement
        """
        pass
    
    def fetch_by_zones(self, city: str, **search_params) -> Dict[str, List[RealEstateAd]]:
        """
        Fetch ads for all zones in a city.
        
        Args:
            city: City name
            **search_params: Additional search parameters
            
        Returns:
            Dictionary mapping zone names to lists of ads
        """
        zones = self.get_city_zones(city)
        zone_ads = {}
        
        if not zones.get('zones'):
            self.logger.warning(f"No zones found for city: {city}")
            return zone_ads
        
        for zone_key, zone_info in zones['zones'].items():
            zone_name = zone_info.get('name')
            zone_id = zone_info.get('id')
            
            if not zone_id:
                self.logger.warning(f"No ID found for zone: {zone_name}")
                continue
            
            self.logger.info(f"Fetching ads for zone: {zone_name} (ID: {zone_id})")
            
            try:
                # Add zone-specific parameters
                zone_search_params = search_params.copy()
                zone_search_params.update({
                    'city': city,
                    'zone_id': zone_id,
                    'zone_name': zone_name
                })
                
                ads = self.fetch_ads(**zone_search_params)
                zone_ads[zone_name] = ads
                
                self.logger.info(f"Zone {zone_name}: Found {len(ads)} ads")
                
            except Exception as e:
                self.logger.error(f"Error fetching ads for zone {zone_name}: {e}")
                zone_ads[zone_name] = []
        
        return zone_ads


class ImmobiliareAdRetriever(RealEstateAdRetriever):
    """
    Specialized retriever for immobiliare.it website.
    
    This class implements the abstract methods from RealEstateAdRetriever
    specifically for the immobiliare.it API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Immobiliare retriever with specific configuration."""
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://www.immobiliare.it/api-next/search-list/listings/')
        
        # Load city data
        cities_file = Path(__file__).parent / "common_cities.json"
        try:
            with open(cities_file, 'r', encoding='utf-8') as f:
                self.cities_data = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading cities data: {e}")
            self.cities_data = {}
    
    def get_city_zones(self, city: str) -> Dict[str, Any]:
        """Get zones for a city from the cities database."""
        city_lower = city.lower()
        return self.cities_data.get(city_lower, {})
    
    def build_search_params(self, **kwargs) -> Dict[str, Any]:
        """Build search parameters for immobiliare.it API."""
        contract_type = kwargs.get('contract_type', 'rent')
        city = kwargs.get('city', 'genova')
        region = kwargs.get('region')
        zone_id = kwargs.get('zone_id')
        macrozones = kwargs.get('macrozones', [])
        
        # Determine contract and path parameters
        if contract_type == "rent":
            path_start = "affitto-case"
            id_contratto = "2"
        else:
            path_start = "vendita-case"
            id_contratto = "1"
        
        # Base parameters
        params = {
            "idNazione": "IT",
            "idContratto": id_contratto,
            "idCategoria": "1",
            "__lang": "it",
            "pag": 1,
            "paramsCount": 0,
            "path": f"/{path_start}/{city}/"
        }
        
        # Add region if provided
        if region:
            params["fkRegione"] = region
        
        # Add zone-specific parameters
        if zone_id:
            params["idMacrozona[0]"] = zone_id
            params["paramsCount"] = 1
        
        # Add macrozone filters
        if macrozones:
            for i, zone_id in enumerate(macrozones):
                params[f"idMacrozona[{i}]"] = zone_id
            params["paramsCount"] = len(macrozones)
        
        return params
    
    def fetch_page(self, params: Dict[str, Any], page: int) -> Tuple[List[Dict], bool]:
        """Fetch a single page from immobiliare.it API."""
        page_params = params.copy()
        page_params["pag"] = page
        
        try:
            response = self.session.get(self.base_url, params=page_params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            ads = data.get('data', {}).get('ads', [])
            
            # Check if there are more pages
            pagination = data.get('data', {}).get('pagination', {})
            current_page = pagination.get('currentPage', page)
            total_pages = pagination.get('totalPages', 1)
            has_more = current_page < total_pages
            
            return ads, has_more
            
        except requests.RequestException as e:
            self.logger.error(f"HTTP error fetching page {page}: {e}")
            return [], False
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error on page {page}: {e}")
            return [], False
    
    def parse_ad(self, raw_ad: Dict[str, Any]) -> RealEstateAd:
        """Parse raw immobiliare.it ad data into RealEstateAd model."""
        try:
            # Extract basic information
            ad_id = str(raw_ad.get('id', ''))
            title = raw_ad.get('title', '')
            url = f"https://www.immobiliare.it{raw_ad.get('path', '')}"
            
            # Parse price information
            price_info = raw_ad.get('price', {})
            price = price_info.get('value')
            price_formatted = price_info.get('formattedValue', '')
            
            # Parse property details
            property_info = raw_ad.get('properties', {})
            surface = property_info.get('surface')
            rooms = property_info.get('rooms')
            bedrooms = property_info.get('bedrooms')
            bathrooms = property_info.get('bathrooms')
            floor = property_info.get('floor')
            
            # Parse location
            location = raw_ad.get('location', {})
            address = location.get('address')
            latitude = location.get('latitude')
            longitude = location.get('longitude')
            city = location.get('city')
            zone = location.get('zone')
            
            # Parse features
            features = []
            property_features = raw_ad.get('features', [])
            if isinstance(property_features, list):
                features = [str(f) for f in property_features]
            
            # Parse images
            images = []
            image_data = raw_ad.get('images', [])
            if isinstance(image_data, list):
                for img in image_data:
                    if isinstance(img, dict) and 'url' in img:
                        images.append(img['url'])
                    elif isinstance(img, str):
                        images.append(img)
            
            # Create RealEstateAd instance
            ad = RealEstateAd(
                id=ad_id,
                source_url=url,
                source_website='immobiliare.it',
                title=title,
                contract_type=self.config.get('contract_type', 'rent'),
                price=price,
                price_formatted=price_formatted,
                surface=surface,
                rooms=rooms,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                floor=str(floor) if floor is not None else None,
                address=address,
                latitude=latitude,
                longitude=longitude,
                city=city,
                zone=zone,
                features=features,
                images=images
            )
            
            return ad
            
        except Exception as e:
            self.logger.error(f"Error parsing ad: {e}")
            # Return minimal ad with required fields
            return RealEstateAd(
                id=str(raw_ad.get('id', 'unknown')),
                source_url=f"https://www.immobiliare.it{raw_ad.get('path', '')}",
                source_website='immobiliare.it',
                title=raw_ad.get('title', 'Unknown'),
                contract_type=self.config.get('contract_type', 'rent')
            )
    
    def get_ad_details(self, ad_url: str) -> Dict[str, Any]:
        """
        Fetch detailed information for a specific ad URL from immobiliare.it.
        
        Args:
            ad_url: The URL of the specific immobiliare.it advertisement
            
        Returns:
            Dictionary containing detailed information about the advertisement
            
        Examples:
            >>> retriever = ImmobiliareAdRetriever(config)
            >>> details = retriever.get_ad_details("https://www.immobiliare.it/annunci/12345678/")
            >>> print(f"Energy class: {details.get('energy_class')}")
            >>> print(f"Year built: {details.get('year_built')}")
        """
        self.logger.info(f"Fetching details for ad: {ad_url}")
        
        # Extract ad ID from URL
        ad_id = None
        try:
            # URL format: https://www.immobiliare.it/annunci/12345678/
            if "/annunci/" in ad_url:
                parts = ad_url.strip('/').split('/')
                for i, part in enumerate(parts):
                    if part == "annunci" and i + 1 < len(parts):
                        ad_id = parts[i + 1]
                        break
            
            if not ad_id:
                raise ValueError(f"Could not extract ad ID from URL: {ad_url}")
                
        except Exception as e:
            self.logger.error(f"Error extracting ad ID from URL: {e}")
            return {"error": f"Invalid URL format: {ad_url}"}
        
        # API endpoint for detailed ad information
        details_url = f"https://www.immobiliare.it/api-next/detail/ads/{ad_id}"
        
        try:
            # Add delay to respect rate limits
            time.sleep(random.uniform(1.0, 3.0))
            
            response = self.session.get(details_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            ad_data = data.get('data', {}).get('ad', {})
            
            if not ad_data:
                self.logger.warning(f"No data returned for ad ID: {ad_id}")
                return {"error": "No data found for this advertisement"}
            
            # Extract detailed information
            details = {
                # Basic information
                "ad_id": ad_id,
                "title": ad_data.get('title'),
                "description": ad_data.get('description'),
                "last_updated": ad_data.get('lastModified'),
                
                # Property details
                "property_type": ad_data.get('typology', {}).get('name'),
                "property_condition": ad_data.get('condition', {}).get('name'),
                "year_built": ad_data.get('yearBuilt'),
                "floor": ad_data.get('floor'),
                "total_floors": ad_data.get('totalFloors'),
                "surface": ad_data.get('surfaces', {}).get('main'),
                "surface_commercial": ad_data.get('surfaces', {}).get('commercial'),
                "surface_garden": ad_data.get('surfaces', {}).get('garden'),
                "rooms": ad_data.get('rooms'),
                "bedrooms": ad_data.get('bedrooms'),
                "bathrooms": ad_data.get('bathrooms'),
                
                # Financial information
                "price": ad_data.get('price', {}).get('value'),
                "expenses": ad_data.get('expenses', {}).get('value'),
                
                # Energy information
                "energy_class": ad_data.get('energyClass', {}).get('name'),
                "energy_performance": ad_data.get('energyPerformance'),
                
                # Location details
                "address": ad_data.get('location', {}).get('address'),
                "zone": ad_data.get('location', {}).get('zone'),
                "city": ad_data.get('location', {}).get('city'),
                "latitude": ad_data.get('location', {}).get('latitude'),
                "longitude": ad_data.get('location', {}).get('longitude'),
                
                # Features and amenities
                "features": ad_data.get('features', []),
                "has_elevator": any(f.get('name') == 'elevator' for f in ad_data.get('features', [])),
                "has_garage": any(f.get('name') == 'garage' or f.get('name') == 'box' for f in ad_data.get('features', [])),
                "has_garden": any(f.get('name') == 'garden' for f in ad_data.get('features', [])),
                "has_terrace": any(f.get('name') == 'terrace' for f in ad_data.get('features', [])),
                
                # Media
                "images": [img.get('urls', {}).get('large') for img in ad_data.get('images', [])],
                "videos": [video.get('url') for video in ad_data.get('videos', [])],
                "virtual_tour": ad_data.get('virtualTour', {}).get('url'),
                
                # Agent information
                "agent": {
                    "name": ad_data.get('agency', {}).get('name'),
                    "phone": ad_data.get('agency', {}).get('phoneNumber'),
                    "email": ad_data.get('agency', {}).get('email'),
                    "website": ad_data.get('agency', {}).get('website'),
                }
            }
            
            self.logger.info(f"Successfully retrieved details for ad ID: {ad_id}")
            return details
            
        except requests.RequestException as e:
            self.logger.error(f"HTTP error fetching ad details: {e}")
            return {"error": f"Error connecting to immobiliare.it: {str(e)}"}
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error for ad details: {e}")
            return {"error": f"Error parsing response: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {"error": f"Unexpected error: {str(e)}"}
