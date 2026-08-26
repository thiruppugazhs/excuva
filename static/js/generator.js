// generator.js - 7-Step Intelligent Excuse Generator, Versions, Smart AI Modifications & Editor
import { api, showToast, copyToClipboard } from './api.js';

export class GeneratorManager {
  constructor() {
    this.currentStep = 1;
    this.totalSteps = 6;
    this.currentExcuse = null;

    // Version management
    this.versions = [];
    this.activeVersionIndex = 0;

    // Wizard parameters
    this.situation = '';
    this.recipient = 'Manager';
    this.customRecipient = '';
    this.situationType = 'Missed deadline';
    this.tone = 'Professional';
    this.length = 'Medium';
    this.deliveryMethod = 'Email';

    this.isEditing = false;
  }

  init() {
    this.bindEvents();
    this.updateCharacterCount();
  }

  bindEvents() {
    // 1. Step 1: Character count & Suggestions
    const situationInput = document.getElementById('gen-situation');
    if (situationInput) {
      situationInput.addEventListener('input', () => {
        this.situation = situationInput.value;
        this.updateCharacterCount();
        this.autoInferSituationType(this.situation);
      });
    }

    document.querySelectorAll('.scenario-suggestion').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const val = e.currentTarget.dataset.scenario || '';
        if (situationInput) {
          situationInput.value = val;
          this.situation = val;
          this.updateCharacterCount();
          this.autoInferSituationType(val);
          situationInput.focus();
        }
      });
    });

    // 47. Smart preset chips
    document.querySelectorAll('.smart-preset-chip').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tone = e.currentTarget.dataset.tone;
        const recipient = e.currentTarget.dataset.recipient;
        if (tone) {
          this.tone = tone;
          const radioTone = document.querySelector(`input[name="wizard-tone"][value="${tone}"]`);
          if (radioTone) {
            radioTone.checked = true;
            document.querySelectorAll('#tone-card-group .radio-card').forEach(c => c.classList.remove('active-card'));
            const card = radioTone.closest('.radio-card');
            if (card) card.classList.add('active-card');
          }
        }
        if (recipient) {
          this.recipient = recipient;
          const radioRec = document.querySelector(`input[name="wizard-recipient"][value="${recipient}"]`);
          if (radioRec) {
            radioRec.checked = true;
            document.querySelectorAll('#recipient-card-group .radio-card').forEach(c => c.classList.remove('active-card'));
            const card = radioRec.closest('.radio-card');
            if (card) card.classList.add('active-card');
          }
        }
        this.updateSummary();
        showToast(`Preset: ${recipient} (${tone}) selected`, 'info');
      });
    });

    // 2. Step Navigation Buttons
    const btnNext1 = document.getElementById('wizard-btn-next-1');
    if (btnNext1) btnNext1.addEventListener('click', () => this.goToStep(2));

    const btnPrev2 = document.getElementById('wizard-btn-prev-2');
    if (btnPrev2) btnPrev2.addEventListener('click', () => this.goToStep(1));
    const btnNext2 = document.getElementById('wizard-btn-next-2');
    if (btnNext2) btnNext2.addEventListener('click', () => this.goToStep(3));

    const btnPrev3 = document.getElementById('wizard-btn-prev-3');
    if (btnPrev3) btnPrev3.addEventListener('click', () => this.goToStep(2));
    const btnNext3 = document.getElementById('wizard-btn-next-3');
    if (btnNext3) btnNext3.addEventListener('click', () => this.goToStep(4));

    const btnPrev4 = document.getElementById('wizard-btn-prev-4');
    if (btnPrev4) btnPrev4.addEventListener('click', () => this.goToStep(3));
    const btnNext4 = document.getElementById('wizard-btn-next-4');
    if (btnNext4) btnNext4.addEventListener('click', () => this.goToStep(5));

    const btnPrev5 = document.getElementById('wizard-btn-prev-5');
    if (btnPrev5) btnPrev5.addEventListener('click', () => this.goToStep(4));
    const btnNext5 = document.getElementById('wizard-btn-next-5');
    if (btnNext5) btnNext5.addEventListener('click', () => this.goToStep(6));

    const btnPrev6 = document.getElementById('wizard-btn-prev-6');
    if (btnPrev6) btnPrev6.addEventListener('click', () => this.goToStep(5));

    // 3. Radio Card Selections
    this.bindRadioCards('recipient-card-group', 'wizard-recipient', (val) => {
      this.recipient = val;
      const customContainer = document.getElementById('custom-recipient-container');
      if (customContainer) {
        if (val === 'Other') {
          customContainer.classList.remove('hidden');
          const customInp = document.getElementById('gen-custom-recipient');
          if (customInp) customInp.focus();
        } else {
          customContainer.classList.add('hidden');
        }
      }
      this.updateSummary();
    });

    const customRecInput = document.getElementById('gen-custom-recipient');
    if (customRecInput) {
      customRecInput.addEventListener('input', (e) => {
        this.customRecipient = e.target.value.trim();
        this.updateSummary();
      });
    }

    this.bindRadioCards('situation-card-group', 'wizard-situation-type', (val) => {
      this.situationType = val;
      this.updateSummary();
    });

    this.bindRadioCards('tone-card-group', 'wizard-tone', (val) => {
      this.tone = val;
      this.updateSummary();
    });

    this.bindRadioCards('length-card-group', 'wizard-length', (val) => {
      this.length = val;
      this.updateSummary();
    });

    this.bindRadioCards('delivery-card-group', 'wizard-delivery', (val) => {
      this.deliveryMethod = val;
      this.updateSummary();
    });

    // 4. Generate Button Trigger
    const btnGenerate = document.getElementById('btn-generate-wizard') || document.getElementById('btn-generate-excuse');
    if (btnGenerate) {
      btnGenerate.addEventListener('click', () => this.handleGenerate());
    }

    // 5. 21. Action Toolbar: Copy, Save, Regenerate, Edit, Delete
    const btnCopyResult = document.getElementById('btn-copy-result');
    if (btnCopyResult) {
      btnCopyResult.addEventListener('click', () => {
        const text = this.getActiveText();
        if (text) copyToClipboard(text, 'Explanation copied to clipboard');
      });
    }

    const btnSaveResult = document.getElementById('btn-save-result');
    if (btnSaveResult) {
      btnSaveResult.addEventListener('click', () => this.handleToggleFavorite());
    }

    const btnRegenResult = document.getElementById('btn-regenerate-result');
    if (btnRegenResult) {
      btnRegenResult.addEventListener('click', () => this.handleGenerate(true));
    }

    const btnToggleEdit = document.getElementById('btn-toggle-edit') || document.getElementById('btn-toggle-inline-edit');
    if (btnToggleEdit) {
      btnToggleEdit.addEventListener('click', () => this.toggleInlineEdit());
    }

    const btnCancelEdit = document.getElementById('btn-cancel-edit');
    if (btnCancelEdit) {
      btnCancelEdit.addEventListener('click', () => this.cancelInlineEdit());
    }

    const btnSaveInlineEdit = document.getElementById('btn-save-inline-edit');
    if (btnSaveInlineEdit) {
      btnSaveInlineEdit.addEventListener('click', () => this.saveInlineEdit());
    }

    const btnDeleteResult = document.getElementById('btn-delete-result');
    if (btnDeleteResult) {
      btnDeleteResult.addEventListener('click', () => this.handleDeleteExcuse());
    }

    const btnRestart = document.getElementById('btn-wizard-restart');
    if (btnRestart) {
      btnRestart.addEventListener('click', () => this.resetWizard());
    }

    const btnCreateDoc = document.getElementById('btn-goto-proof-doc') || document.getElementById('btn-create-doc-from-result');
    if (btnCreateDoc) {
      btnCreateDoc.addEventListener('click', () => {
        window.dispatchEvent(new CustomEvent('nav:navigate', {
          detail: {
            view: 'documents',
            context: {
              scenario: this.situation,
              recipient: this.getEffectiveRecipient()
            }
          }
        }));
      });
    }

    // 6. 22. Smart AI Modification (Quick Improvement Actions)
    document.querySelectorAll('.quick-mod-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const mod = e.currentTarget.dataset.mod;
        if (mod) this.handleQuickModification(mod);
      });
    });

    // 7. 23. Custom Modification
    const btnApplyCustom = document.getElementById('btn-apply-custom-mod');
    const customInp = document.getElementById('custom-mod-prompt') || document.getElementById('custom-mod-input');
    if (btnApplyCustom) {
      btnApplyCustom.addEventListener('click', () => {
        const instruction = customInp ? customInp.value.trim() : '';
        if (!instruction) {
          showToast('Please specify what you would like to change.', 'error');
          if (customInp) customInp.focus();
          return;
        }
        this.handleQuickModification(instruction, `Custom: ${instruction.slice(0, 15)}...`);
        if (customInp) customInp.value = '';
      });
    }

    if (customInp) {
      customInp.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          if (btnApplyCustom) btnApplyCustom.click();
        }
      });
    }
  }

  bindRadioCards(groupId, radioName, callback) {
    const group = document.getElementById(groupId);
    if (!group) return;

    const radios = group.querySelectorAll(`input[name="${radioName}"]`);
    radios.forEach(radio => {
      radio.addEventListener('change', (e) => {
        group.querySelectorAll('.radio-card').forEach(card => card.classList.remove('active-card'));
        const label = e.target.closest('.radio-card');
        if (label) label.classList.add('active-card');
        callback(e.target.value);
      });
    });
  }

  updateCharacterCount() {
    const charCountEl = document.getElementById('gen-char-count');
    const input = document.getElementById('gen-situation');
    if (charCountEl && input) {
      const len = input.value.length;
      charCountEl.textContent = `Characters: ${len} / 1000`;
    }
  }

  autoInferSituationType(text) {
    const t = text.toLowerCase();
    let inferred = null;
    if (t.includes('deadline') || t.includes('assignment') || t.includes('homework') || t.includes('submit')) {
      inferred = 'Missed deadline';
    } else if (t.includes('traffic') || t.includes('running late') || t.includes('delay') || t.includes('train')) {
      inferred = 'Running late';
    } else if (t.includes('meeting') || t.includes('standup') || t.includes('sync')) {
      inferred = 'Missed a meeting';
    } else if (t.includes('cancel') || t.includes('reschedule')) {
      inferred = 'Need to cancel';
    } else if (t.includes('extension') || t.includes('extra time') || t.includes('more days')) {
      inferred = 'Requesting an extension';
    } else if (t.includes('sick') || t.includes('doctor') || t.includes('emergency') || t.includes('personal')) {
      inferred = 'Personal issue';
    }

    if (inferred) {
      const radio = document.querySelector(`input[name="wizard-situation-type"][value="${inferred}"]`);
      if (radio) {
        radio.checked = true;
        const group = document.getElementById('situation-card-group');
        if (group) {
          group.querySelectorAll('.radio-card').forEach(c => c.classList.remove('active-card'));
          const label = radio.closest('.radio-card');
          if (label) label.classList.add('active-card');
        }
        this.situationType = inferred;
        this.updateSummary();
      }
    }
  }

  getEffectiveRecipient() {
    if (this.recipient === 'Other' && this.customRecipient) {
      return this.customRecipient;
    }
    return this.recipient;
  }

  updateSummary() {
    const sumRec = document.getElementById('summary-recipient') || document.getElementById('sum-recipient');
    const sumType = document.getElementById('summary-type') || document.getElementById('sum-type');
    const sumTone = document.getElementById('summary-tone') || document.getElementById('sum-tone');
    const sumLen = document.getElementById('summary-length') || document.getElementById('sum-length');

    if (sumRec) sumRec.textContent = this.getEffectiveRecipient();
    if (sumType) sumType.textContent = this.situationType;
    if (sumTone) sumTone.textContent = this.tone;
    if (sumLen) sumLen.textContent = this.length;
  }

  goToStep(step) {
    if (step === 2 && !this.situation.trim()) {
      showToast('Please describe the situation first.', 'error');
      const input = document.getElementById('gen-situation');
      if (input) input.focus();
      return;
    }

    this.currentStep = step;

    for (let i = 1; i <= this.totalSteps; i++) {
      const stepEl = document.getElementById(`wizard-step-${i}`);
      if (stepEl) stepEl.classList.add('hidden');
    }

    const targetStep = document.getElementById(`wizard-step-${step}`);
    if (targetStep) targetStep.classList.remove('hidden');

    const indicator = document.getElementById('wizard-step-indicator');
    const progressBar = document.getElementById('wizard-progress-bar');
    if (indicator) indicator.textContent = `Step ${step} of ${this.totalSteps}`;
    if (progressBar) {
      const pct = (step / this.totalSteps) * 100;
      progressBar.style.width = `${pct}%`;
    }

    this.updateSummary();
  }

  async handleGenerate(isRegenerate = false) {
    const wizardContainer = document.getElementById('wizard-container');
    const processingScreen = document.getElementById('wizard-processing-screen');
    const resultScreen = document.getElementById('wizard-result-screen');

    if (!this.situation.trim()) {
      showToast('Please provide a situation description.', 'error');
      this.goToStep(1);
      return;
    }

    if (wizardContainer) wizardContainer.classList.add('hidden');
    if (resultScreen) resultScreen.classList.add('hidden');
    if (processingScreen) processingScreen.classList.remove('hidden');

    // Reset checklist icons
    for (let i = 1; i <= 5; i++) {
      const el = document.getElementById(`check-step-${i}`);
      if (el) {
        el.className = 'flex items-center gap-3 text-slate-400 transition-colors';
        const icon = el.querySelector('.check-icon');
        if (icon) {
          icon.textContent = '○';
          icon.className = 'check-icon w-4 h-4 rounded-full border border-slate-700 flex items-center justify-center text-[10px]';
        }
      }
    }

    const checkStep = async (stepNum, delayMs) => {
      await new Promise(r => setTimeout(r, delayMs));
      const el = document.getElementById(`check-step-${stepNum}`);
      if (el) {
        el.className = 'flex items-center gap-3 text-emerald-400 font-semibold transition-colors';
        const icon = el.querySelector('.check-icon');
        if (icon) {
          icon.textContent = '✓';
          icon.className = 'check-icon w-4 h-4 rounded-full bg-emerald-950 border border-emerald-700 text-emerald-300 flex items-center justify-center text-[10px]';
        }
      }
    };

    const animPromise = (async () => {
      await checkStep(1, 200);
      await checkStep(2, 250);
      await checkStep(3, 250);
      await checkStep(4, 250);
      await checkStep(5, 250);
    })();

    try {
      const recipient = this.getEffectiveRecipient();
      const apiPromise = api.post('/excuses/generate', {
        scenario: this.situation,
        recipient: recipient,
        situation_type: this.situationType,
        tone: this.tone,
        length: this.length,
        delivery_method: this.deliveryMethod
      });

      const [_, data] = await Promise.all([animPromise, apiPromise]);

      this.currentExcuse = data.excuse;

      // Initialize Version History
      this.versions = [
        { label: `Version 1 (${this.tone})`, text: data.excuse.primary_text, tone: this.tone }
      ];
      this.activeVersionIndex = 0;

      await new Promise(r => setTimeout(r, 200));

      if (processingScreen) processingScreen.classList.add('hidden');
      if (resultScreen) resultScreen.classList.remove('hidden');

      this.renderResult(data.excuse);
      showToast(isRegenerate ? 'New version generated' : 'Your generated response is ready', 'success');

      resultScreen.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
      if (processingScreen) processingScreen.classList.add('hidden');
      if (wizardContainer) wizardContainer.classList.remove('hidden');
      showToast(err.message || 'Generation failed. Please try again.', 'error');
    }
  }

  renderResult(excuse) {
    // Badges
    const bTone = document.getElementById('result-badge-tone');
    const bLen = document.getElementById('result-badge-length');
    const bRec = document.getElementById('result-badge-recipient');
    const bDel = document.getElementById('result-badge-delivery');

    if (bTone) bTone.textContent = `Tone: ${excuse.tone || this.tone}`;
    if (bLen) bLen.textContent = `Length: ${this.length}`;
    if (bRec) bRec.textContent = `Recipient: ${excuse.recipient || this.getEffectiveRecipient()}`;
    if (bDel) bDel.textContent = `Channel: ${this.deliveryMethod}`;

    this.renderVersions();
    this.updatePrimaryDisplay();

    this.updateSaveButtonState(excuse.is_favorite === 1);

    // Believability Score & Risk
    const scoreVal = document.getElementById('result-score-val');
    const scoreBar = document.getElementById('result-score-bar');
    const riskBadge = document.getElementById('result-risk-badge');

    if (scoreVal) scoreVal.textContent = `${excuse.believability_score}%`;
    if (scoreBar) scoreBar.style.width = `${excuse.believability_score}%`;

    if (riskBadge) {
      riskBadge.textContent = `${excuse.risk_level} Risk`;
      if (excuse.risk_level === 'Low') {
        riskBadge.className = 'px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800';
      } else if (excuse.risk_level === 'Moderate') {
        riskBadge.className = 'px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950 text-amber-300 border border-amber-800';
      } else {
        riskBadge.className = 'px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-950 text-rose-300 border border-rose-800';
      }
    }

    // Tactical Advice Tips
    const tipsList = document.getElementById('result-tips-list');
    if (tipsList) {
      tipsList.innerHTML = '';
      const tips = excuse.tips || [];
      if (tips.length === 0) {
        tipsList.innerHTML = '<li class="text-xs text-slate-400">Keep your explanation consistent if asked for minor clarification.</li>';
      } else {
        tips.forEach(tip => {
          const li = document.createElement('li');
          li.className = 'flex items-start gap-2 text-xs text-slate-300';
          li.innerHTML = `
            <svg class="w-4 h-4 text-blue-400 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>${tip}</span>
          `;
          tipsList.appendChild(li);
        });
      }
    }

    // Alternative Variations
    const varContainer = document.getElementById('result-variations-container');
    if (varContainer) {
      varContainer.innerHTML = '';
      const vars = excuse.variations || [];
      vars.forEach((v, idx) => {
        const card = document.createElement('div');
        card.className = 'p-4 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-850 transition-colors space-y-3';
        card.innerHTML = `
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-300 uppercase tracking-wider">${v.title || `Option ${idx + 1}`}</span>
            <button type="button" class="btn-use-var text-xs font-semibold text-blue-400 hover:text-blue-300 transition-colors" data-index="${idx}">
              Use as Version
            </button>
          </div>
          <p class="text-xs sm:text-sm font-mono text-slate-300 whitespace-pre-line leading-relaxed">${v.text}</p>
          <div class="flex justify-end pt-1">
            <button type="button" class="btn-copy-var btn-ghost text-xs px-2.5 py-1 flex items-center gap-1" data-index="${idx}">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
              <span>Copy</span>
            </button>
          </div>
        `;
        varContainer.appendChild(card);
      });

      varContainer.querySelectorAll('.btn-use-var').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const idx = parseInt(e.currentTarget.dataset.index);
          const chosen = vars[idx];
          if (chosen) {
            const vNum = this.versions.length + 1;
            this.versions.push({
              label: `Version ${vNum} (${chosen.title || 'Alternative'})`,
              text: chosen.text
            });
            this.activeVersionIndex = this.versions.length - 1;
            this.renderVersions();
            this.updatePrimaryDisplay();
            showToast('Added as new active version', 'info');
          }
        });
      });

      varContainer.querySelectorAll('.btn-copy-var').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const idx = parseInt(e.currentTarget.dataset.index);
          const chosen = vars[idx];
          if (chosen) {
            copyToClipboard(chosen.text, 'Alternative variation copied');
          }
        });
      });
    }
  }

  // 24. Excuse Versions Rendering
  renderVersions() {
    const listEl = document.getElementById('result-versions-list');
    if (!listEl) return;

    listEl.innerHTML = '';
    this.versions.forEach((ver, idx) => {
      const isActive = idx === this.activeVersionIndex;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = `text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${
        isActive
          ? 'bg-blue-600 border-blue-500 text-white shadow-md'
          : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700'
      }`;
      btn.textContent = ver.label;
      btn.addEventListener('click', () => {
        this.activeVersionIndex = idx;
        this.renderVersions();
        this.updatePrimaryDisplay();
      });
      listEl.appendChild(btn);
    });
  }

  getActiveText() {
    if (this.versions[this.activeVersionIndex]) {
      return this.versions[this.activeVersionIndex].text;
    }
    const textEl = document.getElementById('result-primary-text');
    return textEl ? textEl.textContent : '';
  }

  updatePrimaryDisplay() {
    const text = this.getActiveText();
    const textEl = document.getElementById('result-primary-text');
    const textarea = document.getElementById('result-editable-textarea');
    if (textEl) textEl.textContent = text;
    if (textarea) textarea.value = text;
  }

  // 21. Action Toolbar: Edit Mode
  toggleInlineEdit() {
    this.isEditing = !this.isEditing;
    const displayBox = document.getElementById('result-text-display-container');
    const editorBox = document.getElementById('result-inline-editor-container');
    const editBtnLabel = document.getElementById('edit-btn-label');
    const textarea = document.getElementById('result-editable-textarea');

    if (this.isEditing) {
      if (displayBox) displayBox.classList.add('hidden');
      if (editorBox) editorBox.classList.remove('hidden');
      if (editBtnLabel) editBtnLabel.textContent = 'Editing...';
      if (textarea) {
        textarea.value = this.getActiveText();
        textarea.focus();
      }
    } else {
      if (displayBox) displayBox.classList.remove('hidden');
      if (editorBox) editorBox.classList.add('hidden');
      if (editBtnLabel) editBtnLabel.textContent = 'Edit';
    }
  }

  cancelInlineEdit() {
    this.isEditing = true;
    this.toggleInlineEdit();
  }

  async saveInlineEdit() {
    const textarea = document.getElementById('result-editable-textarea');
    const newText = textarea ? textarea.value.trim() : '';

    if (!newText) {
      showToast('Text cannot be empty', 'error');
      return;
    }

    if (this.currentExcuse) {
      try {
        await api.put(`/excuses/${this.currentExcuse.id}`, { primary_text: newText });
        this.currentExcuse.primary_text = newText;
      } catch (err) {
        // Fallback silently if offline
      }
    }

    // Update active version text
    if (this.versions[this.activeVersionIndex]) {
      this.versions[this.activeVersionIndex].text = newText;
    }

    this.isEditing = true;
    this.toggleInlineEdit();
    this.updatePrimaryDisplay();
    showToast('Changes saved successfully', 'success');
  }

  async handleDeleteExcuse() {
    if (!this.currentExcuse) {
      this.resetWizard();
      return;
    }

    if (!confirm('Are you sure you want to delete this generated explanation?')) return;

    try {
      await api.delete(`/excuses/${this.currentExcuse.id}`);
      showToast('Explanation deleted', 'info');
      this.resetWizard();
    } catch (err) {
      showToast('Failed to delete excuse', 'error');
    }
  }

  // 22. Smart AI Modification (Make Shorter, Make More Formal, etc.)
  async handleQuickModification(instruction, label = null) {
    const currentText = this.getActiveText();
    if (!currentText) return;

    showToast(`Applying "${instruction}"...`, 'info');

    try {
      const data = await api.post('/excuses/rewrite', {
        text: currentText,
        instruction: instruction,
        tone: this.tone
      });

      if (data && data.rewritten_text) {
        const vNum = this.versions.length + 1;
        const vLabel = label || `Version ${vNum} (${instruction.replace('Make ', '')})`;
        this.versions.push({
          label: vLabel,
          text: data.rewritten_text
        });
        this.activeVersionIndex = this.versions.length - 1;
        this.renderVersions();
        this.updatePrimaryDisplay();
        showToast('Created new refined version', 'success');
      }
    } catch (err) {
      showToast(err.message || 'Modification failed', 'error');
    }
  }

  updateSaveButtonState(isFavorite) {
    const saveLabel = document.getElementById('save-btn-label');
    const starIcon = document.getElementById('star-icon');
    if (saveLabel) saveLabel.textContent = isFavorite ? 'Saved' : 'Save';
    if (starIcon) {
      if (isFavorite) {
        starIcon.setAttribute('class', 'w-4 h-4 text-amber-500 fill-current');
      } else {
        starIcon.setAttribute('class', 'w-4 h-4 text-stone-400 fill-current');
      }
    }
  }

  async handleToggleFavorite() {
    if (!this.currentExcuse) return;
    try {
      const res = await api.post(`/excuses/${this.currentExcuse.id}/favorite`, {});
      this.currentExcuse.is_favorite = res.is_favorite ? 1 : 0;
      this.updateSaveButtonState(res.is_favorite);
      showToast(res.is_favorite ? 'Saved to favorites' : 'Removed from favorites', 'info');
    } catch (err) {
      showToast('Failed to update favorite', 'error');
    }
  }

  resetWizard() {
    this.goToStep(1);
    this.isEditing = false;
    const wizardContainer = document.getElementById('wizard-container');
    const resultScreen = document.getElementById('wizard-result-screen');
    const processingScreen = document.getElementById('wizard-processing-screen');
    const situationInput = document.getElementById('gen-situation');
    const displayBox = document.getElementById('result-text-display-container');
    const editorBox = document.getElementById('result-inline-editor-container');

    if (wizardContainer) wizardContainer.classList.remove('hidden');
    if (resultScreen) resultScreen.classList.add('hidden');
    if (processingScreen) processingScreen.classList.add('hidden');
    if (displayBox) displayBox.classList.remove('hidden');
    if (editorBox) editorBox.classList.add('hidden');

    if (situationInput) {
      situationInput.value = '';
      this.situation = '';
      this.updateCharacterCount();
      situationInput.focus();
    }
  }
}

export const generator = new GeneratorManager();
