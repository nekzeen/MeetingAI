"""Widget d'affichage des informations d'un média."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel

from meetingai.models.media_file import MediaFile


class MediaInformationWidget(QGroupBox):
    """Affiche les métadonnées d'un média sélectionné.

    Ce widget est un panneau groupé : il reçoit un objet ``MediaFile`` via la
    méthode ``set_media`` et met à jour ses labels. Il ne réalise aucune
    opération sur le système de fichiers et ne dépend pas de ``MediaService``.

    Args:
        parent: Widget parent éventuel.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise le widget avec un état vide."""
        super().__init__("Média en cours", parent)
        self._setup_ui()
        self.set_media(None)

    def _setup_ui(self) -> None:
        """Crée une fiche compacte de métadonnées avec alignement clair."""
        layout = QGridLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)
        layout.setColumnStretch(1, 1)
        layout.setColumnMinimumWidth(0, 60)

        self._name_label = QLabel(self)
        self._name_label.setWordWrap(True)
        self._name_label.setStyleSheet("font-weight: bold; font-size: 15px;")
        self._type_label = QLabel(self)
        self._size_label = QLabel(self)

        self._name_label.setToolTip("Nom du fichier")
        self._type_label.setToolTip("Type de média")
        self._size_label.setToolTip("Taille du fichier")

        labels = ("Fichier :", "Type :", "Taille :")
        for index, text in enumerate(labels):
            label = QLabel(text, self)
            label.setStyleSheet("font-weight: bold; color: #495057;")
            label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            layout.addWidget(label, index, 0)

        self._name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._type_label.setStyleSheet("color: #212529;")
        self._size_label.setStyleSheet("color: #212529;")

        layout.addWidget(self._name_label, 0, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._type_label, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._size_label, 2, 1, alignment=Qt.AlignmentFlag.AlignLeft)

    def set_media(self, media: MediaFile | None) -> None:
        """Met à jour l'affichage avec les informations du média.

        Args:
            media: Média à afficher, ou ``None`` pour afficher l'état vide.
        """
        if media is None:
            self._name_label.setText("Aucun média sélectionné")
            self._type_label.setText("-")
            self._size_label.setText("-")
            return

        self._name_label.setText(media.name)
        self._type_label.setText(media.type)
        self._size_label.setText(f"{media.size} octets")
