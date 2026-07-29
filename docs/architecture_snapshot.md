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

### Erreurs

Si le chargement échoue (bibliothèque absente, répertoire du modèle introuvable, erreur interne), `transcribe()` lève une `RuntimeError` explicite qui remonte jusqu'à l'utilisateur via le signal `transcription_failed` du contrôleur.

### Contrôle explicite

La méthode publique `load_model()` reste disponible pour un chargement anticipé ou un rechargement manuel si nécessaire.
