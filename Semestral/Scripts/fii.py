import requests
import base64
import json
import time
import os
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

# Disable SSL warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define the URLs
list_url = "https://sistemaswebb3-listados.b3.com.br/fundsProxy/fundsCall/GetListedFundsSIG/eyJ0eXBlRnVuZCI6NywicGFnZU51bWJlciI6MSwicGFnZVNpemUiOjYwfQ=="
detail_url_template = "https://sistemaswebb3-listados.b3.com.br/fundsProxy/fundsCall/GetDetailFundSIG/{}"

# Define file paths
fiiJson = os.path.join("Finais", "Parcial", "fiis.json")
fii_txt = os.path.join("Suporte", "fii.txt")

def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_fii(page_number, page_size=60, session=None):
    if session is None:
        session = create_session()
        
    payload = base64.b64encode(json.dumps({
        "typeFund": 7,
        "pageNumber": page_number,
        "pageSize": page_size
    }).encode()).decode()
    
    url = f"https://sistemaswebb3-listados.b3.com.br/fundsProxy/fundsCall/GetListedFundsSIG/{payload}"
    try:
        response = session.get(url, verify=False)
        response.raise_for_status()
        time.sleep(2)  # Add delay between requests
        return response.json()
    except Exception as e:
        print(f"Error fetching FII list (page {page_number}): {e}")
        time.sleep(5)  # Longer delay on error
        raise

def fetch_details(cnpj, acronym, session=None):
    if session is None:
        session = create_session()
        
    detail_payload = base64.b64encode(json.dumps({
        "typeFund": 7,
        "cnpj": cnpj,
        "identifierFund": acronym
    }).encode()).decode()
    
    detail_url = detail_url_template.format(detail_payload)
    try:
        response = session.get(detail_url, verify=False)
        response.raise_for_status()
        time.sleep(2)  # Add delay between requests
        return response.json()
    except Exception as e:
        print(f"Error fetching details for {acronym}: {e}")
        time.sleep(5)  # Longer delay on error
        raise

# Load existing FIIs data if available
if os.path.exists(fiiJson):
    with open(fiiJson, 'r', encoding='utf-8') as file:
        old_fiis = json.load(file)
else:
    old_fiis = []

start_time = time.time()

session = create_session()

# Get the initial data to find the total number of pages
try:
    initial_data = fetch_fii(page_number=1, session=session)
    total_pages = initial_data['page']['totalPages']
    all_funds = initial_data['results']

    print("Carregando todas as FIIs...")
    for page_number in range(2, total_pages + 1):
        data = fetch_fii(page_number, session=session)
        all_funds.extend(data['results'])
        print(f"Página {page_number} de {total_pages}")

    fiis = []
    total_fii = len(all_funds)

    for i, fund in enumerate(all_funds, start=1):
        try:
            detail_data = fetch_details(fund['cnpj'], fund['acronym'], session=session)
            
            fii_details = {
                "nomeCompletoFII": detail_data['detailFund']['companyName'],
                "nomeFII": detail_data['detailFund']['tradingName'],
                "codigoFII": detail_data['detailFund']['acronym'],
                "codigo": detail_data['detailFund']['tradingCode'].strip().split(),
                "quotaCount": detail_data['detailFund']['quotaCount'],
                "quotaDateApproved": detail_data['detailFund']['quotaDateApproved'],
                "industria": "Financeiro e Outros",
                "segmento": "Fundos Imobiliarios",
                "informacoes": {
                    "cnpj": detail_data['detailFund']['cnpj'],
                    "site": detail_data['detailFund']['webSite']
                }
            }
            fiis.append(fii_details)
            
            print(f"FII: {fund['fundName']} - {i} / {total_fii}")
            time.sleep(0.5)
        except Exception as e:
            print(f"Failed to process FII {fund['fundName']}: {e}")
            continue

except Exception as e:
    print(f"Fatal error: {e}")
    exit(1)

# Save FII details to file
with open(fiiJson, 'w', encoding='utf-8') as fiis_file:
    json.dump(fiis, fiis_file, ensure_ascii=False, indent=4)

# Analyze changes
old_fiis_dict = {fii['codigoFII']: fii for fii in old_fiis}
new_fiis_dict = {fii['codigoFII']: fii for fii in fiis}

added_fiis = [fii for codigo, fii in new_fiis_dict.items() if codigo not in old_fiis_dict]
removed_fiis = [fii for codigo, fii in old_fiis_dict.items() if codigo not in new_fiis_dict]
altered_fiis = []
for codigo, new_fii in new_fiis_dict.items():
    if codigo in old_fiis_dict and new_fii != old_fiis_dict[codigo]:
        altered_fiis.append({
            "codigoFII": codigo,
            "nomeFII": new_fii["nomeFII"],
            "alteracoes": {
                "antigo": old_fiis_dict[codigo],
                "novo": new_fii
            }
        })

end_time = time.time()
execution_time_min = (end_time - start_time) / 60
execution_time_secs = (end_time - start_time) % 60
print(f"Tempo de execução FII: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos")
tempo_medio = (end_time - start_time) / (total_fii)
print(f"Tempo médio: {tempo_medio:.2f} segundos")


# Write added, removed, and altered FIIs to a single file
with open(fii_txt, 'w', encoding='utf-8') as f:
    f.write(f"Relatório de FIIs gerado em: {datetime.now().strftime('%d / %m / %Y  %H:%M')}\n\n")
    f.write(f"Tempo de execução: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos.\n\n")
    f.write(f"Total FII: {total_fii}\n")

    f.write(f"Total FIIs adicionados: {len(added_fiis)}\n")
    if added_fiis:
        f.write("FIIs Adicionados:\n")
        for fii in added_fiis:
            f.write(f"- {fii['nomeFII']} (Código: {fii['codigoFII']})\n")
    
    f.write(f"\nTotal FIIs removidos: {len(removed_fiis)}\n")
    if removed_fiis:
        f.write("FIIs Removidos:\n")
        for fii in removed_fiis:
            f.write(f"- {fii['nomeFII']} (Código: {fii['codigoFII']})\n")

    f.write(f"\nTotal FIIs alterados: {len(altered_fiis)}\n")
    if altered_fiis:
        f.write("FIIs Alterados:\n")
        for change in altered_fiis:
            f.write(f"- {change['nomeFII']} (Código: {change['codigoFII']})\n")
            f.write("  Antigo:\n")
            f.write(json.dumps(change["alteracoes"]["antigo"], ensure_ascii=False, indent=4))
            f.write("\n  Novo:\n")
            f.write(json.dumps(change["alteracoes"]["novo"], ensure_ascii=False, indent=4))
            f.write("\n\n")


