#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Point d'entrée de l'application MeetingAI."""

import sys

from meetingai.gui.application import MeetingAIApplication


def main() -> int:
    """Lance l'application MeetingAI.

    Returns:
        Code de retour de l'application.
    """
    app = MeetingAIApplication()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
