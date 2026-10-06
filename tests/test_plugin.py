from unittest.mock import Mock, patch

import pytest
from ovos_plugin_manager.utils.audio import AudioData

from ovos_stt_plugin_elevenlabs import API_URL, ElevenLabsScribeSTT


def audio() -> AudioData:
    return AudioData(b"\x00\x00" * 1600, 16000, 2)


def plugin(**config) -> ElevenLabsScribeSTT:
    with patch("ovos_stt_plugin_elevenlabs.resolve_api_key", return_value="secret-key"):
        return ElevenLabsScribeSTT(config=config)


def test_execute_posts_wav_and_returns_text():
    stt = plugin(no_verbatim=True)
    response = Mock()
    response.json.return_value = {"text": "  Turn on the lights.  "}
    stt.session.post = Mock(return_value=response)

    assert stt.execute(audio(), "en-US") == "Turn on the lights."

    response.raise_for_status.assert_called_once_with()
    call = stt.session.post.call_args
    assert call.args == (API_URL,)
    assert call.kwargs["headers"] == {"xi-api-key": "secret-key"}
    assert call.kwargs["data"] == {
        "model_id": "scribe_v2",
        "tag_audio_events": "false",
        "diarize": "false",
        "no_verbatim": "true",
        "language_code": "en",
    }
    filename, wav, mime = call.kwargs["files"]["file"]
    assert filename == "utterance.wav"
    assert wav.startswith(b"RIFF")
    assert mime == "audio/wav"
    assert call.kwargs["timeout"] == 30


def test_execute_allows_provider_options():
    stt = plugin(
        model="scribe_v2",
        no_verbatim=False,
        timeout=12,
        keyterms=["Dravon", "OpenClaw"],
    )
    response = Mock()
    response.json.return_value = {"text": "Dravon, open OpenClaw."}
    stt.session.post = Mock(return_value=response)

    stt.execute(audio(), "en-GB")

    data = stt.session.post.call_args.kwargs["data"]
    assert data["no_verbatim"] == "false"
    assert data["keyterms"] == ["Dravon", "OpenClaw"]
    assert stt.session.post.call_args.kwargs["timeout"] == 12


def test_execute_propagates_http_errors_for_ovos_fallback():
    stt = plugin()
    response = Mock()
    response.raise_for_status.side_effect = RuntimeError("provider unavailable")
    stt.session.post = Mock(return_value=response)

    with pytest.raises(RuntimeError, match="provider unavailable"):
        stt.execute(audio())


def test_execute_rejects_malformed_response():
    stt = plugin()
    response = Mock()
    response.json.return_value = {"language_code": "en"}
    stt.session.post = Mock(return_value=response)

    with pytest.raises(RuntimeError, match="did not contain transcript text"):
        stt.execute(audio())


def test_shutdown_closes_session():
    stt = plugin()
    stt.session.close = Mock()

    stt.shutdown()

    stt.session.close.assert_called_once_with()
