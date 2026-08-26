// profile_settings.js - User Profile, Dashboard Stats, Defaults, Photo Upload & Privacy Controls
import { api, showToast } from './api.js';
import { auth } from './auth.js';

export class ProfileSettingsManager {
  constructor() {
    this.settings = {};
  }

  init() {
    this.bindEvents();
    this.applyTheme(localStorage.getItem('excuse_ai_theme') || 'light');
  }

  bindEvents() {
    // 39. Theme toggle buttons in settings
    document.querySelectorAll('.theme-option-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.theme-option-btn').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        const theme = e.currentTarget.dataset.theme;
        this.applyTheme(theme);
      });
    });

    // 39. Save preferences button
    const savePrefsBtn = document.getElementById('btn-save-preferences');
    if (savePrefsBtn) {
      savePrefsBtn.addEventListener('click', () => this.handleSavePreferences());
    }

    // 38. Save profile button
    const saveProfileBtn = document.getElementById('btn-save-profile');
    if (saveProfileBtn) {
      saveProfileBtn.addEventListener('click', () => this.handleSaveProfile());
    }

    // Avatar upload trigger
    const uploadTriggerBtn = document.getElementById('btn-trigger-upload-avatar');
    const avatarFileInput = document.getElementById('profile-avatar-file');
    if (uploadTriggerBtn && avatarFileInput) {
      uploadTriggerBtn.addEventListener('click', () => avatarFileInput.click());
      avatarFileInput.addEventListener('change', (e) => this.handleAvatarUpload(e));
    }

    // Change password button & Request OTP button
    const changePassBtn = document.getElementById('btn-change-password');
    if (changePassBtn) {
      changePassBtn.addEventListener('click', () => this.handleChangePassword());
    }

    const requestOtpBtn = document.getElementById('btn-request-pass-otp');
    if (requestOtpBtn) {
      requestOtpBtn.addEventListener('click', () => this.handleRequestPasswordOtp());
    }

    // 50. Delete All History button
    const deleteHistoryBtn = document.getElementById('btn-delete-all-history');
    if (deleteHistoryBtn) {
      deleteHistoryBtn.addEventListener('click', () => this.handleDeleteAllHistory());
    }

    // 50. Delete Account button
    const deleteAccountBtn = document.getElementById('btn-delete-account');
    if (deleteAccountBtn) {
      deleteAccountBtn.addEventListener('click', () => this.handleDeleteAccount());
    }
  }

  applyTheme(theme) {
    if (theme === 'system') {
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      theme = prefersDark ? 'dark' : 'light';
    }

    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.body.classList.remove('bg-[#fbf9f5]', 'text-stone-900');
    } else {
      document.documentElement.removeAttribute('data-theme');
      document.body.classList.add('bg-[#fbf9f5]', 'text-stone-900');
    }
    localStorage.setItem('excuse_ai_theme', theme);
  }

  async loadSettings() {
    try {
      const data = await api.get('/user/settings');
      this.settings = data.settings || {};

      const toneSelect = document.getElementById('setting-default-tone');
      const lengthSelect = document.getElementById('setting-default-length');
      const deliverySelect = document.getElementById('setting-default-delivery');
      const apiKeyInput = document.getElementById('setting-api-key');

      if (toneSelect && this.settings.default_tone) toneSelect.value = this.settings.default_tone;
      if (lengthSelect && this.settings.default_length) lengthSelect.value = this.settings.default_length;
      if (deliverySelect && this.settings.default_delivery) deliverySelect.value = this.settings.default_delivery;
      if (apiKeyInput && this.settings.masked_api_key) apiKeyInput.placeholder = `Configured: ${this.settings.masked_api_key}`;

      const currentTheme = this.settings.theme_preference || localStorage.getItem('excuse_ai_theme') || 'light';
      this.applyTheme(currentTheme);
      document.querySelectorAll('.theme-option-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === currentTheme);
      });
    } catch (err) {
      // Quiet fail if guest
    }
  }

  async loadProfile() {
    const user = auth.getUser();
    if (!user) return;

    const nameInput = document.getElementById('profile-name');
    const emailInput = document.getElementById('profile-email');
    const avatarImg = document.getElementById('profile-avatar-display');
    const nameDisplay = document.getElementById('profile-name-display');
    const memberSinceEl = document.getElementById('profile-member-since');

    if (nameInput) nameInput.value = user.name || '';
    if (emailInput) emailInput.value = user.email || '';
    if (nameDisplay) nameDisplay.textContent = user.name || 'User';
    
    const avatarSrc = user.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name || 'User')}&background=854d0e&color=ffffff`;
    if (avatarImg) {
      avatarImg.src = avatarSrc;
    }

    if (memberSinceEl) {
      const createdDate = user.created_at ? new Date(user.created_at) : new Date();
      const monthYear = createdDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
      memberSinceEl.textContent = `Member Since: ${monthYear}`;
    }
  }

  getTimeGreeting() {
    const hour = new Date().getHours();
    if (hour >= 4 && hour < 12) return 'Good morning 👋';
    if (hour >= 12 && hour < 17) return 'Good afternoon 👋';
    return 'Good evening 👋';
  }

  async loadDashboardStats() {
    const greetingEl = document.getElementById('dash-greeting');
    if (greetingEl) {
      greetingEl.textContent = this.getTimeGreeting();
    }

    try {
      const data = await api.get('/dashboard/stats');
      const s = data.stats || {};

      const totalExcusesEl = document.getElementById('dash-stat-excuses');
      const savedExcusesEl = document.getElementById('dash-stat-saved');
      const totalDocsEl = document.getElementById('dash-stat-docs');
      const totalFavsEl = document.getElementById('dash-stat-favs');

      const totalExcuses = s.total_excuses || 0;
      const totalDocs = s.total_documents || 0;
      const totalFavs = s.total_favorites || 0;

      if (totalExcusesEl) totalExcusesEl.textContent = totalExcuses;
      if (savedExcusesEl) savedExcusesEl.textContent = totalExcuses;
      if (totalDocsEl) totalDocsEl.textContent = totalDocs;
      if (totalFavsEl) totalFavsEl.textContent = totalFavs;

      const recentList = document.getElementById('dash-recent-list');
      if (recentList) {
        recentList.innerHTML = '';
        const recents = data.recent_excuses || [];
        if (recents.length === 0) {
          recentList.innerHTML = '<p class="text-sm text-stone-500 py-6 text-center">No explanations generated yet. Click "Generate Excuse" above to start!</p>';
        } else {
          recents.forEach(item => {
            const row = document.createElement('div');
            row.className = 'flex items-center justify-between p-3.5 rounded-xl bg-white border border-stone-200 text-sm hover:border-amber-700/40 transition-colors shadow-sm';
            row.innerHTML = `
              <div class="truncate mr-4">
                <p class="font-medium text-stone-900 truncate">${item.scenario}</p>
                <p class="text-xs text-stone-500 mt-0.5">To: ${item.recipient} • ${new Date(item.created_at).toLocaleDateString()}</p>
              </div>
              <span class="px-2.5 py-0.5 rounded text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 shrink-0 font-mono">
                ${item.believability_score}% Believable
              </span>
            `;
            recentList.appendChild(row);
          });
        }
      }
    } catch (err) {}
  }

  async handleAvatarUpload(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      showToast('Please select a valid image file', 'error');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      showToast('Image size must be less than 5MB', 'error');
      return;
    }

    const filenameLabel = document.getElementById('profile-upload-filename');
    if (filenameLabel) filenameLabel.textContent = file.name;

    const reader = new FileReader();
    reader.onload = async (e) => {
      const base64Data = e.target.result;
      
      // Update preview immediately
      const avatarImg = document.getElementById('profile-avatar-display');
      if (avatarImg) avatarImg.src = base64Data;
      document.querySelectorAll('.current-user-avatar').forEach(img => img.src = base64Data);

      try {
        const formData = new FormData();
        formData.append('avatar_file', file);
        
        const token = localStorage.getItem('excuse_ai_token');
        const res = await fetch('/api/user/avatar', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to upload photo');
        
        auth.currentUser = data.user;
        showToast('Profile photo updated successfully', 'success');
      } catch (err) {
        showToast(err.message || 'Failed to upload photo', 'error');
      }
    };
    reader.readAsDataURL(file);
  }

  async handleSavePreferences() {
    const toneSelect = document.getElementById('setting-default-tone');
    const lengthSelect = document.getElementById('setting-default-length');
    const deliverySelect = document.getElementById('setting-default-delivery');
    const apiKeyInput = document.getElementById('setting-api-key');
    const activeThemeBtn = document.querySelector('.theme-option-btn.active');

    const default_tone = toneSelect ? toneSelect.value : 'Professional';
    const default_length = lengthSelect ? lengthSelect.value : 'Medium';
    const default_delivery = deliverySelect ? deliverySelect.value : 'WhatsApp';
    const theme_preference = activeThemeBtn ? activeThemeBtn.dataset.theme : 'light';
    const custom_api_key = apiKeyInput && apiKeyInput.value.trim() ? apiKeyInput.value.trim() : undefined;

    try {
      await api.post('/user/settings', {
        default_tone,
        default_length,
        default_delivery,
        theme_preference,
        custom_api_key
      });
      showToast('Preferences saved successfully', 'success');
      if (apiKeyInput) apiKeyInput.value = '';
      this.loadSettings();
    } catch (err) {
      showToast(err.message || 'Failed to save preferences', 'error');
    }
  }

  async handleSaveProfile() {
    const nameInput = document.getElementById('profile-name');
    const name = nameInput ? nameInput.value.trim() : '';

    if (!name) {
      showToast('Name cannot be empty', 'error');
      return;
    }

    try {
      const data = await api.post('/user/profile', { name });
      auth.currentUser = data.user;
      showToast('Profile updated successfully', 'success');
      this.loadProfile();
    } catch (err) {
      showToast(err.message || 'Failed to update profile', 'error');
    }
  }

  async handleRequestPasswordOtp() {
    const btn = document.getElementById('btn-request-pass-otp');
    if (btn) btn.disabled = true;
    try {
      const res = await api.post('/user/request-password-otp', {});
      showToast(res.message || '6-digit OTP sent to your email', 'info');
      const otpInput = document.getElementById('pass-otp');
      if (otpInput) {
        otpInput.focus();
      }
    } catch (err) {
      showToast(err.message || 'Failed to send OTP', 'error');
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  async handleChangePassword() {
    const oldPassInput = document.getElementById('pass-current');
    const otpInput = document.getElementById('pass-otp');
    const newPassInput = document.getElementById('pass-new');
    const confirmPassInput = document.getElementById('pass-confirm');

    const old_password = oldPassInput ? oldPassInput.value : '';
    const otp_code = otpInput ? otpInput.value.trim() : '';
    const new_password = newPassInput ? newPassInput.value : '';
    const confirm_password = confirmPassInput ? confirmPassInput.value : '';

    if (!new_password || new_password.length < 6) {
      showToast('New password must be at least 6 characters', 'error');
      return;
    }
    if (new_password !== confirm_password) {
      showToast('Passwords do not match', 'error');
      return;
    }

    try {
      if (otp_code) {
        // Verification with 6-digit OTP
        const res = await api.post('/user/verify-password-otp', {
          otp_code,
          new_password,
          confirm_password
        });
        showToast(res.message || 'Password updated successfully', 'success');
      } else {
        // Direct password change with old password
        if (!old_password) {
          showToast('Enter your current password or request an email OTP', 'error');
          return;
        }
        await api.post('/user/change-password', {
          old_password,
          new_password,
          confirm_password
        });
        showToast('Password updated successfully', 'success');
      }

      if (oldPassInput) oldPassInput.value = '';
      if (otpInput) otpInput.value = '';
      if (newPassInput) newPassInput.value = '';
      if (confirmPassInput) confirmPassInput.value = '';
    } catch (err) {
      showToast(err.message || 'Failed to change password', 'error');
    }
  }

  // 50. Privacy & Data Controls: Delete All History
  async handleDeleteAllHistory() {
    const confirmed = confirm('Are you sure you want to delete ALL your explanation history and generated documents? This cannot be undone.');
    if (!confirmed) return;

    try {
      await api.delete('/user/history');
      showToast('All history records cleared', 'info');
      this.loadDashboardStats();
    } catch (err) {
      showToast('Failed to clear history', 'error');
    }
  }

  // 50. Privacy & Data Controls: Delete Account
  async handleDeleteAccount() {
    const confirmed = confirm('WARNING: Are you sure you want to permanently delete your account and all associated data? You will be logged out immediately.');
    if (!confirmed) return;

    try {
      await api.delete('/user/account');
      showToast('Account permanently deleted', 'info');
      auth.logout();
    } catch (err) {
      showToast('Failed to delete account', 'error');
    }
  }
}

export const profileSettings = new ProfileSettingsManager();
