from db_connect import db_login
import pandas as pd

conn, error = db_login()


def create_table_if_not_exists(conn,error):
    if error:
        print("Nie można utworzyć tabeli z powodu błędu połączenia z bazą.")
        return

auction_item = """
    CREATE TABLE IF NOT EXISTS auction_item (
    id                  BIGINT PRIMARY KEY,          -- z API: object.id
    external_id         BIGINT,                     -- auctionId
    name                TEXT NOT NULL,
    city                TEXT,
    institution_name    TEXT,
    date_created        TIMESTAMP WITH TIME ZONE,
    start_auction       TIMESTAMP WITH TIME ZONE,
    end_auction         TIMESTAMP WITH TIME ZONE,
    margin_due_date     TIMESTAMP WITH TIME ZONE,
    estimate            NUMERIC(15,2),
    opening_value       NUMERIC(15,2),
    margin              NUMERIC(15,2),
    bid_step            NUMERIC(15,2),
    auction_category    TEXT,
    project_link        TEXT
);
    """

itemCategory = """
    CREATE TABLE item_category (
    id           BIGINT PRIMARY KEY,
    key          INTEGER,
    value        TEXT,
    category     TEXT,
    code         TEXT,
    external_id  BIGINT
);

ALTER TABLE auction_item
    ADD COLUMN item_category_id BIGINT
        REFERENCES item_category(id);
    """

auction_attachment = """
CREATE TABLE auction_attachment (
    id              BIGSERIAL PRIMARY KEY,
    auction_id      BIGINT NOT NULL REFERENCES auction_item(id),
    file_name       TEXT NOT NULL,
    file_content    TEXT,      -- base64 jako TEXT
    file_content_small TEXT,   -- też base64
    def_attach      BOOLEAN,
    width           INTEGER,
    height          INTEGER,
    size_type       TEXT
);
"""

bailiffData = """
CREATE TABLE bailiff_data (
    id              BIGSERIAL PRIMARY KEY,
    institution_name TEXT,
    street          TEXT,
    building_no     TEXT,
    flat_no         TEXT,
    city            TEXT,
    zip_code        TEXT,
    country         TEXT,
    province        TEXT,
    bank_name       TEXT,
    bank_iban       TEXT
);

ALTER TABLE auction_item
    ADD COLUMN bailiff_data_id BIGINT
        REFERENCES bailiff_data(id);

"""
auction_additional_param = """
CREATE TABLE auction_additional_param (
    id          BIGSERIAL PRIMARY KEY,
    auction_id  BIGINT NOT NULL REFERENCES auction_item(id),
    param_key   TEXT NOT NULL,      -- 'AREA', 'NUMBEROFROOMS', ...
    value       TEXT NOT NULL,      -- np. '363.4', '6', 'wolnostojący'
    format      TEXT                -- 'SINGLE' / 'MULTI'
);

"""

try:
    cursor = conn.cursor()
    cursor.execute(auction_item)
    cursor.execute(itemCategory)
    cursor.execute(auction_attachment)
    cursor.execute(bailiffData)
    cursor.execute(auction_additional_param)
    conn.commit()
    cursor.close()
    print("Tables have been created or already exist.")
except Exception as e:
    print("Error creating tables:", e)


