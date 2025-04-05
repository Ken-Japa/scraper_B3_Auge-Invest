import json
import os

# Define paths
input_path = os.path.join("Finais","Parcial", "bdr.json")
output_path = os.path.join("Finais", "bdrs.json")

def format_bdr(bdr, is_sponsored=True):
    """Format a single BDR entry"""
    # Create formatted entry with original industry and segment
    formatted = {
        "nome": bdr.get("nomeEmpresa", ""),
        "cnpj": bdr.get("informações", {}).get("cnpj", ""),
        "industria": bdr.get("industria", "Não Classificados") if is_sponsored else "Não Classificados",
        "segmento": bdr.get("segmento", "Não Classificados") if is_sponsored else "Não Classificados",
        "tipoBDR": bdr.get("tipoBDR", ""),
        "codigos": []
    }
    
    # Add code
    codigo = bdr.get("codigo")
    if codigo:
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
            bdr_data = json.load(f)
        
        # Format sponsored BDRs
        formatted_bdrs = []
        if "bdrs" in bdr_data:
            formatted_bdrs.extend([format_bdr(bdr, True) for bdr in bdr_data["bdrs"]])
        
        # Format non-sponsored BDRs
        if "bdr_nao_patrocinados" in bdr_data:
            formatted_bdrs.extend([format_bdr(bdr, False) for bdr in bdr_data["bdr_nao_patrocinados"]])
        
        # Write output file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_bdrs, f, ensure_ascii=False, indent=2)
        
        print(f"Formatação concluída. Arquivo salvo em {output_path}")
        print(f"Total de BDRs processadas: {len(formatted_bdrs)}")
        
    except Exception as e:
        print(f"Erro ao processar o arquivo: {str(e)}")

if __name__ == "__main__":
    main()