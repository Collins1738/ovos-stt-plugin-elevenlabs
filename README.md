# OVOS ElevenLabs Scribe STT Plugin

Use ElevenLabs Scribe v2 as an OpenVoiceOS speech-to-text provider. OVOS captures
a completed utterance, sends a 16 kHz WAV file to ElevenLabs, and receives the
transcript before continuing intent processing.

## Install

```bash
pip install ovos-stt-plugin-elevenlabs
```

For local development:

```bash
pip install -e '.[test]'
```

## Credentials

Create a dedicated ElevenLabs key restricted to Speech to Text. Avoid putting it
in `mycroft.conf` or source control.

On macOS, store it in Keychain. Leaving `-w` last opens a secure password prompt:

```bash
security add-generic-password \
  -U \
  -s ovos-elevenlabs-stt \
  -a api-key \
  -w
```

The plugin checks, in order:

1. `api_key` in plugin configuration, supported but discouraged
2. `ELEVENLABS_API_KEY`
3. macOS Keychain service `ovos-elevenlabs-stt`, account `api-key`

## Configure OVOS

Keep local Whisper as the fallback so network or provider failures do not stop
voice input:

```json
{
  "stt": {
    "module": "ovos-stt-plugin-elevenlabs",
    "fallback_module": "ovos-stt-plugin-whispercpp",
    "ovos-stt-plugin-elevenlabs": {
      "model": "scribe_v2",
      "no_verbatim": true,
      "timeout": 30
    },
    "ovos-stt-plugin-whispercpp": {
      "model": "small.en"
    }
  }
}
```

`no_verbatim=true` removes filler words, false starts, and non-speech sounds.
Optional `keyterms` can improve uncommon-name recognition but currently add a
20% surcharge to ElevenLabs transcription charges.

## Failure behavior

HTTP errors, timeouts, malformed responses, and missing credentials are raised
to OVOS. Dinkum Listener then invokes the configured `fallback_module`. An empty
successful transcript also lets OVOS try the fallback.

## Test

```bash
python -m pytest -q
```
