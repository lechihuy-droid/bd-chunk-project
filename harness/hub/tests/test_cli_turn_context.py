from __future__ import annotations

from services.providers.base import turn_context, turn_prompt


def test_turn_context_joins_system_messages() -> None:
    messages = [
        {"role": "system", "content": "[Attached file: notes.txt]\nMARKER"},
        {"role": "user", "content": "what is in the file?"},
    ]
    assert turn_context(messages) == "[Attached file: notes.txt]\nMARKER"


def test_turn_context_ignores_user_and_assistant_turns() -> None:
    messages = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "reply"},
        {"role": "user", "content": "second"},
    ]
    assert turn_context(messages) == ""


def test_turn_context_skips_blank_system_messages() -> None:
    messages = [
        {"role": "system", "content": "   "},
        {"role": "system", "content": "kept"},
        {"role": "user", "content": "hi"},
    ]
    assert turn_context(messages) == "kept"


def _prompt_for(module, messages, session_id=None):
    """Ask the adapter's own assembly for the prompt it would send.

    Calling the shared helper the adapters actually use — rather than
    re-implementing it here — is the point: if an adapter stops routing through
    it, these tests must fail.
    """
    assert module.turn_prompt is turn_prompt
    return module.turn_prompt(messages)


def test_cli_adapters_carry_attachment_context_into_the_prompt() -> None:
    """Regression: chat file attachments never reached codex/claude.

    The hub injects attachment text as a system message, but the CLI adapters
    send a single prompt string built from the latest *user* message, so the
    attachment was silently dropped for those providers while it worked for the
    HTTP provider.
    """
    from services.providers import claude_cli, codex_cli

    messages = [
        {"role": "system", "content": "[Attached file: probe.txt]\nMARKER_XYZZY_42"},
        {"role": "user", "content": "which marker is in the file?"},
    ]
    for module in (codex_cli, claude_cli):
        prompt = _prompt_for(module, messages)
        assert "MARKER_XYZZY_42" in prompt
        assert "which marker is in the file?" in prompt


def test_attachment_context_survives_a_resumed_session() -> None:
    """It must ride along every turn: a file can be attached mid-conversation,
    unlike the agent's static system prompt, which is sent only on turn one."""
    from services.providers import codex_cli

    messages = [
        {"role": "system", "content": "[Attached file: late.txt]\nADDED_LATER"},
        {"role": "user", "content": "read it"},
    ]
    assert "ADDED_LATER" in _prompt_for(codex_cli, messages, session_id="sess-123")
