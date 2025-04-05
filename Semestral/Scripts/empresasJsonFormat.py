import json
import os

# Define paths
input_path = os.path.join("Finais", "Parcial", "empresas.json")
output_path = os.path.join("Finais", "empresas.json")

def format_empresa(empresa):
    """Format a single company entry"""
    # Create formatted entry with original industry and segment
    formatted = {
        "nome": empresa.get("nomeEmpresa", ""),
        "cnpj": empresa.get("informacoes", {}).get("cnpj", ""),
        "industria": empresa.get("industria", ""),
        "segmento": empresa.get("segmento", ""),
        "codigos": []
    }
    
    # Add codes
    for codigo in empresa.get("codigos", []):
        formatted["codigos"].append({
            "codigo": codigo,
            "preco": None,
            "valor mercado": None,
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
            empresas = json.load(f)
        
        # Format each company
        formatted_empresas = [format_empresa(empresa) for empresa in empresas]
        
        # Write output file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_empresas, f, ensure_ascii=False, indent=2)
        
        print(f"Formatação concluída. Arquivo salvo em {output_path}")
        print(f"Total de empresas processadas: {len(formatted_empresas)}")
        
    except Exception as e:
        print(f"Erro ao processar o arquivo: {str(e)}")

if __name__ == "__main__":
    main()