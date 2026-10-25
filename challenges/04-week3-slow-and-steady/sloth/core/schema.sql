-- Skunkworks Sloth schema (coordinator-owned; lanes request changes in their lane log).
-- Idempotent: safe to re-run.

CREATE TABLE IF NOT EXISTS links (
    id              BIGSERIAL PRIMARY KEY,
    url             TEXT NOT NULL,
    canonical_url   TEXT NOT NULL UNIQUE,
    title           TEXT,
    folder_path     TEXT,
    saved_at        TIMESTAMPTZ,
    source          TEXT NOT NULL DEFAULT 'reading-list',   -- reading-list | x | gmail
    status          TEXT NOT NULL DEFAULT 'new',            -- new | enriched | kept (build candidate, buildable >= 2) | reading (relevant, nothing to build) | valhalla | unsure
    batch_id        TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS enrichment (
    link_id             BIGINT PRIMARY KEY REFERENCES links(id) ON DELETE CASCADE,
    http_status         INT,
    final_url           TEXT,
    content_kind        TEXT,                -- html | github | pdf | video | other
    readable_text       TEXT,
    readable_chars      INT,
    published_at        TIMESTAMPTZ,
    github_stars        INT,
    github_archived     BOOLEAN,
    github_pushed_at    TIMESTAMPTZ,
    fetched_with        TEXT NOT NULL,       -- http | github | stagehand | failed
    browser_seconds     REAL,
    error               TEXT,
    fetched_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS triage (
    link_id         BIGINT NOT NULL REFERENCES links(id) ON DELETE CASCADE,
    model           TEXT,                    -- null when decided by code
    topic           TEXT,
    vertical        TEXT,
    kind            TEXT,
    still_relevant  BOOLEAN NOT NULL,
    reason          TEXT NOT NULL,
    buildable       SMALLINT NOT NULL DEFAULT 0 CHECK (buildable BETWEEN 0 AND 3),
    one_line_idea   TEXT,
    decided_by      TEXT NOT NULL,           -- code | model
    tokens_in       INT,
    tokens_out      INT,
    ms              INT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (link_id, created_at)
);

CREATE TABLE IF NOT EXISTS valhalla (
    link_id             BIGINT PRIMARY KEY REFERENCES links(id) ON DELETE CASCADE,
    reason              TEXT NOT NULL,
    decided_by          TEXT NOT NULL,       -- code | model
    batch_id            TEXT,
    discord_message_id  TEXT,
    status              TEXT NOT NULL DEFAULT 'proposed',  -- proposed | restored | confirmed
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at         TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS focus (
    id          BIGSERIAL PRIMARY KEY,
    text        TEXT NOT NULL,
    verticals   TEXT[] NOT NULL DEFAULT '{}',
    week_start  DATE NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cards (
    id              TEXT PRIMARY KEY,        -- short stable id, e.g. k7f3
    title           TEXT NOT NULL,
    vertical        TEXT,
    learning_goal   TEXT,
    hypothesis      TEXT,
    done_means      TEXT,
    box_minutes     INT NOT NULL DEFAULT 120,
    link_ids        BIGINT[] NOT NULL DEFAULT '{}',
    kill_criteria   TEXT,
    "column"        TEXT NOT NULL DEFAULT 'backlog',  -- backlog | today | building | built | killed | archived
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    moved_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    picked_on       DATE,
    gh_item_id      TEXT,
    gh_synced_at    TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS reading_picks (  -- the Coordinator's daily reading link from the Curator's `reading` bucket
    id              BIGSERIAL PRIMARY KEY,
    link_id         BIGINT NOT NULL REFERENCES links(id) ON DELETE CASCADE,
    picked_on       DATE NOT NULL,              -- one main recommendation per day (partial unique index below)
    extra           BOOLEAN NOT NULL DEFAULT false,  -- true for `--again` picks on the same day
    vertical        TEXT,
    why             TEXT,                       -- the model's one-line reason, checked against the link's facts
    focus_id        BIGINT REFERENCES focus(id),
    discord_message_id TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Migration for databases created before `extra` existed (idempotent).
ALTER TABLE reading_picks ADD COLUMN IF NOT EXISTS extra BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE reading_picks DROP CONSTRAINT IF EXISTS reading_picks_picked_on_key;
CREATE UNIQUE INDEX IF NOT EXISTS reading_picks_one_per_day ON reading_picks (picked_on) WHERE NOT extra;

CREATE TABLE IF NOT EXISTS runs (
    id          BIGSERIAL PRIMARY KEY,
    card_id     TEXT NOT NULL REFERENCES cards(id),
    model_id    TEXT,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at    TIMESTAMPTZ,
    cost_usd    NUMERIC(10, 4),
    tokens_in   INT,
    tokens_out  INT,
    outcome     TEXT NOT NULL DEFAULT 'building',  -- building | done | boxed_out | killed
    approved    BOOLEAN NOT NULL DEFAULT false,
    repo_url    TEXT,
    repo_dir    TEXT,
    notes_path  TEXT
);

CREATE TABLE IF NOT EXISTS events (       -- the #sk-logs timeline, also kept here for the post's numbers
    id          BIGSERIAL PRIMARY KEY,
    at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    agent       TEXT NOT NULL,              -- curator | coordinator | worker | coordinator-session
    kind        TEXT NOT NULL,
    text        TEXT NOT NULL,
    data        JSONB
);

CREATE INDEX IF NOT EXISTS links_status_idx ON links (status);
CREATE INDEX IF NOT EXISTS cards_column_idx ON cards ("column");
