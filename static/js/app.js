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
  }

  updateNavigationUI() {
    const isAuthed = auth.isAuthenticated();
    const user = auth.getUser();

    // Public Header vs Authenticated Header / Layout
    const publicHeader = document.getElementById('public-header');
    const authHeader = document.getElementById('auth-header');
    const appSidebar = document.getElementById('app-sidebar');

    if (isAuthed) {
      if (publicHeader) publicHeader.classList.add('hidden');
      if (authHeader) authHeader.classList.remove('hidden');
      if (appSidebar) appSidebar.classList.remove('hidden');

      // Update user badge in auth header / sidebar
      const userNameBadges = document.querySelectorAll('.current-user-name');
      userNameBadges.forEach(el => el.textContent = user.name || 'User');

      const userEmailBadges = document.querySelectorAll('.current-user-email');
      userEmailBadges.forEach(el => el.textContent = user.email || '');

      const userAvatarImgs = document.querySelectorAll('.current-user-avatar');
      const avatarSrc = user.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name || 'User')}&background=1e293b&color=94a3b8`;
      userAvatarImgs.forEach(img => img.src = avatarSrc);

      // Active sidebar item highlight
      document.querySelectorAll('.sidebar-nav-item').forEach(item => {
        const itemTarget = item.dataset.view;
        item.classList.toggle('active', itemTarget === this.currentView);
      });
    } else {
      if (publicHeader) publicHeader.classList.remove('hidden');
      if (authHeader) authHeader.classList.add('hidden');
      if (appSidebar) appSidebar.classList.add('hidden');
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
        this.navigate(targetView);
      }

      // Logout buttons
      const logoutBtn = e.target.closest('[data-action="logout"]');
      if (logoutBtn) {
        e.preventDefault();
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
  }

  bindAuthForms() {
    // Register Form
    const registerForm = document.getElementById('form-register');
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
          await auth.register({ name, email, password, confirm_password, terms_accepted });
          this.navigate('dashboard');
        } catch (err) {
          showToast(err.message, 'error');
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
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

    // Google OAuth modal & buttons
    document.querySelectorAll('.btn-google-auth').forEach(btn => {
      btn.addEventListener('click', () => {
        const modal = document.getElementById('google-account-modal');
        if (modal) {
          modal.classList.remove('hidden');
        } else {
          auth.loginWithGoogle().then(() => this.navigate('dashboard'));
        }
      });
    });

    // Google Direct Auth Form inside modal
    const googleAuthForm = document.getElementById('form-google-direct-auth');
    if (googleAuthForm) {
      googleAuthForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('google-auth-name').value.trim();
        const email = document.getElementById('google-auth-email').value.trim();
        const modal = document.getElementById('google-account-modal');
        if (modal) modal.classList.add('hidden');

        try {
          await auth.loginWithGoogle({ name, email });
          this.navigate('dashboard');
        } catch (err) {
          showToast('Google sign-in failed', 'error');
        }
      });
    }

    // Direct Google Quick Connect
    const btnGoogleQuick = document.getElementById('btn-google-quick-connect');
    if (btnGoogleQuick) {
      btnGoogleQuick.addEventListener('click', async () => {
        const modal = document.getElementById('google-account-modal');
        if (modal) modal.classList.add('hidden');
        try {
          await auth.loginWithGoogle();
          this.navigate('dashboard');
        } catch (err) {
          showToast('Google sign-in failed', 'error');
        }
      });
    }

    // Forgot Password Form
    const forgotForm = document.getElementById('form-forgot-password');
    if (forgotForm) {
      forgotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('forgot-email').value;
        const submitBtn = document.getElementById('btn-forgot-submit');
        const resultBox = document.getElementById('forgot-result-box');
        const testLink = document.getElementById('forgot-test-link');

        if (submitBtn) submitBtn.disabled = true;

        try {
          const res = await auth.forgotPassword(email);
          if (resultBox) {
            resultBox.classList.remove('hidden');
          }
          if (testLink && res.debug_reset_token) {
            testLink.dataset.token = res.debug_reset_token;
            testLink.onclick = () => {
              const tokenInput = document.getElementById('reset-token');
              if (tokenInput) tokenInput.value = res.debug_reset_token;
              this.navigate('reset-password');
            };
          }
        } catch (err) {
          showToast(err.message, 'error');
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }

    // Reset Password Form
    const resetForm = document.getElementById('form-reset-password');
    if (resetForm) {
      resetForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = document.getElementById('reset-token').value;
        const new_password = document.getElementById('reset-new-password').value;
        const confirm_password = document.getElementById('reset-confirm-password').value;
        const submitBtn = document.getElementById('btn-reset-submit');

        if (submitBtn) submitBtn.disabled = true;

        try {
          await auth.resetPassword({ token, new_password, confirm_password });
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
