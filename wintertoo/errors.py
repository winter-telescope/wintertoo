"""
Custom errors for wintertoo
"""


class WinterCredentialsError(Exception):
    """Error relating to a credentials validation"""


class WinterValidationError(Exception):
    """Error relating to a request validation"""
