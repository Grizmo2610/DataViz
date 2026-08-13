class UnsupportedFormatError(Exception):
    """Raised when the input file format is not supported."""


class MissingDependencyError(Exception):
    """Raised when a reader needs an unavailable optional dependency."""
