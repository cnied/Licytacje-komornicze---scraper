import pandas as pd
import folium
from .logger import setup_logger
from .db_connect import db_login
import time
from datetime import datetime


logger = setup_logger("MAP")

conn, error = db_login()


def list_addresses(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            ai.id,
            ai.name,
            ai.city,
            ai.estimate,
            ai.openingvalue,
            ai.margin,
            ai.bidstep,
            ai.startauction,
            ai.endauction,
            ai.auctioncategory,
            ai.projectlink,
            aia.lat,
            aia.lon,
            aia.streetprefix,
            aia.street,
            aia.buildingno,
            aia.flatno,
            aia.zipcode,
            aia.city as address_city,
            aia.province,
            aia.district,
            ic.value as category_name
        FROM auction_item ai
        LEFT JOIN auction_item_address aia ON aia.auctionid = ai.id
        LEFT JOIN item_category ic ON ic.id = ai.itemcategoryid
        WHERE ai.aigenerated = false
    """)
    records = cur.fetchall()

    addresses = []
    for item in records:
        auction_id = item[0]

        # Pobierz dodatkowe parametry dla tej aukcji
        cur.execute("""
            SELECT paramkey, value
            FROM auction_additional_param
            WHERE auctionid = %s
        """, (auction_id,))
        params = {row[0]: row[1] for row in cur.fetchall()}

        # Pobierz zdjęcie główne (defAttach=true) lub pierwsze dostępne
        cur.execute("""
            SELECT filecontentsmall, filecontent
            FROM auction_attachment
            WHERE auctionid = %s
            ORDER BY defattach DESC NULLS LAST, id ASC
            LIMIT 1
        """, (auction_id,))
        image_row = cur.fetchone()
        image_base64 = None
        if image_row:
            # Preferuj małe zdjęcie, jeśli brak - użyj pełnego
            image_base64 = image_row[0] or image_row[1]

        addresses.append({
            'id': auction_id,
            'name': item[1],
            'city': item[2],
            'estimate': item[3],
            'openingvalue': item[4],
            'margin': item[5],
            'bidstep': item[6],
            'startauction': item[7],
            'endauction': item[8],
            'auctioncategory': item[9],
            'projectlink': item[10],
            'lat': item[11],
            'lon': item[12],
            'streetprefix': item[13],
            'street': item[14],
            'buildingno': item[15],
            'flatno': item[16],
            'zipcode': item[17],
            'address_city': item[18],
            'province': item[19],
            'district': item[20],
            'category_name': item[21],
            'params': params,
            'image': image_base64
        })

    logger.info("Odpytano bazę o adresy, znaleziono %s rekordów", len(addresses))
    return addresses


def format_price(value):
    """Formatuje cenę z separatorami tysięcy"""
    if value is None:
        return "—"
    return f"{value:,.2f} zł".replace(",", " ").replace(".", ",")


def format_date(dt):
    """Formatuje datę w czytelny sposób"""
    if dt is None:
        return "—"
    if isinstance(dt, datetime):
        return dt.strftime("%d.%m.%Y %H:%M")
    return str(dt)


def build_address_string(item):
    """Buduje pełny adres z dostępnych części"""
    parts = []

    # Ulica z numerem
    street_parts = []
    if item.get('streetprefix'):
        street_parts.append(item['streetprefix'])
    if item.get('street'):
        street_parts.append(item['street'])
    if item.get('buildingno'):
        street_parts.append(item['buildingno'])
    if item.get('flatno'):
        street_parts.append(f"m. {item['flatno']}")

    if street_parts:
        parts.append(" ".join(street_parts))

    # Kod i miasto
    city_parts = []
    if item.get('zipcode'):
        city_parts.append(item['zipcode'])
    if item.get('address_city'):
        city_parts.append(item['address_city'])
    elif item.get('city'):
        city_parts.append(item['city'])

    if city_parts:
        parts.append(" ".join(city_parts))

    # Powiat i województwo
    if item.get('district'):
        parts.append(f"pow. {item['district']}")
    if item.get('province'):
        parts.append(f"woj. {item['province']}")

    return ", ".join(parts) if parts else "Brak adresu"


def get_param_label(key):
    """Zwraca czytelną etykietę dla klucza parametru"""
    labels = {
        'AREA': '📐 Powierzchnia',
        'NUMBEROFROOMS': '🚪 Liczba pokoi',
        'YEARBUILT': '🏗️ Rok budowy',
        'FLOOR': '🏢 Piętro',
        'BUILDINGTYPE': '🏠 Typ budynku',
        'PLOTAREA': '🌳 Powierzchnia działki',
        'GARAGECOUNT': '🚗 Garaże',
        'PARKINGCOUNT': '🅿️ Miejsca parkingowe',
    }
    return labels.get(key, key)


def build_popup_html(item):
    """Buduje ładny HTML popup dla markera"""

    name = item.get('name') or 'Brak nazwy'
    category = item.get('category_name') or item.get('auctioncategory') or ''
    address = build_address_string(item)
    image_base64 = item.get('image')

    # Sekcja ze zdjęciem
    image_html = ''
    if image_base64:
        image_html = f'''
        <div style="margin-bottom: 10px; text-align: center;">
            <img src="data:image/jpeg;base64,{image_base64}"
                 style="max-width: 100%; max-height: 200px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);"
                 alt="Zdjęcie nieruchomości">
        </div>
        '''

    html = f'''
    <div style="min-width: 300px; max-width: 400px; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; line-height: 1.4;">
        {image_html}
        <h4 style="margin: 0 0 8px 0; padding-bottom: 8px; color: #1a5276; border-bottom: 3px solid #3498db; font-size: 14px;">
            {name[:80]}{'...' if len(name) > 80 else ''}
        </h4>

        {f'<p style="margin: 0 0 8px 0; color: #7f8c8d; font-size: 11px;">🏷️ {category}</p>' if category else ''}

        <p style="margin: 0 0 10px 0; color: #2c3e50;">
            <strong>📍 Adres:</strong><br>
            <span style="color: #555;">{address}</span>
        </p>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px; background: #f8f9fa; border-radius: 4px;">
            <tr style="border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 6px 8px; color: #666;">💰 Oszacowanie:</td>
                <td style="padding: 6px 8px; text-align: right; font-weight: bold; color: #27ae60;">{format_price(item.get('estimate'))}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 6px 8px; color: #666;">🏷️ Cena wywoławcza:</td>
                <td style="padding: 6px 8px; text-align: right; font-weight: bold; color: #e67e22;">{format_price(item.get('openingvalue'))}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 6px 8px; color: #666;">💳 Wadium:</td>
                <td style="padding: 6px 8px; text-align: right;">{format_price(item.get('margin'))}</td>
            </tr>
            <tr>
                <td style="padding: 6px 8px; color: #666;">📈 Postąpienie:</td>
                <td style="padding: 6px 8px; text-align: right;">{format_price(item.get('bidstep'))}</td>
            </tr>
        </table>

        <div style="background: #eaf2f8; padding: 8px; border-radius: 4px; margin-bottom: 10px;">
            <p style="margin: 0 0 4px 0;">
                <strong>📅 Start aukcji:</strong>
                <span style="color: #2980b9;">{format_date(item.get('startauction'))}</span>
            </p>
            <p style="margin: 0;">
                <strong>📅 Koniec aukcji:</strong>
                <span style="color: #c0392b;">{format_date(item.get('endauction'))}</span>
            </p>
        </div>
    '''

    # Dodatkowe parametry
    params = item.get('params', {})
    if params:
        html += '<div style="border-top: 1px solid #ddd; padding-top: 8px; margin-bottom: 10px;">'
        html += '<p style="margin: 0 0 6px 0; font-weight: bold; color: #2c3e50;">📋 Szczegóły:</p>'
        for key, value in params.items():
            if value:
                label = get_param_label(key)
                html += f'<p style="margin: 0 0 3px 0; color: #555;">{label}: <strong>{value}</strong></p>'
        html += '</div>'

    # Link do ogłoszenia
    if item.get('projectlink'):
        html += f'''
        <a href="{item['projectlink']}" target="_blank"
           style="display: block; text-align: center; background: #3498db; color: white;
                  padding: 8px; border-radius: 4px; text-decoration: none; font-weight: bold;">
            🔗 Zobacz ogłoszenie
        </a>
        '''

    html += '</div>'
    return html





def update_the_map():
    addresses = list_addresses(conn)
    df = pd.DataFrame(addresses)
    print(f"Załadowano {len(df)} aukcji na mapę")

    # Tworzenie mapy
    mapa = folium.Map(location=[52.0, 19.0], zoom_start=6)

    # Dodawanie markerów
    for index, item in df.iterrows():
        if item['lat']:
            popup_html = build_popup_html(item)
            tooltip_text = item.get('name', 'Aukcja')[:50]

            folium.Marker(
                [item['lat'], item['lon']],
                popup=folium.Popup(popup_html, max_width=420),
                tooltip=tooltip_text
            ).add_to(mapa)

    mapa.save('mapa2.html')
    logger.info("Mapa zapisana do mapa2.html")

if __name__ == '__main__':
    try:
        while True:
            update_the_map()
            time.sleep(5)
    except KeyboardInterrupt:
        print("Zatrzymano")
