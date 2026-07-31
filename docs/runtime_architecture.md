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

À ce stade, aucun provider concret n'est fourni. Les implémentations futures
représenteront par exemple le runtime Python, les drivers CUDA, les modèles
Whisper, etc.

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

1. L'application construit un `RuntimeManager` au démarrage.
2. Elle y enregistre les providers pertinents.
3. L'interface graphique peut interroger `status()` ou `report()` pour
   afficher l'état du système.
4. Avant une opération nécessitant une capacité, `ensure(capability)` permet
   de vérifier et de tenter de réparer automatiquement la dépendance.
5. Les résultats sont présentés à l'utilisateur via les rapports.
