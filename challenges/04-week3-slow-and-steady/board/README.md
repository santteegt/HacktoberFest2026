# board/

The skunkworks board as markdown: `board/<column>/<card-id>.md`, one file per card, columns
`backlog`, `today`, `building`, `built`, `killed`, `archived`. Postgres is the source of truth;
these files are rewritten by `sloth board build`, `sloth board render`, `sloth pick choose` and
`sloth board sync`, so never edit them by hand. They are gitignored because they hold titles and
links from the private Reading List. The same card text is mirrored to the private GitHub Project
"Skunkworks Sloth" by `sloth board sync`.
