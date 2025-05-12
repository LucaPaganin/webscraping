// Stato globale dell'estensione
let automationState = {
  status: 'idle',    // 'idle', 'running', 'paused'
  currentPageUrl: null,
  currentTabId: null,
  delayMs: 1000,
  timeoutId: null
};

// Array per memorizzare i dati estratti durante l'automazione
let extractedData = [];

// Regole di estrazione caricate da storage
let scrapingRules = [];

// Inizializzazione e caricamento dati da storage
chrome.runtime.onInstalled.addListener(() => {
  loadStateFromStorage();
});

// Gestione dei messaggi
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Background received message:', message, 'from:', sender);

  // Gestione dei messaggi dal popup
  if (message.action === 'startAutomation') {
    startAutomation(message.delay);
  } else if (message.action === 'pauseAutomation') {
    pauseAutomation();
  } else if (message.action === 'stopAutomation') {
    stopAutomation();
  } else if (message.action === 'startInteractiveSelection') {
    startInteractiveSelection(message.selectionType);
  } else if (message.action === 'requestPreview') {
    requestPreview();
  } else if (message.action === 'requestDownloadData') {
    sendDataForDownload();
  }

  // Gestione dei messaggi dal content script
  else if (message.action === 'interactiveSelectionComplete') {
    handleSelectionComplete(message.rule);
  } else if (message.action === 'dataExtracted') {
    handleDataExtracted(message.data);
  } else if (message.action === 'nextButtonNotFound') {
    handleNextButtonNotFound();
  } else if (message.action === 'previewDataResult') {
    sendPreviewToPopup(message.data);
  } else if (message.action === 'pageLoaded') {
    handlePageLoaded(sender.tab.id);
  }

  return true; // Indica che la risposta potrebbe essere asincrona
});

// Listener per il caricamento completo delle pagine
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && 
      automationState.status === 'running' && 
      tabId === automationState.currentTabId) {
    console.log('Tab loaded completely:', tabId, tab.url);
    
    // Attendiamo un po' per assicurarci che la pagina sia completamente renderizzata
    setTimeout(() => {
      // Inietta il content script
      injectContentScript(tabId, () => {
        // Invia un messaggio al content script per iniziare l'estrazione
        chrome.tabs.sendMessage(tabId, { 
          action: 'extractData', 
          rules: scrapingRules 
        }).catch(error => {
          console.error('Error sending message to content script:', error);
        });
      });
    }, 500); // Attendi 500ms per dare tempo alla pagina di renderizzare completamente
  }
});

// Funzioni di gestione automazione
async function startAutomation(delay) {
  console.log('Starting automation with delay:', delay);
  
  // Carica le regole da storage
  await loadRulesFromStorage();
  
  // Se non ci sono regole, avvisa l'utente
  if (scrapingRules.length === 0) {
    notifyPopup({ 
      event: 'error', 
      message: 'Nessuna regola di estrazione definita. Aggiungi almeno una regola prima di iniziare.' 
    });
    return;
  }
  
  // Verifica se esiste una regola per il pulsante "avanti"
  const hasNextButton = scrapingRules.some(rule => rule.type === 'next_button');
  if (!hasNextButton) {
    notifyPopup({ 
      event: 'error', 
      message: 'Nessuna regola per il pulsante "avanti" definita. Aggiungi una regola per la paginazione.' 
    });
    return;
  }
  
  // Aggiorna lo stato
  automationState.status = 'running';
  automationState.delayMs = delay || 1000;
  saveAutomationState();
  
  // Resetta i dati estratti
  extractedData = [];
  
  // Invia un messaggio al popup per aggiornare l'UI
  updatePopupStatus();
  
  // Ottieni la tab attiva
  try {
    const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!activeTab) throw new Error('No active tab found');
    
    automationState.currentTabId = activeTab.id;
    automationState.currentPageUrl = activeTab.url;
    saveAutomationState();
    
    // Inietta il content script nella tab attiva
    injectContentScript(activeTab.id, () => {
      // Invia un messaggio al content script per iniziare l'estrazione
      chrome.tabs.sendMessage(activeTab.id, { 
        action: 'extractData', 
        rules: scrapingRules 
      }).catch(error => {
        console.error('Error sending message to content script:', error);
      });
    });
  } catch (error) {
    console.error('Error starting automation:', error);
    stopAutomation();
  }
}

function pauseAutomation() {
  console.log('Pausing automation');
  
  // Ferma eventuali timeout in corso
  if (automationState.timeoutId) {
    clearTimeout(automationState.timeoutId);
    automationState.timeoutId = null;
  }
  
  automationState.status = 'paused';
  saveAutomationState();
  updatePopupStatus();
}

function stopAutomation() {
  console.log('Stopping automation');
  
  // Ferma eventuali timeout in corso
  if (automationState.timeoutId) {
    clearTimeout(automationState.timeoutId);
    automationState.timeoutId = null;
  }
  
  automationState.status = 'idle';
  saveAutomationState();
  updatePopupStatus();
}

function handleDataExtracted(data) {
  console.log('Data extracted:', data);
  
  // Aggiungi i dati estratti all'array globale
  if (Array.isArray(data)) {
    extractedData = extractedData.concat(data);
  } else if (data) {
    extractedData.push(data);
  }
  
  // Se l'automazione è in corso, procedi con il click sul pulsante "avanti"
  if (automationState.status === 'running') {
    // Programma il click sul pulsante "avanti" dopo il delay configurato
    automationState.timeoutId = setTimeout(() => {
      clickNextButton();
    }, automationState.delayMs);
  }
}

function clickNextButton() {
  // Trova la regola per il pulsante "avanti"
  const nextButtonRule = scrapingRules.find(rule => rule.type === 'next_button');
  if (!nextButtonRule) {
    console.error('Next button rule not found');
    handleNextButtonNotFound();
    return;
  }
  
  // Invia un messaggio al content script per cliccare il pulsante
  chrome.tabs.sendMessage(automationState.currentTabId, {
    action: 'clickNextButton',
    selector: nextButtonRule.selector
  }).catch(error => {
    console.error('Error sending click next button message:', error);
    handleNextButtonNotFound(); // Treat communication error as button not found
  });
}

function handleNextButtonNotFound() {
  console.log('Next button not found, stopping automation');
  
  // Ferma l'automazione quando non viene trovato il pulsante "avanti"
  automationState.status = 'idle';
  saveAutomationState();
  updatePopupStatus();
}

async function startInteractiveSelection(selectionType) {
  try {
    // Ottieni la tab attiva
    const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!activeTab) throw new Error('No active tab found');
    
    // Inietta il content script
    injectContentScript(activeTab.id, () => {
      // Invia un messaggio al content script per iniziare la selezione interattiva
      chrome.tabs.sendMessage(activeTab.id, {
        action: 'startInteractiveSelection',
        selectionType: selectionType
      }).catch(error => {
        console.error('Error sending interactive selection message:', error);
      });
    });
  } catch (error) {
    console.error('Error starting interactive selection:', error);
  }
}

function handleSelectionComplete(rule) {
  console.log('Selection complete, rule created:', rule);
  
  // Invia la regola al popup
  chrome.runtime.sendMessage({
    event: 'selectionComplete',
    rule: rule
  });
}

async function requestPreview() {
  try {
    // Carica le regole da storage
    await loadRulesFromStorage();
    
    // Ottieni la tab attiva
    const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!activeTab) throw new Error('No active tab found');
    
    // Inietta il content script
    injectContentScript(activeTab.id, () => {
      // Invia un messaggio al content script per eseguire l'anteprima
      chrome.tabs.sendMessage(activeTab.id, {
        action: 'previewData',
        rules: scrapingRules
      }).catch(error => {
        console.error('Error sending preview data message:', error);
      });
    });
  } catch (error) {
    console.error('Error requesting preview:', error);
  }
}

function sendPreviewToPopup(data) {
  // Invia i dati di anteprima al popup
  chrome.runtime.sendMessage({
    event: 'previewData',
    data: data
  });
}

function sendDataForDownload() {
  // Invia i dati estratti al popup per il download
  chrome.runtime.sendMessage({
    event: 'downloadData',
    data: extractedData
  });
}

function handlePageLoaded(tabId) {
  console.log('Page loaded in tab:', tabId);
  
  // Se l'automazione è in esecuzione e questa è la tab corretta
  if (automationState.status === 'running' && tabId === automationState.currentTabId) {
    // Aggiorna l'URL corrente
    chrome.tabs.get(tabId, (tab) => {
      automationState.currentPageUrl = tab.url;
      saveAutomationState();
      updatePopupStatus();
    });
  }
}

// Funzioni di utilità
function injectContentScript(tabId, callback) {
  // Verifichiamo prima se il content script è già stato iniettato
  chrome.tabs.sendMessage(tabId, { action: 'ping' })
    .then(() => {
      console.log('Content script already injected');
      if (callback) callback();
    })
    .catch(() => {
      // Se c'è un errore, significa che il content script non è iniettato o non risponde
      chrome.scripting.executeScript({
        target: { tabId: tabId },
        files: ['content.js']
      }).then(() => {
        console.log('Content script injected');
        if (callback) callback();
      }).catch(error => {
        console.error('Error injecting content script:', error);
      });
    });
}

function updatePopupStatus() {
  // Invia lo stato dell'automazione al popup
  chrome.runtime.sendMessage({
    event: 'automationStatusUpdate',
    status: automationState.status,
    currentUrl: automationState.currentPageUrl
  });
}

async function loadStateFromStorage() {
  try {
    const data = await chrome.storage.local.get(['automationState', 'scrapingRules']);
    if (data.automationState) {
      // Assicurati che lo stato sia sempre pulito all'avvio
      automationState = { 
        ...data.automationState, 
        status: 'idle', // Force idle on load
        timeoutId: null 
      };
    }
    if (data.scrapingRules) {
      scrapingRules = data.scrapingRules;
    }
  } catch (error) {
    console.error('Error loading state from storage:', error);
  }
}

async function loadRulesFromStorage() {
  try {
    const data = await chrome.storage.local.get('scrapingRules');
    if (data.scrapingRules) {
      scrapingRules = data.scrapingRules;
    } else {
      scrapingRules = [];
    }
    console.log('Loaded rules:', scrapingRules);
  } catch (error) {
    console.error('Error loading rules from storage:', error);
    scrapingRules = [];
  }
}

// Funzione per inviare notifiche al popup
function notifyPopup(message) {
  chrome.runtime.sendMessage(message).catch(error => {
    // Gestisce l'errore se il popup non è aperto
    console.log('Could not notify popup:', error);
  });
}