import base64
import requests
import json
import os
import time
from datetime import datetime
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings()

def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,  # number of retries
        backoff_factor=1,  # wait 1, 2, 4 seconds between retries
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_dividends(trading_name, page_number=1, page_size=60, session=None):
    if session is None:
        session = create_session()
        
    params = {
        "language": "pt-br",
        "pageNumber": page_number,
        "pageSize": page_size,
        "tradingName": trading_name
    }
    params_str = json.dumps(params)
    encoded_params = base64.b64encode(params_str.encode('utf-8')).decode('utf-8')
    base_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetListedCashDividends/"
    url = base_url + encoded_params
    
    try:
        response = session.get(url, verify=False)
        response.raise_for_status()
        time.sleep(2)  # Increased delay between requests
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching dividends for {trading_name} (page {page_number}): {e}")
        time.sleep(5)  # Longer delay on error
        raise

def reset_file(filename):
    if os.path.exists(filename):
        os.remove(filename)

def main():
    start_time = time.time()
    session = create_session()  # Create session here
    
    empresasJson = os.path.join("Finais/Parcial", "empresas.json")
    with open(empresasJson, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    companies_with_code = [company for company in companies if company.get("codigoEmpresa")]    

    all_dividends = []
    total_companies_len = len(companies_with_code)
    

    # Coleta de dividendos para empresas com código
    for i, company in enumerate(companies_with_code, start=1):
        try:
            trading_name = company["nomeEmpresa"]
            print(f"Dividendos de {trading_name} - {i} de {total_companies_len}")

            first_page = fetch_dividends(trading_name, session=session)
            total_pages = first_page['page']['totalPages']
            all_results = first_page['results']

            for page_number in range(2, total_pages + 1):
                page_data = fetch_dividends(trading_name, page_number, session=session)
                all_results.extend(page_data['results'])
                print(f"Página {page_number} de {total_pages} para {trading_name}")

            formatted_dividends = [
                {
                    "tipo": div["typeStock"],
                    "dataAprovacao": div["dateApproval"],
                    "valor": div["valueCash"],
                    "ratio": div["ratio"],
                    "tipoDividendo": div["corporateAction"],
                    "ultimoDiaCom": div["lastDatePriorEx"],
                    "valorUltimoDiaCom": div["closingPricePriorExDate"]
                }
                for div in all_results
            ]
            
            time.sleep(0.5)
            # Verifica se há dividendos para adicionar à lista
            if formatted_dividends:
                company_dividends = {
                    "nomeEmpresa": trading_name,
                    "dividendos": formatted_dividends
                }
                all_dividends.append(company_dividends)
                
        except Exception as e:
            print(f"Error processing {trading_name}: {e}")
            time.sleep(10)  # Wait longer before continuing to next company
            continue

    # Salvando apenas as empresas com dividendos
    dividendosJson = os.path.join("Finais", "dividendosEmpresas.json")
    with open(dividendosJson, 'w', encoding='utf-8') as f:
        json.dump(all_dividends, f, ensure_ascii=False, indent=4)

    total_companies_processed = len(companies_with_code)
    print(f"Total de dividendos processados: {total_companies_processed}")
    end_time = time.time()
    execution_time_min = (end_time - start_time)/60
    execution_time_secs = (end_time - start_time)%60
    print(f"Tempo de execução DIVIDENDOS: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos")
    tempo_medio = (end_time - start_time) / total_companies_processed
    print(f"Tempo médio: {tempo_medio:.2f} segundos")

    txt_filename = os.path.join("Suporte", "dividendosEmpresas.txt")
    reset_file(txt_filename)
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write(f"Relatório de Dividendos gerado em: {datetime.now().strftime('%d / %m / %Y  %H:%M')}\n\n")
        f.write(f"Tempo de execução: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos.\n\n")
        f.write(f"Total codigos com dividendos: {len(all_dividends)}")

if __name__ == "__main__":
    main()
