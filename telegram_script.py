import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# ---- Carrega variáveis do .env ----
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TG_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# ---- Config Vans ----
base_url = "https://www.vans.com.br"
url = (
    "https://www.vans.com.br/arezzocoocc/v2/vans/products/search?"
    "category=ULTIMASUNIDADES&currentPage=0&pageSize=240&fields=FULL&"
    "query=:creation-time:shoeSize:42&storeFinder=false"
)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )
}

MAX_RETRIES = 3
RETRY_DELAY = 5  # segundos


# ---- Função para carregar blacklist do arquivo ----
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


# ---- Função para enviar mensagem ao Telegram ----
def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ TELEGRAM_TOKEN ou CHAT_ID não definidos no .env")
        return

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                TG_URL,
                params={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"},
                timeout=10,
            )

            if response.status_code == 200:
                print("[✅ Enviado para o Telegram]")
                return
            else:
                print(
                    f"[Erro Telegram - Tentativa {attempt}] Código: {response.status_code}"
                )
                print(response.text)

        except Exception as e:
            print(f"[Erro ao enviar Telegram - Tentativa {attempt}]: {e}")

        if attempt < MAX_RETRIES:
            print(f"⏳ Tentando novamente em {RETRY_DELAY} segundos...")
            time.sleep(RETRY_DELAY)

    print("[❌ Falha ao enviar mensagem para o Telegram após várias tentativas]")


# ---- Função auxiliar para fazer requisição GET com retries ----
def get_with_retries(url, headers=None, timeout=10):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp
        except Exception as e:
            print(f"[Erro na requisição {url} - Tentativa {attempt}]: {e}")
            if attempt < MAX_RETRIES:
                print(f"⏳ Tentando novamente em {RETRY_DELAY} segundos...")
                time.sleep(RETRY_DELAY)
    return None


# ---- Função para checar produtos e enviar mensagens (CORRIGIDA) ----
def check_products():
    # Carrega a blacklist atualizada a cada execução
    black_list = load_blacklist()

    try:
        resp = get_with_retries(url, headers=headers)
        if not resp:
            raise Exception("Falha ao obter dados principais da API.")

        data = resp.json()

        messages = []
        for produto in data.get("products", []):
            name = produto.get("name") or ""
            discount_value = produto.get("discountPrice", {}).get("value")
            price_value = produto.get("price", {}).get(
                "value"
            )  # Adicionado: Pega o preço normal

            if not name or price_value is None:
                continue

            # **CORREÇÃO 1: Lógica de Preços para Blacklist**
            # Usa o valor do desconto se existir, ou o preço normal.
            # Isso garante que todos os produtos com um preço sejam checados,
            # mesmo que não estejam em promoção.
            price_to_check = (
                discount_value if discount_value is not None else price_value
            )

            # Ignorar produtos na blacklist
            if (name.lower().strip(), price_to_check) in [
                (n.lower().strip(), d) for n, d in black_list
            ]:
                continue

            # O produto é válido e não está na blacklist, prossegue com a checagem de estoque.

            product_code = produto.get("code")
            product_url = (
                f"{base_url}/arezzocoocc/v2/vans/products/{product_code}/"
                "dynamic-product-fields?fields=DYNAMIC_FIELDS_PDP"
            )

            # **CORREÇÃO 2: Removido o breakpoint() que pausava o script**

            prod_resp = get_with_retries(product_url, headers=headers)
            if not prod_resp:
                print(
                    f"[Aviso] Falha ao obter dados do produto {product_code}, pulando..."
                )
                continue

            prod_data = prod_resp.json()

            sellable_42 = False
            stock_level_42 = 0
            stock_status_42 = "outOfStock"

            for variant in prod_data.get("variantOptions", []):
                if variant.get("code") == f"{product_code}-42":
                    sellable_42 = variant.get("sellable", False)
                    stock_level_42 = variant.get("stock", {}).get("stockLevel", 0)
                    stock_status_42 = variant.get("stock", {}).get(
                        "stockLevelStatus", "outOfStock"
                    )
                    break

            percentual_of_discount = produto.get("percentualOfDiscount", 0)
            product_page_url = base_url + produto.get("url", "")

            # Formata a mensagem com base no preço.
            # Se discount_value for None, mostramos apenas o preço normal e 0% de desconto.
            price_info = f"<b>Preço:</b> R$ {price_value}"
            discount_info = ""
            if discount_value is not None:
                price_info = f"<b>Preço Normal:</b> R$ {price_value}"
                discount_info = (
                    f"<b>Preço Atual:</b> R$ {discount_value}\n"
                    f"<b>Desconto:</b> -{percentual_of_discount}%\n"
                )

            message = (
                f"<b>Nome:</b> {name}\n"
                f"<b>Link:</b> {product_page_url}\n"
                f"{price_info}\n"
                f"{discount_info}"
                f"<b>Disponível:</b> {'Sim' if sellable_42 else 'Não'}\n"
                f"<b>Estoque:</b> {stock_level_42} [{stock_status_42}]\n"
                f"{'-'*40}"
            )
            messages.append(message)

        if messages:
            full_message = (
                f"<b>Atualização {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</b>\n\n"
                + "\n\n".join(messages)
            )
            send_telegram(full_message)
        else:
            print("Nenhum produto novo ou válido para enviar.")

    except Exception as e:
        print(f"[Erro geral]: {e}")
        try:
            send_telegram(f"<b>Erro geral</b>: {e}")
        except:
            print("[Erro ao enviar mensagem de erro para Telegram]")


# ---- Loop principal que roda a cada 5 minutos ----
print("✅ Bot iniciado. Esperando próximo múltiplo de 5 minutos...")

check_products()

# while True:
#     try:
#         now = datetime.now()
#         if now.minute % 5 == 0:
#             print(f"⏰ Rodando check_products() às {now.strftime('%H:%M:%S')}")
#             check_products()

#             # Espera até o próximo minuto para evitar múltiplos envios dentro do mesmo minuto
#             while datetime.now().minute == now.minute:
#                 time.sleep(5)
#         else:
#             time.sleep(10)
#     except Exception as e:
#         print(f"[Erro no loop principal]: {e}")
#         time.sleep(30)
