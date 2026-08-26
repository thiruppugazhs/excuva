// app.js - Main Application Orchestrator & View Router
import { auth } from './auth.js';
import { generator } from './generator.js';
import { documents } from './documents.js';
import { historyManager } from './history.js';
import { profileSettings } from './profile_settings.js';
import { showToast } from './api.js';

class AppRouter {
  constructor() {
    this.currentView = 'landing';
    this.historyStack = [];
  }

  async init() {
    // Initialize components
    generator.init();
    documents.init();
    historyManager.init();
    profileSettings.init();

    this.bindGlobalEvents();
    this.bindAuthForms();

    // Check for Google OAuth callback token in URL hash or search params
    const hash = window.location.hash || '';
    const search = window.location.search || '';
    let urlToken = null;

    if (hash.includes('google_token=')) {
      urlToken = new URLSearchParams(hash.substring(hash.indexOf('?'))).get('google_token');
    } else if (search.includes('google_token=')) {
      urlToken = new URLSearchParams(search).get('google_token');
    }

    if (urlToken) {
      const { api } = await import('./api.js');
      api.setToken(urlToken);
      window.history.replaceState(null, '', window.location.pathname + '#dashboard');
    }

    // Check user auth state
    const user = await auth.init();
    if (user) {
      this.navigate('dashboard');
    } else {
      this.navigate('landing');
    }
  }

  navigate(viewName, params = {}) {
    // Auth guards
    const authenticatedViews = ['dashboard', 'generator', 'documents', 'history', 'favorites', 'profile', 'settings'];
    const publicOnlyViews = ['login', 'register', 'forgot-password', 'reset-password'];

    const isAuthed = auth.isAuthenticated();

    if (authenticatedViews.includes(viewName) && !isAuthed) {
      showToast('Please log in to access this page', 'info');
      this.navigate('login');
      return;
    }

    if (publicOnlyViews.includes(viewName) && isAuthed) {
      this.navigate('dashboard');
      return;
    }

    // Hide all view containers
    document.querySelectorAll('.view-section').forEach(el => {
      el.classList.add('hidden');
    });

    // Show target view container
    const targetEl = document.getElementById(`view-${viewName}`);
    if (targetEl) {
      targetEl.classList.remove('hidden');
      this.currentView = viewName;
      window.scrollTo({ top: 0, behavior: 'instant' });
    }

    // Update Nav bar state
    this.updateNavigationUI();

    // View-specific initialization hooks
    if (viewName === 'dashboard') {
      profileSettings.loadDashboardStats();
    } else if (viewName === 'history') {
      historyManager.loadData(false);
    } else if (viewName === 'favorites') {
      historyManager.loadData(true);
    } else if (viewName === 'profile') {
      profileSettings.loadProfile();
    } else if (viewName === 'settings') {
      profileSettings.loadSettings();
    } else if (viewName === 'documents' && params.context) {
      documents.setContext(params.context);
    }
    // Close mobile drawer on navigation
    this.closeMobileSidebar();
  }

  toggleMobileSidebar() {
    const sidebar = document.getElementById('app-sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (!sidebar) return;

    const isOpen = sidebar.classList.contains('mobile-open');
    if (isOpen) {
      this.closeMobileSidebar();
    } else {
      sidebar.classList.remove('hidden');
      sidebar.classList.add('mobile-open');
      if (backdrop) backdrop.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
    }
  }

  closeMobileSidebar() {
    const sidebar = document.getElementById('app-sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (sidebar) {
      sidebar.classList.remove('mobile-open');
      if (!auth.isAuthenticated() || ['landing', 'how-it-works', 'features', 'login', 'register', 'forgot-password', 'reset-password'].includes(this.currentView)) {
        sidebar.classList.add('hidden');
      }
    }
    if (backdrop) backdrop.classList.add('hidden');
    document.body.style.overflow = '';
  }

  updateNavigationUI() {
    const isAuthed = auth.isAuthenticated();
    const user = auth.getUser();
    const publicViews = ['landing', 'how-it-works', 'features', 'login', 'register', 'forgot-password', 'reset-password'];
    const isPublicView = publicViews.includes(this.currentView);

    // Public Header vs Authenticated Header / Layout
    const publicHeader = document.getElementById('public-header');
    const authHeader = document.getElementById('auth-header');
    const appSidebar = document.getElementById('app-sidebar');

    if (isAuthed && !isPublicView) {
      if (publicHeader) publicHeader.classList.add('hidden');
      if (authHeader) authHeader.classList.remove('hidden');
      if (appSidebar) appSidebar.classList.remove('hidden');

      // Update user badge in auth header / sidebar
      const userNameBadges = document.querySelectorAll('.current-user-name');
      userNameBadges.forEach(el => el.textContent = user.name || 'User');

      const userEmailBadges = document.querySelectorAll('.current-user-email');
      userEmailBadges.forEach(el => el.textContent = user.email || '');

      const userAvatarImgs = document.querySelectorAll('.current-user-avatar');
      const avatarSrc = user.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name || 'User')}&background=854d0e&color=ffffff`;
      userAvatarImgs.forEach(img => img.src = avatarSrc);

      // Active sidebar item highlight
      document.querySelectorAll('.sidebar-nav-item').forEach(item => {
        const itemTarget = item.dataset.view;
        item.classList.toggle('active', itemTarget === this.currentView);
      });
    } else {
      if (publicHeader) publicHeader.classList.remove('hidden');
      if (authHeader) authHeader.classList.add('hidden');
      if (appSidebar) {
        appSidebar.classList.add('hidden');
        appSidebar.classList.remove('mobile-open');
      }
      this.closeMobileSidebar();
    }
  }

  bindGlobalEvents() {
    // Listen for custom navigation events
    window.addEventListener('nav:navigate', (e) => {
      const { view, context } = e.detail;
      this.navigate(view, { context });
    });

    window.addEventListener('auth:change', () => {
      this.updateNavigationUI();
      if (!auth.isAuthenticated()) {
        this.navigate('landing');
      }
    });

    window.addEventListener('auth:unauthorized', () => {
      showToast('Session expired. Please log in again.', 'error');
      this.navigate('login');
    });

    // Global navigation clicks
    document.addEventListener('click', (e) => {
      const navTarget = e.target.closest('[data-nav]');
      if (navTarget) {
        e.preventDefault();
        const targetView = navTarget.dataset.nav;
        this.closeMobileSidebar();
        this.navigate(targetView);
      }

      // Logout buttons
      const logoutBtn = e.target.closest('[data-action="logout"]');
      if (logoutBtn) {
        e.preventDefault();
        this.closeMobileSidebar();
        auth.logout();
      }

      // Close modal triggers
      const closeModal = e.target.closest('[data-close-modal]');
      if (closeModal) {
        const modalId = closeModal.dataset.closeModal;
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.add('hidden');
      }
    });

    // Custom Document preview renderer event
    window.addEventListener('doc:render', (e) => {
      if (e.detail && e.detail.document) {
        documents.currentDocument = e.detail.document;
        documents.renderDocumentPreview(e.detail.document);
        const previewSection = document.getElementById('doc-preview-section');
        if (previewSection) {
          previewSection.classList.remove('hidden');
          previewSection.scrollIntoView({ behavior: 'smooth' });
        }
      }
    });

    // Mobile Sidebar Toggle & Close Handlers
    const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
    if (btnToggleSidebar) {
      btnToggleSidebar.addEventListener('click', () => this.toggleMobileSidebar());
    }

    const btnCloseSidebar = document.getElementById('btn-close-sidebar');
    if (btnCloseSidebar) {
      btnCloseSidebar.addEventListener('click', () => this.closeMobileSidebar());
    }

    const sidebarBackdrop = document.getElementById('sidebar-backdrop');
    if (sidebarBackdrop) {
      sidebarBackdrop.addEventListener('click', () => this.closeMobileSidebar());
    }

    // Toggle OAuth Setup Guide
    const btnToggleOAuth = document.getElementById('btn-toggle-oauth-guide');
    if (btnToggleOAuth) {
      btnToggleOAuth.addEventListener('click', () => {
        const box = document.getElementById('oauth-setup-box');
        if (box) box.classList.toggle('hidden');
      });
    }
  }

    // Helper to wire Orbital OTP digit slots
    const setupOrbitalSlots = (containerSelector, hiddenInputId) => {
      const container = document.querySelector(containerSelector);
      const hiddenInput = document.getElementById(hiddenInputId);
      if (!container || !hiddenInput) return;

      const slots = container.querySelectorAll('.orbit-slot-input');

      const updateHiddenValue = () => {
        let code = '';
        slots.forEach(slot => {
          code += slot.value || '';
          slot.classList.toggle('filled', !!slot.value);
        });
        hiddenInput.value = code;
      };

      slots.forEach((slot, idx) => {
        slot.addEventListener('input', (e) => {
          const val = e.target.value.replace(/\D/g, '');
          slot.value = val ? val[val.length - 1] : '';
          updateHiddenValue();

          if (slot.value && idx < slots.length - 1) {
            slots[idx + 1].focus();
            slots[idx + 1].select();
          }
        });

        slot.addEventListener('keydown', (e) => {
          if (e.key === 'Backspace' && !slot.value && idx > 0) {
            slots[idx - 1].focus();
            slots[idx - 1].value = '';
            updateHiddenValue();
          }
        });

        slot.addEventListener('paste', (e) => {
          e.preventDefault();
          const pasteData = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');
          if (pasteData) {
            for (let i = 0; i < slots.length; i++) {
              slots[i].value = pasteData[i] || '';
            }
            updateHiddenValue();
            const lastFilled = Math.min(pasteData.length, slots.length) - 1;
            if (lastFilled >= 0) slots[lastFilled].focus();
          }
        });
      });
    };

    setupOrbitalSlots('.reg-orbit-slots', 'reg-otp-code');
    setupOrbitalSlots('.reset-orbit-slots', 'reset-otp-code');

    // Register Form - Step 1: Send OTP
    const registerForm = document.getElementById('form-register');
    const registerOtpForm = document.getElementById('form-register-otp');

    if (registerForm) {
      registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('reg-name').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        const confirm_password = document.getElementById('reg-confirm-password').value;
        const terms_accepted = document.getElementById('reg-terms').checked;
        const submitBtn = document.getElementById('btn-register-submit');

        if (submitBtn) submitBtn.disabled = true;

        try {
          pendingRegData = { name, email, password, confirm_password, terms_accepted };
          const res = await auth.sendRegistrationOtp(pendingRegData);
          registerForm.classList.add('hidden');
          if (registerOtpForm) {
            registerOtpForm.classList.remove('hidden');
            const emailDisplay = document.getElementById('reg-otp-email-display');
            if (emailDisplay) emailDisplay.textContent = email;
            const slots = registerOtpForm.querySelectorAll('.orbit-slot-input');
            slots.forEach(s => { s.value = ''; s.classList.remove('filled'); });
            const hiddenOtp = document.getElementById('reg-otp-code');
            if (hiddenOtp) hiddenOtp.value = '';
            if (slots.length > 0) slots[0].focus();
          }
        } catch (err) {
          showToast(err.message, 'error');
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }

    // Resend registration OTP button
    const btnResendReg = document.getElementById('btn-resend-reg-otp');
    if (btnResendReg) {
      btnResendReg.addEventListener('click', async () => {
        if (!pendingRegData) return;
        try {
          await auth.sendRegistrationOtp(pendingRegData);
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    }

    // Register Form - Step 2: Verify OTP
    if (registerOtpForm) {
      registerOtpForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const otp_code = document.getElementById('reg-otp-code').value;
        const submitBtn = document.getElementById('btn-verify-reg-otp');

        if (!pendingRegData) {
          showToast('Registration details missing. Please start over.', 'error');
          registerOtpForm.classList.add('hidden');
          if (registerForm) registerForm.classList.remove('hidden');
          return;
        }

        if (!otp_code || otp_code.length !== 6) {
          showToast('Please enter all 6 verification digits.', 'error');
          return;
        }

        if (submitBtn) submitBtn.disabled = true;

        try {
          await auth.verifyRegistrationOtp({
            name: pendingRegData.name,
            email: pendingRegData.email,
            password: pendingRegData.password,
            otp_code
          });
          this.navigate('dashboard');
        } catch (err) {
          showToast(err.message, 'error');
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }

    // Back to registration edit button
    const btnBackToReg = document.getElementById('btn-back-to-reg');
    if (btnBackToReg) {
      btnBackToReg.addEventListener('click', () => {
        if (registerOtpForm) registerOtpForm.classList.add('hidden');
        if (registerForm) registerForm.classList.remove('hidden');
      });
    }

    // Login Form
    const loginForm = document.getElementById('form-login');
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const remember_me = document.getElementById('login-remember').checked;
        const submitBtn = document.getElementById('btn-login-submit');

        if (submitBtn) submitBtn.disabled = true;

        try {
          await auth.login({ email, password, remember_me });
          this.navigate('dashboard');
        } catch (err) {
          showToast(err.message, 'error');
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }

    // Google OAuth Direct Redirect
    document.querySelectorAll('.btn-google-auth').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        window.location.href = '/api/auth/google/login';
      });
    });

    // Forgot Password Form (Requests 6-Digit OTP)
    const forgotForm = document.getElementById('form-forgot-password');
    if (forgotForm) {
      forgotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('forgot-email').value;
        const submitBtn = document.getElementById('btn-forgot-submit');

        if (submitBtn) submitBtn.disabled = true;

        try {
          await auth.forgotPassword(email);
          const resetEmailInput = document.getElementById('reset-email-input');
          if (resetEmailInput) resetEmailInput.value = email;
          const slots = document.querySelectorAll('.reset-orbit-slots .orbit-slot-input');
          slots.forEach(s => { s.value = ''; s.classList.remove('filled'); });
          const hiddenOtp = document.getElementById('reset-otp-code');
          if (hiddenOtp) hiddenOtp.value = '';
          this.navigate('reset-password');
          if (slots.length > 0) setTimeout(() => slots[0].focus(), 150);
        } catch (err) {
          showToast(err.message, 'error');
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }

    // Reset Password Form (Submits 6-Digit OTP + New Password)
    const resetForm = document.getElementById('form-reset-password');
    if (resetForm) {
      resetForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('reset-email-input').value;
        const otp_code = document.getElementById('reset-otp-code').value;
        const new_password = document.getElementById('reset-new-password').value;
        const confirm_password = document.getElementById('reset-confirm-password').value;
        const submitBtn = document.getElementById('btn-reset-submit');

        if (submitBtn) submitBtn.disabled = true;

        try {
          await auth.resetPasswordWithOtp({ email, otp_code, new_password, confirm_password });
          this.navigate('login');
        } catch (err) {
          showToast(err.message, 'error');
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }
  }
}

export const router = new AppRouter();

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  router.init();
});
