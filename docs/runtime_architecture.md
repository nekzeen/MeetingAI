# Architecture Runtime

Ce document décrit la couche `Runtime` de MeetingAI, responsable de la
gestion des dépendances d'exécution (bibliothèques, drivers, modèles) et de
l'observabilité de l'état de santé de l'application.

## Objectifs

- Centraliser le diagnostic des dépendances nécessaires à l'application.
- Offrir une API extensible pour ajouter de nouveaux types de dépendances sans
  modifier la logique métier existante.
- Permettre l'installation ou la réparation automatique lorsque cela est
  supporté.
- Fournir à l'interface graphique un état global simple (sain, dégradé,
  manquant, erreur) et des rapports détaillés par composant.

## Concepts

### RuntimeStatus

`RuntimeStatus` représente l'état de santé d'un provider ou de l'ensemble du
Runtime. Les valeurs sont ordonnées par sévérité croissante :

- `HEALTHY` : le provider est opérationnel.
- `DEGRADED` : le provider fonctionne mais avec des limitations.
- `MISSING` : la dépendance n'est pas installée ou introuvable.
- `ERROR` : une erreur empêche le fonctionnement.
- `UNKNOWN` : l'état n'a pas pu être déterminé.

Cette sévérité permet à `RuntimeManager.status()` de retourner l'état le plus
critique en un seul appel.

### RuntimeCapability

`RuntimeCapability` identifie un domaine fonctionnel de l'application :

- `SPEECH_TO_TEXT`
- `GPU_ACCELERATION`
- `SUMMARIZATION`
- `PDF_EXPORT`
- `DOCX_EXPORT`

Chaque provider déclare les capacités qu'il couvre. Le manager peut ensuite
vérifier qu'une capacité requise dispose d'au moins un provider sain.

### RuntimeProvider

`RuntimeProvider` est l'interface abstraite que chaque provider concret doit
implémenter. Elle expose :

- `name` : nom unique.
- `capabilities` : capacités couvertes.
- `status()` : évaluation rapide.
- `diagnose()` : rapport détaillé.
- `can_install()` : indique si une installation/réparation est possible.
- `install()` : procède à l'installation/réparation.

Les providers concrets suivants sont fournis et enregistrés par
``create_runtime_manager`` :

- ``PythonRuntimeProvider`` : version de Python, plateforme, packages clés.
- ``FFmpegRuntimeProvider`` : présence et version de FFmpeg.
- ``WhisperRuntimeProvider`` : package faster-whisper **et gestion des modèles**.
- ``OllamaRuntimeProvider`` : serveur Ollama local, **version, et gestion des modèles**.
- ``CudaRuntimeProvider`` : disponibilité de CUDA via torch ou nvidia-smi.

Aucun de ces providers ne modifie le système lors du diagnostic.

## Gestion des modèles Whisper

``WhisperRuntimeProvider`` est le gestionnaire unique des modèles Whisper. Il
offre les opérations suivantes, chacune retournant un ``RuntimeReport`` :

- ``list_installed_models(models_directory)`` : liste les modèles complets.
- ``is_model_present(model_size, models_directory)`` : détecte un modèle local.
- ``install_model(model_size, models_directory)`` : télécharge un modèle.
- ``remove_model(model_size, models_directory)`` : supprime un modèle local.
- ``verify_model_integrity(model_size, models_directory)`` : vérifie la présence
  des fichiers requis.

``FasterWhisperService`` délègue la gestion des modèles à ce provider. Il accepte
un provider injecté via le paramètre ``runtime_provider`` et, par défaut, en crée
un avec sa configuration. Lors du chargement, le service demande au provider
d'installer le modèle si celui-ci n'est pas présent, puis charge le modèle en
mode ``local_files_only=True``.

## Gestion des modèles et du serveur Ollama

``OllamaRuntimeProvider`` est le gestionnaire unique d'Ollama. Il détecte le
package ou le binaire Ollama, interroge le serveur local et offre les opérations
suivantes, chacune retournant un ``RuntimeReport`` :

- ``is_ollama_present()`` : détection du package Python ou du binaire.
- ``is_server_reachable()`` : vérification que le serveur répond.
- ``get_version()`` : récupération de la version du serveur.
- ``list_installed_models()`` : liste des modèles présents sur le serveur.
- ``install_model(model_name)`` : téléchargement d'un modèle via ``/api/pull``.
- ``remove_model(model_name)`` : suppression d'un modèle via ``/api/delete``.
- ``is_model_available(model_name)`` : vérification qu'un modèle est installé.
- ``generate(prompt, model_name)`` : génération via ``/api/generate``.

``OllamaSummarizationService`` utilise exclusivement ce provider. Il accepte un
provider injecté via ``runtime_provider`` et, par défaut, en crée un avec sa
configuration. ``is_available``, ``summarize`` et ``available_models`` délèguent
les appels au provider et interprètent les ``RuntimeReport``.

### RuntimeReport

`RuntimeReport` est un rapport immuable (``frozen``) décrivant :

- le provider concerné ;
- son état après diagnostic ou opération ;
- les capacités concernées ;
- un message résumé ;
- des détails techniques libres (versions, chemins, erreurs).

### RuntimeManager

`RuntimeManager` agrège les providers et expose des opérations globales :

- `register(provider)` : ajoute un provider.
- `status()` : retourne l'état global.
- `report()` : retourne la liste des rapports de diagnostic.
- `providers_for(capability)` : filtre les providers par capacité.
- `ensure(capability)` : diagnostic et tentative d'installation automatique
  pour une capacité donnée.

## Responsabilités

| Composant | Rôle |
|-----------|------|
| `RuntimeProvider` | Contrat pour chaque type de dépendance. |
| `RuntimeManager` | Point d'entrée unique pour interroger et maintenir le Runtime. |
| `RuntimeStatus` | Vocabulaire commun d'état de santé. |
| `RuntimeCapability` | Vocabulaire commun des capacités fonctionnelles. |
| `RuntimeReport` | Structure de rapport partagée. |

## Extensibilité

Pour ajouter un nouveau provider :

1. Créer une classe héritant de `RuntimeProvider`.
2. Implémenter `status()`, `diagnose()`, `can_install()` et `install()`.
3. Déclarer les `RuntimeCapability` couvertes.
4. Enregistrer l'instance dans `RuntimeManager` au démarrage de
   l'application.

Aucune modification de `RuntimeManager` n'est nécessaire.

## Cycle de vie

1. L'application construit un `RuntimeManager` via `create_runtime_manager()` au
   démarrage.
2. Cette factory enregistre automatiquement les providers standard.
3. L'interface graphique peut interroger `status()` ou `report()` pour
   afficher l'état du système.
4. Avant une opération nécessitant une capacité, `ensure(capability)` permet
   de vérifier et de tenter de réparer automatiquement la dépendance.
5. Les résultats sont présentés à l'utilisateur via les rapports.
