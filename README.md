# MeetingAI

<div align="center">

# 🎙️ MeetingAI

### Assistant IA de transcription et de compte-rendu de réunions

Transcrivez vos réunions, générez des comptes-rendus professionnels et automatisez la création de documents grâce à l'IA.

![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![Status](https://img.shields.io/badge/Status-En%20développement-orange)

</div>

---

## 📖 Présentation

MeetingAI est une application de bureau développée en Python permettant de transcrire automatiquement des réunions, conférences, formations ou interviews grâce à **faster-whisper**.

L'objectif n'est pas seulement de produire une transcription, mais de fournir un véritable assistant de réunion capable de générer automatiquement :

- une transcription complète ;
- un résumé intelligent ;
- les décisions prises ;
- les actions à réaliser ;
- un compte-rendu professionnel ;
- des exports dans différents formats.

Le projet est conçu pour fonctionner **entièrement en local**, sans envoyer vos données vers un service externe (hors fonctionnalités IA optionnelles).

---

# ✨ Fonctionnalités

## Version 1

- Interface graphique moderne (PySide6)
- Glisser-déposer des fichiers
- Transcription locale avec faster-whisper
- Détection automatique de la langue
- Export TXT
- Export PDF
- Barre de progression
- Journal d'exécution

---

## Version 2 (prévue)

- Résumé automatique
- Extraction des décisions
- Extraction des actions
- Export Markdown
- Export Word

---

## Version 3 (prévue)

- Reconnaissance des intervenants (Diarisation)
- Statistiques de parole
- Recherche dans les réunions
- Historique

---

## Version 4 (prévue)

- IA locale via Ollama
- Résumé avec Llama 3
- Résumé avec Gemma
- Résumé avec Mistral

---

## Version 5 (prévue)

- Intégration Microsoft Teams
- Surveillance automatique d'un dossier
- Traitement automatique des nouveaux enregistrements
- Gestion multi-projets

---

# 🚀 Fonctionnement

```text
           Audio / Vidéo

                  │

                  ▼

      faster-whisper (local)

                  │

                  ▼

         Transcription TXT

                  │

        ┌─────────┴─────────┐

        ▼                   ▼

     Export PDF        Résumé IA

        │                   │

        └─────────┬─────────┘

                  ▼

          Compte-rendu final
```

---

# 📂 Formats supportés

## Audio

- MP3
- WAV
- FLAC
- OGG
- M4A

## Vidéo

- MP4
- MKV
- AVI
- MOV

---

# 📦 Exports

MeetingAI pourra produire automatiquement :

```
Réunion.txt
Réunion.pdf
Réunion.docx
Réunion.md
Réunion.json
```

---

# 🖥️ Interface

L'application utilise **PySide6** afin d'offrir une interface moderne inspirée des applications Windows récentes.

Fonctionnalités prévues :

- thème sombre
- glisser-déposer
- barre de progression
- historique
- paramètres
- sélection du modèle Whisper

---

# ⚙️ Technologies utilisées

## Interface

- PySide6

## Transcription

- faster-whisper
- CTranslate2
- PyAV

## Export

- ReportLab
- python-docx
- Markdown

## IA

- Ollama (optionnel)
- OpenAI (optionnel)

---

# 📁 Architecture

```
MeetingAI
│
├── meetingai/
│   ├── gui/
│   ├── core/
│   ├── ai/
│   ├── export/
│   ├── models/
│   ├── utils/
│   └── resources/
│
├── tests/
├── docs/
├── output/
├── requirements.txt
├── README.md
└── main.py
```

---

# 📥 Installation

## Cloner le dépôt

```bash
git clone https://github.com/nekzeen/MeetingAI.git
```

Puis :

```bash
cd MeetingAI
```

Créer un environnement virtuel :

```bash
py -m venv .venv
```

Activation :

### Windows

```bash
.venv\Scripts\activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

---

# ▶️ Lancement

```bash
python main.py
```

---

# 📋 Dépendances principales

- Python 3.12 ou supérieur
- PySide6
- faster-whisper
- reportlab
- python-docx
- pydub

---

# 🗺️ Feuille de route

## v1.0

- [x] Création du projet
- [ ] Interface graphique
- [ ] Transcription
- [ ] Export TXT
- [ ] Export PDF

---

## v1.1

- [ ] Paramètres
- [ ] Choix du modèle
- [ ] Journal

---

## v2.0

- [ ] Résumé IA
- [ ] Décisions
- [ ] Actions
- [ ] Export Word

---

## v3.0

- [ ] Diarisation
- [ ] Historique
- [ ] Recherche

---

## v4.0

- [ ] IA locale
- [ ] Ollama
- [ ] Llama
- [ ] Gemma
- [ ] Mistral

---

## v5.0

- [ ] Microsoft Teams
- [ ] Outlook
- [ ] Synchronisation
- [ ] Automatisation

---

# 🤝 Contribution

Les contributions sont les bienvenues.

Avant toute contribution importante, merci d'ouvrir une *Issue* afin de discuter des évolutions proposées.

---

# 📜 Licence

Ce projet est distribué sous licence **MIT**.

Voir le fichier **LICENSE** pour plus d'informations.

---

# 👤 Auteur

**Gaël Morvan**

GitHub : https://github.com/nekzeen

---

# ⭐ Objectif du projet

Créer un assistant de réunion open source, moderne et entièrement local, capable de remplacer les solutions propriétaires tout en garantissant la confidentialité des données.

L'objectif final est de proposer un outil complet permettant de produire automatiquement des comptes-rendus professionnels à partir d'un simple enregistrement audio ou vidéo.

---

<div align="center">

**MeetingAI** — *Your meetings, intelligently transcribed.*

</div>
