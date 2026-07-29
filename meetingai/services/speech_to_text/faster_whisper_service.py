"""Implémentation Speech-To-Text basée sur faster-whisper."""

from __future__ import annotations

import threading
import time
import uuid
from pathlib import Path
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
    charge un modèle présent sur le disque local, transcrit un média et retourne
    un ``TranscriptionResult`` complet.

    Aucun téléchargement automatique n'est réalisé : ``local_files_only`` est
    systématiquement activé. Le modèle est recherché dans ``models_directory``.

    Args:
        model_size: Taille ou chemin du modèle Whisper à utiliser.
        models_directory: Répertoire racine contenant les modèles locaux.
        device: Périphérique d'exécution (``cpu`` ou ``cuda``).
        compute_type: Type de calcul (``int8``, ``float16``, etc.).
    """

    _DEFAULT_MODEL_SIZE: str = "small"
    _DEFAULT_MODELS_DIRECTORY: Path = Path("models")
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
        models_directory: str | Path | None = None,
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        """Initialise le service avec la configuration du modèle."""
        self._model_size = model_size or self._DEFAULT_MODEL_SIZE
        self._models_directory = (
            Path(models_directory)
            if models_directory is not None
            else self._DEFAULT_MODELS_DIRECTORY
        )
        self._device = device
        self._compute_type = compute_type
        self._model: Any | None = None
        self._model_lock = threading.Lock()

    def _resolve_model_path(self) -> Path:
        """Retourne le chemin local attendu pour le modèle configuré."""
        return self._models_directory / self._model_size

    def load_model(self) -> None:
        """Charge le modèle faster-whisper depuis le disque local.

        Raises:
            RuntimeError: Si ``faster-whisper`` n'est pas installé, si le
                répertoire du modèle n'existe pas ou si le chargement échoue.
        """
        if _FASTER_WHISPER is None:
            raise RuntimeError(
                "La bibliothèque faster-whisper n'est pas installée."
            )

        model_path = self._resolve_model_path()
        if not model_path.exists():
            raise RuntimeError(
                f"Le modèle faster-whisper est introuvable : {model_path}"
            )

        try:
            self._model = _FASTER_WHISPER.WhisperModel(
                str(model_path),
                device=self._device,
                compute_type=self._compute_type,
                local_files_only=True,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Impossible de charger le modèle faster-whisper : {exc}"
            ) from exc

    def transcribe(self, media: MediaFile, task: Task) -> TranscriptionResult:
        """Transcrit le média avec faster-whisper.

        Le modèle est chargé automatiquement lors du premier appel s'il ne
        l'est pas déjà, puis réutilisé pour les transcriptions suivantes.

        Args:
            media: Média à transcrire.
            task: Tâche associée. Son état sera mis à jour avec la progression
                lorsque celle-ci sera implémentée ; actuellement elle est
                simplement marquée comme terminée en cas de succès.

        Returns:
            Résultat complet de la transcription.

        Raises:
            RuntimeError: Si le modèle ne peut pas être chargé ou si la
                transcription échoue.
        """
        with self._model_lock:
            if self._model is None:
                self.load_model()

        start_time = time.perf_counter()
        try:
            segments, info = self._model.transcribe(
                str(media.path),
                beam_size=5,
                condition_on_previous_text=False,
            )
            text_parts = [segment.text for segment in segments]
            full_text = " ".join(text_parts).strip()
            processing_time = time.perf_counter() - start_time

            task.update_progress(100)

            return TranscriptionResult(
                text=full_text,
                language=info.language or "unknown",
                duration=getattr(info, "duration", 0.0),
                model=self._model_size,
                processing_time=processing_time,
                metadata={
                    "language_probability": getattr(
                        info, "language_probability", None
                    ),
                },
            )
        except Exception as exc:
            raise RuntimeError(
                f"Échec de la transcription faster-whisper : {exc}"
            ) from exc

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
