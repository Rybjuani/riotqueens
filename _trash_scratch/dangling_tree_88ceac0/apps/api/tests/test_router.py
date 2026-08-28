import pytest

from app.domain.contracts import MessageInput, ModelRequest, ModelResponse, Route
from app.domain.providers.errors import ProviderContentBlockedError
from app.domain.router import MockModelProvider, ModelRouter


@pytest.mark.asyncio
async def test_router_selects_provider_and_validates() -> None:
    request = ModelRequest(
        route=Route.FAST_CHAT,
        character_id="host",
        user_id="user",
        conversation_id="conversation",
        messages=[MessageInput(role="user", content="Hola")],
    )
    response = await ModelRouter().generate(request)
    assert response.provider == "mock"
    assert response.validation and response.validation.is_valid
    assert response.retry_count == 0
    assert "anfitriona de prueba" not in response.content.lower()


@pytest.mark.asyncio
async def test_router_retries_once_then_recovers() -> None:
    class BrokenProvider(MockModelProvider):
        calls = 0

        async def generate(self, request: ModelRequest):
            self.calls += 1
            response = await super().generate(request)
            response.content = ""
            return response

    provider = BrokenProvider()
    router = ModelRouter({route: provider for route in Route})
    request = ModelRequest(
        route=Route.MEMORY,
        character_id="host",
        user_id="user",
        conversation_id="conversation",
        messages=[MessageInput(role="user", content="Hola")],
    )
    response = await router.generate(request)
    assert provider.calls == 2
    assert response.retry_count == 1
    assert response.provider == "server-fallback"
    assert "no el hilo" in response.content


@pytest.mark.asyncio
async def test_router_uses_secondary_provider_after_identity_break() -> None:
    class IdentityBreakProvider(MockModelProvider):
        name = "identity-break"
        model = "primary"

        async def generate(self, request: ModelRequest) -> ModelResponse:
            return ModelResponse(
                provider=self.name,
                model=self.model,
                content="Soy Gemini. ¿Cuál es el siguiente paso en el repositorio?",
            )

    class ContinuityProvider(MockModelProvider):
        name = "continuity"
        model = "secondary"

        async def generate(self, request: ModelRequest) -> ModelResponse:
            return ModelResponse(
                provider=self.name,
                model=self.model,
                content="Sigo siendo La Bardera. Decime qué te pasó y seguimos desde ahí.",
            )

    primary = IdentityBreakProvider()
    secondary = ContinuityProvider()
    router = ModelRouter(
        providers={route: primary for route in Route},
        fallback_providers={route: (secondary,) for route in Route},
        max_retries=0,
    )
    request = ModelRequest(
        route=Route.FAST_CHAT,
        character_id="bardera",
        user_id="user",
        conversation_id="conversation",
        messages=[MessageInput(role="user", content="Hola")],
    )

    response = await router.generate(request)

    assert response.provider == "continuity"
    assert response.model == "secondary"
    assert response.validation and response.validation.is_valid


@pytest.mark.asyncio
async def test_router_turns_explicit_provider_block_into_server_continuity() -> None:
    class BlockedProvider(MockModelProvider):
        async def generate(self, request: ModelRequest) -> ModelResponse:
            raise ProviderContentBlockedError()

    provider = BlockedProvider()
    router = ModelRouter(
        providers={route: provider for route in Route},
        max_retries=0,
    )
    request = ModelRequest(
        route=Route.FAST_CHAT,
        character_id="bardera",
        user_id="user",
        conversation_id="conversation",
        messages=[MessageInput(role="user", content="Hola")],
    )

    response = await router.generate(request)

    assert response.provider == "server-fallback"
    assert response.model == "server-owned-continuity"
    assert response.validation and response.validation.is_valid
