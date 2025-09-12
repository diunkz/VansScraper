import requests
import json

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


resp = requests.get(url, headers=headers)
resp.raise_for_status()

data = resp.json()  # Agora é um dicionário Python

for produto in data.get("products", []):
    name = produto.get("name")
    discount_value = produto.get("discountPrice", {}).get("value")

    # Ignora produtos da blacklist
    if (name.lower().strip(), discount_value) in [(n.lower().strip(), d) for n, d in black_list]:
        continue

    product_code = produto.get("code")
    product_url = f"{base_url}/arezzocoocc/v2/vans/products/{product_code}/dynamic-product-fields?fields=DYNAMIC_FIELDS_PDP"

    # Consulta a página do produto para checar o tamanho 42
    prod_resp = requests.get(product_url, headers=headers)
    prod_resp.raise_for_status()
    prod_data = prod_resp.json()

    sellable_42 = ""
    stock_level_42 = ""
    stock_status_42 = ""

    for variant in prod_data.get("variantOptions", []):
        if variant.get("code") == f"{product_code}-42":
            sellable_42 = variant.get("sellable", False)
            stock_level_42 = variant.get("stock", {}).get("stockLevel", 0)
            stock_status_42 = variant.get("stock", {}).get("stockLevelStatus", "outOfStock")
            break

    price_value = produto.get("price", {}).get("value")
    percentual_of_discount = produto.get("percentualOfDiscount")
    product_page_url = base_url + produto.get('url', '')

    # Pega a imagem principal (thumbnail)
    image_url = produto.get("primaryImage", {}).get("url") or produto.get("allImages", [{}])[0].get("url")

    # Mostra as informações
    print("Name:", name)
    print("Product URL:", product_page_url)
    # print("Image URL:", image_url)
    #print("Product code:", product_code)
    print("Sellable:", sellable_42)
    print(f"Stock: {stock_level_42} [{stock_status_42}]")
    print(f"Price value: R$ {price_value}")
    print(f"Percentual of Discount: {percentual_of_discount}%")
    print(f"Discount value: R$ {discount_value}")
    print("-" * 50)