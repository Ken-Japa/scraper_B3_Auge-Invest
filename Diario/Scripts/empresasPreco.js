const fs = require("fs");
const path = require("path");
const { google } = require("googleapis");

async function updateCompaniesFromExcel() {
  const inputJsonPath = path.join(__dirname, "../Jsons/empresas.json");
  const outputJsonPath = path.join(__dirname, "../Finais/empresas.json");
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
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: "1IIzI-y8EwgAubUSW9aquchv53sCdqUmmVn0qkqMle00",
      range: "Precos!A:C",
      valueRenderOption: "FORMATTED_VALUE",
    });

    const rows = response.data.values;

    rows.slice(1).forEach((row) => {
      const [codigo, precoStr, valorMercadoStr] = row;

      // Skip if code is missing
      if (!codigo) {
        console.log("Skipping row with missing code");
        return;
      }

      // Process price - handle missing or invalid values
      let preco = null;
      if (precoStr && precoStr !== "#N/A") {
        const parsedPreco = Number(
          String(precoStr)
            .replace("R$", "")
            .replace(/\./g, "")
            .replace(",", ".")
            .trim()
        );

        if (!isNaN(parsedPreco)) {
          preco = parsedPreco;
        } else {
          console.log(`Invalid price for ${codigo}: ${precoStr}`);
        }
      }

      // Process market value - handle missing or invalid values
      let valorMercado = null;
      if (valorMercadoStr && valorMercadoStr !== "#N/A") {
        const parsedValorMercado = Number(
          String(valorMercadoStr)
            .replace("R$", "")
            .replace(/\./g, "")
            .replace(",", ".")
            .trim()
        );

        if (!isNaN(parsedValorMercado)) {
          valorMercado = parsedValorMercado;
        } else {
          console.log(`Invalid market value for ${codigo}: ${valorMercadoStr}`);
        }
      }

      // Skip if both price and market value are missing or invalid
      if (preco === null && valorMercado === null) {
        console.log(`Skipping ${codigo}: No valid data available`);
        return;
      }

      // Update company data
      empresasData.forEach((empresa) => {
        if (empresa.codigos) {
          empresa.codigos.forEach((codigoObj) => {
            if (codigoObj.codigo === codigo) {
              // Handle price update
              if (preco !== null) {
                if (codigoObj.preco !== null && codigoObj.preco !== undefined) {
                  codigoObj.precoAnterior = codigoObj.preco;
                }

                let variacao = null;
                if (
                  codigoObj.precoAnterior !== null &&
                  codigoObj.precoAnterior !== undefined
                ) {
                  variacao =
                    ((preco - codigoObj.precoAnterior) /
                      codigoObj.precoAnterior) *
                    100;
                }

                codigoObj.preco = preco;
                codigoObj.variacao =
                  variacao !== null ? Number(variacao.toFixed(2)) : null;
              }

              // Handle market value update
              if (valorMercado !== null) {
                codigoObj["valor mercado"] = valorMercado;
              }
            }
          });
        }
      });
    });

    fs.writeFileSync(
      outputJsonPath,
      JSON.stringify(empresasData, null, 2),
      "utf8"
    );
    console.log("JSON file created successfully in " + outputJsonPath);
  } catch (error) {
    console.error("Error:", error);
  }
}

updateCompaniesFromExcel();
