// Common utility functions shared between popup.js and background.js

export async function saveAutomationState(automationState) {
  try {
    await chrome.storage.local.set({ automationState });
    console.log('Automation state saved:', automationState);
  } catch (error) {
    console.error('Error saving automation state:', error);
  }
}
