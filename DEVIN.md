# Guide de développement MeetingAI

Ce document constitue la référence permanente pour toute contribution au projet MeetingAI.

---

## Présentation du projet

MeetingAI est une application de bureau développée en Python. Elle permet de :

- transcrire des réunions en local ;
- générer des résumés par IA ;
- exporter les comptes-rendus au format PDF et DOCX ;
- conserver un historique des traitements ;
- étendre les fonctionnalités via une architecture à plugins.

---

## Technologies

Le projet repose sur les technologies et bibliothèques suivantes :

- Python 3.12+
- PySide6 (interface graphique)
- faster-whisper (transcription locale)
- ReportLab (export PDF)
- python-docx (export DOCX)
- logging (journalisation)
- JSON (persistance de la configuration)

Aucune dépendance supplémentaire ne doit être ajoutée sans validation préalable.

---

## Organisation du projet

```text
meetingai/
├── gui/        # Interface graphique et composants visuels
├── core/       # Logique métier et traitements principaux
├── services/   # Intégrations externes et adaptateurs
└── resources/  # Ressources embarquées (icônes, styles, traductions)

docs/           # Documentation technique et guides
tests/          # Tests unitaires et d'intégration
output/         # Fichiers générés par l'application
```

Les dossiers suivants pourront être ajoutés ultérieurement si nécessaire :

- `workers/` : traitements longs exécutés en arrière-plan ;
- `models/` : définitions des entités et structures de données ;
- `config/` : gestion centralisée de la configuration ;
- `assets/` : ressources graphiques et médias.

---

## Règles d'architecture

- L'interface graphique ne contient jamais de logique métier ;
- La logique métier appartient à `core/` ;
- Les intégrations externes et les appels réseau appartiennent à `services/` ;
- Les traitements longs sont isolés de l'interface graphique ;
- La composition est privilégiée à l'héritage ;
- Les variables globales sont proscrites.

---

## Règles de développement

Le code doit respecter les principes suivants :

- conformité à la PEP 8 ;
- utilisation des annotations de type ;
- docstrings pour les fonctions, classes et modules publics ;
- fonctions courtes et lisibles ;
- noms explicites et cohérents ;
- absence de duplication de code ;
- absence de code mort ou de commentaires inutiles ;
- pas de `TODO` sauf demande explicite.

---

## Dépendances

Avant d'ajouter une bibliothèque au projet, vérifier que :

1. Une bibliothèque existante ne peut pas répondre au besoin ;
2. La licence est compatible avec le projet ;
3. Le surcoût en taille et en maintenance est acceptable.

---

## Git

### Branches

- Une fonctionnalité = une branche dédiée.
- Une Pull Request = une fonctionnalité livrée.
- La branche principale est `main`.

### Commits

Les messages de commit suivent la convention [Conventional Commits](https://www.conventionalcommits.org/) :

```text
feat(gui): add main window
fix(pdf): correct export alignment
docs: update architecture
```

---

## Documentation

- Toute API publique doit être documentée.
- Toute décision d'architecture importante doit être consignée dans `docs/`.
- Les guides utilisateurs et techniques sont maintenus à jour.

---

## Revue de code

Avant de considérer une mission comme terminée, vérifier :

- les imports sont valides ;
- aucune erreur de syntaxe n'est présente ;
- la documentation est mise à jour si nécessaire ;
- aucun fichier hors périmètre n'a été modifié.
