import json
import os

# Define paths
input_path = os.path.join("Finais", "Parcial", "etf.json")
output_path = os.path.join("Finais", "etf.json")

def format_etf(etf):
    """Format a single ETF entry"""
    # Create formatted entry
    formatted = {
        "nome": etf.get("nomeETF", ""),
        "nomeCompleto": etf.get("nomeCompletoETF", ""),
        "cnpj": etf.get("informacoes", {}).get("cnpj", ""),
        "codigos": []
    }
    
    # Add code
    codigo = etf.get("codigo")
    if codigo:
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
            etfs = json.load(f)
        
        # Format each ETF
        formatted_etfs = [format_etf(etf) for etf in etfs]
        
        # Write output file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_etfs, f, ensure_ascii=False, indent=2)
        
        print(f"Formatação concluída. Arquivo salvo em {output_path}")
        print(f"Total de ETFs processados: {len(formatted_etfs)}")
        
    except Exception as e:
        print(f"Erro ao processar o arquivo: {str(e)}")

if __name__ == "__main__":
    main()