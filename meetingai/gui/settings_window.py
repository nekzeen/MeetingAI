"""Fenêtre de paramètres de MeetingAI."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SettingsWindow(QDialog):
    """Fenêtre de modification des paramètres de l'application.

    Cette vue affiche les paramètres regroupés par sections. Elle ne contient
    aucune logique métier : elle se contente de collecter les valeurs saisies
    par l'utilisateur et de les exposer via ``get_settings``.

    Args:
        initial_settings: Valeurs actuelles des paramètres.
        parent: Widget parent éventuel.
    """

    def __init__(
        self,
        initial_settings: dict[str, str],
        parent: QWidget | None = None,
    ) -> None:
        """Initialise la fenêtre de paramètres."""
        super().__init__(parent)
        self.setWindowTitle("Paramètres")
        self._initial_settings = initial_settings
        self._setup_ui()
        self._load_values()

    def _setup_ui(self) -> None:
        """Construit les sections et les champs du formulaire."""
        self._layout = QVBoxLayout(self)

        self._general_group = QGroupBox("Général", self)
        self._general_layout = QFormLayout(self._general_group)
        self._theme_combo = QComboBox(self._general_group)
        self._language_combo = QComboBox(self._general_group)
        self._general_layout.addRow("Thème :", self._theme_combo)
        self._general_layout.addRow("Langue :", self._language_combo)

        self._stt_group = QGroupBox("Speech-To-Text", self)
        self._stt_layout = QFormLayout(self._stt_group)
        self._provider_combo = QComboBox(self._stt_group)
        self._model_edit = QLineEdit(self._stt_group)
        self._device_combo = QComboBox(self._stt_group)
        self._compute_type_combo = QComboBox(self._stt_group)
        self._stt_layout.addRow("Provider :", self._provider_combo)
        self._stt_layout.addRow("Modèle :", self._model_edit)
        self._stt_layout.addRow("Device :", self._device_combo)
        self._stt_layout.addRow("Compute Type :", self._compute_type_combo)

        self._export_group = QGroupBox("Export", self)
        self._export_layout = QFormLayout(self._export_group)
        self._output_directory_edit = QLineEdit(self._export_group)
        self._browse_button = QPushButton("Parcourir...", self._export_group)
        self._browse_button.clicked.connect(self._browse_output_directory)
        output_row = QHBoxLayout()
        output_row.addWidget(self._output_directory_edit)
        output_row.addWidget(self._browse_button)
        self._export_layout.addRow(
            "Répertoire de sortie :", output_row
        )

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

        self._layout.addWidget(self._general_group)
        self._layout.addWidget(self._stt_group)
        self._layout.addWidget(self._export_group)
        self._layout.addStretch()
        self._layout.addWidget(self._button_box)

    def _load_values(self) -> None:
        """Remplit les champs avec les valeurs initiales."""
        self._theme_combo.addItems(["light", "dark"])
        self._theme_combo.setCurrentText(self._initial_settings["theme"])

        self._language_combo.addItems(["fr", "en"])
        self._language_combo.setCurrentText(self._initial_settings["language"])

        self._provider_combo.addItems(["fake", "faster-whisper"])
        self._provider_combo.setCurrentText(self._initial_settings["provider"])

        self._model_edit.setText(self._initial_settings["model_name"])

        self._device_combo.addItems(["auto", "cpu", "cuda"])
        self._device_combo.setCurrentText(self._initial_settings["device"])

        self._compute_type_combo.addItems(
            ["int8", "float16", "int16", "float32"]
        )
        self._compute_type_combo.setCurrentText(
            self._initial_settings["compute_type"]
        )

        self._output_directory_edit.setText(
            self._initial_settings["output_directory"]
        )

    def _browse_output_directory(self) -> None:
        """Ouvre une boîte de dialogue pour choisir le répertoire de sortie."""
        current = self._output_directory_edit.text() or "."
        directory = QFileDialog.getExistingDirectory(
            self, "Répertoire de sortie", current
        )
        if directory:
            self._output_directory_edit.setText(directory)

    def get_settings(self) -> dict[str, str]:
        """Retourne les valeurs actuelles des paramètres.

        Returns:
            Dictionnaire des paramètres modifiés.
        """
        return {
            "theme": self._theme_combo.currentText(),
            "language": self._language_combo.currentText(),
            "provider": self._provider_combo.currentText(),
            "model_name": self._model_edit.text(),
            "device": self._device_combo.currentText(),
            "compute_type": self._compute_type_combo.currentText(),
            "output_directory": self._output_directory_edit.text(),
        }
