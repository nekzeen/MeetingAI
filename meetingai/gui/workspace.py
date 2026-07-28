"""Conteneur principal des vues de l'application MeetingAI."""

from PySide6.QtWidgets import QHBoxLayout, QWidget

from meetingai.controllers.media_controller import MediaController
from meetingai.core.service_registry import ServiceRegistry
from meetingai.gui.widgets.media_information_widget import MediaInformationWidget


class Workspace(QWidget):
    """Widget central contenant le layout principal de l'application.

    Le ``Workspace`` accueille les panneaux de l'interface graphique. Il
    utilise un ``QHBoxLayout`` horizontal afin de faciliter l'ajout de
    plusieurs vues côte à côte.

    Ce composant intègre ``MediaInformationWidget`` et le connecte au
    contrôleur média afin d'afficher automatiquement les informations du
    média chargé.
    """

    _MARGIN: int = 12
    _SPACING: int = 12

    def __init__(
        self,
        parent: QWidget | None = None,
        media_controller: MediaController | None = None,
    ) -> None:
        """Initialise le workspace et ses panneaux.

        Args:
            parent: Widget parent éventuel.
            media_controller: Contrôleur média dont le signal
                ``media_loaded`` mettra à jour le widget d'information. S'il
                n'est pas fourni, le workspace tente de le récupérer depuis le
                ``ServiceRegistry``.
        """
        super().__init__(parent)
        self._setup_ui()
        self._connect_controller(media_controller)

    def _setup_ui(self) -> None:
        """Crée le layout horizontal et ajoute les panneaux."""
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(
            self._MARGIN, self._MARGIN, self._MARGIN, self._MARGIN
        )
        self._layout.setSpacing(self._SPACING)

        self._info_widget = MediaInformationWidget(self)
        self._layout.addWidget(self._info_widget)

    def _connect_controller(self, media_controller: MediaController | None) -> None:
        """Connecte le signal ``media_loaded`` au widget d'information."""
        if media_controller is None:
            try:
                media_controller = ServiceRegistry().get("media_controller")
            except KeyError:
                return
        media_controller.media_loaded.connect(self._info_widget.set_media)

    def layout(self) -> QHBoxLayout:
        """Retourne le layout principal du workspace.

        Returns:
            Le ``QHBoxLayout`` du workspace.
        """
        return self._layout

    @property
    def media_information_widget(self) -> MediaInformationWidget:
        """Retourne le widget d'information du média."""
        return self._info_widget
