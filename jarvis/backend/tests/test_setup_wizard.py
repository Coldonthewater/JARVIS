"""
Tests for backend/setup.py.

Only the non-interactive parts are tested here (file writing,
first-run detection) — the interactive prompts themselves are simple
enough (thin wrappers around `input()`) that they're best verified by
manual testing rather than mocking stdin extensively.
"""

from backend.setup import _write_env_file, ensure_configured


def test_write_env_file_creates_file_with_expected_keys(tmp_path, monkeypatch):
    fake_env_path = tmp_path / "config" / ".env"
    monkeypatch.setattr("backend.setup.ENV_PATH", fake_env_path)

    _write_env_file(
        {
            "GATEWAY_AUTH_TOKEN": "test-token-123",
            "AI_LOCAL_PROVIDER": "ollama",
            "AI_CLOUD_PROVIDER": "openai",
            "AI_FALLBACK_PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-test",
            "GATEWAY_HOST": "127.0.0.1",
            "GATEWAY_PORT": "8000",
        }
    )

    assert fake_env_path.exists()
    content = fake_env_path.read_text()
    assert "GATEWAY_AUTH_TOKEN=test-token-123" in content
    assert "OPENAI_API_KEY=sk-test" in content
    assert "AI_LOCAL_PROVIDER=ollama" in content


def test_ensure_configured_does_not_overwrite_existing_env(tmp_path, monkeypatch):
    fake_env_path = tmp_path / "config" / ".env"
    fake_env_path.parent.mkdir(parents=True)
    fake_env_path.write_text("EXISTING=true\n")
    monkeypatch.setattr("backend.setup.ENV_PATH", fake_env_path)

    ensure_configured()  # should be a no-op since the file already exists

    assert fake_env_path.read_text() == "EXISTING=true\n"
