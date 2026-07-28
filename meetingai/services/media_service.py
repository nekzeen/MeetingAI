"""Service de gestion des fichiers médias de MeetingAI."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from meetingai.models.media_file import MediaFile, MediaType


class MediaService:
    """Service centralisé d'ouverture et de validation des fichiers médias.

    Cette classe suit le pattern singleton afin de garantir un point d'accès
    unique aux opérations sur les médias. Elle valide l'existence, le type et
    le format du fichier avant de retourner un objet ``MediaFile``.

    Les formats supportés sont déclarés sous forme d'ensembles afin de
    faciliter l'ajout futur de nouvelles extensions.
    """

    _instance: ClassVar[MediaService | None] = None
    _initialized: ClassVar[bool] = False

    AUDIO_EXTENSIONS: ClassVar[frozenset[str]] = frozenset(
        {".mp3", ".wav", ".flac", ".m4a", ".ogg"}
    )
    VIDEO_EXTENSIONS: ClassVar[frozenset[str]] = frozenset(
        {".mp4", ".mkv", ".avi", ".mov", ".webm"}
    )

    @property
    def supported_extensions(self) -> frozenset[str]:
        """Ensemble de toutes les extensions supportées."""
        return self.AUDIO_EXTENSIONS | self.VIDEO_EXTENSIONS

    def __new__(cls) -> MediaService:
        """Retourne l'instance unique du service média."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialise le service si nécessaire."""
        if MediaService._initialized:
            return
        MediaService._initialized = True

    def open(self, path: str | Path) -> MediaFile:
        """Ouvre et valide un fichier média.

        Args:
            path: Chemin du fichier à ouvrir.

        Returns:
            Une instance immuable ``MediaFile`` représentant le média.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
            IsADirectoryError: Si le chemin pointe vers un dossier.
            ValueError: Si l'extension du fichier n'est pas supportée.
        """
        file_path = Path(path).expanduser().resolve()

        if not file_path.exists():
            raise FileNotFoundError(f"Le fichier n'existe pas : {file_path}")

        if not file_path.is_file():
            raise IsADirectoryError(f"Le chemin n'est pas un fichier : {file_path}")

        extension = file_path.suffix.lower()
        if extension not in self.supported_extensions:
            raise ValueError(
                f"Format non supporté : {extension}. "
                f"Formats supportés : {', '.join(sorted(self.supported_extensions))}"
            )

        return MediaFile(
            path=file_path,
            name=file_path.name,
            extension=extension,
            size=file_path.stat().st_size,
            media_type=self._resolve_media_type(extension),
        )

    def _resolve_media_type(self, extension: str) -> MediaType:
        """Détermine le type de média à partir de l'extension."""
        if extension in self.AUDIO_EXTENSIONS:
            return MediaType.AUDIO
        return MediaType.VIDEO

    @classmethod
    def _reset_instance(cls) -> None:
        """Réinitialise le singleton. Réservé aux tests."""
        cls._instance = None
        cls._initialized = False
