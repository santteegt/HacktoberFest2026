---
type: topic
title: "Hacktoberfest 2026 schedule"
description: "Challenge windows, GHW dates, and where data sources disagree. Dates as fetched 2026-10-04."
tags: [program, challenges]
timestamp: "2026-10-04T00:00:00Z"
---

## Definition

The October 2026 timeline for DEV Challenge rounds and Global Hack Week: Hacktoberfest. All times are UTC. Re-fetch from `get_challenges` and the schedule feed before relying on them.

## Key Points

| Item | Window (UTC) |
| --- | --- |
| Launch livestream | Oct 1, 15:00-15:30 |
| Weekend Challenge (DEV 78) | Oct 2 02:00 → Oct 5 06:59 |
| Week 1 (DEV 79) | Oct 5 → Oct 12 06:59 |
| GHW: Hacktoberfest | Oct 9 14:00 → Oct 15 17:00 |
| Week 2 (DEV 80) | Oct 12 → Oct 19 06:59 |
| Week 3 (DEV 81) | Oct 19 → Oct 26 06:59 |
| Week 4 (DEV 82) | Oct 26 → Oct 31 / Nov 1 06:59 |

- **Discrepancy:** the schedule feed and DevRelay KB start Week 1 at Oct 5 07:00; the DEV Events API says Oct 5 16:00. Week 4 ends Oct 31 06:59 in the DEV API but Nov 1 06:59 in the feed. The challenge page wins.
- Weekend deadline in local time: Sun Oct 4, 11:59 PM PDT.
- Weeks 1-4 launch on Mondays with a new theme each and show empty details until launch.
- Feeds: `https://hacktoberfest-api.mlh.com/api/schedule` (livestreams, rounds, GHW) and `/api/events` (Fests).

## Related Concepts

- [Weekend challenge: Build for a Friend](weekend-challenge-build-for-a-friend.md)
- [Global Hack Week](global-hack-week.md)
- [Hacktoberfest 2026](hacktoberfest-2026.md)

## Sources

- [DevRelay KB: Hacktoberfest 2026](sources/devrelay-kb-hacktoberfest.md)
- [DEV Challenge 78](sources/dev-challenge-78-weekend-build-for-a-friend.md)
