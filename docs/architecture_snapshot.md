# Vue d'ensemble de l'architecture

Ce document capture les décisions d'architecture importantes de MeetingAI.

---

## Architecture globale V1

MeetingAI est organisé en couches unidirectionnelles. La couche graphique ne
contient aucune logique métier ; elle délègue aux contrôleurs, qui coordonnent
les briques du noyau (`core`) et les services (`services`).

```text
┌─────────────────────────────────────────────┐
│                     GUI                       │
│  MainWindow · Workspace · SettingsWindow      │
├─────────────────────────────────────────────┤
│                 Controllers                 │
│  Media · Transcription · Summarization        │
│  Export · Settings · Pipeline               │
├─────────────────────────────────────────────┤
│                    Core                     │
│  TaskManager · WorkerManager · Workers       │
├─────────────────────────────────────────────┤
│                   Runtime                     │
│  RuntimeManager · RuntimeProvider · Reports   │
├─────────────────────────────────────────────┤
│                   Services                  │
│  Speech-To-Text · Summarization · Export    │
│  Media · Models                             │
└─────────────────────────────────────────────┘
```

### Règles de dépendance

- `gui` dépend de `controllers` et de `core` uniquement via les signaux.
- `controllers` dépend de `core`, de `runtime` et de `services`.
- `core` ne dépend pas de `gui` ni de `controllers`.
- `runtime` ne dépend pas de `gui`, de `controllers` ni de `core`.
- `services` ne dépendent ni de `gui`, ni de `controllers`, ni du flux applicatif.
- Aucune dépendance circulaire n'est autorisée.

### Flux de données

1. L'utilisateur déclenche une action depuis `MainWindow`.
2. `ActionManager` transmet le signal au contrôleur concerné.
3. Le contrôleur utilise `core` (tâches, workers) pour exécuter un traitement
   long sans bloquer l'interface.
4. Le worker délègue le traitement réel à un service.
5. Les résultats remontent par signaux jusqu'aux widgets.

---

## Workflows utilisateur principaux

### Ouvrir un média

1. `MainWindow` déclenche `MediaController.open_media()`.
2. `MediaController` affiche `QFileDialog` et valide le fichier via
   `MediaService`.
3. Le signal `media_loaded` met à jour `MediaInformationWidget`.

### Transcrire

1. `MainWindow` déclenche `TranscriptionController.transcribe(media)`.
2. Un `TranscriptionWorker` exécute `SpeechToTextService.transcribe()` dans un
   thread dédié.
3. Les signaux `transcription_started`, `transcription_progress`,
   `transcription_ready` mettent à jour l'interface.

### Résumer

1. `MainWindow` déclenche
   `SummarizationController.summarize_current_transcription()`.
2. Le contrôleur résout le `SummaryProfile` configuré et appelle
   `SummarizationService.summarize(text, profile)`.
3. Le signal `summary_ready` met à jour `SummaryWidget`.

### Exporter

1. `MainWindow` déclenche `ExportController.export_txt()` ou
   `export_markdown()`.
2. Le contrôleur appelle `ExportService.export()` avec le dernier
   `TranscriptionResult` connu.
3. Le signal `export_succeeded` retourne le chemin du fichier généré.

### Pipeline automatique

1. `MainWindow` déclenche `PipelineController.start(media)`.
2. Le pipeline enchaîne transcription, résumé puis export TXT.
3. Toute erreur interrompt le déroulement et est propagée via
   `pipeline_failed`.

---

## Interface principale

`MainWindow` (`meetingai/gui/main_window.py`) adopte une disposition guidée par
le workflow utilisateur :

- **Écran d'accueil** : `WelcomeWidget` s'affiche tant qu'aucun média n'est
  ouvert. Il présente un message de bienvenue, un gros bouton "Ouvrir un média"
  et un rappel visuel des quatre étapes du workflow.
- **Zone d'édition** : dès qu'un média est chargé, `Workspace` bascule vers
  `_EditorWidget`. Un `QSplitter` horizontal place le panneau latéral
  (informations média + historique) à gauche et la zone de travail principale
  (transcription + résumé) à droite. La transcription occupe la majeure partie
  de l'écran.
- **Barre d'outils** : expose les actions clés (Ouvrir, Transcrire, Résumer,
  Exporter) via `ActionManager`.
- **Barre d'état** : affiche l'état du Runtime, le fournisseur STT, le
  fournisseur IA, un message de progression et une barre de progression
  indéterminée pendant les traitements.

Les informations du média sont présentées de manière compacte dans
`MediaInformationWidget` : nom, type et taille, les détails techniques étant
accessibles uniquement via des tooltips.

---

## Cycle de vie du modèle Faster-Whisper

### Initialisation

Le modèle `faster-whisper` est chargé de manière **paresseuse** :

- aucun modèle n'est chargé lors de la création du service par `SpeechToTextFactory` ;
- le chargement est déclenché automatiquement lors du **premier appel** à `FasterWhisperService.transcribe()` ;
- le modèle chargé est mis en cache dans `FasterWhisperService._model` ;
- les appels suivants à `transcribe()` réutilisent directement le modèle mis en cache.

### Résolution du modèle

`WhisperRuntimeProvider` est l'unique source de vérité pour l'emplacement des
modèles. Il tente d'abord de détecter un modèle déjà présent dans
`models_directory / model_size` (par exemple `models/small`). Si le modèle est
présent, ce chemin est utilisé directement.

Si le modèle n'existe pas, le provider télécharge le modèle dans
`models_directory / model_size` via `faster_whisper.download_model` et retourne
le chemin réel fourni par la bibliothèque. `FasterWhisperService` charge le
modèle en `local_files_only=True` depuis ce chemin exact. Aucune manipulation
manuelle n'est donc requise pour une installation neuve disposant d'une
connexion internet.

Si le téléchargement échoue (pas de réseau, espace insuffisant...), une
`RuntimeError` claire est remontée. Elle indique :

- le nom du modèle concerné ;
- l'emplacement exact utilisé ;
- la cause réelle de l'échec (message retourné par `WhisperRuntimeProvider`) ;
- la commande `WhisperRuntimeProvider.install_model(...)` permettant de
  télécharger le modèle explicitement.

Cette erreur est remontée jusqu'à l'interface via `transcription_failed` (ou
`pipeline_failed`) et présentée à l'utilisateur dans une boîte de dialogue.

### Phases visibles pour l'utilisateur

`TranscriptionWorker` émet un signal `status` (textuel) en plus du signal
`progress` (numérique). Ce signal est relayé par `TranscriptionController` sous
le nom `transcription_status` et affiché dans la barre de statut de
`MainWindow`. Les phases suivantes sont distinguées :

- **Préparation** : signal initial avec `progress == 0`.
- **Téléchargement du modèle** : affiché lors de la première utilisation si le
  modèle n'est pas déjà présent (`is_model_present() == False`).
- **Chargement du modèle** : affiché si le modèle est déjà présent ou une fois
  le téléchargement terminé.
- **Transcription en cours** : affiché dès que le service signale une
  progression.
- **Terminé** : `progress == 100` et affichage du résultat.

La progression numérique reste inchangée : 0 au début, puis les valeurs
fournies par le service (`0–100`).

À l'issue de chaque transcription, `TranscriptionController` émet un message
d'état final (`Transcription terminée.`, `Erreur de transcription.` ou
`Transcription annulée.`) via `transcription_status`. Un garde-fou vérifie que
les messages de phase provenant d'un worker (`status`) ne sont relayés que
tant que ce worker est encore répertorié comme actif, évitant ainsi qu'un
signal asynchrone retardé n'écrase l'état final.

### Périphérique d'exécution

Le périphérique configuré (`auto`, `cpu`, `cuda`) est transmis à
`WhisperModel`. Si l'initialisation échoue avec un message lié à CUDA
(`cublas`, `cudnn`, `cuda_runtime`, etc.) et que le périphérique demandé
n'est pas déjà `cpu`, le service tente de recharger automatiquement le
modèle sur `cpu` avec `int8`. Cet événement est :

- journalisé en `WARNING` lors du basculement ;
- journalisé en `INFO` une fois le modèle chargé en CPU ;
- signalé à l'utilisateur via une boîte de dialogue lorsque le résultat de
  transcription est prêt.

Lorsque CUDA est correctement installé, aucun fallback n'est déclenché et
le périphérique configuré est utilisé normalement.

### Responsabilités

- **`FasterWhisperService`** est responsable du cycle de vie de son modèle : il le charge, le garde en cache et le réutilise.
- **`SpeechToTextFactory`** crée l'instance du service avec la configuration utilisateur, mais ne charge pas le modèle.
- **`TranscriptionController`** et **`TranscriptionWorker`** délèguent l'exécution au service sans gérer le modèle.

### Thread-safety

Le chargement du modèle est protégé par un verrou (`threading.Lock`) afin d'éviter que plusieurs transcriptions lancées simultanément ne chargent plusieurs fois le modèle.

### Vérification de présence

`SpeechToTextService` expose `is_model_present()` (valeur par défaut `True`).
`FasterWhisperService` la surcouche pour vérifier l'existence du répertoire
local `models_directory / model_size`. Cette information permet à
`TranscriptionWorker` d'afficher le bon message de phase à l'utilisateur
("téléchargement" vs "chargement") avant la première transcription.

### Téléchargement / installation

`WhisperRuntimeProvider.install_model()` offre un mécanisme de téléchargement
explicite. Cette méthode délègue à `faster_whisper.download_model()` en lui
passant `output_dir=models_directory / model_size`, et retourne le chemin du
modèle téléchargé dans le `RuntimeReport`. `FasterWhisperService` déclenche
automatiquement cette installation lors du premier chargement si le modèle
n'est pas déjà présent. En cas d'échec, une `RuntimeError` explicite est
remontée.

### Erreurs

Si le chargement échoue (bibliothèque absente, répertoire du modèle introuvable, erreur interne), `transcribe()` lève une `RuntimeError` explicite qui remonte jusqu'à l'utilisateur via le signal `transcription_failed` du contrôleur. Le message inclut le nom du modèle et l'emplacement recherché.

### Contrôle explicite

Les méthodes publiques `FasterWhisperService.load_model()` et
`WhisperRuntimeProvider.install_model()` restent disponibles pour un chargement
anticipé, un rechargement manuel ou un téléchargement explicite.

---

## Versionnement de la configuration

### Principe

Le fichier de configuration locale `config/config.json` n'est pas versionné. Il est généré automatiquement par `ConfigManager` à partir des valeurs par défaut s'il est absent.

Le fichier `config/config.example.json` sert de modèle versionné : il présente la structure complète et les valeurs par défaut pour les développeurs et les déploiements.

### Règles

- `config/config.json` est ignoré par Git (``.gitignore``) ;
- `config/config.example.json` est versionné et mis à jour lorsque la structure de configuration évolue ;
- `ConfigManager` crée automatiquement `config/config.json` avec les valeurs par défaut si le fichier est absent au démarrage.

---

## Fenêtre de paramètres

### Vue

`SettingsWindow` (`meetingai/gui/settings_window.py`) est une `QDialog` organisée en sections :

- **Général** : thème, langue ;
- **Speech-To-Text** : provider, modèle, device, compute type ;
- **Export** : répertoire de sortie.

La vue ne contient aucune logique métier. Elle se contente de collecter les valeurs via `get_settings()` et de les restituer à l'appelant.

### Contrôleur

`SettingsController` (`meetingai/controllers/settings_controller.py`) est responsable du chargement et de la sauvegarde des paramètres via `ConfigManager`. Il valide les valeurs avant persistance.

### Intégration

`MainWindow` ouvre la fenêtre de paramètres lors du déclenchement de l'action ``Préférences``. Elle charge les valeurs actuelles, affiche le dialogue, puis appelle `SettingsController.save_settings()` si l'utilisateur valide.

---

## Progression de la transcription

### Principe

La progression affichée à l'utilisateur est désormais calculée à partir de l'avancement réel de la transcription.

### Flux

1. **`FasterWhisperService.transcribe()`** accepte un `progress_callback`. Pendant l'itération sur les segments retournés par faster-whisper, il calcule le pourcentage d'avancement à partir du timestamp de fin du segment et de la durée totale du média.
2. **`TranscriptionWorker`** passe une fonction de rappel à `SpeechToTextService.transcribe()` ; à chaque appel, elle émet le signal `progress` et met à jour `Task.update_progress()`.
3. **`TranscriptionController`** relie le signal `progress` du worker à son propre signal `transcription_progress`, qui alimente l'interface graphique.
4. **`FakeSpeechToTextService`** reste compatible : il signale simplement 100% de progression, car il n'y a pas de traitement réel à mesurer.

### Limites

- faster-whisper ne fournit pas de callback natif de progression. La progression est donc estimée à partir des segments produits.
- La granularité dépend de la taille des segments : de courts fichiers audio peuvent passer directement de 0 à 100%.

---

## Export des transcriptions

### Architecture

L'export repose sur le pattern **Stratégie** pour rester extensible.

- **`Exporter`** (`meetingai/services/export/exporter.py`) : contrat commun avec une propriété ``extension`` et une méthode ``export``.
- **`TxtExporter`** / **`MarkdownExporter`** : implémentations concrètes pour les formats TXT et Markdown.
- **`ExportService`** (`meetingai/services/export/export_service.py`) : registre des exporteurs. De nouveaux formats (DOCX, PDF, JSON...) s'ajoutent via ``register_exporter()`` sans modifier le code existant.
- **`ExportController`** (`meetingai/controllers/export_controller.py`) : garde le dernier résultat de transcription et déclenche l'export. Il choisit le répertoire de sortie depuis ``ConfigManager``.

### Intégration UI

Les actions ``Exporter en TXT`` et ``Exporter en Markdown`` sont ajoutées au menu ``Fichier`` par ``MainWindow`` et connectées à ``ExportController``. Aucune logique métier n'est présente dans la vue.

---

## Architecture de résumé IA

### Principe

Le résumé IA suit la même architecture abstraite que Speech-To-Text et Export afin de rester indépendant du fournisseur.

### Composants

- **`SummarizationService`** (`meetingai/services/summarization/summarization_service.py`) : contrat commun avec `name()`, `is_available()` et `summarize(text)`.
- **`SummaryResult`** (`meetingai/services/summarization/summary_result.py`) : dataclass retournée par `summarize()`.
- **`FakeSummarizationService`** : implémentation factice retournant un résumé fixe, utilisée pour valider l'architecture sans appel IA réel.
- **`SummarizationFactory`** (`meetingai/services/summarization/summarization_factory.py`) : registre des providers. De nouveaux providers (OpenAI, Ollama, LM Studio, Azure OpenAI...) s'ajoutent via `register_provider()` sans modifier le code existant.

### Extensibilité

Chaque futur provider n'a qu'à hériter de ``SummarizationService`` et être enregistré dans la factory pour être disponible dans l'application.

---

## Intégration du résumé IA

### Workflow

1. **`SummarizationController`** est créé par ``ApplicationContext`` avec ``SummarizationFactory`` et ``ConfigManager``.
2. Le contrôleur écoute ``transcription_ready`` du ``TranscriptionController`` pour conserver la dernière transcription.
3. L'action ``Résumer la transcription`` dans le menu ``Outils`` déclenche ``SummarizationController.summarize_current_transcription()``.
4. Le contrôleur instancie le provider configuré (``fake`` par défaut) et appelle ``summarize()`` avec le texte complet de la transcription.
5. Le signal ``summary_ready`` met à jour ``SummaryWidget``.

### Indépendance du provider

Le contrôleur ne dépend d'aucun provider concret : il utilise ``SummarizationFactory`` et la clé ``summarization.provider`` de la configuration. Seul le provider ``fake`` est activé dans cette version.

---

## Gestion des providers IA

### Configuration

La fenêtre de paramètres expose désormais deux sections alimentées dynamiquement par les factories :

- **Speech-To-Text** : la liste des providers provient de ``SpeechToTextFactory.available_providers()``.
- **Résumé IA** : la liste des providers provient de ``SummarizationFactory.available_providers()``.

`SettingsController` charge les listes depuis les factories, les transmet à `SettingsWindow`, et persiste les choix via `ConfigManager`. Aucune valeur n'est codée en dur dans la vue.

### Persistance

Les clés utilisées sont :

- ``speech_to_text.provider`` pour la transcription ;
- ``summarization.provider`` pour le résumé IA.

L'ajout d'un futur provider n'implique qu'une inscription dans la factory correspondante ; l'interface se met automatiquement à jour.

---

## Provider Ollama

### Implémentation

`OllamaSummarizationService` est le premier provider réel de résumé IA :

- Appelle les endpoints HTTP ``/api/tags`` (disponibilité) et ``/api/generate`` (génération).
- Paramètres configurables via ``ConfigManager`` :
  - ``summarization.ollama_url`` (défaut : ``http://localhost:11434``)
  - ``summarization.ollama_model`` (défaut : ``llama3.2``)
  - ``summarization.ollama_timeout`` (défaut : ``30``)
- Retourne un ``SummaryResult`` avec le texte produit par le modèle.
- Gère les erreurs réseau, les délais d'attente et les réponses JSON invalides en levant ``RuntimeError``.

### Intégration

Le provider est automatiquement enregistré dans ``SummarizationFactory``. Le contrôleur l'instancie avec la configuration courante lorsque ``summarization.provider`` vaut ``ollama``. Aucune modification structurelle du contrôleur ou de l'interface n'a été nécessaire.

---

## Gestion des modèles Ollama

### Détection automatique

`OllamaSummarizationService` expose une méthode ``available_models()`` qui interroge ``/api/tags`` pour récupérer la liste des modèles installés localement. La méthode retourne une liste triée des noms et lève ``RuntimeError`` en cas d'indisponibilité du serveur ou de réponse invalide.

### Sélection dans les paramètres

`SettingsController` appelle ``available_models()`` lors du chargement de la fenêtre de paramètres et transmet la liste à `SettingsWindow`. La fenêtre affiche une liste déroulante éditable permettant de choisir un modèle parmi ceux détectés ou d'en saisir un manuellement si le serveur n'est pas joignable. Le modèle sélectionné est persisté sous ``summarization.ollama_model``.

### Extensibilité

La méthode ``available_models()`` fait partie de l'interface ``SummarizationService``. Les futurs providers qui proposent plusieurs modèles pourront l'implémenter de la même manière sans modifier le contrôleur ou la vue.

---

## Pipeline automatique

### Objectif

Le pipeline automatique enchaîne en une seule action la transcription, la génération du résumé IA et l'export du résultat. Il s'appuie exclusivement sur les contrôleurs existants sans dupliquer leur logique.

### Composants

- **`PipelineController`** (`meetingai/controllers/pipeline_controller.py`) : orchestre les étapes en connectant les signaux des contrôleurs dédiés.
- **`TranscriptionController`** : exécute la transcription de manière asynchrone.
- **`SummarizationController`** : génère le résumé IA dès que la transcription est prête.
- **`ExportController`** : exporte la transcription au format TXT une fois le résumé produit.

### Flux

1. L'utilisateur déclenche l'action ``Traitement automatique`` dans le menu ``Outils``.
2. `PipelineController.start(media)` lance la transcription.
3. Sur ``transcription_ready`` :
   - le pipeline émet ``pipeline_step_started(summarization)`` ;
   - il appelle `SummarizationController.summarize_current_transcription()`.
4. Sur ``summary_ready`` :
   - le pipeline émet ``pipeline_step_started(export)`` ;
   - il appelle `ExportController.export_txt()`.
5. Sur ``export_succeeded``, le pipeline émet ``pipeline_succeeded`` avec le chemin du fichier exporté.
6. Si une étape échoue, le pipeline s'arrête immédiatement et émet ``pipeline_failed`` avec le message d'erreur.

### Signaux

- `pipeline_started` : début du pipeline.
- `pipeline_step_started(str)` : nom de l'étape en cours (``transcription``, ``summarization``, ``export``).
- `pipeline_progress(int)` : progression de la transcription remontée durant le pipeline.
- `pipeline_succeeded(list[str])` : liste des chemiers exportés.
- `pipeline_failed(str)` : raison de l'échec.

### Extensibilité

Chaque étape reste un contrôleur dédié. Ajouter une nouvelle étape (traduction, analyse...) consiste à insérer un nouveau contrôleur entre `SummarizationController` et `ExportController` sans modifier les étapes existantes.

## Dette technique identifiée

Les points suivants ont été repérés lors de l'audit V1. Ils n'ont pas été
corrigés afin de ne pas introduire de changement fonctionnel, mais pourront faire
l'objet de refactorisations futures :

- `ConfigManager` conserve une section `transcription` historique en plus de
  `speech_to_text`. La fusion ou le retrait de cette section nécessiterait une
  migration des configurations existantes.
- `SummarizationFactory.create()` contient une branche spécifique au provider
  `ollama`. Une amélioration consisterait à faire accepter une configuration à
  chaque provider de manière uniforme, sans logique conditionnelle dans la
  factory.
- Le type `Worker` défini dans `core/worker.py` est une abstraction peu exploitée
  : `TranscriptionWorker` n'en hérite pas car il doit être un `QObject` porteur
  de signaux Qt.

## Profils de résumé

### Définition

Un profil de résumé est représenté par ``SummaryProfile`` (clé, libellé affiché, instruction). Les profils par défaut sont :

- ``concise`` : résumé concis ;
- ``meeting_minutes`` : compte rendu structuré de réunion ;
- ``key_points`` : points clés ;
- ``action_items`` : actions à entreprendre ;
- ``decisions`` : décisions prises.

``ProfileRegistry`` centralise les profils disponibles et permet d'en ajouter de nouveaux sans modifier les providers.

### Transmission au provider

L'interface ``SummarizationService.summarize(text, profile)`` reçoit désormais le profil sélectionné. Chaque provider utilise ``profile.instruction`` pour guider la génération. Le provider ``fake`` intègre l'instruction du profil dans son résumé simulé afin de faciliter les tests.

### Profil personnalisé

En plus des profils intégrés, un profil ``custom`` est disponible. L'utilisateur peut saisir ses propres instructions dans `SettingsWindow`. Celles-ci sont persistées sous ``summarization.custom_profile_instruction``. Lorsque le profil ``custom`` est sélectionné, `SummarizationController` construit le ``SummaryProfile`` avec cette instruction avant de l'envoyer au provider.

### Sélection et persistance

- `SummarizationController` lit ``summarization.profile`` (défaut : ``concise``) et transmet le profil au provider.
- `SettingsController` charge les profils intégrés via ``ProfileRegistry``, ajoute le profil personnalisé et propose l'ensemble dans `SettingsWindow`.
- La clé sélectionnée est persistée sous ``summarization.profile``.
- L'instruction personnalisée est persistée sous ``summarization.custom_profile_instruction``.
