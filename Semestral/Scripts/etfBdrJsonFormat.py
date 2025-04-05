import json
import os

# Define paths
input_path = os.path.join("Finais", "Parcial", "etfBdr.json")
output_path = os.path.join("Finais", "etfBdr.json")

def format_etf_bdr(etf_bdr):
    """Format a single ETF BDR entry"""
    # Create formatted entry
    formatted = {
        "nome": etf_bdr.get("nomeETF", ""),
        "nomeCompleto": etf_bdr.get("nomeCompletoETF", ""),
        "codigos": []
    }
    
    # Add code if it exists
    codigo = etf_bdr.get("codigo")
    if codigo and codigo.strip():
        formatted["codigos"].append({
            "codigo": codigo,
            "preco": None,
            "precoAnterior": None,
            "variacao": None
        })
    
    return formatted

def main():
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Read input file
        with open(input_path, 'r', encoding='utf-8') as f:
            etf_bdrs = json.load(f)
        
        # Format each ETF BDR
        formatted_etf_bdrs = [format_etf_bdr(etf_bdr) for etf_bdr in etf_bdrs]
        
        # Filter out ETF BDRs without codes
        formatted_etf_bdrs_with_codes = [etf_bdr for etf_bdr in formatted_etf_bdrs if etf_bdr["codigos"]]
        
        # Write output file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_etf_bdrs_with_codes, f, ensure_ascii=False, indent=2)
        
        print(f"Formatação concluída. Arquivo salvo em {output_path}")
        print(f"Total de ETF BDRs processados: {len(formatted_etf_bdrs)}")
        print(f"Total de ETF BDRs com códigos: {len(formatted_etf_bdrs_with_codes)}")
        
    except Exception as e:
        print(f"Erro ao processar o arquivo: {str(e)}")

if __name__ == "__main__":
    main()