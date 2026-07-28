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
const correctPdfRotationButton = document.getElementById("correctPdfRotationButton");
const runRuleBasedSegmentationButton = document.getElementById("runRuleBasedSegmentationButton");
const pageNumberInput = document.getElementById("pageNumberInput");
const pdfPreview = document.getElementById("pdfPreview");
const pdfCanvas = document.getElementById("pdfCanvas");
const statusOutput = document.getElementById("statusOutput");
const messageOutput = document.getElementById("messageOutput");
const blockList = document.getElementById("blockList");
const loadBlockButton = document.getElementById("loadBlockButton");
const refreshBlocksButton = document.getElementById("refreshBlocksButton");
const blockSectionInput = document.getElementById("blockSectionInput");
const blockContentTextarea = document.getElementById("blockContentTextarea");
const boxLeftInput = document.getElementById("boxLeftInput");
const boxTopInput = document.getElementById("boxTopInput");
const boxRightInput = document.getElementById("boxRightInput");
const boxBottomInput = document.getElementById("boxBottomInput");
const drawnBoxLeftInput = document.getElementById("drawnBoxLeftInput");
const drawnBoxTopInput = document.getElementById("drawnBoxTopInput");
const drawnBoxWidthInput = document.getElementById("drawnBoxWidthInput");
const drawnBoxHeightInput = document.getElementById("drawnBoxHeightInput");
const drawAngleInput = document.getElementById("drawAngleInput");
const blockChangeSummary = document.getElementById("blockChangeSummary");
const saveBlockButton = document.getElementById("saveBlockButton");

let currentDocId = null;
let currentDocName = null;
let currentPageCount = 0;
let currentPdfUrl = null;
let currentBlockId = null;
let currentBlocks = [];
let currentPageMetadata = {};
let currentViewportTransform = null;
let pendingDeepLink = null;

function parseDeepLinkParams() {
  const params = new URLSearchParams(window.location.search);
  return {
    docId: params.get("doc"),
    blockId: params.get("block"),
  };
}

function updateDeepLinkUrl(docId = null, blockId = null) {
  const url = new URL(window.location.href);
  if (docId) {
    url.searchParams.set("doc", docId);
  } else {
    url.searchParams.delete("doc");
  }

  if (blockId) {
    url.searchParams.set("block", blockId);
  } else {
    url.searchParams.delete("block");
  }

  window.history.replaceState({}, "", `${url.pathname}${url.search}`);
}

function getBlockBoxOnPage(block, pageNumber) {
  if (!block || !Array.isArray(block.pages) || !Array.isArray(block.bboxes)) {
    return null;
  }

  const pageIndex = block.pages.indexOf(pageNumber);
  if (pageIndex >= 0 && block.bboxes[pageIndex]) {
    return block.bboxes[pageIndex];
  }

  return block.bboxes[0] || null;
}

function getBlockRotationForPage(block, pageNumber) {
  if (!block || !Array.isArray(block.pages) || !Array.isArray(block.page_rotations)) {
    return null;
  }

  const pageIndex = block.pages.indexOf(pageNumber);
  if (pageIndex >= 0 && Number.isFinite(block.page_rotations[pageIndex])) {
    return Number(block.page_rotations[pageIndex]);
  }

  return null;
}

function formatCoordinate(value) {
  return Number.isFinite(value) ? value.toFixed(2) : "—";
}

function updateBlockEditorMetadata() {
  if (!blockChangeSummary) {
    return;
  }

  if (!currentBlockId) {
    if (boxLeftInput) boxLeftInput.value = "";
    if (boxTopInput) boxTopInput.value = "";
    if (boxRightInput) boxRightInput.value = "";
    if (boxBottomInput) boxBottomInput.value = "";
    if (drawnBoxLeftInput) drawnBoxLeftInput.value = "";
    if (drawnBoxTopInput) drawnBoxTopInput.value = "";
    if (drawnBoxWidthInput) drawnBoxWidthInput.value = "";
    if (drawnBoxHeightInput) drawnBoxHeightInput.value = "";
    if (drawAngleInput) drawAngleInput.value = "";
    blockChangeSummary.textContent = "Bitte einen Block auswählen.";
    return;
  }

  const selectedBlock = currentBlocks.find((block) => block.id === currentBlockId);
  if (!selectedBlock) {
    if (boxLeftInput) boxLeftInput.value = "";
    if (boxTopInput) boxTopInput.value = "";
    if (boxRightInput) boxRightInput.value = "";
    if (boxBottomInput) boxBottomInput.value = "";
    if (drawnBoxLeftInput) drawnBoxLeftInput.value = "";
    if (drawnBoxTopInput) drawnBoxTopInput.value = "";
    if (drawnBoxWidthInput) drawnBoxWidthInput.value = "";
    if (drawnBoxHeightInput) drawnBoxHeightInput.value = "";
    if (drawAngleInput) drawAngleInput.value = "";
    blockChangeSummary.textContent = "Der ausgewählte Block konnte nicht gefunden werden.";
    return;
  }

  const pageNumber = parseInt(pageNumberInput.value, 10) || 1;
  const bbox = getBlockBoxOnPage(selectedBlock, pageNumber);
  if (!bbox || !Array.isArray(bbox) || bbox.length < 4) {
    if (boxLeftInput) boxLeftInput.value = "";
    if (boxTopInput) boxTopInput.value = "";
    if (boxRightInput) boxRightInput.value = "";
    if (boxBottomInput) boxBottomInput.value = "";
    if (drawnBoxLeftInput) drawnBoxLeftInput.value = "";
    if (drawnBoxTopInput) drawnBoxTopInput.value = "";
    if (drawnBoxWidthInput) drawnBoxWidthInput.value = "";
    if (drawnBoxHeightInput) drawnBoxHeightInput.value = "";
    if (drawAngleInput) drawAngleInput.value = "";
    blockChangeSummary.textContent = "Für die aktuelle Seite ist keine Segmentierungs-Box verfügbar.";
    return;
  }

  const [x0, y0, x1, y1] = bbox;
  const left = Math.min(x0, x1);
  const top = Math.min(y0, y1);
  const right = Math.max(x0, x1);
  const bottom = Math.max(y0, y1);

  const pageRotation = getBlockRotationForPage(selectedBlock, pageNumber);
  const pageInfoWithRotation = pageRotation === null
    ? currentPageMetadata[pageNumber]
    : { ...currentPageMetadata[pageNumber], rotation: pageRotation };

  const transformed = window.projectPdfBBoxToCanvas(
    bbox,
    pageInfoWithRotation,
    pdfCanvas?.width || 0,
    pdfCanvas?.height || 0,
    currentViewportTransform || null
  );

  if (boxLeftInput) boxLeftInput.value = formatCoordinate(left);
  if (boxTopInput) boxTopInput.value = formatCoordinate(top);
  if (boxRightInput) boxRightInput.value = formatCoordinate(right);
  if (boxBottomInput) boxBottomInput.value = formatCoordinate(bottom);
  if (drawnBoxLeftInput) drawnBoxLeftInput.value = transformed ? formatCoordinate(transformed.left) : "—";
  if (drawnBoxTopInput) drawnBoxTopInput.value = transformed ? formatCoordinate(transformed.top) : "—";
  if (drawnBoxWidthInput) drawnBoxWidthInput.value = transformed ? formatCoordinate(transformed.width) : "—";
  if (drawnBoxHeightInput) drawnBoxHeightInput.value = transformed ? formatCoordinate(transformed.height) : "—";
  if (drawAngleInput) drawAngleInput.value = pageRotation === null ? "—" : `${pageRotation}°`;

  const pageLabel = currentPageMetadata[pageNumber] ? `Seite ${pageNumber}` : `Seite ${pageNumber}`;
  const pagesLabel = Array.isArray(selectedBlock.pages) && selectedBlock.pages.length > 0
    ? selectedBlock.pages.join(", ")
    : "keine";

  blockChangeSummary.textContent = `Effektiv geändert werden aktuell nur Abschnitt und Inhalt. Die Box-Koordinaten kommen aus der Segmentierung (${pageLabel}, Seiten: ${pagesLabel}) und werden hier nur angezeigt.`;
}

function getHighlightBlockIdsForPage(pageNumber) {
  if (!currentBlockId) {
    return [];
  }

  const targetBlock = currentBlocks.find((block) => block.id === currentBlockId);
  if (!targetBlock) {
    return [];
  }

  const targetIndex = currentBlocks.findIndex((block) => block.id === currentBlockId);
  const relatedIds = new Set([currentBlockId]);
  const targetPages = new Set(Array.isArray(targetBlock.pages) ? targetBlock.pages : []);

  currentBlocks.forEach((block, index) => {
    if (block.id === currentBlockId) {
      return;
    }

    const blockPages = Array.isArray(block.pages) ? block.pages : [];
    const isOnPage = blockPages.includes(pageNumber);
    const sharesTargetPage = blockPages.some((page) => targetPages.has(page));
    const isAdjacent = targetIndex >= 0 && Math.abs(index - targetIndex) <= 1;
    const isCrossPageContext = blockPages.some((page) => targetPages.has(page)) || targetPages.size > 1 && blockPages.some((page) => page === pageNumber);

    if ((isOnPage && (sharesTargetPage || isAdjacent)) || (isCrossPageContext && isAdjacent)) {
      relatedIds.add(block.id);
    }
  });

  return Array.from(relatedIds);
}

function drawBlockHighlights(pageNumber) {
  if (!pdfCanvas) {
    return;
  }

  const context = pdfCanvas.getContext("2d");
  if (!context) {
    return;
  }

  const pageInfo = currentPageMetadata[pageNumber];
  if (!pageInfo) {
    return;
  }

  const pageWidth = pageInfo.width || 1;
  const pageHeight = pageInfo.height || 1;
  const scaleX = pdfCanvas.width / pageWidth;
  const scaleY = pdfCanvas.height / pageHeight;

  const highlightedIds = getHighlightBlockIdsForPage(pageNumber);

  currentBlocks.forEach((block) => {
    if (!Array.isArray(block.pages) || !block.pages.includes(pageNumber)) {
      return;
    }

    if (!highlightedIds.includes(block.id)) {
      return;
    }

    const bbox = getBlockBoxOnPage(block, pageNumber);
    if (!bbox || bbox.length < 4) {
      return;
    }

    const pageRotation = getBlockRotationForPage(block, pageNumber);
    const pageInfoWithRotation = pageRotation === null
      ? pageInfo
      : { ...pageInfo, rotation: pageRotation };

    const transformed = window.projectPdfBBoxToCanvas(
      bbox,
      pageInfoWithRotation,
      pdfCanvas.width,
      pdfCanvas.height,
      currentViewportTransform || null
    );
    if (!transformed) {
      return;
    }

    const { left, top, width, height } = transformed;

    context.save();
    context.setTransform(1, 0, 0, 1, 0, 0);
    context.fillStyle = block.id === currentBlockId ? "rgba(255, 77, 79, 0.18)" : "rgba(245, 158, 11, 0.16)";
    context.strokeStyle = block.id === currentBlockId ? "#ff4d4f" : "#f59e0b";
    context.lineWidth = block.id === currentBlockId ? 3 : 2;
    context.setLineDash(block.id === currentBlockId ? [] : [6, 4]);
    context.beginPath();
    context.rect(left, top, width, height);
    context.fill();
    context.stroke();
    context.restore();
  });

  updateBlockEditorMetadata();
}

async function focusBlockById(blockId) {
  if (!blockId) {
    return;
  }

  const matchingBlock = currentBlocks.find((block) => block.id === blockId);
  if (!matchingBlock) {
    return;
  }

  const targetPage = Array.isArray(matchingBlock.pages) && matchingBlock.pages.length > 0 ? matchingBlock.pages[0] : 1;
  pageNumberInput.value = targetPage;
  await renderPdfPage();
}

async function applyDeepLinkSelection() {
  pendingDeepLink = parseDeepLinkParams();
  if (!pendingDeepLink.docId || !pendingDeepLink.blockId) {
    return;
  }

  if (!currentDocId || currentDocId !== pendingDeepLink.docId) {
    const matchingPdf = Array.from(pdfList.options).find((option) => option.value === pendingDeepLink.docId);
    if (matchingPdf) {
      pdfList.value = pendingDeepLink.docId;
      await showMetadata(pendingDeepLink.docId);
    }
    return;
  }

  const matchingBlock = currentBlocks.find((block) => block.id === pendingDeepLink.blockId);
  if (matchingBlock) {
    blockList.value = pendingDeepLink.blockId;
    await showBlockDetails(pendingDeepLink.blockId);
  }
}

function setProjectControlsEnabled(enabled) {
  [
    loadPdfListButton,
    pdfList,
    downloadPdfButton,
    renderPageButton,
    correctPdfRotationButton,
    runRuleBasedSegmentationButton,
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
  currentBlocks = [];
  currentPageMetadata = {};
  currentViewportTransform = null;
  pendingDeepLink = parseDeepLinkParams();
  pageNumberInput.max = 1;
  pageNumberInput.value = 1;
  pdfCanvas.width = 0;
  pdfCanvas.height = 0;
  pdfList.innerHTML = "";
  blockList.innerHTML = "";
  blockSectionInput.value = "";
  blockContentTextarea.value = "";
  if (boxLeftInput) boxLeftInput.value = "";
  if (boxTopInput) boxTopInput.value = "";
  if (boxRightInput) boxRightInput.value = "";
  if (boxBottomInput) boxBottomInput.value = "";
  if (blockChangeSummary) blockChangeSummary.textContent = "Bitte einen Block auswählen.";
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

  pendingDeepLink = parseDeepLinkParams();
  if (pendingDeepLink.docId) {
    const matchingPdf = result.pdfs.find((pdf) => pdf.id === pendingDeepLink.docId);
    if (matchingPdf) {
      pdfList.value = matchingPdf.id;
      await showMetadata(matchingPdf.id);
    }
  }
}

async function showMetadata(documentId) {
  const response = await fetch(`/pdf/${documentId}/pages`);
  if (!response.ok) {
    showMessage("Konnte PDF-Metadaten nicht geladen.", "error");
    return;
  }

  const result = await response.json();
  currentDocId = result.doc_id;
  currentDocName = result.doc_name;
  currentPageCount = result.page_count;
  pageNumberInput.max = currentPageCount;
  currentBlockId = null;
  currentBlocks = [];
  currentPageMetadata = Object.fromEntries(result.pages.map((page) => [page.page_num, page]));
  blockSectionInput.value = "";
  blockContentTextarea.value = "";
  updateBlockEditorMetadata();
  updateDeepLinkUrl(currentDocId, null);
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
  currentBlocks = result.blocks || [];
  blockList.innerHTML = "";
  result.blocks.forEach((block) => {
    const option = document.createElement("option");
    const titleText = block.section ? `${block.section}: ${block.content.slice(0, 60)}` : block.content.slice(0, 60);
    option.value = block.id;
    option.textContent = titleText;
    blockList.appendChild(option);
  });

  pendingDeepLink = parseDeepLinkParams();
  if (pendingDeepLink.blockId) {
    const matchingBlock = result.blocks.find((block) => block.id === pendingDeepLink.blockId);
    if (matchingBlock) {
      blockList.value = matchingBlock.id;
      await showBlockDetails(matchingBlock.id);
    }
  }
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
  updateBlockEditorMetadata();
  updateDeepLinkUrl(currentDocId, currentBlockId);
  await focusBlockById(currentBlockId);
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

async function correctPdfRotation() {
  if (!currentDocId) {
    showMessage("Bitte zuerst eine PDF auswählen.", "error");
    return;
  }

  showMessage("PDF-Rotation wird korrigiert...", "info");
  const response = await sendJson(`/pdf/${currentDocId}/correct-rotation`, "POST");

  if (!response.ok) {
    const error = await response.text();
    showMessage(`Korrektur fehlgeschlagen: ${error}`, "error");
    return;
  }

  const result = await response.json();
  showMessage(result.message || "PDF-Rotation korrigiert.", "success");
  await renderPdfPage();
}

async function runRuleBasedSegmentation() {
  if (!currentDocId) {
    showMessage("Bitte zuerst eine PDF auswählen.", "error");
    return;
  }

  showMessage("Rule-based Segmentierung wird ausgeführt...", "info");
  const response = await sendJson(`/pdf/${currentDocId}/parse`, "POST", {
    overwrite_existing: true,
  });

  if (!response.ok) {
    const error = await response.text();
    showMessage(`Segmentierung fehlgeschlagen: ${error}`, "error");
    return;
  }

  const result = await response.json();
  await loadBlockList();
  await loadProjectStatus();
  showMessage(`Segmentierung abgeschlossen: ${result.blocks_created} Blöcke erzeugt.`, "success");
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
    currentViewportTransform = null;
    const context = pdfCanvas.getContext("2d");
    context.clearRect(0, 0, pdfCanvas.width, pdfCanvas.height);
    context.drawImage(image, 0, 0);
    drawBlockHighlights(pageNumber);
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
    currentViewportTransform = viewport.transform;

    const renderContext = {
      canvasContext: context,
      viewport,
    };

    await page.render(renderContext).promise;
    drawBlockHighlights(pageNumber);
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
correctPdfRotationButton.addEventListener("click", correctPdfRotation);
runRuleBasedSegmentationButton.addEventListener("click", runRuleBasedSegmentation);
loadBlockButton.addEventListener("click", async () => {
  if (blockList.value) {
    await showBlockDetails(blockList.value);
  }
});
refreshBlocksButton.addEventListener("click", loadBlockList);
saveBlockButton.addEventListener("click", saveBlock);

setProjectControlsEnabled(false);
resetProjectState();
