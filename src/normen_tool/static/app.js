const pdfJsAvailable = typeof window.pdfjsLib !== "undefined";
if (pdfJsAvailable) {
  window.pdfjsLib.GlobalWorkerOptions.workerSrc =
    "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.10.725/pdf.worker.min.js";
}

const projectFolderInput = document.getElementById("projectFolderInput");
const projectPathInput = document.getElementById("projectPathInput");
const openProjectButton = document.getElementById("openProjectButton");
const refreshStatusButton = document.getElementById("refreshStatusButton");
const loadPdfListButton = document.getElementById("loadPdfListButton");
const pdfList = document.getElementById("pdfList");
const downloadPdfButton = document.getElementById("downloadPdfButton");
const renderPageButton = document.getElementById("renderPageButton");
const pageNumberInput = document.getElementById("pageNumberInput");
const metadataOutput = document.getElementById("metadataOutput");
const pdfPreview = document.getElementById("pdfPreview");
const pdfCanvas = document.getElementById("pdfCanvas");
const statusOutput = document.getElementById("statusOutput");
const messageOutput = document.getElementById("messageOutput");
const blockList = document.getElementById("blockList");
const loadBlockButton = document.getElementById("loadBlockButton");
const refreshBlocksButton = document.getElementById("refreshBlocksButton");
const blockSectionInput = document.getElementById("blockSectionInput");
const blockContentTextarea = document.getElementById("blockContentTextarea");
const saveBlockButton = document.getElementById("saveBlockButton");

let currentDocId = null;
let currentDocName = null;
let currentPageCount = 0;
let currentPdfUrl = null;
let currentBlockId = null;

function setProjectControlsEnabled(enabled) {
  [
    loadPdfListButton,
    pdfList,
    downloadPdfButton,
    renderPageButton,
    pageNumberInput,
    blockList,
    loadBlockButton,
    refreshBlocksButton,
    blockSectionInput,
    blockContentTextarea,
    saveBlockButton,
  ].forEach((element) => {
    if (element) {
      element.disabled = !enabled;
    }
  });
}

function resetProjectState() {
  currentDocId = null;
  currentDocName = null;
  currentPageCount = 0;
  currentPdfUrl = null;
  currentBlockId = null;
  pageNumberInput.max = 1;
  pageNumberInput.value = 1;
  metadataOutput.textContent = "Keine PDF geladen.";
  pdfCanvas.width = 0;
  pdfCanvas.height = 0;
  pdfList.innerHTML = "";
  blockList.innerHTML = "";
  blockSectionInput.value = "";
  blockContentTextarea.value = "";
}

async function sendJson(path, method = "GET", body = null) {
  const response = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : null,
  });
  return response;
}

function showMessage(message, type = "info") {
  if (!messageOutput) {
    return;
  }
  messageOutput.textContent = message;
  messageOutput.className = `message-box ${type}`;
}

async function openProject() {
  const projectDir = projectPathInput.value.trim();
  if (!projectDir) {
    showMessage("Bitte Projektordner-Pfad eingeben.", "error");
    return;
  }

  showMessage("Projekt wird geöffnet...", "info");
  const response = await sendJson("/project/open", "POST", { project_dir: projectDir });
  if (!response.ok) {
    const error = await response.text();
    showMessage(`Fehler: ${error}`, "error");
    setProjectControlsEnabled(false);
    return;
  }

  showMessage("Projekt geöffnet.", "success");
  await loadProjectStatus();
  await loadPdfList();
  setProjectControlsEnabled(true);
}

async function loadProjectStatus() {
  const response = await fetch("/project/status");
  if (!response.ok) {
    showMessage("Projektstatus konnte nicht geladen werden.", "error");
    return;
  }

  const status = await response.json();
  statusOutput.textContent = `Projekt: ${status.project_dir}\nDB: ${status.db_file}\nPDFs: ${status.pdf_count}\nBlöcke: ${status.block_count}`;
  showMessage("Projektstatus geladen.", "success");
}

async function loadPdfList() {
  const response = await fetch("/project/pdfs");
  if (!response.ok) {
    const error = await response.text();
    showMessage(`Fehler: ${error}`, "error");
    return;
  }

  const result = await response.json();
  pdfList.innerHTML = "";
  result.pdfs.forEach((pdf) => {
    const option = document.createElement("option");
    option.value = pdf.id;
    option.textContent = pdf.name;
    pdfList.appendChild(option);
  });
}

async function showMetadata(documentId) {
  const response = await fetch(`/pdf/${documentId}/pages`);
  if (!response.ok) {
    metadataOutput.textContent = "Konnte Metadaten nicht laden.";
    showMessage("Konnte PDF-Metadaten nicht laden.", "error");
    return;
  }

  const result = await response.json();
  currentDocId = result.doc_id;
  currentDocName = result.doc_name;
  currentPageCount = result.page_count;
  pageNumberInput.max = currentPageCount;
  metadataOutput.textContent = JSON.stringify(result, null, 2);
  currentBlockId = null;
  blockSectionInput.value = "";
  blockContentTextarea.value = "";
  await loadBlockList();
  showMessage(`PDF ${result.doc_name} geladen.`, "success");
}

async function handleFolderSelection(event) {
  const files = event.target.files;
  if (!files || files.length === 0) {
    return;
  }

  const firstFile = files[0];
  if (firstFile.path) {
    const fullPath = firstFile.path;
    const folderPath = fullPath.replace(/\\[^\\]*$/, "");
    projectPathInput.value = folderPath;
    showMessage("Projektpfad automatisch eingetragen. Projekt wird geöffnet...", "info");
    await openProject();
  } else if (firstFile.webkitRelativePath) {
    const relativeFolder = firstFile.webkitRelativePath.split("/")[0];
    projectPathInput.value = relativeFolder;
    const manualPath = window.prompt(
      "Der Browser kann den absoluten Projektpfad nicht automatisch lesen. Bitte den vollständigen Projektordner-Pfad eingeben:",
      projectPathInput.value
    );

    if (!manualPath || !manualPath.trim()) {
      showMessage(
        "Der absolute Projektpfad konnte nicht automatisch ermittelt werden. Bitte den vollständigen Pfad im Textfeld eintragen und dann 'Projekt öffnen' klicken.",
        "error"
      );
      return;
    }

    projectPathInput.value = manualPath.trim();
    showMessage("Projektpfad eingetragen. Projekt wird geöffnet...", "info");
    await openProject();
  } else {
    showMessage("Bitte den Projektordner-Pfad manuell eingeben.", "error");
  }
}

async function loadBlockList() {
  if (!currentDocId) {
    return;
  }

  const response = await fetch(`/blocks/${currentDocId}`);
  if (!response.ok) {
    showMessage("Konnte die Block-Liste nicht laden.", "error");
    return;
  }

  const result = await response.json();
  blockList.innerHTML = "";
  result.blocks.forEach((block) => {
    const option = document.createElement("option");
    const titleText = block.section ? `${block.section}: ${block.content.slice(0, 60)}` : block.content.slice(0, 60);
    option.value = block.id;
    option.textContent = titleText;
    blockList.appendChild(option);
  });
}

async function showBlockDetails(blockId) {
  if (!blockId) {
    return;
  }

  const response = await fetch(`/block/${blockId}`);
  if (!response.ok) {
    showMessage("Konnte Block-Daten nicht laden.", "error");
    return;
  }

  const result = await response.json();
  currentBlockId = result.block.id;
  blockSectionInput.value = result.block.section || "";
  blockContentTextarea.value = result.block.content || "";
}

async function saveBlock() {
  if (!currentBlockId) {
    showMessage("Bitte zuerst einen Block auswählen.", "error");
    return;
  }

  const payload = {
    content: blockContentTextarea.value,
    section: blockSectionInput.value,
  };

  showMessage("Block wird gespeichert...", "info");
  const response = await sendJson(`/block/${currentBlockId}`, "PATCH", payload);
  if (!response.ok) {
    const error = await response.text();
    showMessage(`Fehler beim Speichern: ${error}`, "error");
    return;
  }

  showMessage("Block erfolgreich gespeichert.", "success");
  await loadBlockList();
}

async function downloadPdf() {
  if (!currentDocId) {
    showMessage("Bitte zuerst eine PDF auswählen.", "error");
    return;
  }

  window.location.href = `/pdf/${currentDocId}/download`;
}

async function renderPdfPageViaBackend(pageNumber) {
  const response = await fetch(`/pdf/${currentDocId}/rendered/${pageNumber}?format=png&dpi=150`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const imageBlob = await response.blob();
  const objectUrl = URL.createObjectURL(imageBlob);
  try {
    const image = await new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error("Bilddaten konnten nicht geladen werden."));
      img.src = objectUrl;
    });

    pdfCanvas.width = image.width;
    pdfCanvas.height = image.height;
    const context = pdfCanvas.getContext("2d");
    context.clearRect(0, 0, pdfCanvas.width, pdfCanvas.height);
    context.drawImage(image, 0, 0);
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

async function renderPdfPage() {
  if (!currentDocId) {
    showMessage("Bitte zuerst eine PDF auswählen.", "error");
    return;
  }

  const pageNumber = parseInt(pageNumberInput.value, 10) || 1;
  if (pageNumber < 1 || (currentPageCount && pageNumber > currentPageCount)) {
    showMessage("Bitte eine gültige Seitenzahl eingeben.", "error");
    return;
  }

  showMessage("Seite wird gerendert...", "info");

  if (!pdfJsAvailable) {
    try {
      await renderPdfPageViaBackend(pageNumber);
      showMessage("Seite erfolgreich gerendert (Server-Fallback).", "success");
    } catch (error) {
      console.error(error);
      showMessage(`Konnte PDF-Seite nicht rendern: ${error.message}`, "error");
    }
    return;
  }

  const pdfUrl = `/pdf/${currentDocId}/download`;
  try {
    const loadingTask = window.pdfjsLib.getDocument(pdfUrl);
    const pdf = await loadingTask.promise;
    const page = await pdf.getPage(pageNumber);
    const viewport = page.getViewport({ scale: 1.5 });

    pdfCanvas.width = viewport.width;
    pdfCanvas.height = viewport.height;
    const context = pdfCanvas.getContext("2d");

    const renderContext = {
      canvasContext: context,
      viewport,
    };

    await page.render(renderContext).promise;
    showMessage("Seite erfolgreich mit PDF.js gerendert.", "success");
  } catch (error) {
    console.error(error);
    try {
      await renderPdfPageViaBackend(pageNumber);
      showMessage("PDF.js fehlgeschlagen, Server-Fallback erfolgreich.", "success");
    } catch (fallbackError) {
      console.error(fallbackError);
      showMessage(`Konnte PDF-Seite nicht rendern: ${fallbackError.message}`, "error");
    }
  }
}

pdfList.addEventListener("change", async (event) => {
  if (event.target.value) {
    await showMetadata(event.target.value);
  }
});

blockList.addEventListener("change", async (event) => {
  if (event.target.value) {
    await showBlockDetails(event.target.value);
  }
});

projectFolderInput.addEventListener("change", handleFolderSelection);
openProjectButton.addEventListener("click", openProject);
refreshStatusButton.addEventListener("click", loadProjectStatus);
loadPdfListButton.addEventListener("click", loadPdfList);
downloadPdfButton.addEventListener("click", downloadPdf);
renderPageButton.addEventListener("click", renderPdfPage);
loadBlockButton.addEventListener("click", async () => {
  if (blockList.value) {
    await showBlockDetails(blockList.value);
  }
});
refreshBlocksButton.addEventListener("click", loadBlockList);
saveBlockButton.addEventListener("click", saveBlock);

setProjectControlsEnabled(false);
resetProjectState();
