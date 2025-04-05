import os
import sys
import subprocess
import time
from datetime import datetime

def run_script(script_name):
    """Execute um script Python e retorne o código de saída"""
    print(f"\n{'='*80}")
    print(f"Executando {script_name}...")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    # Caminho completo para o script
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Scripts", script_name)
    
    # Executa o script
    result = subprocess.run([sys.executable, script_path], capture_output=False)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"\n{'='*80}")
    print(f"Finalizado {script_name}")
    print(f"Tempo de execução: {execution_time/60:.2f} minutos ({execution_time:.2f} segundos)")
    print(f"Status: {'Sucesso' if result.returncode == 0 else 'Falha'}")
    print(f"{'='*80}\n")
    
    return result.returncode

def main():
    # Lista de scripts para executar em ordem
    scripts = [
        "empresas.py",
        "empresasExcelJson.py",
        "dividendosEmpresas.py",
        "empresasJsonFormat.py",
        "bdr.py",
        "bdrExcelJson.py",
        "dividendosBdr.py",
        "bdrJsonFormat.py",
        "etf.py",
        "etfExcelJson.py",
        "etfJsonFormat.py",
        "etfBdr.py",
        "etfBdrExcelJson.py",
        "etfBdrJsonFormat.py",
        "fii.py",
        "fiiExcelJson.py",
        "dividendosFii.py",
        "fiisJsonFormat.py",
        "dividendosauxiliar.py"
    ]
    
    # Cria pasta de logs se não existir
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Suporte")
    os.makedirs(log_dir, exist_ok=True)
    
    # Arquivo de log
    log_file = os.path.join(log_dir, f"execucao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Registra início da execução
    start_time_total = time.time()
    print(f"Iniciando execução de todos os scripts: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Executa cada script
    results = {}
    for script in scripts:
        script_start = time.time()
        exit_code = run_script(script)
        script_end = time.time()
        
        results[script] = {
            "exit_code": exit_code,
            "status": "Sucesso" if exit_code == 0 else "Falha",
            "tempo": script_end - script_start
        }
    
    # Calcula tempo total
    end_time_total = time.time()
    total_time = end_time_total - start_time_total
    
    # Exibe resumo
    print("\n\n")
    print(f"{'='*80}")
    print(f"RESUMO DA EXECUÇÃO")
    print(f"{'='*80}")
    print(f"Data/Hora início: {datetime.fromtimestamp(start_time_total).strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Data/Hora fim: {datetime.fromtimestamp(end_time_total).strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Tempo total: {total_time/60:.2f} minutos ({total_time:.2f} segundos)")
    print("\nResultados:")
    
    for script, result in results.items():
        print(f"  - {script}: {result['status']} ({result['tempo']/60:.2f} min)")
    
    # Grava log
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Execução de scripts - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        f.write(f"Tempo total: {total_time/60:.2f} minutos ({total_time:.2f} segundos)\n\n")
        f.write("Resultados:\n")
        
        for script, result in results.items():
            f.write(f"  - {script}: {result['status']} ({result['tempo']/60:.2f} min)\n")
    
    print(f"\nLog salvo em: {log_file}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()