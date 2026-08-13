import time
import functools
import logging
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries=3, backoff_factor=2):
    """Decorator for retrying webhook calls with exponential backoff"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {str(e)}. "
                            f"Retrying in {wait_time}s"
                        )
                        time.sleep(wait_time)
            
            logger.error(f"All {max_retries} retries failed: {str(last_exception)}")
            return Response(
                {'error': f'Webhook failed after {max_retries} attempts'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return wrapper
    return decorator