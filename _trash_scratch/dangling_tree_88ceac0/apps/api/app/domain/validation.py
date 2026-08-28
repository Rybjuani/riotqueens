import re

from .contracts import OutputValidationResult

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
INTERNAL_LEAKS = ("<|system|>", "system prompt", "tool_calls", "you are an ai")
PROVIDER_IDENTITY = re.compile(
    r"\b(?:soy|como)\s+(?:gemini|chatgpt|claude|copilot|un(?:a)?\s+"
    r"(?:modelo|asistente)\s+de\s+(?:ia|inteligencia artificial)|"
    r"(?:un(?:a)?\s+)?(?:ia|inteligencia artificial))\b|"
    r"\b(?:i am|i'm|as)\s+(?:gemini|chatgpt|claude|copilot|an?\s+ai|"
    r"an?\s+language model)\b",
    re.IGNORECASE,
)
GENERIC_GUARDRAIL = re.compile(
    r"\bno puedo (?:ayudar|participar|continuar|cumplir)(?:te)?\b"
    r".{0,48}\b(?:eso|solicitud|contenido|conversación|pedido)\b|"
    r"\bi (?:can't|cannot) (?:help|assist|continue)\b"
    r".{0,48}\b(?:that|request|content|conversation)\b",
    re.IGNORECASE,
)


class OutputValidator:
    """Small deterministic gate; it is not a semantic moderation system."""

    def validate(self, content: str) -> OutputValidationResult:
        reasons: list[str] = []
        stripped = content.strip()
        sanitized = CONTROL_CHARS.sub("", content).strip()
        encoding_ok = not CONTROL_CHARS.search(content)
        language_ok = self._looks_like_spanish(stripped)
        not_truncated = not content.rstrip().endswith(("...", "…", ":"))
        not_repetitive = self._not_repetitive(stripped)
        no_internal_leak = not any(marker in stripped.lower() for marker in INTERNAL_LEAKS)
        provider_identity_ok = not PROVIDER_IDENTITY.search(stripped)
        guardrail_continuity_ok = not GENERIC_GUARDRAIL.search(stripped)
        character_consistent = (
            not self._looks_like_internal_fragment(stripped)
            and provider_identity_ok
            and guardrail_continuity_ok
        )
        if not sanitized:
            reasons.append("empty_response")
        if len(stripped) > 12_000:
            reasons.append("excessive_length")
        if not encoding_ok:
            reasons.append("control_character")
        if not language_ok:
            reasons.append("unexpected_language")
        if not not_truncated:
            reasons.append("possible_truncation")
        if not not_repetitive:
            reasons.append("excessive_repetition")
        if not no_internal_leak:
            reasons.append("internal_fragment")
        if not character_consistent:
            reasons.append("unusual_internal_format")
        if not provider_identity_ok:
            reasons.append("provider_identity_leak")
        if not guardrail_continuity_ok:
            reasons.append("provider_guardrail_break")
        return OutputValidationResult(
            is_valid=not reasons,
            language_ok=language_ok,
            encoding_ok=encoding_ok,
            not_truncated=not_truncated,
            not_repetitive=not_repetitive,
            no_internal_leak=no_internal_leak,
            character_consistent=character_consistent,
            reasons=reasons,
        )

    @staticmethod
    def _looks_like_spanish(text: str) -> bool:
        if not text:
            return False
        if re.search(r"[\u0400-\u04ff\u3040-\u30ff\u4e00-\u9fff]", text):
            return False
        words = set(re.findall(r"[a-záéíóúñü]+", text.lower()))
        markers = {"que", "de", "la", "el", "te", "me", "una", "con", "para", "hola"}
        latin = len(re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñÜü]", text))
        return latin > 0 and (bool(words & markers) or len(text.split()) < 4)

    @staticmethod
    def _not_repetitive(text: str) -> bool:
        words = text.lower().split()
        if len(words) < 8:
            return True
        if len(set(words)) / len(words) < 0.35:
            return False
        symbols = sum(not char.isalnum() and not char.isspace() for char in text)
        return symbols / max(len(text), 1) < 0.35

    @staticmethod
    def _looks_like_internal_fragment(text: str) -> bool:
        return text.startswith(("```", '{"', "[SYSTEM", "<assistant>"))
