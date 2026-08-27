"""Model provider adapters.

Each adapter implements the `ModelProvider` Protocol defined in
`app.domain.router`. The domain layer imports no provider SDK; adapters
own their HTTP/SDK clients and translate failures into safe
`ModelResponse` objects (never raise to the router).
"""

from app.domain.providers.openai_compatible import OpenAICompatibleProvider

__all__ = ["OpenAICompatibleProvider"]
