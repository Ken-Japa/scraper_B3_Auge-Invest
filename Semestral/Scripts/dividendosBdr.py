import requests
import base64
import json
import os
import time
from datetime import datetime
import urllib3

urllib3.disable_warnings()

def fetch_dividends(trading_name, max_retries=3):
    params = {
        "issuingCompany": trading_name,
        "language": "pt-br"
    }
    params_str = json.dumps(params)
    encoded_params = base64.b64encode(params_str.encode('utf-8')).decode('utf-8')
    base_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetListedSupplementBDR/"
    url = base_url + encoded_params
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, verify=False)
            response.raise_for_status()
            try:
                return response.json()
            except json.JSONDecodeError:
                print(f"Erro ao decodificar JSON para {trading_name}: {response.text}")
                return None
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
            print(f"\nError fetching dividends for {trading_name}: {str(e)}")
            raise

def reset_file(filename):
    if os.path.exists(filename):
        os.remove(filename)

def main():
    start_time = time.time()
    bdrJson = os.path.join("Finais", "Parcial", "bdr.json")
    with open(bdrJson, 'r', encoding='utf-8') as f:
        bdr_data = json.load(f)
    bdrs = bdr_data.get("bdrs", [])
    bdrs_np = bdr_data.get("bdr_nao_patrocinados", [])
    total_bdrs = len(bdrs) + len(bdrs_np)
    all_dividends = []
    
    for i, bdr in enumerate(bdrs, start=1):
        trading_name = bdr["codigoEmpresa"]
        print(f"Dividendos de {trading_name} - {i} de {total_bdrs}")
        dividendos_data = fetch_dividends(trading_name)
        formatted_dividends = [] 
        if dividendos_data:
            dividendos = dividendos_data[0].get('cashDividends', [])
            formatted_dividends = [
                {
                    "tipo": div["label"],
                    "dataAprovacao": div["approvedOn"],
                    "valor": div["rate"],
                    "dataPagamento": div["paymentDate"],
                    "ultimoDiaCom": div["lastDatePrior"]
                }
                for div in dividendos
            ]
            time.sleep(1.5)
    
        if formatted_dividends:
            company_dividends = {
                "nomeEmpresa": trading_name,
                "dividendos": formatted_dividends
            }
            all_dividends.append(company_dividends)
            
    for i, bdr in enumerate(bdrs_np, start=1):
        trading_name = bdr["codigoEmpresa"]
        print(f"Dividendos de {trading_name} - {i} de {total_bdrs}")
        dividendos_data = fetch_dividends(trading_name)
        formatted_dividends = [] 
        if dividendos_data:
            dividendos = dividendos_data[0].get('cashDividends', [])
            formatted_dividends = [
                {
                    "tipo": div["label"],
                    "dataAprovacao": div["approvedOn"],
                    "valor": div["rate"],
                    "dataPagamento": div["paymentDate"],
                    "ultimoDiaCom": div["lastDatePrior"]
                }
                for div in dividendos
            ]
            time.sleep(1.5)
    
        if formatted_dividends:
            company_dividends = {
                "nomeEmpresa": trading_name,
                "dividendos": formatted_dividends
            }
            all_dividends.append(company_dividends)
        
    dividendosBdrJson = os.path.join("Finais", "dividendosBdr.json")
    with open(dividendosBdrJson, 'w', encoding='utf-8') as f:
        json.dump(all_dividends, f, ensure_ascii=False, indent=4)
        
    print(f"Total de dividendos processados: {total_bdrs}")
    end_time = time.time()
    execution_time_min = (end_time - start_time)/60
    execution_time_secs = (end_time - start_time)%60
    print(f"Tempo de execução DIVIDENDOS: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos")
    tempo_medio = (end_time - start_time) / total_bdrs
    print(f"Tempo médio: {tempo_medio:.2f} segundos")
    
    txt_filename = os.path.join("Suporte", "dividendosBdr.txt")
    reset_file(txt_filename)
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write(f"Relatório de Dividendos gerado em: {datetime.now().strftime('%d / %m / %Y  %H:%M')}\n\n")
        f.write(f"Tempo de execução: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos.\n\n")
        f.write(f"Total codigos com dividendos: {len(all_dividends)}")

if __name__ == "__main__":
    main()