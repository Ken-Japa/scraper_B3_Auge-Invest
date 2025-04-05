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

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Gets the Semanal directory

# Paths
AUXILIAR_JSON = os.path.join(BASE_DIR, "Jsons", "dividendos_auxiliar.json")
EMPRESAS_JSON = os.path.join(BASE_DIR, "Jsons", "dividendosEmpresas.json")
BDR_JSON = os.path.join(BASE_DIR, "Jsons", "dividendosBdr.json")
FII_JSON = os.path.join(BASE_DIR, "Jsons", "dividendosFii.json")
LOG_DIR = os.path.join(BASE_DIR, "Suporte")

# Ensure directories exist
os.makedirs(LOG_DIR, exist_ok=True)

def create_session():
    """Create a session with retry strategy"""
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

def fetch_empresa_dividends(trading_name, session=None):
    """Fetch dividends for a company"""
    if session is None:
        session = create_session()
        
    params = {
        "language": "pt-br",
        "pageNumber": 1,
        "pageSize": 60,
        "tradingName": trading_name
    }
    params_str = json.dumps(params)
    encoded_params = base64.b64encode(params_str.encode('utf-8')).decode('utf-8')
    base_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetListedCashDividends/"
    url = base_url + encoded_params
    
    try:
        response = session.get(url, verify=False)
        response.raise_for_status()
        data = response.json()
        
        # Get all pages
        all_results = data['results']
        total_pages = data['page']['totalPages']
        
        for page_number in range(2, total_pages + 1):
            params["pageNumber"] = page_number
            params_str = json.dumps(params)
            encoded_params = base64.b64encode(params_str.encode('utf-8')).decode('utf-8')
            url = base_url + encoded_params
            
            page_response = session.get(url, verify=False)
            page_response.raise_for_status()
            page_data = page_response.json()
            all_results.extend(page_data['results'])
            time.sleep(0.5)  # Avoid rate limiting
            
        # Format dividends
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
        
        return formatted_dividends
    except Exception as e:
        print(f"Error fetching dividends for company {trading_name}: {e}")
        return []

def fetch_bdr_dividends(trading_name):
    """Fetch dividends for a BDR"""
    params = {
        "issuingCompany": trading_name,
        "language": "pt-br"
    }
    params_str = json.dumps(params)
    encoded_params = base64.b64encode(params_str.encode('utf-8')).decode('utf-8')
    base_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetListedSupplementBDR/"
    url = base_url + encoded_params
    
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return []
            
        dividendos = data[0].get('cashDividends', [])
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
        
        return formatted_dividends
    except Exception as e:
        print(f"Error fetching dividends for BDR {trading_name}: {e}")
        return []

def fetch_fii_dividends(cnpj, acronym, max_retries=3):
    """Fetch dividends for a FII with retry mechanism"""
    dividends_url_template = "https://sistemaswebb3-listados.b3.com.br/fundsProxy/fundsCall/GetListedSupplementFunds/{}"
    
    dividends_payload = base64.b64encode(json.dumps({
        "cnpj": cnpj,
        "identifierFund": acronym,
        "typeFund": 7
    }).encode()).decode()
    
    dividends_url = dividends_url_template.format(dividends_payload)
    
    for attempt in range(max_retries):
        try:
            response = requests.get(dividends_url)
            response.raise_for_status()
            data = response.json()
            
            cash_dividends = [
                {
                    "dataPagamento": dividend["paymentDate"],
                    "valor": dividend["rate"],
                    "relativo": format_related_to(dividend["relatedTo"]),
                    "dataAprovacao": dividend["approvedOn"],
                    "tipoDividendo": dividend["label"],
                    "ultimoDiaCom": dividend["lastDatePrior"]
                }
                for dividend in data.get("cashDividends", [])
            ]
            
            return {
                "quantidade": data.get('quantity', ''),
                "dividendos": cash_dividends
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2, 4, 6 seconds
                print(f"  ⚠ Rate limit hit, waiting {wait_time} seconds before retry ({attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                print(f"Error fetching dividends for FII {acronym}: {e}")
                return {"quantidade": "", "dividendos": []}
        except Exception as e:
            print(f"Error fetching dividends for FII {acronym}: {e}")
            return {"quantidade": "", "dividendos": []}
    
    print(f"  ✗ Failed after {max_retries} retries")
    return {"quantidade": "", "dividendos": []}

def format_related_to(related_to):
    """Format the 'relativo' field for FII dividends"""
    month_map = {
        "janeiro": "01", "fevereiro": "02", "março": "03", "abril": "04",
        "maio": "05", "junho": "06", "julho": "07", "agosto": "08",
        "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12",
        "jan": "01", "fev": "02", "mar": "03", "abr": "04",
        "mai": "05", "jun": "06", "jul": "07", "ago": "08",
        "set": "09", "out": "10", "nov": "11", "dez": "12"
    }

    related_to_lower = related_to.lower().strip()

    # Corrigir "Nº semestre/AAAA/AAAA" para "Nº semestre/AAAA"
    if any(sem in related_to_lower for sem in ['1º sem', '2º sem', '3º sem', '4º sem', '1º semestre', '2º semestre', '3º semestre', '4º semestre']):
        parts = related_to_lower.split('/')
        if len(parts) == 3:
            return f"{parts[0]}/{parts[1]}"
        return related_to_lower

    # Corrigir "Nº trimestre/AAAA/AAAA" para "Nº trimestre/AAAA"
    if any(trim in related_to_lower for trim in ['1º trim', '2º trim', '3º trim', '4º trim', '1º trimestre', '2º trimestre', '3º trimestre', '4º trimestre']):
        parts = related_to_lower.split('/')
        if len(parts) == 3:
            return f"{parts[0]}/{parts[1]}"
        return related_to_lower

    # Corrigir "28/03/2024/2024" para "28/03/2024"
    if related_to_lower.count('/') == 3:
        parts = related_to_lower.split('/')
        return f"{parts[0]}/{parts[1]}/{parts[2]}"

    # Corrigir mês/ano
    for month in month_map:
        if month in related_to_lower:
            parts = related_to_lower.split('/')
            month_number = month_map[month]
            return f"{month_number}/{parts[1]}" if len(parts) > 1 else related_to_lower

    return related_to

def load_json(file_path, default=None):
    """Load JSON file or return default if file doesn't exist"""
    if default is None:
        default = []
        
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return default
    return default

def save_json(file_path, data):
    """Save data to JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Error saving {file_path}: {e}")
        return False

def update_empresas_dividends():
    """Update dividends for companies"""
    print("\n=== Atualizando dividendos de Empresas ===")
    start_time = time.time()
    
    # Load data
    auxiliar_data = load_json(AUXILIAR_JSON)
    existing_dividends = load_json(EMPRESAS_JSON)
    
    # Create lookup for existing dividends
    existing_lookup = {item["nomeEmpresa"]: item for item in existing_dividends}
    
    # Create session for requests
    session = create_session()
    
    # Track statistics
    total = len(auxiliar_data.get("empresas", []))
    processed = 0
    added = 0
    updated = 0
    errors = 0
    
    # Process each company
    for i, empresa in enumerate(auxiliar_data.get("empresas", []), 1):
        nome_empresa = empresa.get("nomeEmpresa")
        
        print(f"Processando {nome_empresa} ({i}/{total})")
        
        try:
            # Fetch dividends
            new_dividends = fetch_empresa_dividends(nome_empresa, session)
            
            if not new_dividends:                
                processed += 1
                continue
                
            # Check if company already exists
            if nome_empresa in existing_lookup:
                # Get existing dividends
                existing_item = existing_lookup[nome_empresa]
                existing_divs = existing_item.get("dividendos", [])
                
                # Create a set of existing dividend keys for comparison
                existing_keys = {f"{div.get('dataAprovacao')}|{div.get('tipoDividendo')}|{div.get('tipo')}" 
                                for div in existing_divs}
                
                # Add only new dividends
                added_count = 0
                for div in new_dividends:
                    div_key = f"{div.get('dataAprovacao')}|{div.get('tipoDividendo')}|{div.get('tipo')}"
                    if div_key not in existing_keys:
                        existing_divs.append(div)
                        added_count += 1
                
                if added_count > 0:
                    print(f"  ✓ Adicionados {added_count} novos dividendos")
                    updated += 1
                
            else:
                # Add new company with dividends
                existing_dividends.append({
                    "nomeEmpresa": nome_empresa,
                    "dividendos": new_dividends
                })
                added += 1
                print(f"  ✓ Adicionados {len(new_dividends)} dividendos")
                
            processed += 1
            
            # Sleep to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"  ✗ Erro: {e}")
            errors += 1
            time.sleep(5)  # Longer sleep on error
    
    # Save updated data
    if added > 0 or updated > 0:
        save_json(EMPRESAS_JSON, existing_dividends)
        
    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"\nEstatísticas de Empresas:")
    print(f"  Total processado: {processed}/{total}")
    print(f"  Novas empresas: {added}")
    print(f"  Empresas atualizadas: {updated}")
    print(f"  Erros: {errors}")
    print(f"  Tempo de execução: {execution_time/60:.2f} minutos")
    
    return {
        "processed": processed,
        "added": added,
        "updated": updated,
        "errors": errors,
        "execution_time": execution_time
    }

def update_bdr_dividends():
    """Update dividends for BDRs"""
    print("\n=== Atualizando dividendos de BDRs ===")
    start_time = time.time()
    
    # Load data
    auxiliar_data = load_json(AUXILIAR_JSON)
    existing_dividends = load_json(BDR_JSON)
    
    # Create lookup for existing dividends
    existing_lookup = {item["nomeEmpresa"]: item for item in existing_dividends}
    
    # Track statistics
    total = len(auxiliar_data.get("bdrs", []))
    processed = 0
    added = 0
    updated = 0
    errors = 0
    
    # Process each BDR
    for i, bdr in enumerate(auxiliar_data.get("bdrs", []), 1):
        codigo_empresa = bdr.get("codigoEmpresa")
        
        print(f"Processando {codigo_empresa} ({i}/{total})")
        
        try:
            # Fetch dividends
            new_dividends = fetch_bdr_dividends(codigo_empresa)
            
            if not new_dividends:                
                processed += 1
                continue
                
            # Check if BDR already exists
            if codigo_empresa in existing_lookup:
                # Get existing dividends
                existing_item = existing_lookup[codigo_empresa]
                existing_divs = existing_item.get("dividendos", [])
                
                # Create a set of existing dividend keys for comparison
                existing_keys = {f"{div.get('dataAprovacao')}|{div.get('tipo')}" 
                                for div in existing_divs}
                
                # Add only new dividends
                added_count = 0
                for div in new_dividends:
                    div_key = f"{div.get('dataAprovacao')}|{div.get('tipo')}"
                    if div_key not in existing_keys:
                        existing_divs.append(div)
                        added_count += 1
                
                if added_count > 0:
                    print(f"  ✓ Adicionados {added_count} novos dividendos")
                    updated += 1
                
            else:
                # Add new BDR with dividends
                existing_dividends.append({
                    "nomeEmpresa": codigo_empresa,
                    "dividendos": new_dividends
                })
                added += 1
                print(f"  ✓ Adicionados {len(new_dividends)} dividendos")
                
            processed += 1
            
            # Sleep to avoid rate limiting
            time.sleep(1.5)
            
        except Exception as e:
            print(f"  ✗ Erro: {e}")
            errors += 1
            time.sleep(5)  # Longer sleep on error
    
    # Save updated data
    if added > 0 or updated > 0:
        save_json(BDR_JSON, existing_dividends)
        
    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"\nEstatísticas de BDRs:")
    print(f"  Total processado: {processed}/{total}")
    print(f"  Novos BDRs: {added}")
    print(f"  BDRs atualizados: {updated}")
    print(f"  Erros: {errors}")
    print(f"  Tempo de execução: {execution_time/60:.2f} minutos")
    
    return {
        "processed": processed,
        "added": added,
        "updated": updated,
        "errors": errors,
        "execution_time": execution_time
    }

def update_fii_dividends():
    """Update dividends for FIIs"""
    print("\n=== Atualizando dividendos de FIIs ===")
    start_time = time.time()
    
    # Load data
    auxiliar_data = load_json(AUXILIAR_JSON)
    existing_dividends = load_json(FII_JSON)
    
    # Create lookup for existing dividends
    existing_lookup = {item["nomeFII"]: item for item in existing_dividends}
    
    # Track statistics
    total = len(auxiliar_data.get("fiis", []))
    processed = 0
    added = 0
    updated = 0
    errors = 0
    
    # Process each FII
    for i, fii in enumerate(auxiliar_data.get("fiis", []), 1):
        nome_fii = fii.get("nomeFII")
        codigo_fii = fii.get("codigoFII")
        cnpj = fii.get("cnpj")
        
        print(f"Processando {nome_fii} ({i}/{total})")
        
        try:
            # Fetch dividends
            result = fetch_fii_dividends(cnpj, codigo_fii)
            new_dividends = result["dividendos"]
            
            if not new_dividends:
                processed += 1
                continue
                
            # Check if FII already exists
            if nome_fii in existing_lookup:
                # Get existing dividends
                existing_item = existing_lookup[nome_fii]
                existing_divs = existing_item.get("dividendos", [])
                
                # Create a set of existing dividend keys for comparison
                existing_keys = {f"{div.get('dataAprovacao')}|{div.get('tipoDividendo')}|{div.get('dataPagamento')}" 
                                for div in existing_divs}
                
                # Add only new dividends
                added_count = 0
                for div in new_dividends:
                    div_key = f"{div.get('dataAprovacao')}|{div.get('tipoDividendo')}|{div.get('dataPagamento')}"
                    if div_key not in existing_keys:
                        existing_divs.append(div)
                        added_count += 1
                
                if added_count > 0:
                    print(f"  ✓ Adicionados {added_count} novos dividendos")
                    updated += 1
                
                    
                # Update quantidade if needed
                if result["quantidade"] and result["quantidade"] != existing_item.get("quantidade", ""):
                    existing_item["quantidade"] = result["quantidade"]
                    if added_count == 0:  # Only count as update if we didn't already count it
                        updated += 1
                        print(f"  ✓ Quantidade atualizada: {result['quantidade']}")
            else:
                # Add new FII with dividends
                existing_dividends.append({
                    "nomeFII": nome_fii,
                    "quantidade": result["quantidade"],
                    "dividendos": new_dividends
                })
                added += 1
                print(f"  ✓ Adicionados {len(new_dividends)} dividendos")
                
            processed += 1
            
            # Sleep to avoid rate limiting - increased from 0.5 to 1.5 seconds
            time.sleep(1.5)
            
        except Exception as e:
            print(f"  ✗ Erro: {e}")
            errors += 1
            time.sleep(5)  # Longer sleep on error
    
    # Save updated data
    if added > 0 or updated > 0:
        save_json(FII_JSON, existing_dividends)
        
    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"\nEstatísticas de FIIs:")
    print(f"  Total processado: {processed}/{total}")
    print(f"  Novos FIIs: {added}")
    print(f"  FIIs atualizados: {updated}")
    print(f"  Erros: {errors}")
    print(f"  Tempo de execução: {execution_time/60:.2f} minutos")
    
    return {
        "processed": processed,
        "added": added,
        "updated": updated,
        "errors": errors,
        "execution_time": execution_time
    }

def main():
    """Main function"""
    print("=== Iniciando atualização de dividendos ===")
    start_time = time.time()
    
    # Check if auxiliar file exists
    if not os.path.exists(AUXILIAR_JSON):
        print(f"Erro: Arquivo auxiliar {AUXILIAR_JSON} não encontrado")
        return
    
    # Update dividends
    empresas_stats = update_empresas_dividends()
    bdr_stats = update_bdr_dividends()
    fii_stats = update_fii_dividends()
    
    # Calculate total execution time
    end_time = time.time()
    total_time = end_time - start_time
    
    # Create log file
    log_file = os.path.join(LOG_DIR, f"dividendos_atualizacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Relatório de Atualização de Dividendos - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        f.write(f"Tempo total de execução: {total_time/60:.2f} minutos ({total_time:.2f} segundos)\n\n")
        
        f.write("=== Empresas ===\n")
        f.write(f"Processados: {empresas_stats['processed']}\n")
        f.write(f"Novas empresas: {empresas_stats['added']}\n")
        f.write(f"Empresas atualizadas: {empresas_stats['updated']}\n")
        f.write(f"Erros: {empresas_stats['errors']}\n")
        f.write(f"Tempo: {empresas_stats['execution_time']/60:.2f} minutos\n\n")
        
        f.write("=== BDRs ===\n")
        f.write(f"Processados: {bdr_stats['processed']}\n")
        f.write(f"Novos BDRs: {bdr_stats['added']}\n")
        f.write(f"BDRs atualizados: {bdr_stats['updated']}\n")
        f.write(f"Erros: {bdr_stats['errors']}\n")
        f.write(f"Tempo: {bdr_stats['execution_time']/60:.2f} minutos\n\n")
        
        f.write("=== FIIs ===\n")
        f.write(f"Processados: {fii_stats['processed']}\n")
        f.write(f"Novos FIIs: {fii_stats['added']}\n")
        f.write(f"FIIs atualizados: {fii_stats['updated']}\n")
        f.write(f"Erros: {fii_stats['errors']}\n")
        f.write(f"Tempo: {fii_stats['execution_time']/60:.2f} minutos\n")
    
    print(f"\n=== Atualização concluída ===")
    print(f"Tempo total: {total_time/60:.2f} minutos")
    print(f"Log salvo em: {log_file}")

if __name__ == "__main__":
    main()