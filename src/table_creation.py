from tkinter.constants import E
from src.logger import setup_logger

#conn, error = db_login()

logger = setup_logger("TABLE_CREATION")

def create_tables_if_not_exists(conn, error):
    if error or conn is None:
        logger.error("Cannot create tables without database connection.")
        return

    itemCategory = """
    CREATE TABLE IF NOT EXISTS item_category (
        id         BIGINT PRIMARY KEY,
        "key"      INTEGER,
        value      TEXT,
        category   TEXT,
        code       TEXT,
        externalId BIGINT
    );
    """

    bailiffData = """
    CREATE TABLE IF NOT EXISTS bailiff_data (
        id              BIGSERIAL PRIMARY KEY,
        institutionName TEXT,
        street          TEXT,
        buildingNo      TEXT,
        flatNo          TEXT,
        city            TEXT,
        zipCode         TEXT,
        country         TEXT,
        province        TEXT,
        bankName        TEXT,
        bankIban        TEXT
    );
    """

    auction_item = """
    CREATE TABLE IF NOT EXISTS auction_item (
        id              BIGINT PRIMARY KEY,   -- object.id
        auctionId       BIGINT,               -- auctionId
        name            TEXT,
        city            TEXT,
        institutionName TEXT,
        dateCreated     TIMESTAMPTZ,
        startAuction    TIMESTAMPTZ,
        endAuction      TIMESTAMPTZ,
        marginDueDate   TIMESTAMPTZ,
        estimate        NUMERIC(15,2),
        openingValue    NUMERIC(15,2),
        margin          NUMERIC(15,2),
        bidStep         NUMERIC(15,2),
        auctionCategory TEXT,
        projectLink     TEXT,
        itemCategoryId  BIGINT,
        bailiffDataId   BIGINT,
        aiGenerated     BOOLEAN DEFAULT FALSE
    );
    """

    auction_attachment = """
    CREATE TABLE IF NOT EXISTS auction_attachment (
        id               BIGSERIAL PRIMARY KEY,
        auctionId        BIGINT NOT NULL,
        fileName         TEXT,
        fileContent      TEXT,      -- base64
        fileContentSmall TEXT,      -- base64
        defAttach        BOOLEAN,
        width            INTEGER,
        height           INTEGER,
        sizeType         TEXT
    );
    """

    auction_additional_param = """
    CREATE TABLE IF NOT EXISTS auction_additional_param (
        id        BIGSERIAL PRIMARY KEY,
        auctionId BIGINT NOT NULL,
        paramKey  TEXT NULL,   -- 'AREA', 'NUMBEROFROOMS', ...
        value     TEXT NULL,   -- np. '363.4', '6', 'wolnostojący'
        format    TEXT         -- 'SINGLE' / 'MULTI'
    );
    """

    auction_item_address = """
    CREATE TABLE IF NOT EXISTS auction_item_address (
        id              BIGSERIAL PRIMARY KEY,
        auctionId       BIGINT NOT NULL,
        institutionName TEXT,
        foreignAddress  BOOLEAN NOT NULL DEFAULT FALSE,
        streetPrefix    TEXT,
        street          TEXT,
        buildingNo      TEXT,
        flatNo          TEXT,
        city            TEXT,
        zipCode         TEXT,
        postOffice      TEXT,
        country         TEXT,
        province        TEXT,
        district        TEXT,
        lon             NUMERIC,
        lat             NUMERIC,
        community       TEXT
    );
    """


    fk_itemcategory = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'auction_item_itemcategoryid_fkey'
        ) THEN
            ALTER TABLE auction_item
                ADD CONSTRAINT auction_item_itemcategoryid_fkey
                FOREIGN KEY (itemCategoryId) REFERENCES item_category(id);
        END IF;
    END$$;
    """

    fk_bailiffdata = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'auction_item_bailiffdataid_fkey'
        ) THEN
            ALTER TABLE auction_item
                ADD CONSTRAINT auction_item_bailiffdataid_fkey
                FOREIGN KEY (bailiffDataId) REFERENCES bailiff_data(id);
        END IF;
    END$$;
    """

    fk_attachment_auction = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'auction_attachment_auctionid_fkey'
        ) THEN
            ALTER TABLE auction_attachment
                ADD CONSTRAINT auction_attachment_auctionid_fkey
                FOREIGN KEY (auctionId) REFERENCES auction_item(id);
        END IF;
    END$$;
    """

    fk_param_auction = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'auction_additional_param_auctionid_fkey'
        ) THEN
            ALTER TABLE auction_additional_param
                ADD CONSTRAINT auction_additional_param_auctionid_fkey
                FOREIGN KEY (auctionId) REFERENCES auction_item(id);
        END IF;
    END$$;
    """

    fk_address_auction = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'auction_item_address_auctionid_fkey'
        ) THEN
            ALTER TABLE auction_item_address
                ADD CONSTRAINT auction_item_address_auctionid_fkey
                FOREIGN KEY (auctionId) REFERENCES auction_item(id);
        END IF;
    END$$;
    """

    fk_address_unique = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'auction_item_address_auctionid_key'
        ) THEN
            ALTER TABLE auction_item_address
                ADD CONSTRAINT auction_item_address_auctionid_key
                UNIQUE (auctionId);
        END IF;
    END$$;
    """

    bailiff_unique = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'bailiff_data_unique_key'
        ) THEN
            ALTER TABLE bailiff_data
                ADD CONSTRAINT bailiff_data_unique_key
                UNIQUE (
                    institutionName,
                    street,
                    buildingNo,
                    flatNo,
                    city,
                    zipCode,
                    country,
                    province,
                    bankName,
                    bankIban
                );
        END IF;
    END$$;
    """

    # Usunięcie duplikatów przed dodaniem UNIQUE constraints
    cleanup_attachment_duplicates = """
    DELETE FROM auction_attachment a
    USING auction_attachment b
    WHERE a.id < b.id
      AND a.auctionId = b.auctionId
      AND a.fileName = b.fileName;
    """

    cleanup_param_duplicates = """
    DELETE FROM auction_additional_param a
    USING auction_additional_param b
    WHERE a.id < b.id
      AND a.auctionId = b.auctionId
      AND a.paramKey = b.paramKey;
    """

    attachment_unique = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'auction_attachment_unique_key'
        ) THEN
            ALTER TABLE auction_attachment
                ADD CONSTRAINT auction_attachment_unique_key
                UNIQUE (auctionId, fileName);
        END IF;
    END$$;
    """

    param_unique = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'auction_additional_param_unique_key'
        ) THEN
            ALTER TABLE auction_additional_param
                ADD CONSTRAINT auction_additional_param_unique_key
                UNIQUE (auctionId, paramKey);
        END IF;
    END$$;
    """

    # UNIQUE na auctionId w auction_item - zapobiega duplikatom aukcji
    auction_item_auctionid_unique = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'auction_item_auctionid_unique_key'
        ) THEN
            -- Najpierw usuń duplikaty (zostaw najnowszy rekord)
            DELETE FROM auction_item a
            USING auction_item b
            WHERE a.id < b.id
              AND a.auctionId = b.auctionId
              AND a.auctionId IS NOT NULL;

            -- Dodaj UNIQUE constraint
            ALTER TABLE auction_item
                ADD CONSTRAINT auction_item_auctionid_unique_key
                UNIQUE (auctionId);
        END IF;
    END$$;
    """

    # Naprawiony UNIQUE na bailiff_data z obsługą NULL (COALESCE)
    bailiff_unique_index = """
    DO $$
    BEGIN
        -- Usuń stary constraint jeśli istnieje
        IF EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'bailiff_data_unique_key'
        ) THEN
            ALTER TABLE bailiff_data DROP CONSTRAINT bailiff_data_unique_key;
        END IF;

        -- Usuń stary indeks jeśli istnieje
        DROP INDEX IF EXISTS bailiff_data_unique_idx;

        -- Usuń duplikaty przed utworzeniem indeksu
        DELETE FROM bailiff_data a
        USING bailiff_data b
        WHERE a.id < b.id
          AND COALESCE(a.institutionName, '') = COALESCE(b.institutionName, '')
          AND COALESCE(a.street, '') = COALESCE(b.street, '')
          AND COALESCE(a.buildingNo, '') = COALESCE(b.buildingNo, '')
          AND COALESCE(a.flatNo, '') = COALESCE(b.flatNo, '')
          AND COALESCE(a.city, '') = COALESCE(b.city, '')
          AND COALESCE(a.zipCode, '') = COALESCE(b.zipCode, '')
          AND COALESCE(a.country, '') = COALESCE(b.country, '')
          AND COALESCE(a.province, '') = COALESCE(b.province, '')
          AND COALESCE(a.bankName, '') = COALESCE(b.bankName, '')
          AND COALESCE(a.bankIban, '') = COALESCE(b.bankIban, '');

        -- Utwórz unikalny indeks z COALESCE
        CREATE UNIQUE INDEX bailiff_data_unique_idx ON bailiff_data (
            COALESCE(institutionName, ''),
            COALESCE(street, ''),
            COALESCE(buildingNo, ''),
            COALESCE(flatNo, ''),
            COALESCE(city, ''),
            COALESCE(zipCode, ''),
            COALESCE(country, ''),
            COALESCE(province, ''),
            COALESCE(bankName, ''),
            COALESCE(bankIban, '')
        );
    END$$;
    """

    commands = [
        itemCategory,
        bailiffData,
        auction_item,
        auction_attachment,
        auction_additional_param,
        auction_item_address,
        fk_itemcategory,
        fk_bailiffdata,
        fk_attachment_auction,
        fk_param_auction,
        fk_address_auction,
        fk_address_unique,
        # Cleanup duplikatów i UNIQUE constraints
        cleanup_attachment_duplicates,
        cleanup_param_duplicates,
        attachment_unique,
        param_unique,
        # Nowe constraints zapobiegające duplikatom
        auction_item_auctionid_unique,
        bailiff_unique_index,  # zastępuje stary bailiff_unique z obsługą NULL
    ]

    try:
        with conn:
            with conn.cursor() as cursor:
                for cmd in commands:
                    cursor.execute(cmd)
        logger.info("Tables have been created or already exists")
    except Exception as e:
        logger.error("Error while creating tables: %s",e)


if __name__ == "__main__":
    create_tables_if_not_exists(conn, error)
