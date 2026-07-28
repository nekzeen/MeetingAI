"""Implémentation Speech-To-Text basée sur faster-whisper."""

from __future__ import annotations

import uuid
from typing import Any

from meetingai.core.task import Task
from meetingai.models.media_file import MediaFile
from meetingai.services.speech_to_text.speech_to_text_service import (
    SpeechToTextService,
)
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)

try:  # pragma: no cover - dépend de l'environnement d'exécution
    import faster_whisper  # type: ignore

    _FASTER_WHISPER = faster_whisper
except Exception:  # pragma: no cover - faster-whisper peut ne pas être installé
    _FASTER_WHISPER = None


class FasterWhisperService(SpeechToTextService):
    """Implémentation de ``SpeechToTextService`` utilisant faster-whisper.

    Cette classe encapsule le moteur de transcription ``faster-whisper``. Elle
    est conçue pour être substituée à ``FakeSpeechToTextService`` dans
    ``ApplicationContext`` une fois un modèle disponible.

    Pour cette story, le service vérifie la présence de la bibliothèque et
    charge le modèle uniquement sur demande. Aucun téléchargement automatique
    n'est réalisé.

    Args:
        model_size: Taille du modèle Whisper à utiliser (ex. ``small``).
        device: Périphérique d'exécution (``cpu`` ou ``cuda``).
        compute_type: Type de calcul (``int8``, ``float16``, etc.).
    """

    _DEFAULT_MODEL_SIZE: str = "small"
    _SUPPORTED_LANGUAGES: tuple[str, ...] = (
        "af",
        "am",
        "ar",
        "as",
        "az",
        "ba",
        "be",
        "bg",
        "bn",
        "bo",
        "br",
        "bs",
        "ca",
        "cs",
        "cy",
        "da",
        "de",
        "el",
        "en",
        "es",
        "et",
        "eu",
        "fa",
        "fi",
        "fo",
        "fr",
        "gl",
        "gu",
        "ha",
        "haw",
        "he",
        "hi",
        "hr",
        "ht",
        "hu",
        "hy",
        "id",
        "is",
        "it",
        "ja",
        "jw",
        "ka",
        "kk",
        "km",
        "kn",
        "ko",
        "la",
        "lb",
        "ln",
        "lo",
        "lt",
        "lv",
        "mg",
        "mi",
        "mk",
        "ml",
        "mn",
        "mr",
        "ms",
        "mt",
        "my",
        "ne",
        "nl",
        "nn",
        "no",
        "oc",
        "pa",
        "pl",
        "ps",
        "pt",
        "ro",
        "ru",
        "sa",
        "sd",
        "si",
        "sk",
        "sl",
        "sn",
        "so",
        "sq",
        "sr",
        "su",
        "sv",
        "sw",
        "ta",
        "te",
        "tg",
        "th",
        "tk",
        "tl",
        "tr",
        "tt",
        "uk",
        "ur",
        "uz",
        "vi",
        "yi",
        "yo",
        "zh",
    )

    def __init__(
        self,
        model_size: str | None = None,
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        """Initialise le service avec la configuration du modèle."""
        self._model_size = model_size or self._DEFAULT_MODEL_SIZE
        self._device = device
        self._compute_type = compute_type
        self._model: Any | None = None

    def load_model(self) -> None:
        """Charge le modèle faster-whisper depuis le disque local.

        Raises:
            RuntimeError: Si ``faster-whisper`` n'est pas installé ou si le
                modèle local n'est pas disponible.
        """
        if _FASTER_WHISPER is None:
            raise RuntimeError(
                "La bibliothèque faster-whisper n'est pas installée."
            )

        try:
            self._model = _FASTER_WHISPER.WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
                local_files_only=True,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Impossible de charger le modèle faster-whisper : {exc}"
            ) from exc

    def transcribe(self, media: MediaFile, task: Task) -> TranscriptionResult:
        """Prépare la transcription d'un média.

        Pour cette story, la méthode retourne une erreur explicite si le
        modèle n'a pas été chargé. La transcription réelle sera implémentée
        dans une mission ultérieure.

        Args:
            media: Média à transcrire.
            task: Tâche associée.

        Returns:
            Résultat de la transcription (futur).

        Raises:
            RuntimeError: Si le modèle n'est pas chargé.
        """
        if self._model is None:
            raise RuntimeError(
                "Le modèle faster-whisper n'est pas chargé. "
                "Appelez load_model() après avoir vérifié sa disponibilité."
            )
        raise NotImplementedError(
            "La transcription réelle sera implémentée une fois le modèle validé."
        )

    def cancel(self, task_id: uuid.UUID) -> None:
        """Lève NotImplementedError car l'annulation n'est pas supportée."""
        raise NotImplementedError(
            "L'annulation n'est pas supportée par FasterWhisperService."
        )

    def is_available(self) -> bool:
        """Indique si la bibliothèque faster-whisper est installée."""
        return _FASTER_WHISPER is not None

    def name(self) -> str:
        """Retourne le nom du moteur."""
        return "FasterWhisper"

    def version(self) -> str:
        """Retourne la version de faster-whisper, ou ``unknown`` sinon."""
        if _FASTER_WHISPER is None:
            return "unknown"
        return getattr(_FASTER_WHISPER, "__version__", "unknown")

    def supported_languages(self) -> list[str]:
        """Retourne la liste des langues supportées par Whisper."""
        return list(self._SUPPORTED_LANGUAGES)
