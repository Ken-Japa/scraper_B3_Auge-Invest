# Inicio-Bd
Repositório com as funções iniciais para criar o Banco de Dados

O projeto foi dividido em três partes, de acordo com a necessidade de rodagem:

1. Criação do Banco de Dados - Pasta Semestral
2. Atualização diária do Banco de Dados - Pasta Diário
3. Atualização semanal do Banco de Dados - Pasta Semanal

## Semestral
A pasta Semestral contém os scripts para criação do Banco de Dados, criação dos jsons e criação dos arquivos Excel.

### Pastas e Arquivos:
Essa parte do projeto pode ser ativado com o script "run_all_semestral.py". (por conta disso existe uma duplicidade de pastas para quando se rodar esse script ou os scripts individualmente encontrados na pasta "Script").

#### Scripts:
Aqui temos os scripts para coletar no site da B3 os dados das Empresas, Bdr, Etf, EtfBdr e Fii.

Esses scripts vem como um grupo de script, primeiro o ativo.py que faz de fato o scrap.
Depois o script ativoExcelJson.py que cria os arquivos json e os arquivos Excel (faz uma verificação de quais códigos estão retornando valores válidos) (arquivo para preço e histórico) (pasta "Excel").
Finalmente o script ativoJsonFormat.py que irá formatar os arquivos json para que fiquem prontos para serem inseridos no banco de dados.

Cria-se na pasta "Suporte" dados sobre o processamento e/ou problema dos scripts. 
Os jsons gerados estarão na pasta "Finais" que são os arquivos prontos, dentro dela existe a pasta "Parcial" que foram os .json gerados durante o processo e a pasta "Copiar" que contém todos os códigos dos ativos feito para facilitar a criação do arquivo no drive Google Sheets.

Também existem scripts para coleta os dividendos de Empresas, Bdr, e Fii. Os scripts são como dividendosativos.py

Existe também um script "dividendoauxiliar.py" que cria um arquivo "dividendos_auxiliar.json" que servirá para auxiliar na atualização semanal dos dividendos.

### Necessidades:

Precisamos ainda criar os scripts para alguns ativos como Selic, Inflação, Tesouro Direto, Moedas e Commodities (talvez outros mais). Talves esses scripts estejam na pasta Semanal.

É preciso verificar se os códigos removidos através do retorno da verificação no Excel estão sendo removidos corretamente.

Estudar a criação do arquivo Excel para o histórico de preços da Empresa. Penso em desmembrar o arquivo através dos segmentos/industrias das empresas, para reduzir o tamanho do arquivo. Esse script poderia ser só para criar o arquivo estático inicial do Banco de Dados. Depois poderiamos estudar para que na atualização diária dos preços, seja incluída uma função que atualize o histórico.

## Diário
A pasta Diário contém os scripts para atualização diária do Banco de Dados, inserção de dados na tabela de histórico e atualização dos dados na tabela de dados.

### Pastas e Arquivos:
Essa parte do projeto pode ser ativado com o script "run_all_diario.py".

#### Scripts:
Aqui temos os scripts para atualizar os json com os preços das Empresas, Bdr, Etf, EtfBdr e Fii. (ativoPreco.js)

Temos o "empresasSumario.js" que cria um sumário das empresas com os dados mais atualizados.

A pasta "Jsons" contém os arquivos json iniciais, sem valores ainda, como se fossem os dados de entrada.
Na pasta "Finais" contém os arquivos json com os valores atualizados. Caso já existam os arquivos atualizam esses jsons (úteis para atualizar as props de "precoAnterior" e "variacao").

Também existe a pasta "config" que contém a configuração para acessar a nuvem do Drive.

### Necessidades:

Precisamos ainda criar os scripts para atualizar os históricos.
Precisamos do script para atualizar os preços dos derivativos.

## Semanal
A pasta Semanal contém os scripts para atualização semanal do Banco de Dados. Por enquanto, tratamos apenas de atualizar os dividendos. 

Segue uma estrutura semelhante do projeto.

### Necessidades:

Pegar os derivativos novos.


## Dicionário
Adicionei a pasta "Dicionário" com arquivos estáticos contendo o(s) dicionário(s) que estou criando para melhorar as informações no FrontEnd.

## Exemplos técnicos e lembretes
Para que as biblotecas não sejam adicionadas no Git, o python necessita de um ambiente virtual (venv\Scripts\activate) (deactivate). Depois de instalar as bibliotecas (pip freeze > requirements.txt)
Navegar até a pasta e no terminal caso seja python: "python run_all_semestral.py". Caso seja javascript: "node empresasPreco.js".

O arquivo historicoEmpresas foi adicionado ao gitignore (Diario/Finais/empresasHistorico.json)

### Bibliotecas utilizadas:
pip install requests urllib3 openpyxl xlwings requests urllib3
npm install googleapis