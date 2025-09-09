// Global variables for Firebase config and app ID (provided by Canvas environment)
const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-app-id';

// --- DOM Elements ---
const scenarioInput = document.getElementById('scenario');
const urgencySelect = document.getElementById('urgency');
const detailsTextarea = document.getElementById('details');
const generateExcuseBtn = document.getElementById('generateExcuseBtn');
const buttonText = document.getElementById('buttonText');
const loadingSpinner = document.getElementById('loadingSpinner');
const excuseOutputDiv = document.getElementById('excuseOutput');
const generatedExcuseText = document.getElementById('generatedExcuseText');
// Removed references to generateProofBtn, triggerEmergencyBtn, generateApologyBtn
const excuseHistoryDiv = document.getElementById('excuseHistory');
const noHistoryMessage = document.getElementById('noHistoryMessage');

// --- Event Listeners ---
generateExcuseBtn.addEventListener('click', generateExcuse);
// Removed event listeners for generateProofBtn, triggerEmergencyBtn, generateApologyBtn


// --- Constants ---
// Point to your Flask backend URL
const BACKEND_URL = 'http://127.0.0.1:5000'; // Default Flask development server URL
const HISTORY_KEY = `excuse_history_${appId}`; // Unique key for local storage

// --- Functions ---

/**
 * Displays a temporary message to the user.
 * @param {string} message - The message to display.
 * @param {string} type - Type of message (e.g., 'error', 'info').
 */
function showMessage(message, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `p-3 mb-4 rounded-lg text-sm ${type === 'error' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`;
    messageDiv.textContent = message;
    excuseOutputDiv.parentNode.insertBefore(messageDiv, excuseOutputDiv); // Insert before excuse output
    setTimeout(() => {
        messageDiv.remove();
    }, 5000); // Remove after 5 seconds
}

/**
 * Generates an excuse by calling the Python backend.
 */
async function generateExcuse() {
    const scenario = scenarioInput.value.trim();
    const urgency = urgencySelect.value;
    const details = detailsTextarea.value.trim();

    if (!scenario) {
        showMessage('Please enter a scenario to generate an excuse.', 'error');
        return;
    }

    // Show loading state
    generateExcuseBtn.disabled = true;
    buttonText.textContent = 'Generating...';
    loadingSpinner.classList.remove('hidden');
    excuseOutputDiv.classList.add('hidden'); // Hide previous output

    try {
        const response = await fetch(`${BACKEND_URL}/generate_excuse_direct`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario, urgency, details })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Backend error: ${response.status} - ${errorData.error || 'Unknown error'}`);
        }

        const result = await response.json();

        if (result.excuse) {
            const excuse = result.excuse;
            generatedExcuseText.textContent = excuse;
            excuseOutputDiv.classList.remove('hidden');
            saveExcuseToHistory(scenario, urgency, details, excuse);
        } else {
            showMessage('Failed to generate excuse. Unexpected backend response structure.', 'error');
            console.error('Unexpected backend response:', result);
        }
    } catch (error) {
        showMessage(`Error generating excuse: ${error.message}. Please ensure the Python backend is running and accessible.`, 'error');
        console.error('Fetch error:', error);
    } finally {
        // Hide loading state
        generateExcuseBtn.disabled = false;
        buttonText.textContent = 'Generate Excuse';
        loadingSpinner.classList.add('hidden');
    }
}

// Removed callBackendPlaceholder function as it's no longer used


/**
 * Saves the generated excuse to local storage.
 * @param {string} scenario
 * @param {string} urgency
 * @param {string} details
 * @param {string} excuse
 */
function saveExcuseToHistory(scenario, urgency, details, excuse) {
    let history = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
    const newEntry = {
        id: Date.now(), // Unique ID
        timestamp: new Date().toLocaleString(),
        scenario,
        urgency,
        details,
        excuse,
        favorite: false // New field for favorites
    };
    history.unshift(newEntry); // Add to the beginning
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    renderExcuseHistory();
}

/**
 * Renders the excuse history from local storage.
 */
function renderExcuseHistory() {
    const history = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
    excuseHistoryDiv.innerHTML = ''; // Clear existing history

    if (history.length === 0) {
        noHistoryMessage.classList.remove('hidden');
        excuseHistoryDiv.appendChild(noHistoryMessage);
        return;
    } else {
        noHistoryMessage.classList.add('hidden');
    }

    history.forEach(entry => {
        const excuseCard = document.createElement('div');
        excuseCard.className = 'card p-4 border border-gray-200 rounded-lg';
        excuseCard.innerHTML = `
            <div class="flex justify-between items-start mb-2">
                <h4 class="text-lg font-medium text-gray-800">Scenario: ${entry.scenario}</h4>
                <button data-id="${entry.id}" class="favorite-btn text-gray-400 hover:text-yellow-500 transition-colors ${entry.favorite ? 'text-yellow-500' : ''}">
                            &#9733; <!-- Star icon -->
                        </button>
                    </div>
                    <p class="text-gray-600 text-sm mb-1"><strong>Urgency:</strong> ${entry.urgency}</p>
                    <p class="text-gray-600 text-sm mb-1"><strong>Details:</strong> ${entry.details || 'N/A'}</p>
                    <p class="text-gray-800 mt-2 leading-relaxed">${entry.excuse}</p>
                    <p class="text-gray-500 text-xs mt-3">Generated on: ${entry.timestamp}</p>
                    <div class="mt-3 flex gap-2">
                        <button data-id="${entry.id}" class="copy-btn btn-secondary text-xs px-2 py-1">Copy</button>
                        <button data-id="${entry.id}" class="delete-btn btn-secondary text-xs px-2 py-1">Delete</button>
                    </div>
                `;
        excuseHistoryDiv.appendChild(excuseCard);
    });

    // Add event listeners for copy, delete, and favorite buttons
    excuseHistoryDiv.querySelectorAll('.copy-btn').forEach(button => {
        button.addEventListener('click', (event) => {
            const id = parseInt(event.target.dataset.id);
            const entry = history.find(e => e.id === id);
            if (entry) {
                copyToClipboard(entry.excuse);
                showMessage('Excuse copied to clipboard!', 'info');
            }
        });
    });

    excuseHistoryDiv.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', (event) => {
            const id = parseInt(event.target.dataset.id);
            deleteExcuse(id);
        });
    });

    excuseHistoryDiv.querySelectorAll('.favorite-btn').forEach(button => {
        button.addEventListener('click', (event) => {
            const id = parseInt(event.target.dataset.id);
            toggleFavorite(id);
        });
    });
}

/**
 * Copies text to the clipboard.
 * @param {string} text - The text to copy.
 */
function copyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
}

/**
 * Deletes an excuse from local storage.
 * @param {number} id - The ID of the excuse to delete.
 */
function deleteExcuse(id) {
    let history = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
    history = history.filter(entry => entry.id !== id);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    renderExcuseHistory();
    showMessage('Excuse deleted.', 'info');
}

/**
 * Toggles the favorite status of an excuse.
 * @param {number} id - The ID of the excuse to toggle.
 */
function toggleFavorite(id) {
    let history = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
    history = history.map(entry => {
        if (entry.id === id) {
            return { ...entry, favorite: !entry.favorite };
        }
        return entry;
    });
    // Sort to bring favorites to the top
    history.sort((a, b) => (b.favorite - a.favorite) || (b.id - a.id));
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    renderExcuseHistory();
    showMessage('Favorite status updated!', 'info');
}

// Initial render of history when the page loads
document.addEventListener('DOMContentLoaded', renderExcuseHistory);
