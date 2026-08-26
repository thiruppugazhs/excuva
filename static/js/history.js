// history.js - Search, Tone/Date Filters, Favorites, and Item Management
import { api, showToast, copyToClipboard } from './api.js';

export class HistoryManager {
  constructor() {
    this.excuses = [];
    this.documents = [];
    this.activeTab = 'all'; // 'all', 'excuses', 'documents', 'favorites'
    this.searchTerm = '';
    this.selectedTone = 'all';
    this.selectedDate = 'all';
  }

  init() {
    this.bindEvents();
  }

  bindEvents() {
    // 34. Search input
    const searchInput = document.getElementById('history-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchTerm = e.target.value.toLowerCase().trim();
        this.render();
      });
    }

    // 33. Filter type tabs
    document.querySelectorAll('.history-tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.history-tab-btn').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        this.activeTab = e.currentTarget.dataset.tab;
        this.render();
      });
    });

    // 35. Filter by Tone
    const toneFilter = document.getElementById('history-filter-tone');
    if (toneFilter) {
      toneFilter.addEventListener('change', (e) => {
        this.selectedTone = e.target.value;
        this.render();
      });
    }

    // 35. Filter by Date
    const dateFilter = document.getElementById('history-filter-date');
    if (dateFilter) {
      dateFilter.addEventListener('change', (e) => {
        this.selectedDate = e.target.value;
        this.render();
      });
    }
  }

  async loadData(favoritesOnly = false) {
    if (favoritesOnly) {
      this.activeTab = 'favorites';
      document.querySelectorAll('.history-tab-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.tab === 'favorites');
      });
    }

    try {
      const [excusesData, docsData] = await Promise.all([
        api.get('/excuses'),
        api.get('/documents')
      ]);

      this.excuses = excusesData.excuses || [];
      this.documents = docsData.documents || [];
      this.render();
      this.renderDedicatedFavorites();
    } catch (err) {
      showToast('Failed to load history records', 'error');
    }
  }

  filterByDate(dateObj) {
    if (this.selectedDate === 'all') return true;
    const now = new Date();
    const itemDate = new Date(dateObj);

    if (this.selectedDate === 'today') {
      return now.toDateString() === itemDate.toDateString();
    } else if (this.selectedDate === 'week') {
      const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      return itemDate >= sevenDaysAgo;
    } else if (this.selectedDate === 'month') {
      const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      return itemDate >= thirtyDaysAgo;
    }
    return true;
  }

  formatRelativeDate(dateStr) {
    const d = new Date(dateStr);
    const now = new Date();
    if (d.toDateString() === now.toDateString()) return 'Today';
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    if (d.toDateString() === yesterday.toDateString()) return 'Yesterday';
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  render() {
    const listContainer = document.getElementById('history-items-list');
    const emptyState = document.getElementById('history-empty-state');
    if (!listContainer) return;

    listContainer.innerHTML = '';

    let filteredExcuses = this.excuses;
    let filteredDocs = this.documents;

    // Tab Filter
    if (this.activeTab === 'favorites') {
      filteredExcuses = filteredExcuses.filter(e => e.is_favorite);
      filteredDocs = filteredDocs.filter(d => d.is_favorite);
    }

    // Tone Filter
    if (this.selectedTone !== 'all') {
      filteredExcuses = filteredExcuses.filter(e => e.tone && e.tone.toLowerCase() === this.selectedTone.toLowerCase());
    }

    // Date Filter
    filteredExcuses = filteredExcuses.filter(e => this.filterByDate(e.created_at));
    filteredDocs = filteredDocs.filter(d => this.filterByDate(d.created_at));

    // Search Filter
    if (this.searchTerm) {
      filteredExcuses = filteredExcuses.filter(e =>
        (e.scenario && e.scenario.toLowerCase().includes(this.searchTerm)) ||
        (e.primary_text && e.primary_text.toLowerCase().includes(this.searchTerm)) ||
        (e.recipient && e.recipient.toLowerCase().includes(this.searchTerm)) ||
        (e.tone && e.tone.toLowerCase().includes(this.searchTerm))
      );

      filteredDocs = filteredDocs.filter(d =>
        (d.title && d.title.toLowerCase().includes(this.searchTerm)) ||
        (d.organization && d.organization.toLowerCase().includes(this.searchTerm)) ||
        (d.recipient && d.recipient.toLowerCase().includes(this.searchTerm))
      );
    }

    const items = [];
    if (this.activeTab === 'all' || this.activeTab === 'excuses' || this.activeTab === 'favorites') {
      filteredExcuses.forEach(e => items.push({ ...e, itemType: 'excuse', sortDate: new Date(e.created_at) }));
    }
    if (this.activeTab === 'all' || this.activeTab === 'documents' || this.activeTab === 'favorites') {
      filteredDocs.forEach(d => items.push({ ...d, itemType: 'document', sortDate: new Date(d.created_at) }));
    }

    items.sort((a, b) => b.sortDate - a.sortDate);

    if (items.length === 0) {
      if (emptyState) emptyState.classList.remove('hidden');
      return;
    } else {
      if (emptyState) emptyState.classList.add('hidden');
    }

    items.forEach(item => {
      listContainer.appendChild(this.createItemCard(item));
    });

    this.bindCardActions(listContainer);
  }

  createItemCard(item) {
    const card = document.createElement('div');
    card.className = 'p-4 sm:p-5 rounded-xl border border-slate-800 bg-slate-900/70 hover:border-slate-700 transition-all space-y-3';
    const relDate = this.formatRelativeDate(item.created_at);

    if (item.itemType === 'excuse') {
      card.innerHTML = `
        <div class="flex items-start justify-between gap-4">
          <div>
            <div class="flex flex-wrap items-center gap-2 mb-1">
              <span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-950 text-blue-300 border border-blue-800">Explanation</span>
              <span class="text-xs text-slate-400">To: <strong class="text-slate-200">${item.recipient}</strong></span>
              <span class="text-xs text-slate-400">• Tone: <strong class="text-slate-200">${item.tone}</strong></span>
              <span class="text-xs text-slate-400">• ${relDate}</span>
            </div>
            <h4 class="text-sm sm:text-base font-bold text-white">${item.scenario}</h4>
          </div>

          <button type="button" class="btn-fav-history p-1.5 rounded text-slate-400 hover:text-amber-400 ${item.is_favorite ? 'text-amber-400' : ''}" data-id="${item.id}" data-type="excuse" title="Toggle Favorite">
            <svg class="w-5 h-5 fill-current" viewBox="0 0 24 24">
              <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
            </svg>
          </button>
        </div>

        <div class="p-3 rounded-lg border border-slate-800 bg-slate-950/80 font-mono text-xs sm:text-sm text-slate-300 whitespace-pre-line leading-relaxed select-all">
          ${item.primary_text}
        </div>

        <div class="flex items-center justify-between pt-1 border-t border-slate-800/80 text-xs text-slate-400">
          <span class="font-mono text-[11px] text-emerald-400">${item.believability_score || 96}% Believable</span>
          <div class="flex items-center gap-2">
            <button type="button" class="btn-copy-history btn-ghost px-2.5 py-1 text-xs" data-text="${encodeURIComponent(item.primary_text)}">
              Copy ✓
            </button>
            <button type="button" class="btn-delete-history btn-ghost px-2.5 py-1 text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-950/30" data-id="${item.id}" data-type="excuse">
              Delete
            </button>
          </div>
        </div>
      `;
    } else {
      card.innerHTML = `
        <div class="flex items-start justify-between gap-4">
          <div>
            <div class="flex flex-wrap items-center gap-2 mb-1">
              <span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800">Supporting Document</span>
              <span class="text-xs text-slate-400">Recipient: <strong class="text-slate-200">${item.recipient}</strong></span>
              <span class="text-xs text-slate-400">• ${relDate}</span>
            </div>
            <h4 class="text-sm sm:text-base font-bold text-white">${item.title}</h4>
          </div>

          <button type="button" class="btn-fav-history p-1.5 rounded text-slate-400 hover:text-amber-400 ${item.is_favorite ? 'text-amber-400' : ''}" data-id="${item.id}" data-type="document" title="Toggle Favorite">
            <svg class="w-5 h-5 fill-current" viewBox="0 0 24 24">
              <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
            </svg>
          </button>
        </div>

        <div class="p-3 rounded-lg border border-slate-800 bg-slate-950/80 font-mono text-xs text-slate-300">
          <p><strong>Document Type:</strong> ${item.doc_type} | <strong>Date of Record:</strong> ${item.issue_date}</p>
        </div>

        <div class="flex items-center justify-between pt-1 border-t border-slate-800/80 text-xs text-slate-400">
          <span class="text-slate-400">Official draft</span>
          <div class="flex items-center gap-2">
            <button type="button" class="btn-view-doc-history btn-ghost px-2.5 py-1 text-xs text-blue-400 hover:text-blue-300" data-id="${item.id}">
              Open in Editor →
            </button>
            <button type="button" class="btn-delete-history btn-ghost px-2.5 py-1 text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-950/30" data-id="${item.id}" data-type="document">
              Delete
            </button>
          </div>
        </div>
      `;
    }
    return card;
  }

  renderDedicatedFavorites() {
    const favContainer = document.getElementById('favorites-items-list');
    const favEmpty = document.getElementById('favorites-empty-state');
    if (!favContainer) return;

    favContainer.innerHTML = '';
    const favExcuses = this.excuses.filter(e => e.is_favorite);
    const favDocs = this.documents.filter(d => d.is_favorite);

    const items = [];
    favExcuses.forEach(e => items.push({ ...e, itemType: 'excuse', sortDate: new Date(e.created_at) }));
    favDocs.forEach(d => items.push({ ...d, itemType: 'document', sortDate: new Date(d.created_at) }));
    items.sort((a, b) => b.sortDate - a.sortDate);

    if (items.length === 0) {
      if (favEmpty) favEmpty.classList.remove('hidden');
    } else {
      if (favEmpty) favEmpty.classList.add('hidden');
      items.forEach(item => {
        favContainer.appendChild(this.createItemCard(item));
      });
      this.bindCardActions(favContainer);
    }
  }

  bindCardActions(container) {
    // Copy button
    container.querySelectorAll('.btn-copy-history').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const text = decodeURIComponent(e.currentTarget.dataset.text || '');
        copyToClipboard(text, 'Copied ✓');
      });
    });

    // Favorite star toggle
    container.querySelectorAll('.btn-fav-history').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const id = e.currentTarget.dataset.id;
        const type = e.currentTarget.dataset.type;
        try {
          const endpoint = type === 'excuse' ? `/excuses/${id}/favorite` : `/documents/${id}/favorite`;
          const res = await api.post(endpoint, {});
          
          if (type === 'excuse') {
            const item = this.excuses.find(x => x.id == id);
            if (item) item.is_favorite = res.is_favorite ? 1 : 0;
          } else {
            const item = this.documents.find(x => x.id == id);
            if (item) item.is_favorite = res.is_favorite ? 1 : 0;
          }

          this.render();
          this.renderDedicatedFavorites();
          showToast(res.is_favorite ? '★ Added to favorites' : 'Removed from favorites', 'info');
        } catch (err) {
          showToast('Failed to update favorite', 'error');
        }
      });
    });

    // Delete item
    container.querySelectorAll('.btn-delete-history').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const id = e.currentTarget.dataset.id;
        const type = e.currentTarget.dataset.type;
        if (!confirm('Are you sure you want to delete this record?')) return;

        try {
          const endpoint = type === 'excuse' ? `/excuses/${id}` : `/documents/${id}`;
          await api.delete(endpoint);

          if (type === 'excuse') {
            this.excuses = this.excuses.filter(x => x.id != id);
          } else {
            this.documents = this.documents.filter(x => x.id != id);
          }

          this.render();
          this.renderDedicatedFavorites();
          showToast('Record deleted', 'info');
        } catch (err) {
          showToast('Failed to delete record', 'error');
        }
      });
    });

    // View / Open document in editor
    container.querySelectorAll('.btn-view-doc-history').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.currentTarget.dataset.id;
        const doc = this.documents.find(x => x.id == id);
        if (doc) {
          window.dispatchEvent(new CustomEvent('nav:navigate', {
            detail: { view: 'documents' }
          }));
          setTimeout(() => {
            const canvas = document.getElementById('formal-doc-canvas');
            const editorSection = document.getElementById('doc-editor-section');
            if (canvas && editorSection) {
              const content = doc.content || {};
              canvas.textContent = content.content_text || doc.title || '';
              editorSection.classList.remove('hidden');
              editorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
          }, 100);
        }
      });
    });
  }
}

export const historyManager = new HistoryManager();
