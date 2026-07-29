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
