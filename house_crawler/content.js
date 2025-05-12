// Stato del content script
// Preveniamo la ridichiarazione della variabile state
if (typeof window.scraperState === 'undefined') {
  window.scraperState = {
    isSelecting: false,
    selectionType: null,
    selectionStep: null, // 'container', 'value', 'key'
    selectedContainerElement: null,
    tempRule: null
  };
}
// Semplifichiamo l'accesso con un alias locale
const state = window.scraperState;

// Overlay per evidenziare gli elementi durante la selezione
let highlightOverlay = null;

// Stili per la selezione interattiva
const overlayStyles = `
  .scraper-highlight {
    position: absolute;
    pointer-events: none;
    background-color: rgba(0, 123, 255, 0.3);
    border: 2px solid rgba(0, 123, 255, 0.8);
    z-index: 9999;
    transition: opacity 0.2s;
  }
  .scraper-hover {
    position: absolute;
    pointer-events: none;
    background-color: rgba(255, 193, 7, 0.3);
    border: 2px solid rgba(255, 193, 7, 0.8);
    z-index: 10000;
    transition: opacity 0.1s;
  }
  .scraper-ui {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 12px;
    z-index: 10001;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    font-family: Arial, sans-serif;
    font-size: 14px;
    max-width: 300px;
  }
  .scraper-button {
    background-color: #4CAF50;
    border: none;
    color: white;
    padding: 6px 12px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 14px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 4px;
  }
  .scraper-button-cancel {
    background-color: #f44336;
  }
  .scraper-input {
    width: 100%;
    padding: 6px;
    margin-bottom: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
`;

// Attiva la comunicazione con il background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Content script received message:', message);

  if (message.action === 'ping') {
    // Risponde al ping per verificare che il content script sia attivo
    sendResponse({status: 'ok'});
    return true; // Mantiene il canale di comunicazione aperto per la risposta asincrona
  } else if (message.action === 'startInteractiveSelection') {
    startInteractiveSelection(message.selectionType);
  } else if (message.action === 'extractData') {
    extractData(message.rules);
  } else if (message.action === 'clickNextButton') {
    clickNextButton(message.selector);
  } else if (message.action === 'previewData') {
    previewData(message.rules);
  }

  return true; // Indica che la risposta potrebbe essere asincrona
});

// Notifica al background script che la pagina è caricata
chrome.runtime.sendMessage({ action: 'pageLoaded' });

// SELEZIONE INTERATTIVA
function startInteractiveSelection(selectionType) {
  console.log('Starting interactive selection:', selectionType);

  // Inizializza lo stato
  state.isSelecting = true;
  state.selectionType = selectionType;
  state.tempRule = {
    id: `rule_${Date.now()}`,
    type: selectionType === 'nextButton' ? 'next_button' : 
          selectionType === 'multipleContainer' ? 'multiple' : 'single',
    name: '', // Verrà impostato dall'utente
    selector: ''
  };

  // Imposta lo step corretto in base al tipo di selezione
  if (selectionType === 'multipleContainer') {
    state.selectionStep = 'container';
  } else {
    state.selectionStep = 'value';
  }

  // Inietta gli stili e crea l'overlay per l'evidenziazione al passaggio del mouse
  injectStyles();
  createHoverOverlay();

  // Crea l'overlay per le istruzioni
  showInstructions();

  // Aggiungi listener per il passaggio del mouse e il click
  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('click', handleElementClick, true);
}

function injectStyles() {
  // Inietta gli stili per l'evidenziazione e l'UI
  if (!document.getElementById('scraper-styles')) {
    const styleElement = document.createElement('style');
    styleElement.id = 'scraper-styles';
    styleElement.textContent = overlayStyles;
    document.head.appendChild(styleElement);
  }
}

function createHoverOverlay() {
  // Crea l'overlay per evidenziare gli elementi al passaggio del mouse
  if (!document.getElementById('scraper-hover-overlay')) {
    const overlay = document.createElement('div');
    overlay.id = 'scraper-hover-overlay';
    overlay.className = 'scraper-hover';
    overlay.style.display = 'none';
    document.body.appendChild(overlay);
    highlightOverlay = overlay;
  }
}

function showInstructions() {
  // Crea un elemento UI per mostrare istruzioni all'utente
  if (!document.getElementById('scraper-ui')) {
    const ui = document.createElement('div');
    ui.id = 'scraper-ui';
    ui.className = 'scraper-ui';

    let instructionText = '';
    switch (state.selectionType) {
      case 'nextButton':
        instructionText = 'Seleziona il pulsante "Avanti" per la navigazione alla pagina successiva';
        break;
      case 'multipleContainer':
        instructionText = 'Seleziona un elemento contenitore di una lista (ad es. un singolo prodotto in una lista di prodotti)';
        break;
      case 'singleData':
        instructionText = 'Seleziona l\'elemento da estrarre';
        break;
      default:
        instructionText = 'Seleziona un elemento';
    }

    ui.innerHTML = `
      <div style="margin-bottom: 10px;">${instructionText}</div>
      <button id="scraper-cancel" class="scraper-button scraper-button-cancel">Annulla</button>
    `;
    
    document.body.appendChild(ui);
    
    // Aggiungi event listener per il pulsante di annullamento
    document.getElementById('scraper-cancel').addEventListener('click', cancelSelection);
  }
}

function handleMouseMove(event) {
  if (!state.isSelecting) return;
  
  // Ignora gli elementi dell'UI del scraper
  if (event.target.closest('.scraper-ui')) {
    highlightOverlay.style.display = 'none';
    return;
  }
  
  const element = document.elementFromPoint(event.clientX, event.clientY);
  if (element) {
    const rect = element.getBoundingClientRect();
    
    highlightOverlay.style.display = 'block';
    highlightOverlay.style.top = `${window.scrollY + rect.top}px`;
    highlightOverlay.style.left = `${window.scrollX + rect.left}px`;
    highlightOverlay.style.width = `${rect.width}px`;
    highlightOverlay.style.height = `${rect.height}px`;
  }
}

function handleElementClick(event) {
  if (!state.isSelecting) return;
  
  // Ignora i click sull'UI dello scraper
  if (event.target.closest('.scraper-ui')) return;
  
  // Previeni il comportamento default del click (evita navigazione)
  event.preventDefault();
  event.stopPropagation();
  
  const element = event.target;
  
  switch (state.selectionStep) {
    case 'container':
      handleContainerSelection(element);
      break;
    case 'value':
      handleValueSelection(element);
      break;
    case 'key':
      handleKeySelection(element);
      break;
  }
}

function handleContainerSelection(element) {
  // Salva l'elemento container selezionato
  state.selectedContainerElement = element;
  
  // Genera il selettore per il container
  state.tempRule.selector = generateSelector(element);
  
  // Passa al prossimo step
  state.selectionStep = 'value';
  
  // Aggiorna le istruzioni
  updateInstructions('Ora seleziona un elemento DENTRO il contenitore da cui estrarre il valore');
  
  // Evidenzia il container selezionato
  highlightElement(element, 'rgba(0, 123, 255, 0.3)');
}

function handleValueSelection(element) {
  // Se stiamo selezionando un elemento all'interno di un container
  if (state.selectionType === 'multipleContainer' && state.selectedContainerElement) {
    // Verifica che l'elemento selezionato sia contenuto nel container
    if (!state.selectedContainerElement.contains(element)) {
      alert('Seleziona un elemento DENTRO il contenitore');
      return;
    }
    
    // Genera un selettore relativo rispetto al container
    state.tempRule.relativeSelector = generateRelativeSelector(element, state.selectedContainerElement);
  } else {
    // Per singoli elementi o nextButton, salva il selettore direttamente
    state.tempRule.selector = generateSelector(element);
  }
  
  // Per il pulsante "avanti", finiamo qui
  if (state.selectionType === 'nextButton') {
    requestRuleName('Pulsante Avanti', finalizeRule);
  } else {
    // Altrimenti, proseguiamo alla selezione della chiave
    state.selectionStep = 'key';
    showKeyInputOptions();
  }
}

function handleKeySelection(element) {
  // Genera il selettore per l'elemento chiave
  if (state.selectionType === 'multipleContainer' && state.selectedContainerElement) {
    // Per liste, genera un selettore relativo rispetto al container
    if (!state.selectedContainerElement.contains(element)) {
      alert('Seleziona un elemento DENTRO il contenitore');
      return;
    }
    state.tempRule.keySelector = generateRelativeSelector(element, state.selectedContainerElement);
  } else {
    // Per singoli elementi, genera un selettore assoluto
    state.tempRule.keySelector = generateSelector(element);
  }
  
  // Concludi la selezione chiedendo il nome della regola
  requestRuleName('', finalizeRule);
}

function updateInstructions(text) {
  const ui = document.getElementById('scraper-ui');
  if (ui) {
    const instructionDiv = ui.querySelector('div');
    if (instructionDiv) {
      instructionDiv.textContent = text;
    }
  }
}

function showKeyInputOptions() {
  const ui = document.getElementById('scraper-ui');
  if (ui) {
    ui.innerHTML = `
      <div>Come vuoi definire la chiave (nome campo) per questo dato?</div>
      <button id="scraper-select-key" class="scraper-button">Seleziona elemento per la chiave</button>
      <div style="margin-top: 10px;">OPPURE inserisci manualmente:</div>
      <input type="text" id="scraper-manual-key" class="scraper-input" placeholder="Nome campo (es: prezzo, titolo)">
      <button id="scraper-use-manual-key" class="scraper-button">Usa questa chiave</button>
      <button id="scraper-cancel" class="scraper-button scraper-button-cancel">Annulla</button>
    `;
    
    document.getElementById('scraper-select-key').addEventListener('click', () => {
      updateInstructions('Seleziona l\'elemento da usare come nome campo');
    });
    
    document.getElementById('scraper-use-manual-key').addEventListener('click', () => {
      const manualKey = document.getElementById('scraper-manual-key').value.trim();
      if (manualKey) {
        state.tempRule.manualKey = manualKey;
        requestRuleName(manualKey, finalizeRule);
      } else {
        alert('Inserisci un nome per il campo');
      }
    });
    
    document.getElementById('scraper-cancel').addEventListener('click', cancelSelection);
  }
}

function requestRuleName(defaultName, callback) {
  const ui = document.getElementById('scraper-ui');
  if (ui) {
    ui.innerHTML = `
      <div>Dai un nome a questa regola di estrazione:</div>
      <input type="text" id="scraper-rule-name" class="scraper-input" placeholder="Nome regola" value="${defaultName}">
      <button id="scraper-save-rule" class="scraper-button">Salva Regola</button>
      <button id="scraper-cancel" class="scraper-button scraper-button-cancel">Annulla</button>
    `;
    
    document.getElementById('scraper-save-rule').addEventListener('click', () => {
      const ruleName = document.getElementById('scraper-rule-name').value.trim();
      if (ruleName) {
        state.tempRule.name = ruleName;
        if (callback) callback();
      } else {
        alert('Inserisci un nome per la regola');
      }
    });
    
    document.getElementById('scraper-cancel').addEventListener('click', cancelSelection);
  }
}

function finalizeRule() {
  // Invia la regola completata al background script
  chrome.runtime.sendMessage({
    action: 'interactiveSelectionComplete',
    rule: state.tempRule
  });
  
  // Pulisci lo stato e rimuovi gli elementi UI
  cleanupSelection();
}

function cancelSelection() {
  cleanupSelection();
}

function cleanupSelection() {
  // Rimuovi eventi listener
  document.removeEventListener('mousemove', handleMouseMove);
  document.removeEventListener('click', handleElementClick, true);
  
  // Rimuovi elementi UI
  const ui = document.getElementById('scraper-ui');
  if (ui) ui.remove();
  
  // Rimuovi highlight overlay
  if (highlightOverlay) highlightOverlay.style.display = 'none';
  
  // Rimuovi eventuali highlight temporanei
  const highlights = document.querySelectorAll('.scraper-highlight');
  highlights.forEach(el => el.remove());
  
  // Resetta lo stato
  state.isSelecting = false;
  state.selectionType = null;
  state.selectionStep = null;
  state.selectedContainerElement = null;
  state.tempRule = null;
}

function highlightElement(element, color) {
  // Crea un overlay per evidenziare l'elemento selezionato
  const highlight = document.createElement('div');
  highlight.className = 'scraper-highlight';
  const rect = element.getBoundingClientRect();
  
  highlight.style.top = `${window.scrollY + rect.top}px`;
  highlight.style.left = `${window.scrollX + rect.left}px`;
  highlight.style.width = `${rect.width}px`;
  highlight.style.height = `${rect.height}px`;
  
  if (color) {
    highlight.style.backgroundColor = color;
  }
  
  document.body.appendChild(highlight);
  return highlight;
}

// ESTRAZIONE DATI
function extractData(rules) {
  console.log('Extracting data with rules:', rules);
  
  if (!rules || rules.length === 0) {
    chrome.runtime.sendMessage({
      action: 'dataExtracted',
      data: []
    });
    return;
  }
  
  try {
    // Filtra le regole per tipo, escludendo 'next_button'
    const extractionRules = rules.filter(rule => rule.type !== 'next_button');
    
    // Se abbiamo regole di tipo 'multiple', estraiamo liste
    const multipleLists = [];
    const singleItems = {};
    
    // Prima estrai le liste, che possono contenere più elementi
    extractionRules.filter(rule => rule.type === 'multiple').forEach(rule => {
      const items = extractMultipleItems(rule);
      if (items.length > 0) {
        multipleLists.push(items);
      }
    });
    
    // Poi estrai i singoli campi
    extractionRules.filter(rule => rule.type === 'single').forEach(rule => {
      const item = extractSingleItem(rule);
      if (item) {
        Object.assign(singleItems, item);
      }
    });
    
    let extractedData = [];
    
    // Se abbiamo liste multiple, dobbiamo "zipparle" insieme
    if (multipleLists.length > 0) {
      // Trova la lista più lunga per determinare quanti item creare
      const maxItems = Math.max(...multipleLists.map(list => list.length));
      
      // Crea un oggetto per ogni item, combinando i dati di tutte le liste
      for (let i = 0; i < maxItems; i++) {
        const item = { ...singleItems };
        
        // Aggiungi i dati da ciascuna lista per questo indice
        multipleLists.forEach(list => {
          if (i < list.length) {
            Object.assign(item, list[i]);
          }
        });
        
        extractedData.push(item);
      }
    } else if (Object.keys(singleItems).length > 0) {
      // Se abbiamo solo singoli campi, crea un unico item
      extractedData.push(singleItems);
    }
    
    console.log('Extracted data:', extractedData);
    
    // Invia i dati estratti al background script
    chrome.runtime.sendMessage({
      action: 'dataExtracted',
      data: extractedData
    });
  } catch (error) {
    console.error('Error extracting data:', error);
    chrome.runtime.sendMessage({
      action: 'dataExtracted',
      data: [],
      error: error.message
    });
  }
}

function extractSingleItem(rule) {
  try {
    // Cerca l'elemento usando il selettore
    const element = document.querySelector(rule.selector);
    if (!element) {
      console.warn(`Element not found for selector: ${rule.selector}`);
      return null;
    }
    
    // Estrai il valore (testo dell'elemento)
    const value = element.textContent.trim();
    
    // Determina la chiave (nome del campo)
    let key = rule.manualKey;
    
    if (!key && rule.keySelector) {
      // Se non c'è una chiave manuale ma c'è un selettore per la chiave
      const keyElement = document.querySelector(rule.keySelector);
      if (keyElement) {
        key = keyElement.textContent.trim();
      }
    }
    
    // Se non abbiamo una chiave, usa il nome della regola
    if (!key) {
      key = rule.name;
    }
    
    // Crea un oggetto con la chiave e il valore
    const result = {};
    result[key] = value;
    return result;
  } catch (error) {
    console.error(`Error extracting single item for rule ${rule.name}:`, error);
    return null;
  }
}

function extractMultipleItems(rule) {
  try {
    // Cerca tutti gli elementi contenitore usando il selettore
    const containers = document.querySelectorAll(rule.selector);
    if (!containers || containers.length === 0) {
      console.warn(`No containers found for selector: ${rule.selector}`);
      return [];
    }
    
    const items = [];
    
    // Per ogni contenitore, estrai il valore e la chiave
    containers.forEach(container => {
      // Estrai il valore usando il selettore relativo
      let value = null;
      if (rule.relativeSelector) {
        const valueElement = container.querySelector(rule.relativeSelector);
        if (valueElement) {
          value = valueElement.textContent.trim();
        }
      } else {
        // Se non c'è un selettore relativo, usa il testo del contenitore stesso
        value = container.textContent.trim();
      }
      
      // Determina la chiave (nome del campo)
      let key = rule.manualKey;
      
      if (!key && rule.keySelector) {
        // Se non c'è una chiave manuale ma c'è un selettore per la chiave
        const keyElement = container.querySelector(rule.keySelector);
        if (keyElement) {
          key = keyElement.textContent.trim();
        }
      }
      
      // Se non abbiamo una chiave, usa il nome della regola
      if (!key) {
        key = rule.name;
      }
      
      // Crea un oggetto con la chiave e il valore
      if (value !== null) {
        const item = {};
        item[key] = value;
        items.push(item);
      }
    });
    
    return items;
  } catch (error) {
    console.error(`Error extracting multiple items for rule ${rule.name}:`, error);
    return [];
  }
}

// NAVIGAZIONE AUTOMATICA
function clickNextButton(selector) {
  try {
    // Cerca il pulsante "avanti" usando il selettore
    const nextButton = document.querySelector(selector);
    
    if (nextButton) {
      console.log('Next button found, clicking:', nextButton);
      // Simula un click sul pulsante
      nextButton.click();
    } else {
      console.warn('Next button not found for selector:', selector);
      // Invia un messaggio al background script per notificare che il pulsante "avanti" non è stato trovato
      chrome.runtime.sendMessage({
        action: 'nextButtonNotFound'
      });
    }
  } catch (error) {
    console.error('Error clicking next button:', error);
    chrome.runtime.sendMessage({
      action: 'nextButtonNotFound',
      error: error.message
    });
  }
}

// ANTEPRIMA DATI
function previewData(rules) {
  // Usa la stessa funzione di estrazione dati ma invia i risultati come anteprima
  try {
    // Estrai i dati
    // Filtra le regole per tipo, escludendo 'next_button'
    const extractionRules = rules.filter(rule => rule.type !== 'next_button');
    
    // Se abbiamo regole di tipo 'multiple', estraiamo liste
    const multipleLists = [];
    const singleItems = {};
    
    // Prima estrai le liste, che possono contenere più elementi
    extractionRules.filter(rule => rule.type === 'multiple').forEach(rule => {
      const items = extractMultipleItems(rule);
      if (items.length > 0) {
        multipleLists.push(items);
      }
    });
    
    // Poi estrai i singoli campi
    extractionRules.filter(rule => rule.type === 'single').forEach(rule => {
      const item = extractSingleItem(rule);
      if (item) {
        Object.assign(singleItems, item);
      }
    });
    
    let previewData = [];
    
    // Se abbiamo liste multiple, dobbiamo "zipparle" insieme
    if (multipleLists.length > 0) {
      // Trova la lista più lunga per determinare quanti item creare
      const maxItems = Math.max(...multipleLists.map(list => list.length));
      
      // Crea un oggetto per ogni item, combinando i dati di tutte le liste
      for (let i = 0; i < maxItems; i++) {
        const item = { ...singleItems };
        
        // Aggiungi i dati da ciascuna lista per questo indice
        multipleLists.forEach(list => {
          if (i < list.length) {
            Object.assign(item, list[i]);
          }
        });
        
        previewData.push(item);
      }
    } else if (Object.keys(singleItems).length > 0) {
      // Se abbiamo solo singoli campi, crea un unico item
      previewData.push(singleItems);
    }
    
    // Limita la quantità di dati da inviare per l'anteprima
    if (previewData.length > 5) {
      previewData = previewData.slice(0, 5);
    }
    
    // Invia i dati di anteprima al background script
    chrome.runtime.sendMessage({
      action: 'previewDataResult',
      data: previewData
    });
  } catch (error) {
    console.error('Error generating preview data:', error);
    chrome.runtime.sendMessage({
      action: 'previewDataResult',
      data: [],
      error: error.message
    });
  }
}

// UTILITIES PER LA GENERAZIONE DI SELETTORI
function generateSelector(element) {
  // Prova a generare un selettore CSS ottimale per l'elemento
  
  // 1. Se l'elemento ha un ID, usa quello (è il più specifico)
  if (element.id) {
    return `#${cssEscape(element.id)}`;
  }
  
  // 2. Se l'elemento ha una classe unica, usala
  if (element.className && typeof element.className === 'string') {
    const classes = element.className.trim().split(/\s+/);
    for (const className of classes) {
      // Verifica se questa classe è unica nella pagina
      if (document.getElementsByClassName(className).length === 1) {
        return `.${cssEscape(className)}`;
      }
    }
  }
  
  // 3. Prova con attributi specifici comuni
  const specificAttributes = ['data-id', 'data-test-id', 'data-testid', 'name', 'title', 'aria-label'];
  for (const attr of specificAttributes) {
    if (element.hasAttribute(attr)) {
      const value = element.getAttribute(attr);
      const selector = `${element.tagName.toLowerCase()}[${attr}="${value}"]`;
      if (document.querySelectorAll(selector).length === 1) {
        return selector;
      }
    }
  }
  
  // 4. Costruisci un percorso CSS più specifico usando nth-child
  let current = element;
  let path = [];
  
  while (current && current !== document.body && current !== document.documentElement) {
    let selector = current.tagName.toLowerCase();
    
    // Se è un tag comune, aggiungi più specificità
    if (['div', 'span', 'p', 'a', 'li', 'ul', 'ol'].includes(selector)) {
      const parent = current.parentElement;
      if (parent) {
        // Find the index of the current element among its siblings of the same type
        const siblings = Array.from(parent.children).filter(el => el.tagName === current.tagName);
        const index = siblings.indexOf(current);
        
        if (siblings.length > 1) {
          selector += `:nth-child(${index + 1})`;
        }
        
        // Add any unique classes
        if (current.className && typeof current.className === 'string') {
          const classes = current.className.trim().split(/\s+/).filter(Boolean);
          for (const className of classes) {
            // Skip very common or dynamic classes
            if (!className.match(/^(active|selected|hover|focus|hidden|visible|disabled|enabled)$/)) {
              selector += `.${cssEscape(className)}`;
              break; // Just use one class to avoid over-specification
            }
          }
        }
      }
    }
    
    path.unshift(selector);
    
    // Verifica se il selettore attuale è già sufficientemente specifico
    if (path.length >= 2) {
      const testSelector = path.join(' > ');
      if (document.querySelectorAll(testSelector).length === 1) {
        return testSelector;
      }
    }
    
    current = current.parentElement;
  }
  
  // Limita la profondità del selettore a 4 livelli per evitare selettori troppo lunghi
  if (path.length > 4) {
    path = path.slice(path.length - 4);
  }
  
  return path.join(' > ');
}

function generateRelativeSelector(element, container) {
  // Genera un selettore CSS relativo a un elemento contenitore
  if (!element || !container || !container.contains(element)) {
    console.error('Invalid elements for relative selector generation');
    return '';
  }
  
  // Se l'elemento ha un ID, usa quello come selettore relativo
  if (element.id) {
    return `#${cssEscape(element.id)}`;
  }
  
  // Se l'elemento ha una classe unica all'interno del contenitore, usala
  if (element.className && typeof element.className === 'string') {
    const classes = element.className.trim().split(/\s+/).filter(Boolean);
    for (const className of classes) {
      // Verifica se questa classe è unica all'interno del contenitore
      if (container.getElementsByClassName(className).length === 1) {
        return `.${cssEscape(className)}`;
      }
    }
  }
  
  // Prova con attributi specifici comuni
  const specificAttributes = ['data-id', 'data-test-id', 'data-testid', 'name', 'title', 'aria-label'];
  for (const attr of specificAttributes) {
    if (element.hasAttribute(attr)) {
      const value = element.getAttribute(attr);
      const selector = `${element.tagName.toLowerCase()}[${attr}="${value}"]`;
      if (container.querySelectorAll(selector).length === 1) {
        return selector;
      }
    }
  }
  
  // Costruisci un percorso relativo dall'elemento al contenitore utilizzando nth-child
  let path = [];
  let current = element;
  
  while (current && current !== document.body && current !== container) {
    let selector = current.tagName.toLowerCase();
    
    // Se è un tag comune, aggiungi più specificità
    if (['div', 'span', 'p', 'a', 'li', 'ul', 'ol'].includes(selector)) {
      const parent = current.parentElement;
      if (parent) {
        // Trova l'indice dell'elemento tra i suoi fratelli dello stesso tipo
        const siblings = Array.from(parent.children).filter(el => el.tagName === current.tagName);
        const index = siblings.indexOf(current);
        
        if (siblings.length > 1) {
          selector += `:nth-child(${index + 1})`;
        }
        
        // Aggiungi eventuali classi uniche
        if (current.className && typeof current.className === 'string') {
          const classes = current.className.trim().split(/\s+/).filter(Boolean);
          for (const className of classes) {
            // Salta classi molto comuni o dinamiche
            if (!className.match(/^(active|selected|hover|focus|hidden|visible|disabled|enabled)$/)) {
              selector += `.${cssEscape(className)}`;
              break; // Usa solo una classe per evitare sovra-specificazione
            }
          }
        }
      }
    }
    
    path.unshift(selector);
    
    // Verifica se il selettore attuale è già sufficientemente specifico
    if (path.length >= 2) {
      const testSelector = path.join(' > ');
      if (container.querySelectorAll(testSelector).length === 1) {
        return testSelector;
      }
    }
    
    current = current.parentElement;
  }
  
  // Limita la profondità del selettore a 4 livelli
  if (path.length > 4) {
    path = path.slice(path.length - 4);
  }
  
  return path.join(' > ');
}

// Utility per l'escape di caratteri speciali in selettori CSS
function cssEscape(value) {
  // Escape dei caratteri speciali nei selettori CSS
  if (CSS && CSS.escape) {
    return CSS.escape(value);
  } else {
    // Implementazione fallback per browser che non supportano CSS.escape
    return value.replace(/[!"#$%&'()*+,./:;<=>?@[\\\]^`{|}~]/g, '\\$&')
                .replace(/^-/, '\\-');
  }
}