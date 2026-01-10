from src.db_connect import db_login
from src.logger import setup_logger


conn, error = db_login()
logger = setup_logger()


def save_auction(data, address_data=None, conn=conn):
    if conn is None:
        logger.error("Lack of DB connection, cannot save auction.")
        return

    obj = data.get("object", {})
    ai_generated = obj.get("aiGenerated", False)

    with conn:
        with conn.cursor() as cur:
            # 1. item_category
            category = obj.get("itemCategory")
            item_category_id = None
            if ai_generated:
                pass  # Skip saving AI-generated categories
            elif category:
                item_category_id = category.get("id")
                if not ai_generated:
                    logger.info("Saving item category: %s", item_category_id)
                    cur.execute(
                        """
                        INSERT INTO item_category (id, "key", value, category, code, externalId)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE
                        SET "key"      = EXCLUDED."key",
                            value      = EXCLUDED.value,
                            category   = EXCLUDED.category,
                            code       = EXCLUDED.code,
                            externalId = EXCLUDED.externalId
                        """,
                        (
                            category.get("id"),
                            category.get("key"),
                            category.get("value"),
                            category.get("category"),
                            category.get("code"),
                            category.get("externalId"),
                        ),
                    )

            # 2. bailiff_data
            bailiff = obj.get("bailiffData") or {}
            bailiff_data_id = None
            if bailiff:
                address_data_bailiff = bailiff.get("addressData") or {}
                bailiff_addr = address_data_bailiff.get("address") or {}
                institution_name = address_data_bailiff.get("institutionName")

                cur.execute(
                    """
                    INSERT INTO bailiff_data (
                        institutionName, street, buildingNo, flatNo,
                        city, zipCode, country, province,
                        bankName, bankIban
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT ON CONSTRAINT bailiff_data_unique_key DO UPDATE
                    SET institutionName = EXCLUDED.institutionName
                    RETURNING id
                    """,
                    (
                        institution_name,
                        bailiff_addr.get("street"),
                        bailiff_addr.get("buildingNo"),
                        bailiff_addr.get("flatNo"),
                        bailiff_addr.get("city"),
                        bailiff_addr.get("zipCode"),
                        bailiff_addr.get("country"),
                        bailiff_addr.get("province"),
                        bailiff.get("bankName"),
                        bailiff.get("bankIban"),
                    ),
                )
                bailiff_data_id = cur.fetchone()[0]

            # 3. auction_item
            cur.execute(
                """
                INSERT INTO auction_item (
                    id, auctionId, name, city, institutionName,
                    dateCreated, startAuction, endAuction, marginDueDate,
                    estimate, openingValue, margin, bidStep,
                    auctionCategory, projectLink,
                    itemCategoryId, bailiffDataId, aiGenerated
                )
                VALUES (
                    %(id)s, %(auctionId)s, %(name)s, %(city)s, %(institutionName)s,
                    %(dateCreated)s, %(startAuction)s, %(endAuction)s, %(marginDueDate)s,
                    %(estimate)s, %(openingValue)s, %(margin)s, %(bidStep)s,
                    %(auctionCategory)s, %(projectLink)s,
                    %(itemCategoryId)s, %(bailiffDataId)s, %(aiGenerated)s
                )
                ON CONFLICT (id) DO UPDATE
                SET auctionId       = EXCLUDED.auctionId,
                    name            = EXCLUDED.name,
                    city            = EXCLUDED.city,
                    institutionName = EXCLUDED.institutionName,
                    dateCreated     = EXCLUDED.dateCreated,
                    startAuction    = EXCLUDED.startAuction,
                    endAuction      = EXCLUDED.endAuction,
                    marginDueDate   = EXCLUDED.marginDueDate,
                    estimate        = EXCLUDED.estimate,
                    openingValue    = EXCLUDED.openingValue,
                    margin          = EXCLUDED.margin,
                    bidStep         = EXCLUDED.bidStep,
                    auctionCategory = EXCLUDED.auctionCategory,
                    projectLink     = EXCLUDED.projectLink,
                    itemCategoryId  = EXCLUDED.itemCategoryId,
                    bailiffDataId   = EXCLUDED.bailiffDataId,
                    aiGenerated     = EXCLUDED.aiGenerated
                """,
                {
                    "id":              obj.get("id"),
                    "auctionId":       obj.get("auctionId"),
                    "name":            obj.get("name"),
                    "city":            obj.get("city"),
                    "institutionName": obj.get("institutionName"),
                    "dateCreated":     obj.get("dateCreated"),
                    "startAuction":    obj.get("startAuction"),
                    "endAuction":      obj.get("endAuction"),
                    "marginDueDate":   obj.get("marginDueDate"),
                    "estimate":        obj.get("estimate"),
                    "openingValue":    obj.get("openingValue"),
                    "margin":          obj.get("margin"),
                    "bidStep":         obj.get("bidStep"),
                    "auctionCategory": obj.get("auctionCategory"),
                    "projectLink":     obj.get("projectLink"),
                    "itemCategoryId":  item_category_id,
                    "bailiffDataId":   bailiff_data_id,
                    "aiGenerated":     obj.get("aiGenerated"),
                },
            )

            auction_id = obj.get("id")

            # 4. address
            if address_data:
                addr = address_data
                cur.execute(
                    """
                    INSERT INTO auction_item_address (
                        auctionId,
                        institutionName, foreignAddress, streetPrefix,
                        street, buildingNo, flatNo, city,
                        zipCode, postOffice, country, province,
                        district, community
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT ON CONSTRAINT auction_item_address_auctionid_key
                    DO UPDATE SET
                        institutionName = EXCLUDED.institutionName,
                        foreignAddress  = EXCLUDED.foreignAddress,
                        streetPrefix    = EXCLUDED.streetPrefix,
                        street          = EXCLUDED.street,
                        buildingNo      = EXCLUDED.buildingNo,
                        flatNo          = EXCLUDED.flatNo,
                        city            = EXCLUDED.city,
                        zipCode         = EXCLUDED.zipCode,
                        postOffice      = EXCLUDED.postOffice,
                        country         = EXCLUDED.country,
                        province        = EXCLUDED.province,
                        district        = EXCLUDED.district,
                        community       = EXCLUDED.community
                    """,
                    (
                        auction_id,
                        addr.get("institutionName"),
                        addr.get("foreignAddress", False),
                        addr.get("streetPrefix"),
                        addr.get("street"),
                        addr.get("buildingNo"),
                        addr.get("flatNo"),
                        addr.get("city"),
                        addr.get("zipCode"),
                        addr.get("postOffice"),
                        addr.get("country"),
                        addr.get("province"),
                        addr.get("district"),
                        addr.get("community"),
                    ),
                )

            # 5. attachments
            attachments = obj.get("attachments") or []
            for att in attachments:
                file_name = att.get("fileName")
                if not file_name:
                    continue
                cur.execute(
                    """
                    INSERT INTO auction_attachment (
                        auctionId, fileName, fileContent,
                        fileContentSmall, defAttach, width, height, sizeType
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT ON CONSTRAINT auction_attachment_unique_key
                    DO UPDATE SET
                        fileContent = EXCLUDED.fileContent,
                        fileContentSmall = EXCLUDED.fileContentSmall,
                        defAttach = EXCLUDED.defAttach,
                        width = EXCLUDED.width,
                        height = EXCLUDED.height,
                        sizeType = EXCLUDED.sizeType
                    """,
                    (
                        auction_id,
                        file_name,
                        att.get("fileContent"),
                        att.get("fileContentSmall"),
                        att.get("defAttach"),
                        att.get("width"),
                        att.get("height"),
                        att.get("sizeType"),
                    ),
                )

            # 6. additionalParams
            add_params = obj.get("additionalParams") or {}
            for key, param in add_params.items():
                value = param.get("value")
                fmt = param.get("format")
                if isinstance(value, list):
                    value_str = ",".join(map(str, value))
                else:
                    value_str = str(value) if value is not None else ""
                cur.execute(
                    """
                    INSERT INTO auction_additional_param (
                        auctionId, paramKey, value, format
                    )
                    VALUES (%s,%s,%s,%s)
                    ON CONFLICT ON CONSTRAINT auction_additional_param_unique_key
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        format = EXCLUDED.format
                    """,
                    (auction_id, key, value_str, fmt),
                )

    print("Auction saved", obj.get("id"))
