"""Widget d'affichage des informations d'un média."""

from PySide6.QtWidgets import QFormLayout, QLabel, QWidget

from meetingai.models.media_file import MediaFile


class MediaInformationWidget(QWidget):
    """Affiche les métadonnées d'un média sélectionné.

    Ce widget est purement passif : il reçoit un objet ``MediaFile`` via la
    méthode ``set_media`` et met à jour ses labels. Il ne réalise aucune
    opération sur le système de fichiers et ne dépend pas de ``MediaService``.

    Args:
        parent: Widget parent éventuel.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise le widget avec un état vide."""
        super().__init__(parent)
        self._setup_ui()
        self.set_media(None)

    def _setup_ui(self) -> None:
        """Crée les labels d'affichage."""
        layout = QFormLayout(self)
        self._name_label = QLabel(self)
        self._path_label = QLabel(self)
        self._type_label = QLabel(self)
        self._extension_label = QLabel(self)
        self._size_label = QLabel(self)

        layout.addRow("Nom :", self._name_label)
        layout.addRow("Chemin :", self._path_label)
        layout.addRow("Type :", self._type_label)
        layout.addRow("Extension :", self._extension_label)
        layout.addRow("Taille :", self._size_label)

    def set_media(self, media: MediaFile | None) -> None:
        """Met à jour l'affichage avec les informations du média.

        Args:
            media: Média à afficher, ou ``None`` pour afficher l'état vide.
        """
        if media is None:
            self._name_label.setText("Aucun média sélectionné")
            self._path_label.setText("-")
            self._type_label.setText("-")
            self._extension_label.setText("-")
            self._size_label.setText("-")
            return

        self._name_label.setText(media.name)
        self._path_label.setText(str(media.path))
        self._type_label.setText(media.type)
        self._extension_label.setText(media.extension)
        self._size_label.setText(f"{media.size} octets")
