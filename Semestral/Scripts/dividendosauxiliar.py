import json
import os
from datetime import datetime

def reset_file(filename):
    """Remove file if it exists"""
    if os.path.exists(filename):
        os.remove(filename)

def main():
    # Define input and output file paths
    empresas_json = os.path.join("Finais", "Parcial", "empresas.json")
    bdr_json = os.path.join("Finais", "Parcial", "bdr.json")
    fiis_json = os.path.join("Finais", "Parcial", "fiis.json")
    output_json = os.path.join("Finais", "dividendos_auxiliar.json")
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    
    # Initialize result structure
    result = {
        "empresas": [],
        "bdrs": [],
        "fiis": []
    }
    
    # Process empresas.json
    print("Processando empresas.json...")
    try:
        with open(empresas_json, 'r', encoding='utf-8') as f:
            empresas = json.load(f)
            
        for empresa in empresas:
            if "nomeEmpresa" in empresa and "codigoEmpresa" in empresa:
                result["empresas"].append({
                    "nomeEmpresa": empresa["nomeEmpresa"],
                    "codigoEmpresa": empresa["codigoEmpresa"]
                })
        
        print(f"Processadas {len(result['empresas'])} empresas")
    except Exception as e:
        print(f"Erro ao processar empresas.json: {str(e)}")
    
    # Process bdr.json
    print("Processando bdr.json...")
    try:
        with open(bdr_json, 'r', encoding='utf-8') as f:
            bdr_data = json.load(f)
        
        # Process patrocinados
        for bdr in bdr_data.get("bdrs", []):
            if "codigoEmpresa" in bdr:
                result["bdrs"].append({
                    "nomeEmpresa": bdr.get("nomeEmpresa", ""),
                    "codigoEmpresa": bdr["codigoEmpresa"],
                    "tipo": "patrocinado"
                })
        
        # Process não patrocinados
        for bdr in bdr_data.get("bdr_nao_patrocinados", []):
            if "codigoEmpresa" in bdr:
                result["bdrs"].append({
                    "nomeEmpresa": bdr.get("nomeEmpresa", ""),
                    "codigoEmpresa": bdr["codigoEmpresa"],
                    "tipo": "nao_patrocinado"
                })
        
        print(f"Processados {len(result['bdrs'])} BDRs")
    except Exception as e:
        print(f"Erro ao processar bdr.json: {str(e)}")
    
    # Process fiis.json
    print("Processando fiis.json...")
    try:
        with open(fiis_json, 'r', encoding='utf-8') as f:
            fiis = json.load(f)
        
        for fii in fiis:
            if "informacoes" in fii and "cnpj" in fii["informacoes"] and "codigoFII" in fii:
                result["fiis"].append({
                    "nomeFII": fii.get("nomeFII", ""),
                    "codigoFII": fii["codigoFII"],
                    "cnpj": fii["informacoes"]["cnpj"]
                })
        
        print(f"Processados {len(result['fiis'])} FIIs")
    except Exception as e:
        print(f"Erro ao processar fiis.json: {str(e)}")
    
    # Save the consolidated data
    try:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        print(f"Arquivo auxiliar criado com sucesso: {output_json}")
        
        # Create a summary text file
        txt_filename = os.path.join("Suporte", "dividendos_auxiliar.txt")
        os.makedirs(os.path.dirname(txt_filename), exist_ok=True)
        reset_file(txt_filename)
        
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(f"Relatório de Dados Auxiliares para Dividendos gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
            f.write(f"Total de empresas: {len(result['empresas'])}\n")
            f.write(f"Total de BDRs: {len(result['bdrs'])}\n")
            f.write(f"Total de FIIs: {len(result['fiis'])}\n\n")
            f.write("Este arquivo contém os dados necessários para o scraping de dividendos.")
            
        print(f"Arquivo de resumo criado: {txt_filename}")
        
    except Exception as e:
        print(f"Erro ao salvar o arquivo auxiliar: {str(e)}")

if __name__ == "__main__":
    main()