import json
import os

# Define paths
input_path = os.path.join("Finais", "Parcial", "fiis.json")
output_path = os.path.join("Finais", "fiis.json")

def format_fii(fii):
    """Format a single FII entry"""
    # Create formatted entry
    formatted = {
        "nome": fii.get("nomeFII", "").strip(),
        "nomeCompleto": fii.get("nomeCompletoFII", "").strip(),
        "cnpj": fii.get("informacoes", {}).get("cnpj", ""),
        "dataInicio": fii.get("quotaDateApproved", ""),
        "quotaCount": fii.get("quotaCount", ""),
        "codigos": []
    }
    
    # Add codes
    codigos = fii.get("codigo", [])
    if isinstance(codigos, list):
        for codigo in codigos:
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
            fiis = json.load(f)
        
        # Format each FII
        formatted_fiis = [format_fii(fii) for fii in fiis]
        
        # Filter out FIIs without codes
        formatted_fiis_with_codes = [fii for fii in formatted_fiis if fii["codigos"]]
        
        # Write output file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_fiis_with_codes, f, ensure_ascii=False, indent=2)
        
        print(f"Formatação concluída. Arquivo salvo em {output_path}")
        print(f"Total de FIIs processados: {len(formatted_fiis)}")
        print(f"Total de FIIs com códigos: {len(formatted_fiis_with_codes)}")
        
    except Exception as e:
        print(f"Erro ao processar o arquivo: {str(e)}")

if __name__ == "__main__":
    main()