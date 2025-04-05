const fs = require("fs").promises;

async function gerarSumario(caminhoArquivoJson) {
  try {
    const json = JSON.parse(await fs.readFile(caminhoArquivoJson, "utf-8"));

    const sumario = {};
    let valorMercadoTotalGeral = 0;
    let qtdEmpresasTotal = 0;
    let qtdSegmentosTotal = 0;

    const industriasSegmentos = {};

    for (const empresa of json) {
      const industria = empresa.industria;
      const segmento = empresa.segmento;

      if (!industriasSegmentos[industria]) {
        industriasSegmentos[industria] = {
          totalEmpresas: 0,
          segmentos: {},
        };
      }

      industriasSegmentos[industria].totalEmpresas++;

      if (!industriasSegmentos[industria].segmentos[segmento]) {
        industriasSegmentos[industria].segmentos[segmento] = {
          totalEmpresas: 0,
        };
      }

      industriasSegmentos[industria].segmentos[segmento].totalEmpresas++;

      if (!sumario[industria]) {
        sumario[industria] = {
          valorMercadoTotal: 0,
          empresas: 0,
          segmentos: {},
          qtdSegmentos: 0,
        };
      }

      if (!sumario[industria].segmentos[segmento]) {
        sumario[industria].segmentos[segmento] = {
          valorMercado: 0,
          empresas: 0,
          empresasDetalhes: [],
        };
        sumario[industria].qtdSegmentos += 1;
        qtdSegmentosTotal += 1;
      }

      let empresaTemValorMercado = false;
      let valorMercadoEmpresa = 0;

      // Extrair códigos, preços e variações para incluir no sumário
      const codigosInfo = [];
      
      if (empresa.codigos && empresa.codigos.length > 0) {
        for (const codigo of empresa.codigos) {
          // Adicionar informações do código ao array codigosInfo apenas se o preço não for null
          if (codigo.codigo && codigo.preco !== null && codigo.preco !== undefined) {
            codigosInfo.push({
              codigo: codigo.codigo,
              preco: codigo.preco,
              variacao: codigo.variacao
            });
          }
          
          if (codigo["valor mercado"]) {
            let valorMercado;

            if (typeof codigo["valor mercado"] === "string") {
              valorMercado = parseFloat(
                codigo["valor mercado"]
                  .replace(/[^\d,.-]/g, "")
                  .replace(/\./g, "")
                  .replace(/,/g, ".")
              );
            } else {
              valorMercado = parseFloat(codigo["valor mercado"]);
            }

            if (!isNaN(valorMercado)) {
              valorMercadoEmpresa += valorMercado;
              empresaTemValorMercado = true;
            }
          }
        }
      }

      if (empresaTemValorMercado) {
        sumario[industria].valorMercadoTotal += valorMercadoEmpresa;
        sumario[industria].empresas += 1;
        valorMercadoTotalGeral += valorMercadoEmpresa;
        qtdEmpresasTotal += 1;

        sumario[industria].segmentos[segmento].valorMercado +=
          valorMercadoEmpresa;
        sumario[industria].segmentos[segmento].empresas += 1;
        sumario[industria].segmentos[segmento].empresasDetalhes.push({
          empresa: empresa.nome,
          valorMercado: valorMercadoEmpresa,
          participacao: 0,
          codigos: codigosInfo // Adicionar o array de códigos
        });
      } else {
        sumario[industria].empresas += 1;
        sumario[industria].segmentos[segmento].empresas += 1;
        qtdEmpresasTotal += 1;

        sumario[industria].segmentos[segmento].empresasDetalhes.push({
          empresa: empresa.nome,
          valorMercado: 0,
          participacao: 0,
          codigos: codigosInfo // Adicionar o array de códigos
        });
      }
    }

    for (const industria in sumario) {
      const industriaData = sumario[industria];
      industriaData.participacao =
        valorMercadoTotalGeral > 0
          ? (industriaData.valorMercadoTotal / valorMercadoTotalGeral) * 100
          : 0;

      for (const segmento in industriaData.segmentos) {
        const segmentoData = industriaData.segmentos[segmento];
        segmentoData.participacao =
          industriaData.valorMercadoTotal > 0
            ? (segmentoData.valorMercado / industriaData.valorMercadoTotal) *
              100
            : 0;

        for (const empresa of segmentoData.empresasDetalhes) {
          empresa.participacao =
            segmentoData.valorMercado > 0
              ? (empresa.valorMercado / segmentoData.valorMercado) * 100
              : 0;
        }
      }
    }

    const sumarioArray = Object.keys(sumario).map((industria) => ({
      industria: industria,
      valorMercadoTotal: sumario[industria].valorMercadoTotal,
      participacao: sumario[industria].participacao,
      qtdSegmentos: sumario[industria].qtdSegmentos,
      empresas: sumario[industria].empresas,
      segmentos: Object.keys(sumario[industria].segmentos).map((segmento) => ({
        segmento: segmento,
        valorMercado: sumario[industria].segmentos[segmento].valorMercado,
        empresas: sumario[industria].segmentos[segmento].empresas,
        participacao: sumario[industria].segmentos[segmento].participacao,
        empresasDetalhes:
          sumario[industria].segmentos[segmento].empresasDetalhes,
      })),
    }));

    const industriasArray = Object.keys(industriasSegmentos).map(
      (industria) => {
        const segmentosArray = Object.keys(
          industriasSegmentos[industria].segmentos
        ).map((segmento) => ({
          nome: segmento,
          totalEmpresas:
            industriasSegmentos[industria].segmentos[segmento].totalEmpresas,
        }));

        return {
          nome: industria,
          totalEmpresas: industriasSegmentos[industria].totalEmpresas,
          segmentos: segmentosArray,
        };
      }
    );

    const industriasSet = new Set(json.map((item) => item.industria));
    const qtdIndustriasT = industriasSet.size;

    const sumarioTotal = {
      valorMercadoTotalGeral: valorMercadoTotalGeral,
      qtdIndustriasTotal: qtdIndustriasT,
      qtdEmpresasTotal: qtdEmpresasTotal,
      qtdSegmentosTotal: qtdSegmentosTotal,
      industrias: [...industriasSet],
    };

    const resultadoFinal = {
      sumarioTotal: sumarioTotal,
      sumario: sumarioArray,
      industrias: industriasArray,
    };

    const caminhoSumarioJson = "../Finais/empresasSumario.json";

    await fs.writeFile(
      caminhoSumarioJson,
      JSON.stringify(resultadoFinal, null, 2),
      "utf-8"
    );

    console.log(
      `Arquivo de sumário JSON criado com sucesso. Salvo em: ${caminhoSumarioJson}`
    );
  } catch (error) {
    console.error(`Erro ao gerar o sumário: ${error.message}`);
  }
}

// Caminho para o arquivo JSON original
const caminhoArquivoJson = "../Finais/empresas.json";

// Chamar a função para gerar o sumário
gerarSumario(caminhoArquivoJson).catch(console.error);
