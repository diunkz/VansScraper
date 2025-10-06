import requests
import json

base_url = "https://www.vans.com.br"
url = "https://www.vans.com.br/arezzocoocc/v2/vans/products/search?category=ULTIMASUNIDADES&currentPage=0&pageSize=240&fields=FULL&query=:creation-time:shoeSize:42&storeFinder=false"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
}


def load_blacklist(filename="blacklist.txt"):
    black_list = []
    try:
        with open(filename, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.rsplit(",", 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    try:
                        price = float(parts[1].strip())
                        black_list.append((name, price))
                    except ValueError:
                        print(f"Preço inválido na linha: {line}")
                else:
                    print(f"Linha no formato errado: {line}")
    except FileNotFoundError:
        print(f"[Aviso] Arquivo {filename} não encontrado. Blacklist vazia.")
    return black_list


# Lista de produtos para ignorar (nome e valor do desconto)
black_list = load_blacklist()

resp = requests.get(url, headers=headers)
resp.raise_for_status()

data = resp.json()  # Agora é um dicionário Python

for produto in data.get("products", []):
    name = produto.get("name")
    discount_value = produto.get("discountPrice", {}).get("value")

    # Ignora produtos da blacklist
    if (name.lower().strip(), discount_value) in [
        (n.lower().strip(), d) for n, d in black_list
    ]:
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
            stock_status_42 = variant.get("stock", {}).get(
                "stockLevelStatus", "outOfStock"
            )
            break

    price_value = produto.get("price", {}).get("value")
    percentual_of_discount = produto.get("percentualOfDiscount")
    product_page_url = base_url + produto.get("url", "")

    # Pega a imagem principal (thumbnail)
    image_url = produto.get("primaryImage", {}).get("url") or produto.get(
        "allImages", [{}]
    )[0].get("url")

    # Mostra as informações
    print("Name:", name)
    print("Product URL:", product_page_url)
    # print("Image URL:", image_url)
    # print("Product code:", product_code)
    print("Sellable:", sellable_42)
    print(f"Stock: {stock_level_42} [{stock_status_42}]")
    print(f"Price value: R$ {price_value}")
    print(f"Percentual of Discount: {percentual_of_discount}%")
    print(f"Discount value: R$ {discount_value}")

    print("-" * 50)
