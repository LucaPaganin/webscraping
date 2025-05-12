document.addEventListener('DOMContentLoaded', () => {
  // Elementi UI
  const statusDisplay = document.getElementById('status-display');
  const btnStart = document.getElementById('btn-start');
  const btnPause = document.getElementById('btn-pause');
  const btnStop = document.getElementById('btn-stop');
  const btnAddSingle = document.getElementById('btn-add-single');
  const btnAddMultiple = document.getElementById('btn-add-multiple');
  const btnAddNext = document.getElementById('btn-add-next');
  const btnPreview = document.getElementById('btn-preview');
  const btnDownload = document.getElementById('btn-download');
  const delayInput = document.getElementById('delay-input');
  const rulesList = document.getElementById('rules-list');
  const previewContainer = document.getElementById('preview-container');

  // Stato locale
  let scrapingRules = [];
  let automationState = { status: 'idle', currentPageUrl: null, delayMs: 1000 };

  // Inizializzazione: carica regole e stato dall'archivio
  init();

  // Gestione eventi UI
  btnStart.addEventListener('click', startAutomation);
  btnPause.addEventListener('click', pauseAutomation);
  btnStop.addEventListener('click', stopAutomation);
  btnAddSingle.addEventListener('click', () => startInteractiveSelection('singleData'));
  btnAddMultiple.addEventListener('click', () => startInteractiveSelection('multipleContainer'));
  btnAddNext.addEventListener('click', () => startInteractiveSelection('nextButton'));
  btnPreview.addEventListener('click', requestPreview);
  btnDownload.addEventListener('click', downloadData);
  delayInput.addEventListener('change', updateDelay);

  // Gestisce messaggi in arrivo dal background script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Popup received message:', message);

    if (message.event === 'selectionComplete') {
      handleSelectionComplete(message.rule);
    } else if (message.event === 'automationStatusUpdate') {
      updateAutomationStatus(message.status, message.currentUrl);
    } else if (message.event === 'previewData') {
      updatePreviewData(message.data);
    } else if (message.event === 'downloadData') {
      processDownload(message.data);
    } else if (message.event === 'error') {
      // Visualizza l'errore all'utente
      showError(message.message);
    }
  });

  // Funzioni di supporto
  async function init() {
    try {
      const data = await chrome.storage.local.get(['scrapingRules', 'automationState']);
      if (data.scrapingRules) {
        scrapingRules = data.scrapingRules;
        renderRulesList();
      }
      if (data.automationState) {
        automationState = data.automationState;
        updateAutomationUI();
      }
    } catch (error) {
      console.error('Error loading data from storage:', error);
    }
  }

  function updateAutomationUI() {
    // Aggiorna UI in base allo stato dell'automazione
    switch (automationState.status) {
      case 'idle':
        statusDisplay.textContent = 'Idle';
        statusDisplay.className = 'status-indicator';
        btnStart.disabled = false;
        btnPause.disabled = true;
        btnStop.disabled = true;
        btnDownload.disabled = !hasExtractedData();
        break;
      case 'running':
        statusDisplay.textContent = `In esecuzione: ${automationState.currentPageUrl || 'N/A'}`;
        statusDisplay.className = 'status-indicator status-running';
        btnStart.disabled = true;
        btnPause.disabled = false;
        btnStop.disabled = false;
        btnDownload.disabled = true;
        break;
      case 'paused':
        statusDisplay.textContent = 'In pausa';
        statusDisplay.className = 'status-indicator status-paused';
        btnStart.disabled = false;
        btnPause.disabled = true;
        btnStop.disabled = false;
        btnDownload.disabled = false;
        break;
    }
  }

  function hasExtractedData() {
    // Verifica se ci sono dati estratti disponibili per il download
    // Questo dato verrà mantenuto nel background.js
    return automationState.status === 'paused' || automationState.status === 'idle';
  }

  function startAutomation() {
    // Aggiorna lo stato locale e invia messaggio al background per avviare l'automazione
    const delayMs = parseInt(delayInput.value, 10) || 1000;
    chrome.runtime.sendMessage({
      action: 'startAutomation',
      delay: delayMs
    });
  }

  function pauseAutomation() {
    // Invia messaggio al background per mettere in pausa l'automazione
    chrome.runtime.sendMessage({ action: 'pauseAutomation' });
  }

  function stopAutomation() {
    // Invia messaggio al background per fermare l'automazione
    chrome.runtime.sendMessage({ action: 'stopAutomation' });
  }

  function startInteractiveSelection(selectionType) {
    // Invia messaggio al background per iniziare la selezione interattiva
    chrome.runtime.sendMessage({
      action: 'startInteractiveSelection',
      selectionType: selectionType
    });
    
    // Chiudi il popup per mostrare la pagina
    // window.close();
  }

  function requestPreview() {
    // Invia messaggio al background per richiedere l'anteprima dei dati
    chrome.runtime.sendMessage({ action: 'requestPreview' });
  }

  function downloadData() {
    // Invia messaggio al background per richiedere i dati estratti per il download
    chrome.runtime.sendMessage({ action: 'requestDownloadData' });
  }

  function updateDelay() {
    // Aggiorna il delay nell'automationState locale e in storage
    const delayMs = parseInt(delayInput.value, 10) || 1000;
    automationState.delayMs = delayMs;
    saveAutomationState();
  }

  async function saveAutomationState() {
    try {
      await chrome.storage.local.set({ automationState });
    } catch (error) {
      console.error('Error saving automation state:', error);
    }
  }

  async function saveScrapingRules() {
    try {
      await chrome.storage.local.set({ scrapingRules });
      renderRulesList();
    } catch (error) {
      console.error('Error saving scraping rules:', error);
    }
  }

  function renderRulesList() {
    // Visualizza la lista delle regole
    rulesList.innerHTML = '';
    
    if (scrapingRules.length === 0) {
      const emptyItem = document.createElement('div');
      emptyItem.className = 'rule-item';
      emptyItem.textContent = 'Nessuna regola definita';
      rulesList.appendChild(emptyItem);
      return;
    }

    scrapingRules.forEach((rule, index) => {
      const ruleItem = document.createElement('div');
      ruleItem.className = 'rule-item';
      
      const ruleInfo = document.createElement('span');
      ruleInfo.textContent = `${index + 1}. ${rule.name} (${getTypeDisplay(rule.type)})`;
      ruleItem.appendChild(ruleInfo);
      
      const buttonsContainer = document.createElement('div');
      
      // Pulsante modifica (da implementare)
      const editBtn = document.createElement('button');
      editBtn.textContent = '✏️';
      editBtn.className = 'btn btn-secondary';
      editBtn.style.padding = '2px 5px';
      editBtn.style.marginRight = '5px';
      editBtn.title = 'Modifica regola';
      editBtn.addEventListener('click', () => editRule(index));
      
      // Pulsante elimina
      const deleteBtn = document.createElement('button');
      deleteBtn.textContent = '🗑️';
      deleteBtn.className = 'btn btn-danger';
      deleteBtn.style.padding = '2px 5px';
      deleteBtn.title = 'Elimina regola';
      deleteBtn.addEventListener('click', () => deleteRule(index));
      
      buttonsContainer.appendChild(editBtn);
      buttonsContainer.appendChild(deleteBtn);
      
      ruleItem.appendChild(buttonsContainer);
      rulesList.appendChild(ruleItem);
    });
  }

  function getTypeDisplay(type) {
    switch (type) {
      case 'single': return 'Singolo';
      case 'multiple': return 'Lista';
      case 'next_button': return 'Pulsante Avanti';
      default: return type;
    }
  }

  function deleteRule(index) {
    if (confirm(`Sei sicuro di voler eliminare la regola "${scrapingRules[index].name}"?`)) {
      scrapingRules.splice(index, 1);
      saveScrapingRules();
    }
  }

  function editRule(index) {
    // Da implementare: modifica di una regola esistente
    alert('Funzionalità di modifica non ancora implementata');
  }

  function handleSelectionComplete(rule) {
    // Aggiunge una nuova regola alla lista
    if (!rule) return;
    
    // Genera un ID univoco se non presente
    if (!rule.id) {
      rule.id = `rule_${Date.now()}`;
    }
    
    // Se è una regola di tipo 'nextButton', sostituisci eventuali regole esistenti dello stesso tipo
    if (rule.type === 'next_button') {
      scrapingRules = scrapingRules.filter(r => r.type !== 'next_button');
    }
    
    scrapingRules.push(rule);
    saveScrapingRules();
  }

  function updateAutomationStatus(status, currentUrl) {
    automationState.status = status;
    automationState.currentPageUrl = currentUrl;
    updateAutomationUI();
    saveAutomationState();
  }

  function updatePreviewData(data) {
    // Visualizza i dati di anteprima
    if (!data || data.length === 0) {
      previewContainer.textContent = 'Nessun dato estratto';
      return;
    }
    
    // Formatta il JSON con indentazione per una migliore leggibilità
    previewContainer.textContent = JSON.stringify(data, null, 2);
  }

  function processDownload(data) {
    if (!data || data.length === 0) {
      alert('Nessun dato disponibile per il download');
      return;
    }
    
    // Crea un Blob con i dati JSON
    const jsonData = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json' });
    
    // Crea un URL per il blob
    const url = URL.createObjectURL(blob);
    
    // Crea un link di download e simula il click
    const downloadLink = document.createElement('a');
    downloadLink.href = url;
    downloadLink.download = `scraped_data_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    
    // Pulisce
    setTimeout(() => {
      document.body.removeChild(downloadLink);
      URL.revokeObjectURL(url);
    }, 100);
  }

  // Visualizza un messaggio di errore nel popup
  function showError(message) {
    const errorContainer = document.createElement('div');
    errorContainer.className = 'error-message';
    errorContainer.style.cssText = 'background-color: #ffebee; color: #c62828; padding: 10px; margin-bottom: 10px; border-radius: 4px; border-left: 4px solid #c62828;';
    errorContainer.textContent = message;
    
    // Aggiungi un pulsante di chiusura
    const closeBtn = document.createElement('button');
    closeBtn.textContent = '×';
    closeBtn.style.cssText = 'float: right; border: none; background: transparent; font-size: 18px; cursor: pointer; color: #c62828;';
    closeBtn.addEventListener('click', () => {
      errorContainer.remove();
    });
    errorContainer.prepend(closeBtn);
    
    // Aggiungi all'inizio del body
    document.body.insertBefore(errorContainer, document.body.firstChild);
    
    // Auto-dismiss dopo 5 secondi
    setTimeout(() => {
      if (errorContainer.parentNode) {
        errorContainer.remove();
      }
    }, 5000);
  }
});