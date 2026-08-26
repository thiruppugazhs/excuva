-- ====================================================================
-- EXCUSE.AI — Neon Serverless PostgreSQL Database Schema
-- Paste and run this SQL in your Neon Console (Dashboard > SQL Editor)
-- ====================================================================

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT,
    auth_provider VARCHAR(50) DEFAULT 'email',
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. Sessions Table
CREATE TABLE IF NOT EXISTS sessions (
    token VARCHAR(255) PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. Password Reset Tokens Table
CREATE TABLE IF NOT EXISTS password_resets (
    token VARCHAR(255) PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    used INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 4. Excuses Table
CREATE TABLE IF NOT EXISTS excuses (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scenario TEXT NOT NULL,
    urgency VARCHAR(50) NOT NULL,
    recipient VARCHAR(100) NOT NULL,
    tone VARCHAR(100) NOT NULL,
    details TEXT,
    primary_text TEXT NOT NULL,
    variations_json TEXT DEFAULT '[]',
    believability_score INTEGER DEFAULT 95,
    risk_level VARCHAR(50) DEFAULT 'Low',
    tips_json TEXT DEFAULT '[]',
    is_favorite INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 5. Supporting Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    doc_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    recipient VARCHAR(100) NOT NULL,
    issue_date VARCHAR(100) NOT NULL,
    organization VARCHAR(255) NOT NULL,
    content_json TEXT NOT NULL,
    is_favorite INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 6. User Settings Table
CREATE TABLE IF NOT EXISTS user_settings (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    default_tone VARCHAR(100) DEFAULT 'Professional',
    default_recipient VARCHAR(100) DEFAULT 'Manager',
    custom_api_key TEXT,
    theme_preference VARCHAR(50) DEFAULT 'dark',
    email_notifications INTEGER DEFAULT 1
);

-- Create Indexes for Optimal Query Performance
CREATE INDEX IF NOT EXISTS idx_neon_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_neon_sessions_token ON sessions (token);
CREATE INDEX IF NOT EXISTS idx_neon_sessions_user_id ON sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_neon_excuses_user_id ON excuses (user_id);
CREATE INDEX IF NOT EXISTS idx_neon_excuses_created_at ON excuses (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_neon_documents_user_id ON documents (user_id);
CREATE INDEX IF NOT EXISTS idx_neon_documents_created_at ON documents (created_at DESC);
