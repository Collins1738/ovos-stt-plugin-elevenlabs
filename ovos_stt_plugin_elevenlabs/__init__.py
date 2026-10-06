"""ElevenLabs Scribe speech-to-text plugin for OpenVoiceOS."""

from __future__ import annotations

from typing import Optional

import requests
from ovos_plugin_manager.templates.stt import STT
from ovos_plugin_manager.utils.audio import AudioData

from .credentials import resolve_api_key

API_URL = "https://api.elevenlabs.io/v1/speech-to-text"
DEFAULT_MODEL = "scribe_v2"


class ElevenLabsScribeSTT(STT):
    """Transcribe completed OVOS utterances with ElevenLabs Scribe."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = resolve_api_key(self.config)
        self.model = str(self.config.get("model") or DEFAULT_MODEL)
        self.timeout = float(self.config.get("timeout") or 30)
        self.no_verbatim = bool(self.config.get("no_verbatim", True))
        self.api_url = str(self.config.get("api_url") or API_URL)
        self.keyterms = [str(item) for item in self.config.get("keyterms", []) if str(item).strip()]
        self.session = requests.Session()

    def execute(self, audio: AudioData, language: Optional[str] = None) -> str:
        lang = (language or self.lang or "").split("-")[0].lower()
        fields = {
            "model_id": self.model,
            "tag_audio_events": "false",
            "diarize": "false",
            "no_verbatim": str(self.no_verbatim).lower(),
        }
        if lang:
            fields["language_code"] = lang
        if self.keyterms:
            fields["keyterms"] = self.keyterms

        response = self.session.post(
            self.api_url,
            headers={"xi-api-key": self.api_key},
            data=fields,
            files={
                "file": (
                    "utterance.wav",
                    audio.get_wav_data(convert_rate=16000, convert_width=2),
                    "audio/wav",
                )
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        text = payload.get("text")
        if not isinstance(text, str):
            raise RuntimeError("ElevenLabs response did not contain transcript text")
        return text.strip()

    def shutdown(self) -> None:
        self.session.close()


ElevenLabsScribeSTTConfig = {
    "en-US": [
        {
            "model": DEFAULT_MODEL,
            "lang": "en-US",
            "meta": {
                "priority": 70,
                "display_name": "ElevenLabs Scribe v2",
                "offline": False,
            },
        }
    ]
}
