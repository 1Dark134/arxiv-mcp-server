"""Custom exception hierarchy for arxiv-mcp-server."""


class ArxivMCPError(Exception):
    """Base exception for all arxiv-mcp-server errors."""

    def __init__(self, message: str = "An arXiv MCP error occurred", context: dict = None):
        self.context = context or {}
        super().__init__(message)


class ArxivAPIError(ArxivMCPError):
    """Raised when an arXiv API call fails (HTTP errors, timeouts)."""

    def __init__(self, message: str = "arXiv API request failed", context: dict = None):
        super().__init__(message, context)


class ArxivNotFoundError(ArxivMCPError):
    """Raised when a requested paper is not found."""

    def __init__(self, message: str = "Paper not found on arXiv", context: dict = None):
        super().__init__(message, context)


class ArxivParseError(ArxivMCPError):
    """Raised when XML or response parsing fails."""

    def __init__(self, message: str = "Failed to parse arXiv response", context: dict = None):
        super().__init__(message, context)


class ArxivExportError(ArxivMCPError):
    """Raised when paper export encounters a format or data error."""

    def __init__(self, message: str = "Paper export failed", context: dict = None):
        super().__init__(message, context)


class ArxivConnectionError(ArxivMCPError):
    """Raised when the MCP client is not connected to the server."""

    def __init__(self, message: str = "Not connected to arXiv MCP server", context: dict = None):
        super().__init__(message, context)


class ArxivValidationError(ArxivMCPError):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Input validation failed", context: dict = None):
        super().__init__(message, context)
