class TransientFailureError(Exception):
    """Exception raised for errors that are transient and should be retried."""
    pass

class NonRetryableError(Exception):
    """Exception raised for deterministic errors that should NOT be retried."""
    pass

def is_retryable(error: Exception) -> bool:
    """Determine if an error is transient and can be retried."""
    if isinstance(error, TransientFailureError):
        return True
    
    error_msg = str(error).lower()
    transient_keywords = [
        "timeout", "rate limit", "429", "502", "503", "504", 
        "temporary failure", "service unavailable", "connection reset"
    ]
    
    return any(keyword in error_msg for keyword in transient_keywords)
