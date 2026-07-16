BEGIN;

CREATE TABLE IF NOT EXISTS provinces (
    code SMALLINT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT provinces_code_range CHECK (code BETWEEN 1 AND 81),
    CONSTRAINT provinces_name_not_blank CHECK (BTRIM(name) <> '')
);

CREATE TABLE IF NOT EXISTS districts (
    id BIGSERIAL PRIMARY KEY,
    ptt_code INTEGER NOT NULL UNIQUE,
    province_code SMALLINT NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT districts_province_fk
        FOREIGN KEY (province_code)
        REFERENCES provinces(code)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT districts_ptt_code_positive CHECK (ptt_code > 0),
    CONSTRAINT districts_name_not_blank CHECK (BTRIM(name) <> ''),
    CONSTRAINT districts_province_name_unique UNIQUE (province_code, name)
);

CREATE INDEX IF NOT EXISTS districts_province_code_idx
    ON districts(province_code);

CREATE TABLE IF NOT EXISTS neighborhoods (
    id BIGSERIAL PRIMARY KEY,
    district_id BIGINT NOT NULL,
    name VARCHAR(180) NOT NULL,
    postal_code CHAR(5) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT neighborhoods_district_fk
        FOREIGN KEY (district_id)
        REFERENCES districts(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT neighborhoods_name_not_blank CHECK (BTRIM(name) <> ''),
    CONSTRAINT neighborhoods_postal_code_format
        CHECK (postal_code ~ '^[0-9]{5}$'),
    CONSTRAINT neighborhoods_identity_unique
        UNIQUE (district_id, name, postal_code)
);

CREATE INDEX IF NOT EXISTS neighborhoods_district_id_idx
    ON neighborhoods(district_id);

CREATE INDEX IF NOT EXISTS neighborhoods_postal_code_idx
    ON neighborhoods(postal_code);

COMMIT;
