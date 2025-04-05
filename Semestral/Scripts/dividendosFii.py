import requests
import base64
import json
import time
import os
from datetime import datetime

# Constantes
dividends_url_template = "https://sistemaswebb3-listados.b3.com.br/fundsProxy/fundsCall/GetListedSupplementFunds/{}"
fiiJson = os.path.join("Finais", "fiis.json")
dividendoFiiJson = os.path.join("Finais", "Parcial", "dividendosFii.json")
txt_filename = os.path.join("Suporte", "dividendosFii.txt")

# Funções
def fetch_dividends(cnpj, acronym):
    dividends_payload = base64.b64encode(json.dumps({
        "cnpj": cnpj,
        "identifierFund": acronym,
        "typeFund": 7
    }).encode()).decode()
    
    dividends_url = dividends_url_template.format(dividends_payload)
    
    try:
        response = requests.get(dividends_url)
        response.raise_for_status()  # Lança um erro para status HTTP diferente de 200
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição para CNPJ: {cnpj}, Acronym: {acronym}. Erro: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON para CNPJ: {cnpj}, Acronym: {acronym}. Erro: {str(e)}")
        return None

def format_related_to(related_to):
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

def corrigir_relativo(data):
    for fii in data:
        if 'dividendos' in fii:
            for dividend in fii['dividendos']:
                if 'relativo' in dividend:
                    dividend['relativo'] = format_related_to(dividend['relativo'])
    return data

def reset_file(filename):
    if os.path.exists(filename):
        os.remove(filename)

# Início do script principal
start_time = time.time()

# Carregar detalhes dos FIIs do arquivo JSON
with open(fiiJson, 'r', encoding='utf-8') as fiis_file:
    fiis = json.load(fiis_file)

dividends_data = []

total_fiis = len(fiis)
print(f"Coletando informações de dividendos para cada um dos {total_fiis} FIIs...")
for i, fii in enumerate(fiis, start=1):
    dividends = fetch_dividends(fii['informacoes']['cnpj'], fii['codigoFII'])
    
    if dividends is None:
        print(f"{fii['nomeFII']} : erro na coleta de dividendos")
        continue
    
    cash_dividends = [
        {
            "dataPagamento": dividend["paymentDate"],
            "valor": dividend["rate"],
            "relativo": format_related_to(dividend["relatedTo"]),
            "dataAprovacao": dividend["approvedOn"],
            "tipoDividendo": dividend["label"],
            "ultimoDiaCom": dividend["lastDatePrior"]
        }
        for dividend in dividends.get("cashDividends", [])
    ]
    
    dividends_details = {
        "nomeFII": fii['nomeFII'],
        "quantidade": dividends['quantity'],
        "dividendos": cash_dividends
    }
    dividends_data.append(dividends_details)
    
    print(f"Dividendos: {fii['nomeFII']} - {i} / {total_fiis}")
    
    # Adicionar um intervalo entre as solicitações para evitar sobrecarregar o servidor
    time.sleep(0.5)

# Salvar dados de dividendos no arquivo JSON
with open(dividendoFiiJson, 'w', encoding='utf-8') as dividends_file:
    json.dump(dividends_data, dividends_file, ensure_ascii=False, indent=4)

# Carregar, corrigir e salvar o arquivo JSON novamente
with open(dividendoFiiJson, 'r', encoding='utf-8') as dividends_file:
    dividends_data = json.load(dividends_file)

dividends_data_corrigido = corrigir_relativo(dividends_data)

with open(dividendoFiiJson, 'w', encoding='utf-8') as dividends_file:
    json.dump(dividends_data_corrigido, dividends_file, ensure_ascii=False, indent=4)

# Calcular e exibir o tempo de execução
end_time = time.time()
execution_time_min = (end_time - start_time) / 60
execution_time_secs = (end_time - start_time) % 60
print(f"Tempo de execução: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos")
tempo_medio = (end_time - start_time) / total_fiis
print(f"Tempo médio: {tempo_medio:.2f} segundos")

# Escrever informações no arquivo de texto
reset_file(txt_filename)
with open(txt_filename, 'w', encoding='utf-8') as f:
    f.write(f"Relatório de Dividendos FIIs gerado em: {datetime.now().strftime('%d / %m / %Y  %H:%M')}\n\n")
    f.write(f"Tempo de execução: {execution_time_min:.0f} minutos e {execution_time_secs:.0f} segundos.\n\n")
    f.write(f"Total de FIIs com dividendos: {total_fiis}")

print("Arquivo gerado 'dividendosFii.json'.")
