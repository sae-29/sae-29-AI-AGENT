import streamlit as st
from typing import Callable, Any
import time
from functools import wraps

class ErrorHandler:
    @staticmethod
    def create_error_container():
        """Create a container for displaying errors in the UI"""
        return st.empty()

    @staticmethod
    def display_error(container, error_msg: str, error_type: str = "error"):
        """Display error message with appropriate styling"""
        if error_type == "error":
            container.error(f"❌ {error_msg}")
        elif error_type == "warning":
            container.warning(f"⚠️ {error_msg}")
        else:
            container.info(f"ℹ️ {error_msg}")
            
    @staticmethod
    def handle_api_error(func: Callable) -> Callable:
        """Decorator for handling API-related errors"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_container = ErrorHandler.create_error_container()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = str(e)
                if "rate limit" in error_msg.lower():
                    ErrorHandler.display_error(
                        error_container,
                        "Rate limit exceeded. Retrying in 5 seconds...",
                        "warning"
                    )
                    time.sleep(5)
                    return func(*args, **kwargs)
                elif "timeout" in error_msg.lower():
                    ErrorHandler.display_error(
                        error_container,
                        "Request timed out. Please try again.",
                        "error"
                    )
                elif "authentication" in error_msg.lower():
                    ErrorHandler.display_error(
                        error_container,
                        "Invalid API key. Please check your credentials.",
                        "error"
                    )
                else:
                    ErrorHandler.display_error(
                        error_container,
                        f"An unexpected error occurred: {error_msg}",
                        "error"
                    )
                raise
        return wrapper

    @staticmethod
    def retry_with_backoff(max_retries: int = 3, initial_delay: float = 1.0):
        """Decorator for implementing exponential backoff"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                error_container = ErrorHandler.create_error_container()
                delay = initial_delay
                
                for retry in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if retry < max_retries - 1:
                            ErrorHandler.display_error(
                                error_container,
                                f"Attempt {retry + 1} failed. Retrying in {delay:.1f} seconds...",
                                "warning"
                            )
                            time.sleep(delay)
                            delay *= 2
                        else:
                            ErrorHandler.display_error(
                                error_container,
                                f"Maximum retries reached. Error: {str(e)}",
                                "error"
                            )
                            raise
                return None
            return wrapper
        return decorator