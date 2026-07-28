"""Tests du service de gestion des médias."""

import tempfile
import unittest
from pathlib import Path

from meetingai.models.media_file import MediaFile, MediaType
from meetingai.services.media_service import MediaService


class TestMediaService(unittest.TestCase):
    """Tests du service d'ouverture et de validation des médias."""

    @classmethod
    def setUpClass(cls) -> None:
        """Réinitialise le singleton avant la série de tests."""
        MediaService._reset_instance()

    def setUp(self) -> None:
        """Prépare un répertoire temporaire et une instance du service."""
        self.service = MediaService()
        self._temp_dir = tempfile.TemporaryDirectory()
        self._base_path = Path(self._temp_dir.name)

    def tearDown(self) -> None:
        """Nettoie le répertoire temporaire et réinitialise le singleton."""
        self._temp_dir.cleanup()
        MediaService._reset_instance()

    def _write_file(self, name: str, content: bytes = b"content") -> Path:
        """Crée un fichier temporaire et retourne son chemin."""
        path = self._base_path / name
        path.write_bytes(content)
        return path

    def test_open_valid_audio_file(self) -> None:
        """Un fichier audio valide est ouvert correctement."""
        path = self._write_file("sample.mp3")

        media = self.service.open(path)

        self.assertIsInstance(media, MediaFile)
        self.assertEqual(media.name, "sample.mp3")
        self.assertEqual(media.extension, ".mp3")
        self.assertEqual(media.media_type, MediaType.AUDIO)
        self.assertEqual(media.type, "audio")
        self.assertEqual(media.size, len(b"content"))
        self.assertTrue(media.path.is_absolute())

    def test_open_valid_video_file(self) -> None:
        """Un fichier vidéo valide est ouvert correctement."""
        path = self._write_file("meeting.mp4")

        media = self.service.open(path)

        self.assertIsInstance(media, MediaFile)
        self.assertEqual(media.media_type, MediaType.VIDEO)
        self.assertEqual(media.type, "video")

    def test_open_missing_file_raises_file_not_found(self) -> None:
        """L'ouverture d'un fichier inexistant lève FileNotFoundError."""
        missing = self._base_path / "missing.mp3"

        with self.assertRaises(FileNotFoundError):
            self.service.open(missing)

    def test_open_directory_raises_is_a_directory(self) -> None:
        """L'ouverture d'un dossier lève IsADirectoryError."""
        directory = self._base_path / "folder"
        directory.mkdir()

        with self.assertRaises(IsADirectoryError):
            self.service.open(directory)

    def test_open_unsupported_extension_raises_value_error(self) -> None:
        """Une extension non supportée lève ValueError."""
        path = self._write_file("document.txt")

        with self.assertRaises(ValueError):
            self.service.open(path)

    def test_open_case_insensitive_extension(self) -> None:
        """Les extensions en majuscules sont acceptées."""
        path = self._write_file("sample.MP3")

        media = self.service.open(path)

        self.assertEqual(media.extension, ".mp3")
        self.assertEqual(media.media_type, MediaType.AUDIO)

    def test_singleton(self) -> None:
        """MediaService garantit une unique instance."""
        first = MediaService()
        second = MediaService()

        self.assertIs(first, second)


if __name__ == "__main__":
    unittest.main()
