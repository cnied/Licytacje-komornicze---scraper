from .logger import setup_logger

logger = setup_logger("CATEGORY_SERVICE")

def list_category_objects(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM public.item_category")
    records = cur.fetchall()
    categories = [{'value': item[2], 'category': item[3], 'itemcategoryid': item[0]} for item in records]
    logger.info("Odpytano bazę o listę kategorii")
    #print("list of dicts" +  str(categories))
    #print(categories)
    return categories


def get_category_object(category_name,category_value,categories):
    """
    Mapuje nazwę kategorii na obiekt z id zgodny z bazą danych.
    """

    if not category_name or not category_value:
      return None
    
    for item in categories:
        if item.get("category","").lower() == category_name.lower() and item.get("value","").lower() == category_value.lower():
            logger.info("CategoryItemID=%s", item.get("itemcategoryid"))
            #print(item.get("itemcategoryid"))
            return item.get("itemcategoryid")
    return None
