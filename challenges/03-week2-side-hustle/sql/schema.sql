-- PartsPaddock schema (Postgres on Tiger Cloud). Idempotent: safe to run on every `rcparts db init`.
-- pg_trgm is created separately by the CLI inside a try, so a role without CREATE EXTENSION still works.

CREATE TABLE IF NOT EXISTS clubs (
    id                 bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name               text NOT NULL,
    country            text NOT NULL,
    city               text NOT NULL,
    whatsapp_group_jid text UNIQUE,
    created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS members (
    id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    club_id      bigint NOT NULL REFERENCES clubs(id),
    phone        text NOT NULL UNIQUE,          -- digits with country code, no '+'
    display_name text NOT NULL,
    rc_class     text,
    brands       text[] NOT NULL DEFAULT '{}',
    created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS members_club_idx ON members (club_id);

CREATE TABLE IF NOT EXISTS listings (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    club_id     bigint NOT NULL REFERENCES clubs(id),
    member_id   bigint NOT NULL REFERENCES members(id),
    kind        text NOT NULL CHECK (kind IN ('HAVE', 'NEED')),
    brand       text,
    chassis     text,
    part_number text,                           -- normalized: uppercase, no spaces or dashes
    description text,
    condition   text CHECK (condition IN ('new', 'used', 'unknown')),
    price_usd   numeric(10, 2),
    qty         integer NOT NULL DEFAULT 1 CHECK (qty > 0),
    status      text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'matched', 'closed')),
    closed_reason text CHECK (closed_reason IN ('sold', 'unavailable', 'found')),
    closed_at   timestamptz,
    created_at  timestamptz NOT NULL DEFAULT now(),
    -- 'simple' keeps the index language-neutral (members write in Spanish and English).
    -- Tiger's pg_textsearch (BM25) can replace this tsvector + ts_rank ranking later
    -- without changing the matcher's interface.
    search      tsvector GENERATED ALWAYS AS (
        to_tsvector('simple',
            coalesce(brand, '') || ' ' || coalesce(chassis, '') || ' ' ||
            coalesce(part_number, '') || ' ' || coalesce(description, ''))
    ) STORED
);
CREATE INDEX IF NOT EXISTS listings_search_idx ON listings USING gin (search);
CREATE INDEX IF NOT EXISTS listings_part_idx ON listings (club_id, part_number) WHERE part_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS listings_member_idx ON listings (member_id);

CREATE TABLE IF NOT EXISTS matches (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    need_id     bigint NOT NULL REFERENCES listings(id),
    have_id     bigint NOT NULL REFERENCES listings(id),
    method      text NOT NULL,                  -- part_number | text
    score       real NOT NULL,
    notified_at timestamptz,
    notify_error text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (need_id, have_id)
);

CREATE TABLE IF NOT EXISTS orders (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    store           text NOT NULL,
    date            date NOT NULL DEFAULT current_date,
    quote_ids       bigint[] NOT NULL,
    summary         jsonb NOT NULL,
    summary_sent_at timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS quotes (
    id                        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    member_id                 bigint NOT NULL REFERENCES members(id),
    listing_id                bigint REFERENCES listings(id),
    query                     text NOT NULL,
    store                     text NOT NULL,
    store_url                 text NOT NULL,
    store_code                text,
    store_title               text,
    store_price_usd           numeric(10, 2) NOT NULL,
    weight_store              numeric(10, 3) NOT NULL,   -- raw value as the store lists it
    weight_unit               text NOT NULL,             -- WEIGHT_UNIT assumed at quote time
    weight_g                  numeric(10, 1) NOT NULL,
    fee_per_kg_usd            numeric(10, 2) NOT NULL,
    fee_usd                   numeric(10, 2) NOT NULL,
    processing_pct            numeric(5, 2) NOT NULL,
    processing_usd            numeric(10, 2) NOT NULL,
    total_usd                 numeric(10, 2) NOT NULL,   -- store price + weight fee
    total_with_processing_usd numeric(10, 2) NOT NULL,
    in_stock                  boolean,
    stock_note                text,
    -- quoted -> awaiting_tracking -> in_transit (self-order) | awaiting_deposit -> deposit_submitted -> paid (we order it) -> ordered
    status                    text NOT NULL DEFAULT 'quoted' CONSTRAINT quotes_status_check CHECK (status IN
                                  ('quoted', 'accepted', 'awaiting_tracking', 'in_transit', 'awaiting_deposit', 'deposit_submitted', 'paid', 'ordered')),
    with_processing           boolean,
    qty                       integer NOT NULL DEFAULT 1 CHECK (qty > 0),
    accepted_at               timestamptz,
    order_id                  bigint REFERENCES orders(id),
    created_at                timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS quotes_member_idx ON quotes (member_id);
CREATE INDEX IF NOT EXISTS quotes_open_idx ON quotes (status) WHERE order_id IS NULL;

-- Payment receipts (PDF) a member sends for a quote we order for them. Checked by code, confirmed by
-- the maintainer: a mismatch is flagged, never auto-rejected.
CREATE TABLE IF NOT EXISTS deposits (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    quote_id      bigint NOT NULL REFERENCES quotes(id),
    member_id     bigint NOT NULL REFERENCES members(id),
    file_path     text NOT NULL,                -- copy under data/receipts/
    original_name text,
    file_source   text NOT NULL DEFAULT 'argument',   -- argument | hermes_cache_fallback
    expected_usd  numeric(10, 2) NOT NULL,
    amount_usd    numeric(10, 2),               -- read from the PDF text (NULL = not found)
    reference     text,                         -- e.g. RC-Q12 (NULL = not found)
    receipt_date  text,
    checks        jsonb NOT NULL,               -- {amount_ok, reference_ok, ...}
    status        text NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted', 'confirmed', 'rejected')),
    reject_reason text,
    reviewed_at   timestamptz,
    created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS deposits_quote_idx ON deposits (quote_id);

-- Migrations for databases created before these columns and states existed (idempotent).
ALTER TABLE listings ADD COLUMN IF NOT EXISTS closed_reason text;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS closed_at timestamptz;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS tracking_number text;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS tracking_carrier text;
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS tracking_at timestamptz;
ALTER TABLE quotes DROP CONSTRAINT IF EXISTS quotes_status_check;
ALTER TABLE quotes ADD CONSTRAINT quotes_status_check CHECK (status IN
    ('quoted', 'accepted', 'awaiting_tracking', 'in_transit', 'awaiting_deposit', 'deposit_submitted', 'paid', 'ordered'));
