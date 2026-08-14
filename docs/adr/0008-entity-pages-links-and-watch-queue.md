# ADR 0008: Entity pages, link provenance and watch queue

- Status: Accepted
- Date: 2026-08-14

## Context

Peach needs durable performer, studio, creator and series pages instead of treating every name click as a transient list filter. Those pages need summaries, aliases, official/social/catalog links, personal source evidence and search terms. “Watch later” is a queue intent, not a like/dislike/watched judgment.

## Decision

- Canonical identity remains in `entity`; summaries and low-cardinality descriptive fields remain in `metadata_json`.
- `entity_link` stores typed links. Official, social and catalog links are clickable. `source_reference` is private provenance: the API exposes its label/hostname but withholds the URL from the web client.
- `entity_search_term` stores user-maintained discovery or source-lookup vocabulary. Peach does not automatically search or download infringing copies.
- `watch_queue` is profile-scoped and separate from asset feedback. The first deployment seeds the single local default profile.
- Entity portraits are cached files with provenance. Network-sourced, verified images take priority; a representative contact-sheet crop is only a fallback. Stash is not accepted as a portrait source when it returns its default silhouette.
- Clear studio duplicates are merged by a reviewed, dry-run-first script. Old names survive as aliases and flattened `asset.studio` remains a compatibility projection.

## Rejected

- Encoding “watch later” as `feedback='seen'` or another overloaded asset flag.
- Making private acquisition/source URLs directly clickable in the web UI.
- Automatically merging studios solely because punctuation-normalized names collide.
- Treating a Stash placeholder image or search-engine thumbnail as a high-resolution performer portrait.

## Consequences

Entity pages can accumulate trusted metadata without changing the asset model, and future profiles get independent queues. Link and portrait importers require provenance and review, but Peach avoids turning personal source history into an automatic piracy workflow or low-quality image cache.
