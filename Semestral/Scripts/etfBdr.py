import requests
import json
import base64
import os
from datetime import datetime
import time

# Função para decodificar base64
def decode_base64(encoded_str):
    base64_bytes = encoded_str.encode('utf-8')
    message_bytes = base64.b64decode(base64_bytes)
    return message_bytes.decode('utf-8')

# URL inicial para coletar a lista de ETFs de BDR
base_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetCompaniesBDR/"
params_base64 = "eyJsYW5ndWFnZSI6InB0LWJyIiwicGFnZU51bWJlciI6MSwicGFnZVNpemUiOjEyMCwiY29kZUNhdGVnb3J5QlZNRiI6LTF9"

initial_url = base_url + decode_base64(params_base64)
start_time = time.time()

def fetch_etf_bdr(page_number, page_size=120):
    payload = base64.b64encode(json.dumps({
        "language": "pt-br",
        "pageNumber": page_number,
        "pageSize": page_size,
        "codeCategoryBVMF": "-1"
    }).encode()).decode()

    url = f"{base_url}{payload}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao buscar a página {page_number} de ETFs de BDR.")
        return None

def fetch_etf_bdr_details(code_cvm):
    detail_payload = base64.b64encode(json.dumps({
        "codeCVM": code_cvm,
        "language": "pt-br"
    }).encode()).decode()

    detail_url = f"https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetDetail/{detail_payload}"
    response = requests.get(detail_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao buscar detalhes do ETF de BDR com código CVM {code_cvm}.")
        return None

# Lista para armazenar as informações dos ETFs de BDR
etfs_bdr_info = []
existing_etfs = []

# Verificar se o arquivo etfBdr.json existe e carregar os ETFs existentes
etf_bdr_file = os.path.join("Finais", "Parcial", "etfBdr.json")
if os.path.exists(etf_bdr_file):
    with open(etf_bdr_file, 'r', encoding='utf-8') as f:
        existing_etfs = json.load(f)

# Variáveis para controle de páginas e registros
page_number = 1
total_etfs = 0

# Obter o número total de páginas disponíveis e o número total de ETFs
initial_data = fetch_etf_bdr(page_number=1)
if initial_data is None:
    print("Error: Could not fetch initial ETF BDR data")
    exit(1)

total_pages = initial_data['page']['totalPages']
total_etfs += initial_data['page']['totalRecords']

# Iniciar o scraping de todas as páginas disponíveis
while page_number <= total_pages:
    print(f"Buscando página {page_number} de ETFs de BDR...")
    data = fetch_etf_bdr(page_number)
    if data:
        etfs_data = data['results']

        # Iterar sobre cada ETF de BDR na lista da página atual
        for i, etf in enumerate(etfs_data):
            total_etfs_so_far = (page_number - 1) * 120 + i + 1
            print(f"ETF BDR: {etf['companyName']} - {total_etfs_so_far} / {total_etfs}")
            etf_details = fetch_etf_bdr_details(etf['codeCVM'])
            
            try:
                if etf_details:
                    etf_info = {
                        "nomeCompletoETF": etf_details.get('companyName', '') or '',
                        "nomeETF": etf_details.get('tradingName', '') or '',
                        "codigoETF": etf_details.get('issuingCompany', '') or '',
                        "codigo": etf_details.get('otherCodes', [{}])[0].get('code', '') or '' if etf_details.get('otherCodes') else '',
                        "codigoCVM": etf_details.get('codeCVM', '') or '',
                        "industria": "Financeiro e Outros",
                        "segmento": "Fundos de Ações BDRs",
                        "atividade": etf_details.get('describleCategoryBVMF', '') or '',
                        "informações": {
                            "status": etf_details.get('status', '') or '',
                            "marketIndicator": etf_details.get('marketIndicator', '') or '',
                            "dataInicio": etf_details.get('dateListing', '') or '',
                            "tipo": etf_details.get('type', '') or ''
                        }
                    }
                    
                    # Strip whitespace after ensuring no None values
                    etf_info = {k: v.strip() if isinstance(v, str) else v for k, v in etf_info.items()}
                    # Fix for the dictionary comprehension on informações
                    if isinstance(etf_info["informações"], dict):
                        etf_info["informações"] = {k: v.strip() if isinstance(v, str) else v for k, v in etf_info["informações"].items()}
                    
                    etfs_bdr_info.append(etf_info)
                else:
                    print(f"Dados não encontrados para o ETF de BDR: {etf['companyName']}")
                
            except Exception as e:
                print(f"Erro ao processar o ETF de BDR {etf['companyName']}: {str(e)}")
                continue
                
            time.sleep(0.5)

        page_number += 1
    else:
        print(f"Erro ao buscar a página {page_number} de ETFs de BDR.")
        break

# Comparar com os ETFs existentes e identificar alterações
if existing_etfs:
    updated_etfs = []
    added_etfs = []
    removed_etfs = []

    # Verificar ETFs adicionados, atualizados ou removidos
    for etf in etfs_bdr_info:
        found = False
        for existing_etf in existing_etfs:
            if etf['codigoCVM'] == existing_etf['codigoCVM']:
                found = True
                # Comparar os campos relevantes para verificar se há diferenças
                if etf != existing_etf:
                    updated_etfs.append(etf)
                break
        if not found:
            added_etfs.append(etf)

    # Verificar ETFs removidos
    for existing_etf in existing_etfs:
        found = False
        for etf in etfs_bdr_info:
            if existing_etf['codigoCVM'] == etf['codigoCVM']:
                found = True
                break
        if not found:
            removed_etfs.append(existing_etf)

    # Atualizar o arquivo etfBdr.json com os novos dados
    with open(etf_bdr_file, 'w', encoding='utf-8') as f:
        json.dump(etfs_bdr_info, f, ensure_ascii=False, indent=4)
        print("Arquivo etfBdr.json atualizado com sucesso.")

    end_time = time.time()
    execution_time_min = (end_time - start_time) / 60
    execution_time_secs = (end_time - start_time) % 60
    print(f"Tempo de execução: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos")

    # Criar o arquivo de texto com as alterações
    txt_file = os.path.join("Suporte", "etfBdr.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(f"Alterações em ETFs de BDR - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        f.write(f"Tempo de execução: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos.\n\n")
        f.write(f"Total de ETFs coletados: {total_etfs}\n\n")
        
        if updated_etfs:
            f.write("ETFs atualizados:\n")
            for etf in updated_etfs:
                f.write(f"{etf['nomeCompletoETF']}, Código CVM: {etf['codigoCVM']}\n")
            f.write("\n")
        
        if added_etfs:
            f.write("ETFs adicionados:\n")
            for etf in added_etfs:
                f.write(f"{etf['nomeCompletoETF']}, Código CVM: {etf['codigoCVM']}\n")
            f.write("\n")

        if removed_etfs:
            f.write("ETFs removidos:\n")
            for etf in removed_etfs:
                f.write(f"Nome: {etf['nomeCompletoETF']}, Código CVM: {etf['codigoCVM']}\n")
            f.write("\n")
    
else:
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(etf_bdr_file), exist_ok=True)
    
    # Save the collected ETF BDR data to file even if there's no existing file to compare with
    with open(etf_bdr_file, 'w', encoding='utf-8') as f:
        json.dump(etfs_bdr_info, f, ensure_ascii=False, indent=4)
        print("Arquivo etfBdr.json criado com sucesso.")
    
    end_time = time.time()
    execution_time_min = (end_time - start_time) / 60
    execution_time_secs = (end_time - start_time) % 60
    print(f"Tempo de execução: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos")
    
    # Create a text file with initial data
    os.makedirs("Suporte", exist_ok=True)
    txt_file = os.path.join("Suporte", "etfBdr.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(f"Coleta inicial de ETFs de BDR - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        f.write(f"Tempo de execução: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos.\n\n")
        f.write(f"Total de ETFs coletados: {total_etfs}\n\n")
        f.write("Todos os ETFs foram adicionados na coleta inicial.\n")
