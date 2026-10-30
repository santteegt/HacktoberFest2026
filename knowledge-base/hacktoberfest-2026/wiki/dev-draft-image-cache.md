---
type: "concept"
title: "DEV draft image cache"
description: "DEV caches each image at the first draft save, so push the repo before staging; if images stay broken, repin the URLs to a new commit."
tags: "[challenges, tools]"
timestamp: "2026-10-30T00:00:00Z"
---

## Definition

A staging trap for DEV posts whose images are served from a Git host: DEV fetches and caches each image when the draft is first saved, so an image that was missing then stays broken even after the URL works.

## Key Points

- Week 4: the first save came before the push, so some images stayed broken although the URLs returned 200. Repinning every image URL to a new commit fixed it. Week 2 gave the same lesson (point images at a commit SHA).
- Push first, then stage the draft with `create_article` and `published: false`.
- The DevRelay gateway answered "DEV is unavailable" on writes that had succeeded, twice. Read the draft back before retrying a write.
- DEV caps the title at 128 characters; a 130-character draft title had to be shortened (final: 74).

## Related Concepts

- [Challenge playbook](challenge-playbook.md)
- [Week 4 challenge: Ghost in the Machine](week4-challenge-ghost-in-the-machine.md)
- [DevRelay](devrelay.md)

## Sources

- [Retrospective: Week 4 Ghost in the Machine (Eth Ghosts)](sources/retrospective-week4-ghost-in-the-machine.md)
