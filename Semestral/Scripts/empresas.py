import base64
import requests
import json
import os
import time
from datetime import datetime
import urllib3

urllib3.disable_warnings()

def fetch_companies(page_number, page_size):
    params = {
        "language": "pt-br",
        "pageNumber": page_number,
        "pageSize": page_size
    }
    params_str = json.dumps(params)
    encoded_params = base64.b64encode(params_str.encode('utf-8')).decode('utf-8')
    base_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetInitialCompanies/"
    url = base_url + encoded_params
    response = requests.get(url, verify=False)
    response.raise_for_status()
    return response.json()

def fetch_company_details(code_cvm, max_retries=3):
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

def format_company_data(company, details):
    industry_classification = details.get("industryClassification", "").split(" / ")[0] if details else ""
    activity = details.get("activity", "") if details else ""
    website = details.get("website", "") if details else ""
    has_bdr = details.get("hasBDR", False) if details else False

    return {
        "nomeEmpresaCompleto": company["companyName"],
        "nomeEmpresa": company["tradingName"],
        "codigoEmpresa": company["issuingCompany"],
        "codigoCVM": company["codeCVM"],
        "dataInicio": company["dateListing"],
        "industria": industry_classification,
        "segmento": company["segment"],
        "atividade": activity,
        "codigos": [code["code"] for code in details.get("otherCodes", [])] if details and details.get("otherCodes") else [],
        "informacoes": {
            "cnpj": company["cnpj"],
            "site": website,
            "marketIndicator": company["marketIndicator"],
            "temBDR": has_bdr,
            "tipoBDR": company["typeBDR"],
            "status": company["status"],
            "tipo": company["type"],
            "mercado": company["market"]
        }
    }

def load_existing_companies(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"empresas": [], "empresas_sem_codigo": []}

def find_company_by_cvm(companies, code_cvm):
    for company_list in companies.values():
        for company in company_list:
            if company["codigoCVM"] == code_cvm:
                return company
    return None

def reset_file(filename):
    if os.path.exists(filename):
        os.remove(filename)

def main():
    
    if not os.path.exists("Json"):
        os.makedirs("Json")
    if not os.path.exists("Suporte"):
        os.makedirs("Suporte")
        
        
    start_time = time.time()
    page_size = 120
    page_number = 1
    all_companies = []

    initial_data = fetch_companies(page_number, page_size)
    total_pages = initial_data['page']['totalPages']
    all_companies.extend(initial_data['results'])
    print("Carregando todas as empresas...")
    for page_number in range(2, total_pages + 1):
        data = fetch_companies(page_number, page_size)
        all_companies.extend(data['results'])
        print(f"Página {page_number} de {total_pages}")

    detailed_companies = {"empresas": [], "empresas_sem_codigo": []}
    empresas_com_codigo_json = os.path.join("Finais/Parcial", "empresasParcial.json")
    empresas_sem_codigo_json = os.path.join("Finais/Parcial", "empresasSemCodigo.json")
    existing_companies_com_codigo = load_existing_companies(empresas_com_codigo_json)
    existing_companies_sem_codigo = load_existing_companies(empresas_sem_codigo_json)
    existing_companies = {
        "empresas": existing_companies_com_codigo.get("empresas", []),
        "empresas_sem_codigo": existing_companies_sem_codigo.get("empresas_sem_codigo", [])
    }
    added_companies = []
    removed_companies = {"empresas": existing_companies["empresas"].copy(), "empresas_sem_codigo": existing_companies["empresas_sem_codigo"].copy()}
    changes = []

    total_companies = len(all_companies)
    for i, company in enumerate(all_companies, start=1):
        try:
            details = fetch_company_details(company['codeCVM'])
            formatted_company = format_company_data(company, details)
            existing_company = find_company_by_cvm(existing_companies, company['codeCVM'])

            if existing_company:
                removed_companies["empresas"] = [c for c in removed_companies["empresas"] if c["codigoCVM"] != company['codeCVM']]
                removed_companies["empresas_sem_codigo"] = [c for c in removed_companies["empresas_sem_codigo"] if c["codigoCVM"] != company['codeCVM']]
                if formatted_company != existing_company:
                    changes.append({
                        "codigoCVM": company["codeCVM"],
                        "nomeEmpresa": company["tradingName"],
                        "alteracoes": {
                            "antigo": existing_company,
                            "novo": formatted_company
                        }
                    })
            else:
                added_companies.append(formatted_company)

            if formatted_company["codigos"]:
                detailed_companies["empresas"].append(formatted_company)
            else:
                detailed_companies["empresas_sem_codigo"].append(formatted_company)

            print(f"Empresa:  {company['companyName']} - {i} / {total_companies}")
            time.sleep(1.5)  # Increased delay between requests
        except Exception as e:
            print(f"\nError processing company {company['companyName']}: {str(e)}")
            time.sleep(5)  # Longer delay after an error
            continue

    with open(empresas_com_codigo_json, 'w', encoding='utf-8') as f:
        json.dump({"empresas": detailed_companies["empresas"]}, f, ensure_ascii=False, indent=4)
        
    with open(empresas_sem_codigo_json, 'w', encoding='utf-8') as f:
        json.dump({"empresas_sem_codigo": detailed_companies["empresas_sem_codigo"]}, f, ensure_ascii=False, indent=4)

   
    # Reset files if they exist
    txt_Adicionadas = os.path.join("Suporte", "empresas.txt")
    txt_Alteradas = os.path.join("Suporte", "alteracaoEmpresas.txt")
    reset_file(txt_Adicionadas)
    reset_file(txt_Alteradas)

    print(f"Total companhias processadas: {len(detailed_companies['empresas']) + len(detailed_companies['empresas_sem_codigo'])}")
    print(f"Companhias com código: {len(detailed_companies['empresas'])}")
    print(f"Total companhias sem código: {len(detailed_companies['empresas_sem_codigo'])}")

    end_time = time.time()
    execution_time_min = (end_time - start_time) / 60
    execution_time_secs = (end_time - start_time) % 60
    print(f"Tempo de execução EMPRESAS: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos")
    tempo_medio = (end_time - start_time) / (len(detailed_companies["empresas"]) + len(detailed_companies["empresas_sem_codigo"]))
    print(f"Tempo médio: {tempo_medio:.2f} segundos")

    with open(txt_Adicionadas, 'w', encoding='utf-8') as f:
        f.write(f"Relatório de Empresas gerado em: {datetime.now().strftime('%d / %m / %Y  %H:%M')}\n\n")
        f.write(f"Tempo de execução: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos.\n\n")
        f.write(f"Total companhias: {len(detailed_companies['empresas']) + len(detailed_companies['empresas_sem_codigo'])}\n")
        f.write(f"Companhias com código: {len(detailed_companies['empresas'])}\n")
        f.write(f"Companhias sem código: {len(detailed_companies['empresas_sem_codigo'])}\n\n")

        if added_companies or removed_companies["empresas"] or removed_companies["empresas_sem_codigo"]:
            if added_companies:
                f.write("Empresas Adicionadas:\n")
                for company in added_companies:
                    f.write(f"- {company['nomeEmpresa']} (CVM: {company['codigoCVM']})\n")
            if removed_companies["empresas"] or removed_companies["empresas_sem_codigo"]:
                f.write("\nEmpresas Removidas:\n")
                for company in removed_companies["empresas"]:
                    f.write(f"- {company['nomeEmpresa']} (CVM: {company['codigoCVM']})\n")

        if changes:
            f.write("Alterações nas Empresas:\n")
            for change in changes:
                f.write(f"- {change['nomeEmpresa']} (CVM: {change['codigoCVM']})\n")
                f.write("  Antigo:\n")
                f.write(json.dumps(change["alteracoes"]["antigo"], ensure_ascii=False, indent=4))
                f.write("\n  Novo:\n")
                f.write(json.dumps(change["alteracoes"]["novo"], ensure_ascii=False, indent=4))
                f.write("\n\n")


if __name__ == "__main__":
    main()
