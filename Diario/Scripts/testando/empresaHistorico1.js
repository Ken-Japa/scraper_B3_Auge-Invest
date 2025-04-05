const ExcelJS = require("exceljs");
const { format } = require("date-fns");
const fs = require("fs");
const path = require("path");
const axios = require("axios");
const readline = require("readline");

async function downloadFile() {
  const filePath = path.join(__dirname, "downloaded_historic");
  const fileId = "1eFXVNBA3w52zG-XPAWyMSN5niaj_SLKt";

  try {
    console.log("-- Iniciando -- Download do arquivo");
    
    // Try the original method to download the file
    const response = await axios({
      method: "get",
      url: `https://drive.google.com/uc?export=download&id=${fileId}`,
      responseType: "text",
    });

    // Extract the direct download URL from the HTML
    const htmlContent = response.data;

    // Check if we got the virus scan warning page
    if (htmlContent.includes("Google Drive can't scan this file for viruses")) {
      console.log(
        "Recebido aviso de verificação de vírus do Google Drive. Extraindo URL de download direto..."
      );

      // Extract the form action URL and parameters
      const formActionMatch = htmlContent.match(/action="([^"]+)"/);
      const confirmMatch = htmlContent.match(/name="confirm" value="([^"]+)"/);
      const uuidMatch = htmlContent.match(/name="uuid" value="([^"]+)"/);

      if (formActionMatch && confirmMatch) {
        const formAction = formActionMatch[1];
        const confirm = confirmMatch[1];
        const uuid = uuidMatch ? uuidMatch[1] : "";

        // Construct the direct download URL
        const directUrl = `${formAction}?id=${fileId}&export=download&confirm=${confirm}&uuid=${uuid}`;

        console.log("URL de download direto encontrada. Baixando arquivo...");

        // Create a write stream for the file (without extension for now)
        const tempFilePath = `${filePath}.tmp`;
        const writer = fs.createWriteStream(tempFilePath);

        // Download the file using the direct URL with streaming
        const fileResponse = await axios({
          method: "get",
          url: directUrl,
          responseType: "stream",
          maxContentLength: Infinity,
          maxBodyLength: Infinity,
        });

        // Pipe the response to the file
        fileResponse.data.pipe(writer);

        // Wait for the download to complete
        await new Promise((resolve, reject) => {
          writer.on("finish", resolve);
          writer.on("error", reject);
        });

        console.log("Download completo.");
        
        // Determine file type by reading the first few bytes
        const fileHeader = fs.readFileSync(tempFilePath, {
          encoding: null,
          length: 4,
        });
        
        let finalFilePath;
        
        // Check if it's a ZIP/XLSX file (PK header)
        if (fileHeader[0] === 0x50 && fileHeader[1] === 0x4b) {
          console.log("Arquivo detectado como XLSX (formato ZIP)");
          finalFilePath = `${filePath}.xlsx`;
        } else {
          // Assume it's CSV
          console.log("Arquivo detectado como CSV");
          finalFilePath = `${filePath}.csv`;
        }
        
        // Rename the file with the correct extension
        fs.renameSync(tempFilePath, finalFilePath);
        console.log(`Arquivo salvo como: ${finalFilePath}`);
        
        return {
          path: finalFilePath,
          type: path.extname(finalFilePath).substring(1) // Get extension without dot
        };
      } else {
        throw new Error(
          "Não foi possível extrair a URL de download direto da página HTML"
        );
      }
    } else {
      throw new Error(
        "Não foi possível obter a página de download do Google Drive"
      );
    }
  } catch (error) {
    console.error("Erro ao baixar o arquivo:", error.message);
    return false;
  }
}

// Create a function to ask for user input
function askQuestion(query) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) =>
    rl.question(query, (ans) => {
      rl.close();
      resolve(ans);
    })
  );
}

async function processarExcel() {
  // First, just download the file
  const downloadResult = await downloadFile();

  if (!downloadResult) {
    console.log("Download falhou.");
    return;
  }

  // Wait for user confirmation before proceeding
  const answer = await askQuestion(
    "\nDeseja continuar com o processamento do arquivo? (s/n): "
  );

  if (answer.toLowerCase() !== "s") {
    console.log("Processamento cancelado pelo usuário.");
    return;
  }

  const filePath = downloadResult.path;
  const fileType = downloadResult.type;

  try {
    console.log(`\n-- Iniciando processamento do arquivo ${fileType.toUpperCase()}`);

    let fileData;
    
    if (fileType === 'xlsx') {
      // Process XLSX file using ExcelJS for better formula handling
      console.log("Processando arquivo Excel com ExcelJS...");
      const workbook = new ExcelJS.Workbook();
      await workbook.xlsx.readFile(filePath);
      
      const worksheet = workbook.getWorksheet(1);
      console.log(`Planilha encontrada: ${worksheet.name}`);
      
      // Get the used range
      const usedRange = worksheet.getUsedRange();
      if (!usedRange) {
        throw new Error("Não foi possível determinar o range utilizado na planilha");
      }
      
      // Convert worksheet to array of arrays with calculated values
      fileData = [];
      worksheet.eachRow({ includeEmpty: true }, (row, rowNumber) => {
        const rowData = [];
        row.eachCell({ includeEmpty: true }, (cell, colNumber) => {
          // Get the calculated value if it's a formula
          let value = cell.value;
          if (cell.formula) {
            console.log(`Fórmula encontrada em ${cell.address}: ${cell.formula}`);
            // Try to get the calculated value
            value = cell.result;
          }
          rowData[colNumber - 1] = value;
        });
        fileData[rowNumber - 1] = rowData;
      });
      
      // Try to force recalculation of formulas
      console.log("Tentando forçar recálculo de fórmulas...");
      
      // Create a temporary Excel file with updated TODAY() function
      const tempWorkbook = new ExcelJS.Workbook();
      const tempWorksheet = tempWorkbook.addWorksheet('Temp');
      
      // Add a cell with TODAY() formula
      tempWorksheet.getCell('A1').value = { formula: 'TODAY()' };
      
      // Save and read back to get the current date
      const tempFilePath = path.join(__dirname, "temp_today.xlsx");
      await tempWorkbook.xlsx.writeFile(tempFilePath);
      
      // Read it back
      const checkWorkbook = new ExcelJS.Workbook();
      await checkWorkbook.xlsx.readFile(tempFilePath);
      const todayValue = checkWorkbook.getWorksheet('Temp').getCell('A1').value;
      
      console.log(`Data atual do Excel: ${todayValue}`);
      
      // Clean up temp file
      fs.unlinkSync(tempFilePath);
      
      // Set target date for future projections (April 2, 2025)
      const targetDate = new Date(2025, 3, 2); // Month is 0-indexed, so 3 = April
      console.log(`Data alvo para processamento: ${format(targetDate, "dd/MM/yyyy")}`);
      
      // Manually extend data if needed
      console.log("Verificando se é necessário estender os dados até a data alvo...");
    } else if (fileType === 'csv') {
      // Process CSV file
      console.log("Processando arquivo CSV...");
      const csvData = fs.readFileSync(filePath, 'utf8');
      
      // Parse CSV using csv-parse
      const { parse } = require('csv-parse/sync');
      fileData = parse(csvData, {
        columns: false,
        skip_empty_lines: true,
        trim: true
      });
    } else {
      throw new Error(`Tipo de arquivo não suportado: ${fileType}`);
    }

    console.log(`Linhas encontradas: ${fileData.length}`);

    // Process the data
    const historicData = [];
    let latestDate = null;

    // Find the header row
    const headerRow = fileData[0];
    
    // Debug the structure
    console.log("Estrutura do cabeçalho:", headerRow.slice(0, 8));

    // Process data in columns (every 4 columns)
    for (let colIndex = 0; colIndex < headerRow.length; colIndex += 4) {
      const empresa = headerRow[colIndex];
      const codigo = headerRow[colIndex + 1];

      if (!empresa || !codigo) continue;
      
      console.log(`Processando empresa: ${empresa} (${codigo})`);

      const historicoPrecos = [];
      let latestCompanyDate = null;
      let processedRows = 0;

      // Process rows for this company
      for (let rowIndex = 1; rowIndex < fileData.length; rowIndex++) {
        const row = fileData[rowIndex];
        if (!row || row.length <= colIndex) continue;

        const dataValue = row[colIndex];
        const precoValue = row[colIndex + 1];
        const volumeValue = row[colIndex + 2];

        if ((!dataValue && !precoValue) || !dataValue) continue;

        // Process date - handle various formats
        let dataFormatada;
        let dateObj = null;

        if (dataValue instanceof Date) {
          dateObj = dataValue;
          dataFormatada = format(dateObj, "dd/MM/yyyy");
        } else if (typeof dataValue === "string") {
          // Try to parse date string
          try {
            // Check for dd/mm/yyyy format
            if (dataValue.includes("/")) {
              const parts = dataValue.split("/");
              if (parts.length === 3) {
                const day = parseInt(parts[0], 10);
                const month = parseInt(parts[1], 10) - 1;
                const year = parseInt(parts[2], 10);
                dateObj = new Date(year, month, day);
                dataFormatada = format(dateObj, "dd/MM/yyyy");
              } else {
                dataFormatada = dataValue;
              }
            }
            // Check for Excel date format (e.g., "2023-12-08")
            else if (dataValue.includes("-")) {
              dateObj = new Date(dataValue);
              dataFormatada = format(dateObj, "dd/MM/yyyy");
            } 
            // Check for Excel serial date format (e.g., "44653")
            else if (/^\d+$/.test(dataValue)) {
              // Excel dates are days since 1900-01-01, but Excel has a leap year bug
              const excelDate = parseInt(dataValue, 10);
              // Adjust for Excel's leap year bug (Excel thinks 1900 was a leap year)
              const jsDate = new Date(1900, 0, excelDate - 1);
              dataFormatada = format(jsDate, "dd/MM/yyyy");
              dateObj = jsDate;
            } else {
              dataFormatada = dataValue;
            }
          } catch (e) {
            console.log(`Erro ao processar data: ${dataValue}`, e.message);
            dataFormatada = dataValue;
          }
        } else if (typeof dataValue === "number") {
          // Handle numeric Excel dates
          try {
            // Excel dates are days since 1900-01-01, but Excel has a leap year bug
            // Adjust for Excel's leap year bug (Excel thinks 1900 was a leap year)
            const jsDate = new Date(1900, 0, dataValue - 1);
            dataFormatada = format(jsDate, "dd/MM/yyyy");
            dateObj = jsDate;
          } catch (e) {
            console.log(`Erro ao processar data numérica: ${dataValue}`, e.message);
            continue;
          }
        } else {
          continue; // Skip if no valid date
        }

        // Process price
        let preco = precoValue;
        if (typeof preco !== "number") {
          // Try to convert string to number
          if (typeof preco === "string") {
            preco = parseFloat(preco.replace(",", "."));
          }

          if (isNaN(preco)) continue;
        }

        // Process volume
        let volume = volumeValue;
        if (typeof volume !== "number") {
          // Try to convert string to number
          if (typeof volume === "string") {
            volume = parseFloat(volume.replace(",", "."));
          }

          if (isNaN(volume)) {
            volume = null;
          }
        }

        // Update latest date
        if (dateObj && !isNaN(dateObj.getTime())) {
          if (!latestDate || dateObj > latestDate) {
            latestDate = dateObj;
          }

          if (!latestCompanyDate || dateObj > latestCompanyDate) {
            latestCompanyDate = dateObj;
          }
        }

        historicoPrecos.push({ data: dataFormatada, preco, volume });
        processedRows++;
      }
      
      console.log(`  Linhas processadas para ${codigo}: ${processedRows}`);

      // Only add companies with valid historical data
      if (historicoPrecos.length > 0) {
        // Sort historical data by date (newest first)
        historicoPrecos.sort((a, b) => {
          try {
            const dateA = a.data.split("/").reverse().join("-");
            const dateB = b.data.split("/").reverse().join("-");
            return dateB.localeCompare(dateA);
          } catch (e) {
            return 0;
          }
        });

        const latestDateStr = latestCompanyDate
          ? format(latestCompanyDate, "dd/MM/yyyy")
          : "N/A";
        console.log(`  Data mais recente para ${codigo}: ${latestDateStr}`);

        historicData.push({
          empresa,
          codigo,
          historicoPrecos,
        });
      }
    }
    
    if (latestDate) {
      console.log(`Data mais recente encontrada: ${format(latestDate, "dd/MM/yyyy")}`);
    }

    // Save to JSON file
    const outputJsonPath = path.join(
      __dirname,
      "Finais",
      "empresasHistorico.json"
    );

    // Create directory if it doesn't exist
    const outputDir = path.dirname(outputJsonPath);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(
      outputJsonPath,
      JSON.stringify(historicData, null, 2),
      "utf8"
    );

    console.log(
      `Historical data JSON file created successfully at ${outputJsonPath}!`
    );
    console.log(`Total de empresas processadas: ${historicData.length}`);
  } catch (error) {
    console.error(`Erro ao processar o arquivo ${fileType}:`, error);
    console.error(error.stack);
  }
}

processarExcel();
