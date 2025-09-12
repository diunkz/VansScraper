import requests
import json
import time
from datetime import datetime

# ---- Config Telegram ----
TELEGRAM_TOKEN = ""
CHAT_ID = ""
TG_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# ---- Config Vans ----
base_url = "https://www.vans.com.br"
url = "https://www.vans.com.br/arezzocoocc/v2/vans/products/search?category=ULTIMASUNIDADES&currentPage=0&pageSize=24&fields=FULL&query=:creation-time:shoeSize:42&storeFinder=false"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0.0.0 Safari/537.36"
}

# Lista de produtos para ignorar (nome e valor do desconto)
black_list = [
    ("Tênis Rowley Vintage Lx Wind", 539.99),
    ("Tênis Old Skool Fat Lace Checker Red", 314.99),
    ("Tênis Rowley Vintage Lx Incense", 539.99),
    ("Tênis Sk8-Hi Sf Surf Essentials Rainy Day", 409.99),
    ("Tênis Authentic Stackform Pastel Picnic Mixed Plaid", 319.99),
    ("Tênis Authentic Foxglove", 199.99),
    ("Tênis Sport Track Red", 299.99),
    ("Tênis Skate Ave 2.0 Lavender Fog Black", 524.99),
    ("Tênis Knu Slip Silver Metallic True White", 249.99),
    ("Tênis Skate Lizzie Hi Lavender Fog Black", 399.99),
    ("Tênis Slip-On Sf Cheetah Pink", 299.99),
    ("Tênis Rowley Xlt Lx Off Road Egret", 629.99),
    ("Tênis Authentic 44 Dx Anaheim Factory Og Floral Purple", 329.98),
    ("Tênis Style 93 DX Susan Alexandra Pink", 249.99),
    ("Tênis Sk8-Hi Foxglove", 249.99),
    ("Tênis Authentic Floral Checkerboard Marshmallow", 229.99),
    ("Tênis Mary Jane Suede Grape Jam", 199.99),
    ("Tênis Old Skool Foxglove", 229.99),
    ("Tênis Old Skool Foxglove", 229.99)
]

def get_products():
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json().get("products", [])

def get_42_stock(product_code):
    product_url = f"{base_url}/arezzocoocc/v2/vans/products/{product_code}/dynamic-product-fields?fields=DYNAMIC_FIELDS_PDP"
    prod_resp = requests.get(product_url, headers=headers)
    prod_resp.raise_for_status()
    prod_data = prod_resp.json()

    for variant in prod_data.get("variantOptions", []):
        if variant.get("code") == f"{product_code}-42":
            sellable = variant.get("sellable", False)
            stock_level = variant.get("stock", {}).get("stockLevel", 0)
            stock_status = variant.get("stock", {}).get("stockLevelStatus", "outOfStock")
            return sellable, stock_level, stock_status
    return False, 0, "outOfStock"

def format_message(products):
    msg = f"<b>Atualização</b>: {datetime.now().strftime('%d/%m/%Y - %H:%M:%S')}\n\n"
    for produto in products:
        name = produto.get("name")
        discount_value = produto.get("discountPrice", {}).get("value")
        if (name.lower().strip(), discount_value) in [(n.lower().strip(), d) for n, d in black_list]:
            continue

        product_code = produto.get("code")
        sellable_42, stock_level_42, stock_status_42 = get_42_stock(product_code)
        price_value = produto.get("price", {}).get("value")
        percentual_of_discount = produto.get("percentualOfDiscount")
        product_page_url = base_url + produto.get('url', '')

        msg += f"<b>Nome:</b> {name}\n"
        msg += f"<b>Link:</b> {product_page_url}\n"
        msg += f"<b>Preço:</b> R$ {price_value}\n"
        msg += f"<b>Preço com desconto:</b> R$ {discount_value} (-{percentual_of_discount}%)\n"
        msg += f"<b>Disponível</b>: {'Sim' if sellable_42 else 'Não'}\n"
        msg += f"<b>Estoque</b>: {stock_level_42} [{stock_status_42}])\n"
        msg += "\n\n"

    return msg

def send_telegram(message):
    requests.get(TG_URL, params={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

# ---- Loop infinito ----
while True:
    now = datetime.now()
    if now.minute % 5 == 0:
        try:
            produtos = get_products()
            msg = format_message(produtos)
            if msg.strip():
                send_telegram(msg)
        except Exception as e:
            send_telegram(f"<b>Erro na atualização</b>: {e}")

        # Espera até o próximo minuto para não enviar várias vezes
        while datetime.now().minute % 5 == 0:
            time.sleep(240)
    else:
        time.sleep(30)