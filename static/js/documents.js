// documents.js - Proof & Document Generator with Live Formatting Editor
import { api, showToast, copyToClipboard } from './api.js';

export class DocumentsManager {
  constructor() {
    this.selectedType = 'Explanation Letter';
    this.currentDocument = null;
  }

  init() {
    this.bindEvents();
    this.setDefaultDate();
  }

  setDefaultDate() {
    const dateInput = document.getElementById('doc-date-input');
    if (dateInput && !dateInput.value) {
      const now = new Date();
      const formatted = now.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
      dateInput.value = formatted;
    }
  }

  bindEvents() {
    // 1. Document Type Radio Cards
    const typeGroup = document.getElementById('doc-type-group');
    if (typeGroup) {
      const radios = typeGroup.querySelectorAll('input[name="doc-type-radio"]');
      radios.forEach(radio => {
        radio.addEventListener('change', (e) => {
          typeGroup.querySelectorAll('.radio-card').forEach(c => c.classList.remove('active-card'));
          const label = e.target.closest('.radio-card');
          if (label) label.classList.add('active-card');
          this.selectedType = e.target.value;
          this.updateSuggestedTitle();
        });
      });
    }

    // 2. Generate Formal Document Trigger
    const btnGen = document.getElementById('btn-generate-formal-doc');
    if (btnGen) {
      btnGen.addEventListener('click', () => this.handleGenerateDocument());
    }

    // 3. Document Editor Formatting Buttons
    document.querySelectorAll('.format-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const cmd = e.currentTarget.dataset.cmd;
        if (cmd) {
          document.execCommand(cmd, false, null);
          const canvas = document.getElementById('formal-doc-canvas');
          if (canvas) canvas.focus();
        }
      });
    });

    const btnInsertDate = document.getElementById('btn-insert-date');
    if (btnInsertDate) {
      btnInsertDate.addEventListener('click', () => {
        const today = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
        document.execCommand('insertText', false, today);
      });
    }

    const btnInsertSig = document.getElementById('btn-insert-sig');
    if (btnInsertSig) {
      btnInsertSig.addEventListener('click', () => {
        const sigBlock = '\n\nSincerely,\n_________________________\n[Authorized Signer]';
        document.execCommand('insertText', false, sigBlock);
      });
    }

    // 4. Editor Action Buttons (Copy, Save, Print / PDF)
    const btnCopy = document.getElementById('btn-copy-editor-text');
    if (btnCopy) {
      btnCopy.addEventListener('click', () => {
        const canvas = document.getElementById('formal-doc-canvas');
        if (canvas) {
          copyToClipboard(canvas.innerText || canvas.textContent, 'Document text copied');
        }
      });
    }

    const btnSave = document.getElementById('btn-save-edited-doc');
    if (btnSave) {
      btnSave.addEventListener('click', () => this.handleSaveEditedDoc());
    }

    const btnPrint = document.getElementById('btn-print-formal-doc');
    if (btnPrint) {
      btnPrint.addEventListener('click', () => {
        window.print();
      });
    }
  }

  setContext(context) {
    if (!context) return;

    if (context.recipient) {
      const recInput = document.getElementById('doc-recipient-input');
      if (recInput) recInput.value = context.recipient;
    }

    if (context.scenario) {
      const reasonInput = document.getElementById('doc-reason-input');
      if (reasonInput) reasonInput.value = context.scenario;
    }

    this.updateSuggestedTitle();
  }

  updateSuggestedTitle() {
    const titleInput = document.getElementById('doc-title-input');
    if (!titleInput || titleInput.value.trim() !== '') return;

    const titles = {
      'Explanation Letter': 'Formal Explanation of Circumstances',
      'Personal Declaration': 'Personal Statement of Record',
      'Leave Request': 'Formal Leave & Absence Request',
      'Delay Notification': 'Official Schedule Delay Notification',
      'Appointment Request': 'Rescheduling & Appointment Request',
      'Incident Explanation': 'Formal Incident Statement',
      'Extension Request': 'Assignment & Deadline Extension Request',
      'Absence Explanation': 'Official Notice of Absence'
    };

    titleInput.value = titles[this.selectedType] || 'Formal Statement';
  }

  async handleGenerateDocument() {
    const titleInp = document.getElementById('doc-title-input');
    const recInp = document.getElementById('doc-recipient-input');
    const dateInp = document.getElementById('doc-date-input');
    const reasonInp = document.getElementById('doc-reason-input');
    const detailsInp = document.getElementById('doc-details-input');
    const btn = document.getElementById('btn-generate-formal-doc');
    const btnText = document.getElementById('doc-btn-text');
    const spinner = document.getElementById('doc-spinner');

    const title = titleInp ? titleInp.value.trim() : '';
    const recipient = recInp ? recInp.value.trim() : 'Professor';
    const issue_date = dateInp ? dateInp.value.trim() : '';
    const reason = reasonInp ? reasonInp.value.trim() : 'Unexpected personal issue';
    const additional_details = detailsInp ? detailsInp.value.trim() : '';

    if (btn) btn.disabled = true;
    if (btnText) btnText.textContent = 'Generating Document...';
    if (spinner) spinner.classList.remove('hidden');

    try {
      const data = await api.post('/documents/generate', {
        doc_type: this.selectedType,
        title,
        recipient,
        issue_date,
        reason,
        additional_details
      });

      this.currentDocument = data.document;
      this.renderDocumentInEditor(data.document);
      showToast('Formal document generated successfully', 'success');

      const editorSection = document.getElementById('doc-editor-section');
      if (editorSection) {
        editorSection.classList.remove('hidden');
        editorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    } catch (err) {
      showToast(err.message || 'Failed to generate document', 'error');
    } finally {
      if (btn) btn.disabled = false;
      if (btnText) btnText.textContent = 'Generate Supporting Document';
      if (spinner) spinner.classList.add('hidden');
    }
  }

  renderDocumentInEditor(doc) {
    const canvas = document.getElementById('formal-doc-canvas');
    if (!canvas) return;

    const content = doc.content || {};
    const text = content.content_text || doc.title || '';
    canvas.textContent = text;
  }

  async handleSaveEditedDoc() {
    if (!this.currentDocument) {
      showToast('Generate a document first', 'error');
      return;
    }

    const canvas = document.getElementById('formal-doc-canvas');
    const titleInp = document.getElementById('doc-title-input');
    const newText = canvas ? (canvas.innerText || canvas.textContent) : '';
    const title = titleInp ? titleInp.value.trim() : this.currentDocument.title;

    try {
      const res = await api.put(`/documents/${this.currentDocument.id}`, {
        title,
        content_text: newText
      });
      this.currentDocument = res.document;
      showToast('Document saved successfully', 'success');
    } catch (err) {
      showToast('Failed to save document modifications', 'error');
    }
  }
}

export const documents = new DocumentsManager();
