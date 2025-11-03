# Scraper B3 & Análise de Investimentos

Este projeto é uma solução abrangente para a coleta, processamento e análise de dados financeiros da B3 (Bolsa de Valores do Brasil). São sistemas robustos de ponta a ponta para extração de dados, engenharia de dados e preparação para análise de investimentos. O objetivo principal é fornecer dados atualizados e estruturados para auxiliar na tomada de decisões de investimento.

## Visão Geral do Projeto

O projeto é estruturado em três módulos principais, cada um com uma frequência de execução e propósito distintos, refletindo uma abordagem modular e escalável para o gerenciamento de dados. Essa divisão permite otimizar o uso de recursos e garantir a atualização contínua e precisa das informações financeiras.

1. **Módulo Semestral:** Responsável pela criação inicial do banco de dados, coleta de dados históricos e geração de arquivos para análise. Lida com grandes volumes de dados e processos que não exigem atualização frequente.
2. **Módulo Diário:** Focado na atualização diária do banco de dados, inserção de novos dados históricos e atualização de dados existentes. Garante que as informações de mercado estejam sempre atualizadas.
3. **Módulo Semanal:** Dedicado à atualização semanal de dados específicos, como dividendos. Complementa os módulos diário e semestral, garantindo a integridade de dados com ciclos de atualização menos frequentes.

Essa arquitetura demonstra a capacidade de projetar e implementar soluções que atendem a diferentes requisitos de frequência de atualização e volume de dados, utilizando automação e orquestração para manter a consistência e a relevância das informações.

## Módulos Detalhados

### 1. Módulo Semestral

Este módulo é a base do sistema, responsável pela coleta inicial de dados históricos e pela estruturação para o banco de dados. Ele abrange desde o web scraping até a formatação final dos dados, demonstrando proficiência em:

- **Web Scraping e Coleta de Dados:** Utilização de bibliotecas Python como `requests` e `urllib3` para interagir com o site da B3, extraindo dados de Empresas, BDRs, ETFs, ETFs BDRs e FIIs. Isso inclui a manipulação de estruturas HTML e JSON para obter informações cruciais.
- **Processamento e Transformação de Dados (ETL):** Implementação de scripts (`ativoExcelJson.py`, `ativoJsonFormat.py`) para limpar, transformar e validar os dados brutos. Isso envolve a criação de arquivos JSON e Excel (`openpyxl`, `xlwings`) para diferentes finalidades, como a verificação de códigos de ativos válidos e a preparação para inserção no banco de dados.
- **Gerenciamento de Arquivos e Estruturação:** Organização dos dados em pastas como `Finais` (dados prontos), `Parcial` (dados intermediários) e `Copiar` (para integração com outras ferramentas como Google Sheets), evidenciando a preocupação com a organização e o fluxo de dados.
- **Coleta de Dados Específicos:** Desenvolvimento de scripts dedicados para a coleta de dividendos de Empresas, BDRs e FIIs (`dividendosativos.py`), incluindo a criação de arquivos auxiliares (`dividendoauxiliar.py`) para otimizar processos futuros.
- **Logging e Monitoramento:** Geração de logs de processamento e problemas na pasta `Suporte`, o que demonstra a prática de monitoramento e depuração de processos de longa duração.

### 2. Módulo Diário

Este módulo é crucial para manter a base de dados atualizada com as informações mais recentes do mercado. Ele demonstra competências em:

- **Automação e Agendamento:** O script `run_all_diario.py` orquestra a execução diária dos processos, garantindo que os dados de preços e sumários sejam atualizados automaticamente. Isso reflete a capacidade de projetar e implementar rotinas de automação eficientes.
- **Atualização Incremental de Dados:** Scripts como `ativoPreco.js` atualizam os arquivos JSON com os preços mais recentes de Empresas, BDRs, ETFs, ETFs BDRs e FIIs. A lógica de atualização inclui a manipulação de propriedades como `precoAnterior` e `variacao`, demonstrando a habilidade em lidar com a dinâmica de dados financeiros.
- **Processamento de Dados em Tempo Quase Real:** O `empresasSumario.js` cria um sumário atualizado das empresas, consolidando as informações mais relevantes para análise rápida. Isso evidencia a capacidade de processar e apresentar dados de forma eficiente.
- **Integração com Serviços em Nuvem:** A pasta `config` contém as configurações para acessar a nuvem do Google Drive, indicando experiência com integração de APIs e serviços de terceiros para armazenamento e compartilhamento de dados.
- **Desenvolvimento Multi-linguagem:** A utilização de scripts JavaScript (Node.js) para tarefas específicas de atualização de preços e sumários, em conjunto com Python, demonstra flexibilidade e proficiência em diferentes ambientes de desenvolvimento.

### 3. Módulo Semanal

O módulo Semanal complementa os demais, focando em atualizações de dados que não exigem frequência diária, como os dividendos. Ele destaca a capacidade de:

- **Lógica de Negócio Complexa:** A coleta e atualização de dados de dividendos envolvem regras de negócio específicas e a necessidade de garantir a precisão das informações ao longo do tempo. Este módulo demonstra a habilidade em traduzir requisitos de negócio em soluções técnicas robustas.
- **Consistência e Reutilização de Código:** A estrutura deste módulo se assemelha aos demais, promovendo a consistência no design e a reutilização de componentes, o que é fundamental para a manutenção e escalabilidade do projeto.
- **Gerenciamento de Ciclos de Vida de Dados:** A gestão de dados com diferentes ciclos de atualização (diário, semanal, semestral) evidencia a compreensão de estratégias de gerenciamento de dados e a capacidade de projetar sistemas que atendam a essas necessidades.

## Dicionário de Dados

A pasta `Dicionario` contém arquivos estáticos que servem como dicionários de dados, essenciais para padronizar e enriquecer as informações consumidas por outras aplicações, como um FrontEnd. Esta seção demonstra a capacidade de:

- **Modelagem de Dados:** Criação e manutenção de estruturas de dados (`.ts` - TypeScript, se aplicável) para garantir a consistência e a clareza das informações.
- **Integração e Consumo de Dados:** Facilita a integração com interfaces de usuário ou outros serviços, assegurando que os dados sejam interpretados corretamente e apresentados de forma significativa.
- **Boas Práticas de Engenharia de Software:** A separação de dados de configuração e metadados em um dicionário dedicado promove a modularidade e a manutenibilidade do sistema.

## Tecnologias e Ferramentas Utilizadas

Este projeto foi desenvolvido utilizando uma variedade de tecnologias e ferramentas, demonstrando proficiência em um ecossistema de desenvolvimento moderno e eficiente:

- **Linguagens de Programação:**
  - Python
  - JavaScript (Node.js)
- **Bibliotecas Python:**
  - `requests`: Para requisições HTTP e web scraping.
  - `urllib3`: Gerenciamento de pools de conexão HTTP.
  - `openpyxl`: Leitura e escrita de arquivos Excel (`.xlsx`).
  - `xlwings`: Automação e integração entre Python e Excel.
- **Bibliotecas JavaScript:**
  - `googleapis`: Para integração com serviços Google, como Google Drive/Sheets.
- **Ferramentas e Conceitos:**
  - **Git & GitHub:** Controle de versão e colaboração, incluindo a manipulação avançada de histórico com `git filter-repo`.
  - **Web Scraping:** Técnicas para extração de dados de websites.
  - **Automação e Orquestração:** Implementação de rotinas automatizadas para coleta e processamento de dados.
  - **Processamento e Transformação de Dados (ETL):** Habilidades em limpeza, validação e estruturação de dados.
  - **Integração de APIs:** Conexão com serviços externos e plataformas em nuvem.
  - **Estrutura de Dados:** Design e implementação de estruturas para otimização e padronização de informações.
  - **Gerenciamento de Dependências:** Utilização de `pip` e `npm` para gerenciar as bibliotecas do projeto.

## Instruções de Configuração

Para configurar e executar este projeto localmente, siga os passos abaixo:

### Pré-requisitos

Certifique-se de ter as seguintes ferramentas instaladas:

- Python 3.x
- Node.js e npm
- Git

### 1. Clonar o Repositório

```bash
git clone https://github.com/Ken-Japa/scraper_B3_Auge-Invest.git
cd scraper_B3_Auge-Invest
```

### 2. Configuração do Ambiente Python

Crie e ative um ambiente virtual Python:

```bash
python -m venv venv
# No Windows
.\venv\Scripts\activate
# No macOS/Linux
source venv/bin/activate
```

Instale as dependências Python:

```bash
pip install -r requirements.txt
```

### 3. Configuração do Ambiente Node.js

Instale as dependências Node.js:

```bash
npm install
```

### 4. Configuração das Credenciais do Google Cloud

Este projeto interage com o Google Drive. Você precisará configurar suas credenciais:

1. Crie um projeto no [Google Cloud Console](https://console.cloud.google.com/).
2. Habilite a Google Drive API.
3. Crie uma conta de serviço e gere um arquivo `service-account.json`.
4. Salve este arquivo em `Diario/config/service-account.json`.

   **Atenção:** Este arquivo contém informações sensíveis e já está configurado para ser ignorado pelo Git através do `.gitignore` para sua segurança.

### 5. Executando os Scripts

Consulte as pastas `Semestral`, `Diario` e `Semanal` para os scripts específicos e suas instruções de execução.

## Próximos Passos e Melhorias Futuras

Este projeto está em constante evolução. Algumas das melhorias planejadas incluem:

- **Otimização de Performance:** Refatorar scripts para processamento mais rápido e eficiente de grandes volumes de dados.
- **Expansão de Fontes de Dados:** Integrar novas fontes de dados para enriquecer a análise de investimentos.
- **Interface de Usuário (UI):** Desenvolver uma interface gráfica para facilitar a interação com os dados e a visualização dos resultados.
- **Alertas e Notificações:** Implementar um sistema de alertas para eventos importantes do mercado ou alterações significativas nos dados.
- **Testes Automatizados:** Adicionar testes unitários e de integração para garantir a robustez e a confiabilidade do código.

## Contato

Para dúvidas, sugestões ou oportunidades de colaboração, sinta-se à vontade para entrar em contato:

- **Seu Nome:** Ken Japa
- **LinkedIn:** [Seu Perfil no LinkedIn](https://www.linkedin.com/in/ken-japa/)
- **GitHub:** [Seu Perfil no GitHub](https://github.com/Ken-Japa)
