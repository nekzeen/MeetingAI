"""Implémentation Speech-To-Text basée sur faster-whisper."""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)

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

    Si un répertoire local ``models_directory / model_size`` existe, il est
    utilisé en priorité avec ``local_files_only=True``. Sinon, le mécanisme
    natif de téléchargement/cache de ``faster-whisper`` est utilisé.

    Lorsque le périphérique demandé est ``cuda`` ou ``auto`` et que
    l'initialisation échoue (driver/cuBLAS absent...), le service bascule
    automatiquement sur ``cpu`` avec ``int8`` et journalise l'événement.

    Args:
        model_size: Taille ou chemin du modèle Whisper à utiliser.
        models_directory: Répertoire racine des modèles et du cache.
        device: Périphérique d'exécution (``auto``, ``cpu`` ou ``cuda``).
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
        self._used_cpu_fallback: bool = False

    def _resolve_model_path(self) -> Path:
        """Retourne le chemin local attendu pour le modèle configuré."""
        return self._models_directory / self._model_size

    def _is_cuda_error(self, exc: Exception) -> bool:
        """Indique si une exception correspond à un échec d'initialisation CUDA."""
        message = str(exc).lower()
        return any(
            keyword in message
            for keyword in (
                "cublas",
                "cudnn",
                "cuda",
                "cuda_runtime",
                "nvrtc",
                "could not load",
                "not available",
            )
        )

    def _build_model(
        self,
        device: str,
        compute_type: str,
    ) -> Any:
        """Construit une instance ``WhisperModel`` selon le périphérique choisi.

        Si un répertoire local existe, il est utilisé avec
        ``local_files_only=True``. Sinon, le mécanisme natif de
        ``faster-whisper`` est utilisé.
        """
        local_model_path = self._resolve_model_path()

        if local_model_path.exists():
            return _FASTER_WHISPER.WhisperModel(
                str(local_model_path),
                device=device,
                compute_type=compute_type,
                local_files_only=True,
            )

        return _FASTER_WHISPER.WhisperModel(
            self._model_size,
            device=device,
            compute_type=compute_type,
            download_root=str(self._models_directory),
            local_files_only=False,
        )

    def load_model(self) -> None:
        """Charge le modèle faster-whisper.

        Si un répertoire local ``models_directory / model_size`` existe, il est
        utilisé en priorité. Sinon, le mécanisme natif de ``faster-whisper`` est
        utilisé : le modèle est téléchargé dans le cache configuré par
        ``download_root`` puis réutilisé pour les appels suivants.

        Lorsque le périphérique configuré est ``cuda`` ou ``auto`` et que
        l'initialisation échoue sur un problème CUDA (driver, cuBLAS...), le
        service tente de recharger le modèle sur ``cpu`` avec ``int8``.

        Raises:
            RuntimeError: Si ``faster-whisper`` n'est pas installé ou si le
                modèle ne peut être chargé ni trouvé en cache / téléchargé.
        """
        if _FASTER_WHISPER is None:
            raise RuntimeError(
                "La bibliothèque faster-whisper n'est pas installée."
            )

        try:
            self._model = self._build_model(
                device=self._device,
                compute_type=self._compute_type,
            )
        except Exception as exc:
            if self._device == "cpu" or self._used_cpu_fallback:
                raise RuntimeError(
                    f"Impossible de charger le modèle faster-whisper "
                    f"'{self._model_size}'. Vérifiez votre connexion réseau, "
                    f"l'accès au répertoire {self._models_directory}, ou "
                    f"téléchargez le modèle explicitement avec :\n"
                    f"FasterWhisperService.download_model("
                    f"'{self._model_size}', '{self._models_directory}')"
                ) from exc

            failure_message = (
                "Initialisation CUDA échouée"
                if self._is_cuda_error(exc)
                else f"Échec de l'initialisation sur le périphérique '{self._device}'"
            )
            _LOGGER.warning(
                "%s (%s). Basculement sur CPU avec int8.",
                failure_message,
                exc,
            )

            try:
                self._model = self._build_model(
                    device="cpu",
                    compute_type="int8",
                )
            except Exception as cpu_exc:
                raise RuntimeError(
                    f"Impossible de charger le modèle faster-whisper "
                    f"'{self._model_size}' sur CPU après échec CUDA. "
                    f"Vérifiez votre connexion réseau, "
                    f"l'accès au répertoire {self._models_directory}, ou "
                    f"téléchargez le modèle explicitement avec :\n"
                    f"FasterWhisperService.download_model("
                    f"'{self._model_size}', '{self._models_directory}')"
                ) from cpu_exc

            self._used_cpu_fallback = True
            _LOGGER.info(
                "Modèle faster-whisper '%s' chargé sur CPU (fallback).",
                self._model_size,
            )

    def is_model_present(self) -> bool:
        """Indique si le répertoire du modèle configuré existe localement."""
        return self._resolve_model_path().exists()

    @classmethod
    def download_model(
        cls,
        model_size: str | None = None,
        models_directory: str | Path | None = None,
    ) -> Path:
        """Télécharge le modèle faster-whisper demandé.

        Cette méthode n'est jamais appelée automatiquement : elle doit être
        invoquée explicitement par l'utilisateur ou un outil d'installation.

        Args:
            model_size: Taille du modèle à télécharger. Utilise la taille par
                défaut si non fournie.
            models_directory: Répertoire racine de téléchargement.

        Returns:
            Chemin du modèle téléchargé.

        Raises:
            RuntimeError: Si ``faster-whisper`` n'est pas installé ou si le
                téléchargement échoue.
        """
        if _FASTER_WHISPER is None:
            raise RuntimeError(
                "La bibliothèque faster-whisper n'est pas installée."
            )

        size = model_size or cls._DEFAULT_MODEL_SIZE
        directory = (
            Path(models_directory)
            if models_directory is not None
            else cls._DEFAULT_MODELS_DIRECTORY
        )

        try:
            return Path(
                _FASTER_WHISPER.download_model(size, output_dir=directory)
            )
        except Exception as exc:
            raise RuntimeError(
                f"Échec du téléchargement du modèle faster-whisper '{size}' : {exc}"
            ) from exc

    def transcribe(
        self,
        media: MediaFile,
        task: Task,
        progress_callback: Callable[[int], None] | None = None,
    ) -> TranscriptionResult:
        """Transcrit le média avec faster-whisper.

        Le modèle est chargé automatiquement lors du premier appel s'il ne
        l'est pas déjà, puis réutilisé pour les transcriptions suivantes.
        L'avancement est notifié via ``progress_callback`` à partir des
        segments retournés par faster-whisper.

        Args:
            media: Média à transcrire.
            task: Tâche associée. Son état sera mis à jour avec la progression.
            progress_callback: Fonction optionnelle appelée avec un pourcentage
                d'avancement entre 0 et 100.

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

            total_duration = float(getattr(info, "duration", 0.0) or 0.0)
            last_reported_progress = -1
            text_parts: list[str] = []

            for segment in segments:
                text_parts.append(segment.text)
                if progress_callback is not None and total_duration > 0:
                    segment_end = getattr(segment, "end", None)
                    if isinstance(segment_end, (int, float)):
                        progress = int(
                            min(segment_end / total_duration * 100, 100)
                        )
                        if progress != last_reported_progress:
                            progress_callback(progress)
                            last_reported_progress = progress

            if progress_callback is not None:
                progress_callback(100)

            full_text = " ".join(text_parts).strip()
            processing_time = time.perf_counter() - start_time

            task.update_progress(100)

            metadata: dict[str, Any] = {
                "language_probability": getattr(
                    info, "language_probability", None
                ),
            }
            if self._used_cpu_fallback:
                metadata["device"] = "cpu (fallback from cuda)"
                metadata["warning"] = (
                    "CUDA n'est pas disponible ou mal configuré ; "
                    "la transcription a été exécutée en mode CPU."
                )

            return TranscriptionResult(
                text=full_text,
                language=info.language or "unknown",
                duration=total_duration,
                model=self._model_size,
                processing_time=processing_time,
                metadata=metadata,
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
