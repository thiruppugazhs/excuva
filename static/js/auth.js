// auth.js - Authentication State and Flows
import { api, showToast } from './api.js';

class AuthManager {
  constructor() {
    this.currentUser = null;
    this.initialized = false;
  }

  async init() {
    const token = api.getToken();
    if (token) {
      try {
        const data = await api.get('/auth/me');
        this.currentUser = data.user;
      } catch (err) {
        this.currentUser = null;
        api.setToken(null);
      }
    }
    this.initialized = true;
    window.dispatchEvent(new CustomEvent('auth:change', { detail: { user: this.currentUser } }));
    return this.currentUser;
  }

  isAuthenticated() {
    return !!this.currentUser;
  }

  getUser() {
    return this.currentUser;
  }

  async register({ name, email, password, confirm_password, terms_accepted }) {
    // Client-side validation
    if (!name || !name.trim()) {
      throw new Error('Full name is required.');
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email || !emailRegex.test(email.trim())) {
      throw new Error('Please enter a valid email address.');
    }
    if (!password || password.length < 6) {
      throw new Error('Password must be at least 6 characters.');
    }
    if (password !== confirm_password) {
      throw new Error('Passwords do not match.');
    }
    if (!terms_accepted) {
      throw new Error('You must accept the Terms of Service and Privacy Policy.');
    }

    const data = await api.post('/auth/register', {
      name: name.trim(),
      email: email.trim(),
      password,
      confirm_password,
      terms_accepted
    });

    api.setToken(data.token);
    this.currentUser = data.user;
    window.dispatchEvent(new CustomEvent('auth:change', { detail: { user: this.currentUser } }));
    showToast('Account created successfully', 'success');
    return this.currentUser;
  }

  async login({ email, password, remember_me }) {
    if (!email || !password) {
      throw new Error('Incorrect email or password.');
    }

    const data = await api.post('/auth/login', {
      email: email.trim(),
      password,
      remember_me: !!remember_me
    });

    api.setToken(data.token);
    this.currentUser = data.user;
    window.dispatchEvent(new CustomEvent('auth:change', { detail: { user: this.currentUser } }));
    showToast('Welcome back!', 'success');
    return this.currentUser;
  }

  async loginWithGoogle(mockUser = null) {
    const userPayload = mockUser || {
      name: 'Google User',
      email: 'user.google@example.com',
      avatar_url: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80'
    };

    const data = await api.post('/auth/google', userPayload);
    api.setToken(data.token);
    this.currentUser = data.user;
    window.dispatchEvent(new CustomEvent('auth:change', { detail: { user: this.currentUser } }));
    showToast('Signed in with Google', 'success');
    return this.currentUser;
  }

  async forgotPassword(email) {
    if (!email || !email.trim()) {
      throw new Error('Please enter your email address.');
    }
    const data = await api.post('/auth/forgot-password', { email: email.trim() });
    showToast(data.message, 'info');
    return data;
  }

  async resetPassword({ token, new_password, confirm_password }) {
    if (!token) {
      throw new Error('Reset token missing.');
    }
    if (!new_password || new_password.length < 6) {
      throw new Error('Password must be at least 6 characters.');
    }
    if (new_password !== confirm_password) {
      throw new Error('Passwords do not match.');
    }

    const data = await api.post('/auth/reset-password', {
      token,
      new_password,
      confirm_password
    });

    showToast(data.message, 'success');
    return data;
  }

  async logout() {
    try {
      await api.post('/auth/logout', {});
    } catch (err) {
      // Ignore network errors during logout
    }
    api.setToken(null);
    this.currentUser = null;
    window.dispatchEvent(new CustomEvent('auth:change', { detail: { user: null } }));
    showToast('You have been logged out', 'info');
  }
}

export const auth = new AuthManager();
