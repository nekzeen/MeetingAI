"""Abstractions des moteurs Speech-To-Text pour MeetingAI."""

from meetingai.services.speech_to_text.fake_speech_to_text_service import (
    FakeSpeechToTextService,
)
from meetingai.services.speech_to_text.speech_to_text_service import (
    NullSpeechToTextService,
    SpeechToTextService,
)
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)

__all__ = [
    "SpeechToTextService",
    "NullSpeechToTextService",
    "FakeSpeechToTextService",
    "TranscriptionResult",
]
