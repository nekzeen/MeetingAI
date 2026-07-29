# Vue d'ensemble de l'architecture

Ce document capture les décisions d'architecture importantes de MeetingAI.

---

## Cycle de vie du modèle Faster-Whisper

### Initialisation

Le modèle `faster-whisper` est chargé de manière **paresseuse** :

- aucun modèle n'est chargé lors de la création du service par `SpeechToTextFactory` ;
- le chargement est déclenché automatiquement lors du **premier appel** à `FasterWhisperService.transcribe()` ;
- le modèle chargé est mis en cache dans `FasterWhisperService._model` ;
- les appels suivants à `transcribe()` réutilisent directement le modèle mis en cache.

### Responsabilités

- **`FasterWhisperService`** est responsable du cycle de vie de son modèle : il le charge, le garde en cache et le réutilise.
- **`SpeechToTextFactory`** crée l'instance du service avec la configuration utilisateur, mais ne charge pas le modèle.
- **`TranscriptionController`** et **`TranscriptionWorker`** délèguent l'exécution au service sans gérer le modèle.

### Thread-safety

Le chargement du modèle est protégé par un verrou (`threading.Lock`) afin d'éviter que plusieurs transcriptions lancées simultanément ne chargent plusieurs fois le modèle.

### Vérification de présence

Avant le chargement, `FasterWhisperService` vérifie l'existence du répertoire attendu via `is_model_present()`. Si le répertoire est absent, une `RuntimeError` explicite est levée : elle indique le nom du modèle demandé et l'emplacement recherché.

### Téléchargement / installation

`FasterWhisperService.download_model()` offre un mécanisme de téléchargement explicite. Cette méthode délègue à `faster_whisper.download_model()` et retourne le chemin du modèle téléchargé. Elle n'est **jamais appelée automatiquement** ; l'appelant doit l'invoquer explicitement (interface utilisateur, outil d'installation, etc.).

### Erreurs

Si le chargement échoue (bibliothèque absente, répertoire du modèle introuvable, erreur interne), `transcribe()` lève une `RuntimeError` explicite qui remonte jusqu'à l'utilisateur via le signal `transcription_failed` du contrôleur. Le message inclut le nom du modèle et l'emplacement recherché.

### Contrôle explicite

Les méthodes publiques `load_model()` et `download_model()` restent disponibles pour un chargement anticipé, un rechargement manuel ou un téléchargement explicite.

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

L'ajout d'un futur provider (OpenAI, Ollama...) n'implique qu'une inscription dans la factory correspondante ; l'interface se met automatiquement à jour.
