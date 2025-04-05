import requests
import json
import base64
import time
import os
from datetime import datetime

# Função para decodificar a parte criptografada do URL
def decode_base64(encoded_str):
    base64_bytes = encoded_str.encode('utf-8')
    message_bytes = base64.b64decode(base64_bytes)
    return message_bytes.decode('utf-8')

etfJson = os.path.join("Finais", "Parcial", "etf.json")
etfTxt = os.path.join("Suporte", "etf.txt")
start_time = time.time()
# URL inicial para coletar a lista de ETFs
base_url = "https://sistemaswebb3-listados.b3.com.br/fundsProxy/fundsCall/GetListedFundsSIG/"
params_base64 = "eyJ0eXBlRnVuZCI6MjAsInBhZ2VOdW1iZXIiOjEsInBhZ2VTaXplIjo2MH0="
initial_url = base_url + params_base64

def fetch_etf(page_number, page_size=60, max_retries=3):
    payload = base64.b64encode(json.dumps({
        "typeFund": 20,
        "pageNumber": page_number,
        "pageSize": page_size
    }).encode()).decode()
    
    url = f"https://sistemaswebb3-listados.b3.com.br/fundsProxy/fundsCall/GetListedFundsSIG/{payload}"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                wait_time = (2 ** attempt) + 1  # Exponential backoff
                print(f"\nRate limit hit, waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                if attempt == max_retries - 1:
                    raise
                continue
            raise
        except json.JSONDecodeError:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + 1
                print(f"\nJSON decode error for page {page_number}, waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"\nFailed to decode JSON for page {page_number} after {max_retries} attempts")
                raise

def fetch_details(acronym, max_retries=3):
    detail_payload = base64.b64encode(json.dumps({
        "typeFund": 20,
        "identifierFund": acronym
    }).encode()).decode()
    
    detail_url = f"https://sistemaswebb3-listados.b3.com.br/fundsProxy/fundsCall/GetDetailFundSIG/{detail_payload}"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(detail_url)
            response.raise_for_status()  # Will raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                wait_time = (2 ** attempt) + 1  # Exponential backoff
                print(f"\nRate limit hit, waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                if attempt == max_retries - 1:
                    raise
                continue
            raise
        except json.JSONDecodeError:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + 1
                print(f"\nJSON decode error for {acronym}, waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"\nFailed to decode JSON for {acronym} after {max_retries} attempts")
                raise

# Get the initial data to find the total number of pages
etfs_info = []
all_funds = []
try:
    initial_data = fetch_etf(page_number=1)
    if initial_data is None:
        print("Error: Could not fetch initial ETF data")
        exit(1)
    
    total_pages = initial_data['page']['totalPages']
    all_funds = initial_data['results']

    print("Carregando todas as ETFs...")
    for page_number in range(2, total_pages + 1):
        data = fetch_etf(page_number)
        if data is None:
            print(f"Warning: Could not fetch data for page {page_number}, skipping...")
            continue
        all_funds.extend(data['results'])
        print(f"Página {page_number} de {total_pages}")
        time.sleep(0.5)  # Pequeno delay para evitar sobrecarga no servidor

except Exception as e:
    print(f"Error fetching ETF list: {e}")
    exit(1)

total_etf = len(all_funds)

# Iterar sobre cada ETF na lista
for i, etf in enumerate(all_funds):
    try:
        acronym = etf['acronym']
        detail_data = fetch_details(acronym)
        
        if detail_data is None or 'detailFund' not in detail_data:
            print(f"Warning: Could not fetch valid details for {acronym}, skipping...")
            continue
        
        etf_info = {
            "nomeCompletoETF": detail_data['detailFund']['companyName'].strip(),
            "nomeETF": detail_data['detailFund']['tradingName'].strip(),
            "codigoETF": detail_data['detailFund']['acronym'].strip(),
            "codigo": detail_data['detailFund']['tradingCode'].strip(),
            "quotaCount": detail_data['detailFund']['quotaCount'].strip(),
            "quotaDateApproved": detail_data['detailFund']['quotaDateApproved'].strip(),
            "industria": "Financeiro e Outros",
            "segmento": "Fundos de Ações",
            "informacoes": {
                "cnpj": detail_data['detailFund']['cnpj'].strip(),
                "site": detail_data['detailFund']['webSite'].strip(),
            },
        }

        # Adicionar as informações coletadas à lista
        etfs_info.append(etf_info)
        print(f"ETF: {etf['fundName']} - {i + 1} / {total_etf}")
        time.sleep(1.5)  # Pequeno delay para evitar sobrecarga no servidor
    except Exception as e:
        print(f"Error processing ETF {etf.get('fundName', 'unknown')}: {e}")
        continue

# Verificar a existência do arquivo etf.json
if os.path.exists(etfJson):
    with open(etfJson, 'r', encoding='utf-8') as f:
        old_etfs_info = json.load(f)
else:
    old_etfs_info = []

end_time = time.time()
execution_time_min = (end_time - start_time) / 60
execution_time_secs = (end_time - start_time) % 60
print(f"Tempo de execução FII: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos")
tempo_medio = (end_time - start_time) / (total_etf)
print(f"Tempo médio: {tempo_medio:.2f} segundos")

# Comparar os dados antigos com os novos e criar o etf.txt
with open(etfTxt, 'w', encoding='utf-8') as f:
    old_etf_dict = {etf['codigoETF']: etf for etf in old_etfs_info}
    new_etf_dict = {etf['codigoETF']: etf for etf in etfs_info}
    f.write(f"Relatório de ETFs gerado em: {datetime.now().strftime('%d / %m / %Y  %H:%M')}\n\n")
    f.write(f"Tempo de execução: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos.\n\n")
    f.write(f"Total ETF: {total_etf}\n")
    # ETFs adicionadas
    added_etfs = set(new_etf_dict.keys()) - set(old_etf_dict.keys())
    if added_etfs:
        f.write("ETFs adicionadas:\n")
        for etf in added_etfs:
            f.write(json.dumps(new_etf_dict[etf], ensure_ascii=False, indent=4))
            f.write("\n")
    
    # ETFs removidas
    removed_etfs = set(old_etf_dict.keys()) - set(new_etf_dict.keys())
    if removed_etfs:
        f.write("ETFs removidas:\n")
        for etf in removed_etfs:
            f.write(json.dumps(old_etf_dict[etf], ensure_ascii=False, indent=4))
            f.write("\n")
    
    # ETFs alteradas
    altered_etfs = set(new_etf_dict.keys()) & set(old_etf_dict.keys())
    for etf in altered_etfs:
        if new_etf_dict[etf] != old_etf_dict[etf]:
            f.write(f"ETF alterada ({etf}):\n")
            f.write("Antiga:\n")
            f.write(json.dumps(old_etf_dict[etf], ensure_ascii=False, indent=4))
            f.write("\nNova:\n")
            f.write(json.dumps(new_etf_dict[etf], ensure_ascii=False, indent=4))
            f.write("\n")

# Salvar as informações dos ETFs em um arquivo JSON
with open(etfJson, 'w', encoding='utf-8') as f:
    json.dump(etfs_info, f, ensure_ascii=False, indent=4)

print("Informações dos ETFs coletadas e salvas em etf.json")

