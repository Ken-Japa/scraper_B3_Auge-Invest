import base64
import requests
import json
import os
import time
from datetime import datetime
import urllib3

urllib3.disable_warnings()

# Funções para BDRs patrocinados (existentes)
def fetch_bdr_companies(page_number, page_size):
    params = {
        "language": "pt-br",
        "pageNumber": page_number,
        "pageSize": page_size,
        "governance": "14"
    }
    params_str = json.dumps(params)
    encoded_params = base64.b64encode(params_str.encode('utf-8')).decode('utf-8')
    base_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetInitialCompanies/"
    url = base_url + encoded_params
    response = requests.get(url, verify=False)
    response.raise_for_status()
    return response.json()

def fetch_bdr_details(code_cvm, max_retries=3):
    params = {
        "codeCVM": code_cvm,
        "language": "pt-br"
    }
    params_str = json.dumps(params)
    encoded_params = base64.b64encode(params_str.encode('utf-8')).decode('utf-8')
    base_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetDetail/"
    url = base_url + encoded_params
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, verify=False)
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
        except Exception as e:
            print(f"\nError fetching details for CVM {code_cvm}: {str(e)}")
            raise

def format_bdr_data(bdr, details):
    industry_classification = details.get("industryClassification", "").split(" / ")[0] if details else ""
    activity = details.get("activity", "") if details else ""
    website = details.get("website", "") if details else ""

    return {
        "nomeEmpresaCompleto": bdr["companyName"],
        "nomeEmpresa": bdr["tradingName"],
        "codigoEmpresa": bdr["issuingCompany"],
        "codigoCVM": bdr["codeCVM"],
        "dataInicio": bdr["dateListing"],
        "industria": industry_classification,
        "segmento": bdr["segment"],
        "atividade": activity,
        "informações": {
            "cnpj": bdr["cnpj"],
            "site": website,
            "marketIndicator": bdr["marketIndicator"],
            "status": bdr["status"],
            "tipo": bdr["type"],
            "market": bdr["market"]
        },
        "tipoBDR": bdr["typeBDR"],
        "codigo": details.get("code", "")
    }

# Funções para BDRs não patrocinados
def fetch_bdr_nao_patrocinados(page_number, page_size):
    params = {
        "language": "pt-br",
        "pageNumber": page_number,
        "pageSize": page_size,
        "codeCategoryBVMF": 6
    }
    params_str = json.dumps(params)
    encoded_params = base64.b64encode(params_str.encode('utf-8')).decode('utf-8')
    base_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetCompaniesBDR/"
    url = base_url + encoded_params
    response = requests.get(url, verify=False)
    response.raise_for_status()
    return response.json()

def format_bdr_nao_patrocinados_data(bdr, details):
    industry_classification = details.get("industryClassification", "").split(" / ")[0] if details else ""
    activity = details.get("activity", "") if details else ""
    website = details.get("website", "") if details else ""

    return {
        "nomeEmpresaCompleto": bdr["companyName"],
        "nomeEmpresa": bdr["tradingName"],
        "codigoEmpresa": bdr["issuingCompany"],
        "codigoCVM": bdr["codeCVM"],
        "dataInicio": bdr["dateListing"],
        "industria": industry_classification,
        "segmento": bdr["segment"],
        "atividade": activity,
        "informacoes": {
            "cnpj": bdr["cnpj"],
            "site": website,
            "marketIndicator": bdr["marketIndicator"],
            "status": bdr["status"],
            "tipo": bdr["type"],
            "mercado": bdr["market"]
        },
        "tipoBDR": bdr["typeBDR"],
        "codigo": details.get("code", "")
    }

def load_existing_bdrs(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"bdrs": [], "bdr_nao_patrocinados": []}

def find_bdr_by_cvm(bdrs, code_cvm):
    for bdr in bdrs:
        if bdr["codigoCVM"] == code_cvm:
            return bdr
    return None

def main():
    page_size = 120
    page_number = 1

    detailed_bdrs = {"bdrs": [], "bdr_nao_patrocinados": []}
    existing_bdrs = load_existing_bdrs('bdr.json')
    added_bdrs = []
    added_bdr_nao_patrocinados = []
    removed_bdrs = existing_bdrs["bdrs"].copy()
    removed_bdr_nao_patrocinados = existing_bdrs["bdr_nao_patrocinados"].copy()
    bdr_changes = []

    # Process BDRs Patrocinados
    all_bdrs = []

    initial_data = fetch_bdr_companies(page_number, page_size)
    total_pages = initial_data['page']['totalPages']
    all_bdrs.extend(initial_data['results'])
    print("Carregando BDRs patrocinados...")
    for page_number in range(2, total_pages + 1):
        data = fetch_bdr_companies(page_number, page_size)
        all_bdrs.extend(data['results'])
        print(f"Página {page_number} de {total_pages}")

    total_bdrs = len(all_bdrs)
    for i, bdr in enumerate(all_bdrs, start=1):
        details = fetch_bdr_details(bdr['codeCVM'])
        formatted_bdr = format_bdr_data(bdr, details)
        existing_bdr = find_bdr_by_cvm(existing_bdrs["bdrs"], bdr['codeCVM'])

        if existing_bdr:
            removed_bdrs = [c for c in removed_bdrs if c["codigoCVM"] != bdr['codeCVM']]
            if formatted_bdr != existing_bdr:
                bdr_changes.append({
                    "codigoCVM": bdr["codeCVM"],
                    "nomeEmpresa": bdr["tradingName"],
                    "alteracoes": {
                        "antigo": existing_bdr,
                        "novo": formatted_bdr
                    }
                })
        else:
            added_bdrs.append(formatted_bdr)

        detailed_bdrs["bdrs"].append(formatted_bdr)

        print(f"BDR:  {bdr['companyName']} - {i} / {total_bdrs}")
        time.sleep(1.5)

    # Process BDRs Não Patrocinados
    all_bdr_nao_patrocinados = []

    initial_data_nao_patrocinados = fetch_bdr_nao_patrocinados(page_number, page_size)
    total_pages_nao_patrocinados = initial_data_nao_patrocinados['page']['totalPages']
    all_bdr_nao_patrocinados.extend(initial_data_nao_patrocinados['results'])
    print("Carregando BDRs não patrocinados...")
    for page_number in range(2, total_pages_nao_patrocinados + 1):
        data = fetch_bdr_nao_patrocinados(page_number, page_size)
        all_bdr_nao_patrocinados.extend(data['results'])
        print(f"Página {page_number} de {total_pages_nao_patrocinados}")

    total_bdr_nao_patrocinados = len(all_bdr_nao_patrocinados)
    for i, bdr in enumerate(all_bdr_nao_patrocinados, start=1):
        details = fetch_bdr_details(bdr['codeCVM'])
        formatted_bdr = format_bdr_nao_patrocinados_data(bdr, details)
        existing_bdr = find_bdr_by_cvm(existing_bdrs["bdr_nao_patrocinados"], bdr['codeCVM'])

        if formatted_bdr["codigo"]:
            if existing_bdr:
                removed_bdr_nao_patrocinados = [c for c in removed_bdr_nao_patrocinados if c["codigoCVM"] != bdr['codeCVM']]
            else:
                added_bdr_nao_patrocinados.append(formatted_bdr)
                detailed_bdrs["bdr_nao_patrocinados"].append(formatted_bdr)

        print(f"BDR NP:  {bdr['companyName']} - {i} / {total_bdr_nao_patrocinados}")
        time.sleep(1.5)

    # Save to bdr.json
    bdrJson = os.path.join("Finais","Parcial", "bdr.json")
    with open(bdrJson, "w", encoding="utf-8") as f:
        json.dump(detailed_bdrs, f, ensure_ascii=False, indent=4)

    # Relatório de alterações
    txt_BdrAlteracoes = os.path.join("Suporte", "bdr.txt")
    with open(txt_BdrAlteracoes, 'w', encoding='utf-8') as f:
        f.write(f"Relatório de BDRs gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        f.write(f"Total de BDRs: {len(detailed_bdrs['bdrs'])}\n")
        f.write(f"Total de BDRs Não Patrocinados: {len(detailed_bdrs['bdr_nao_patrocinados'])}\n\n")
        
        if added_bdrs or removed_bdrs or added_bdr_nao_patrocinados or removed_bdr_nao_patrocinados:
            if added_bdrs:
                f.write("BDRs Adicionados:\n")
                for bdr in added_bdrs:
                    f.write(f"- {bdr['nomeEmpresa']} (CVM: {bdr['codigoCVM']})\n")
            if removed_bdrs:
                f.write("\nBDRs Removidos:\n")
                for bdr in removed_bdrs:
                    f.write(f"- {bdr['nomeEmpresa']} (CVM: {bdr['codigoCVM']})\n")
            if added_bdr_nao_patrocinados:
                f.write("\nBDRs Não Patrocinados Adicionados:\n")
                for bdr in added_bdr_nao_patrocinados:
                    f.write(f"- {bdr['nomeEmpresa']} (CVM: {bdr['codigoCVM']})\n")
            if removed_bdr_nao_patrocinados:
                f.write("\nBDRs Não Patrocinados Removidos:\n")
                for bdr in removed_bdr_nao_patrocinados:
                    f.write(f"- {bdr['nomeEmpresa']} (CVM: {bdr['codigoCVM']})\n")
        
        if bdr_changes:
            f.write("\nAlterações detalhadas:\n")
            for change in bdr_changes:
                f.write(f"- {change['nomeEmpresa']} (CVM: {change['codigoCVM']})\n")
                f.write(f"  - Antigo: {json.dumps(change['alteracoes']['antigo'], ensure_ascii=False)}\n")
                f.write(f"  - Novo: {json.dumps(change['alteracoes']['novo'], ensure_ascii=False)}\n")

if __name__ == "__main__":
    main()
