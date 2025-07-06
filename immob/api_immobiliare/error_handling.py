#!/usr/bin/env python3
"""
Error Handling and Logging Utilities
===================================

This module provides error handling and logging utilities for the real estate scraping project.
It includes custom exceptions, retry decorators, and a comprehensive logging setup.

Author: Lucas P
Date: July 6, 2025
"""

import os
import sys
import time
import logging
import functools
import traceback
import requests
from typing import Dict, List, Tuple, Optional, Any, Set, Callable, Type, Union
from datetime import datetime
from pathlib import Path

# Configure default logger
logger = logging.getLogger(__name__)


# Custom Exceptions
class RealEstateScraperError(Exception):
    """Base exception for all real estate scraper errors."""
    pass


class NetworkError(RealEstateScraperError):
    """Exception raised for network-related errors."""
    pass


class ParseError(RealEstateScraperError):
    """Exception raised when unable to parse data."""
    pass


class APIError(RealEstateScraperError):
    """Exception raised for API-related errors."""
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


class RateLimitError(APIError):
    """Exception raised when rate limited by the API."""
    def __init__(self, retry_after=None):
        self.retry_after = retry_after
        message = f"Rate limit exceeded. Retry after {retry_after} seconds." if retry_after else "Rate limit exceeded."
        super().__init__(429, message)


class ValidationError(RealEstateScraperError):
    """Exception raised when data validation fails."""
    pass


class ConfigurationError(RealEstateScraperError):
    """Exception raised when there is an issue with configuration."""
    pass


# Decorators for error handling
def retry(
    max_tries: int = 3, 
    delay: float = 1.0, 
    backoff: float = 2.0, 
    exceptions: tuple = (Exception,),
    logger: logging.Logger = None
):
    """
    Retry decorator with exponential backoff for functions that might fail temporarily.
    
    Args:
        max_tries: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier (how much to increase delay each retry)
        exceptions: Tuple of exceptions to catch and retry
        logger: Logger to use (if None, uses module logger)
        
    Returns:
        Decorated function with retry logic
    """
    log = logger or logging.getLogger(__name__)
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = max_tries, delay
            
            # Get function details for better logging
            module = func.__module__
            qualname = func.__qualname__
            full_name = f"{module}.{qualname}"
            
            while mtries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    mtries -= 1
                    if mtries <= 0:
                        log.error(f"Function {full_name} failed after {max_tries} attempts. Error: {e}")
                        raise
                    
                    log.warning(
                        f"Function {full_name} failed. Retrying in {mdelay:.1f} seconds... "
                        f"({max_tries - mtries}/{max_tries}) Error: {e}"
                    )
                    
                    time.sleep(mdelay)
                    mdelay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator


def safe_scraping(func=None, exceptions_to_handle=None, logger=None):
    """
    Decorator to handle common web scraping errors with appropriate logging.
    
    Can be used as @safe_scraping or @safe_scraping(exceptions_to_handle=[...], logger=custom_logger)
    
    Args:
        func: Function to decorate
        exceptions_to_handle: Specific exceptions to handle (default: network errors)
        logger: Logger to use (if None, uses module logger)
        
    Returns:
        Decorated function with error handling
    """
    # Default exceptions to handle
    default_exceptions = {
        requests.ConnectionError: NetworkError("Connection error"),
        requests.Timeout: NetworkError("Request timed out"),
        requests.RequestException: NetworkError("Request error"),
        ValueError: ParseError("Value error")
    }
    
    # Allow use as @safe_scraping or @safe_scraping(...)
    if func is None:
        return lambda f: safe_scraping(
            f, 
            exceptions_to_handle=exceptions_to_handle, 
            logger=logger
        )
    
    exceptions = exceptions_to_handle or default_exceptions
    log = logger or logging.getLogger(__name__)
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get function details for better logging
        module = func.__module__
        qualname = func.__qualname__
        full_name = f"{module}.{qualname}"
        
        try:
            return func(*args, **kwargs)
        except tuple(exceptions.keys()) as e:
            # Map to custom exception if specified
            if type(e) in exceptions:
                custom_exception = exceptions[type(e)]
                if isinstance(custom_exception, Exception):
                    # Add original exception info to the custom one
                    message = f"{str(custom_exception)}: {str(e)}"
                    log.error(f"{full_name}: {message}")
                    
                    # Create new exception of the same type
                    new_exception = custom_exception.__class__(message)
                    raise new_exception from e
            
            # If no mapping, just log and re-raise
            log.error(f"Error in {full_name}: {e}")
            raise
        except Exception as e:
            log.exception(f"Unexpected error in {full_name}: {e}")
            raise
    return wrapper


def measure_time(func=None, logger=None, level=logging.DEBUG):
    """
    Decorator to measure and log execution time of a function.
    
    Args:
        func: Function to decorate
        logger: Logger to use (if None, uses module logger)
        level: Logging level to use
        
    Returns:
        Decorated function that logs execution time
    """
    if func is None:
        return lambda f: measure_time(f, logger=logger, level=level)
    
    log = logger or logging.getLogger(__name__)
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # Get function details for better logging
        module = func.__module__
        qualname = func.__qualname__
        full_name = f"{module}.{qualname}"
        
        log.log(level, f"{full_name} executed in {end_time - start_time:.4f} seconds")
        return result
    return wrapper


# Logging setup
def setup_logging(
    log_file: Optional[str] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    module_levels: Dict[str, int] = None
) -> logging.Logger:
    """
    Configure a comprehensive logging system with console and file handlers.
    
    Args:
        log_file: Path to log file (optional)
        console_level: Logging level for console output
        file_level: Logging level for file output
        module_levels: Dict of module names and their specific log levels
        
    Returns:
        Configured logger
    """
    # Create a custom formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all logs
    
    # Remove existing handlers if any
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console = logging.StreamHandler()
    console.setLevel(console_level)
    console.setFormatter(formatter)
    root_logger.addHandler(console)
    
    # Create file handler if log_file is provided
    if log_file:
        # Ensure the directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        logger.info(f"Logging to file: {log_file}")
    
    # Set specific levels for modules if provided
    if module_levels:
        for module, level in module_levels.items():
            logging.getLogger(module).setLevel(level)
            logger.info(f"Set {module} logging level to {logging.getLevelName(level)}")
    
    logger.info("Logging system initialized")
    return logger


# Context manager for error handling
class ErrorHandler:
    """
    Context manager for handling errors with appropriate logging and actions.
    
    Example:
        with ErrorHandler(logger, "Processing property data") as handler:
            data = process_property_data(property_id)
            if handler.check_condition(not data, "No data found"):
                return None
    """
    
    def __init__(self, logger=None, operation=None, reraise=True):
        """
        Initialize the error handler.
        
        Args:
            logger: Logger to use (if None, uses module logger)
            operation: Description of the operation being performed
            reraise: Whether to re-raise exceptions after logging
        """
        self.logger = logger or logging.getLogger(__name__)
        self.operation = operation
        self.reraise = reraise
        self.error = None
        
    def __enter__(self):
        if self.operation:
            self.logger.debug(f"Starting: {self.operation}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = exc_val
            
            # Log the error with context
            error_msg = f"Error during {self.operation}: {exc_val}" if self.operation else f"Error: {exc_val}"
            self.logger.error(error_msg)
            
            # Log the traceback at debug level
            tb_str = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
            self.logger.debug(f"Traceback:\n{tb_str}")
            
            # Determine whether to suppress the exception
            return not self.reraise
        
        if self.operation:
            self.logger.debug(f"Completed: {self.operation}")
        return False
    
    def check_condition(self, condition, error_message):
        """
        Check a condition and log an error if True.
        
        Args:
            condition: Condition to check
            error_message: Error message if condition is True
            
        Returns:
            The condition value
        """
        if condition:
            self.logger.warning(f"{self.operation}: {error_message}")
        return condition


# Helper functions for exception handling
def handle_request_errors(func):
    """
    Decorator specifically for handling HTTP request errors.
    Maps standard request exceptions to our custom exceptions.
    """
    exception_mapping = {
        requests.ConnectionError: NetworkError("Connection failed"),
        requests.Timeout: NetworkError("Request timed out"),
        requests.TooManyRedirects: NetworkError("Too many redirects"),
        requests.HTTPError: lambda r: APIError(r.status_code, r.reason)
    }
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except tuple(exception_mapping.keys()) as e:
            logger.error(f"Request error in {func.__name__}: {e}")
            
            # Get the appropriate exception
            if isinstance(e, requests.HTTPError):
                custom_exc = exception_mapping[type(e)](e.response)
            else:
                custom_exc = exception_mapping[type(e)]
                
            # If it's a callable, call it to get the exception instance
            if callable(custom_exc):
                custom_exc = custom_exc(e)
                
            raise custom_exc from e
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}: {e}")
            raise
    return wrapper


# Context manager for timing operations
class Timer:
    """
    Context manager for timing operations.
    
    Example:
        with Timer("Data processing", logger) as timer:
            process_data()
            
        # Access timing info
        print(f"Processing took {timer.elapsed:.2f} seconds")
    """
    
    def __init__(self, operation_name, logger=None, level=logging.INFO):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.level = level
        self.start_time = None
        self.end_time = None
        self.elapsed = 0
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time
        
        # Log the timing
        self.logger.log(
            self.level, 
            f"{self.operation_name} completed in {self.elapsed:.4f} seconds"
        )
        
        # Don't suppress exceptions
        return False
