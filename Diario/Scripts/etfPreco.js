const fs = require("fs");
const path = require("path");
const { google } = require("googleapis");

async function updateCompaniesFromExcel() {
  const inputJsonPath = path.join(__dirname, "../Jsons/etf.json");
  const outputJsonPath = path.join(__dirname, "../Finais/etf.json");
  let empresasData;
  if (fs.existsSync(outputJsonPath)) {
    console.log("Using existing output file to preserve previous prices");
    empresasData = JSON.parse(fs.readFileSync(outputJsonPath, "utf8"));
  } else {
    console.log("Using initial input file");
    empresasData = JSON.parse(fs.readFileSync(inputJsonPath, "utf8"));
  }

  const credentials = require("../config/service-account.json");

  const auth = new google.auth.JWT(
    credentials.client_email,
    null,
    credentials.private_key,
    ["https://www.googleapis.com/auth/spreadsheets.readonly"]
  );

  await auth.authorize();

  const sheets = google.sheets({
    version: "v4",
    auth,
  });

  try {
    // First, let's get the sheet names to make sure we're using the correct one
    const spreadsheetInfo = await sheets.spreadsheets.get({
      spreadsheetId: "1CJCRvMFVRUeLRm62RX_kBUmAyMng7Shv8FXabVNPpZM",
    });

    const sheetNames = spreadsheetInfo.data.sheets.map(
      (sheet) => sheet.properties.title
    );

    const sheetName = sheetNames.includes("Precos") ? "Precos" : sheetNames[0];

    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: "1CJCRvMFVRUeLRm62RX_kBUmAyMng7Shv8FXabVNPpZM",
      range: `${sheetName}!A:F`,
      valueRenderOption: "FORMATTED_VALUE",
    });

    const rows = response.data.values;

    if (!rows || rows.length === 0) {
      throw new Error("Planilha vazia ou inacessível");
    }

    // console.log("Headers encontrados na planilha:", rows[0]);

    // Fix: Properly handle spaces in header names
    const headers = rows[0].map((h) => String(h).toLowerCase().trim());
    const empresaIndex = headers.indexOf("empresa");
    const codigoIndex = headers.findIndex(
      (h) => h === "código" || h === "codigo" || h === "code"
    );

    // Fix: Better detection for price column with spaces
    let precoIndex = headers.findIndex(
      (h) =>
        h === "preco" ||
        h === "preço" ||
        h === "price" ||
        h.includes("preco") ||
        h.includes("preço")
    );

    // If still not found, try the 2nd column (index 2) which is often the price column
    if (precoIndex === -1 && headers.length > 2) {
      precoIndex = 2;
    }

    if (codigoIndex === -1) {
      throw new Error("Coluna de código não encontrada na planilha");
    }

    if (precoIndex === -1) {
      throw new Error("Coluna de preço não encontrada na planilha");
    }

    // Count successful updates
    let updatedCount = 0;
    let skippedCount = 0;
    let notFoundCount = 0;

    rows.slice(1).forEach((row) => {
      if (!row[codigoIndex]) return; // Pular linhas sem código

      const codigo = row[codigoIndex];
      const precoStr = row[precoIndex] || "";

      // Função para converter string de valor para número
      const parseValue = (valueStr) => {
        if (!valueStr || valueStr === "#N/A" || valueStr.includes("-")) {
          // Handle cases where value is just a dash
          if (valueStr && valueStr.trim().replace(/[R$\s]/g, "") === "-") {
            return null;
          }
          return null;
        }

        try {
          // Remover o símbolo de moeda, espaços e pontos de separação de milhar
          const cleanedValue = String(valueStr)
            .replace(/[$R\s]/g, "") // Remove R$, $ e espaços
            .replace(/\./g, "") // Remove pontos (separadores de milhar)
            .replace(",", ".") // Substitui vírgula por ponto (decimal)
            .trim();

          const numValue = Number(cleanedValue);

          if (isNaN(numValue)) {
            return null;
          }

          return numValue;
        } catch (e) {
          return null;
        }
      };

      const preco = parseValue(precoStr);

      if (precoStr === "#N/A" || precoStr.includes("-")) {
        skippedCount++;
        return;
      }

      if (preco === null || isNaN(preco)) {
        skippedCount++;
        return;
      }

      // Atualizar os dados da empresa
      let found = false;
      empresasData.forEach((empresa) => {
        if (empresa.codigos) {
          empresa.codigos.forEach((codigoObj) => {
            if (codigoObj.codigo === codigo) {
              found = true;
              if (codigoObj.preco !== null && codigoObj.preco !== undefined) {
                codigoObj.precoAnterior = codigoObj.preco;
              }

              let variacao = null;
              if (
                codigoObj.precoAnterior !== null &&
                codigoObj.precoAnterior !== undefined &&
                preco
              ) {
                variacao =
                  ((preco - codigoObj.precoAnterior) /
                    codigoObj.precoAnterior) *
                  100;
              }

              codigoObj.preco = preco;

              codigoObj.variacao =
                variacao !== null ? Number(variacao.toFixed(2)) : null;

              updatedCount++;
            }
          });
        }
      });

      if (!found) {
        notFoundCount++;
      }
    });

    fs.writeFileSync(
      outputJsonPath,
      JSON.stringify(empresasData, null, 2),
      "utf8"
    );
    console.log("JSON file created successfully in " + outputJsonPath);
    console.log(
      `Estatísticas: ${updatedCount} códigos atualizados, ${skippedCount} ignorados, ${notFoundCount} não encontrados`
    );
  } catch (error) {
    console.error("Error:", error);
  }
}

updateCompaniesFromExcel();
