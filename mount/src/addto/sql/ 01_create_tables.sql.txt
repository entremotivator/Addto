-- WordPress Authentication Manager Database Schema
-- Create tables for user management, authentication, and subscriptions

-- Users table for storing WordPress user data
CREATE TABLE IF NOT EXISTS wp_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    wp_user_id INTEGER,
    consumer_key VARCHAR(255),
    consumer_secret VARCHAR(255),
    jwt_token TEXT,
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Authentication sessions table
CREATE TABLE IF NOT EXISTS auth_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES wp_users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    wp_site_url VARCHAR(500) NOT NULL,
    auth_method VARCHAR(50) DEFAULT 'jwt', -- jwt, basic, custom
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- WordPress subscriptions table
CREATE TABLE IF NOT EXISTS wp_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES wp_users(id) ON DELETE CASCADE,
    subscription_id VARCHAR(255) NOT NULL,
    product_id VARCHAR(255),
    product_name VARCHAR(255),
    status VARCHAR(50) NOT NULL, -- active, cancelled, expired, pending
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    amount DECIMAL(10,2),
    currency VARCHAR(10) DEFAULT 'USD',
    billing_cycle VARCHAR(50), -- monthly, yearly, one-time
    consumer_secret VARCHAR(255) NOT NULL,
    wp_site_url VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subscription_id, consumer_secret)
);

-- API logs table for tracking requests
CREATE TABLE IF NOT EXISTS api_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES wp_users(id) ON DELETE SET NULL,
    endpoint VARCHAR(500) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    request_data JSONB,
    response_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WordPress sites configuration
CREATE TABLE IF NOT EXISTS wp_sites (
    id SERIAL PRIMARY KEY,
    site_url VARCHAR(500) UNIQUE NOT NULL,
    site_name VARCHAR(255),
    api_base_url VARCHAR(500),
    consumer_key VARCHAR(255),
    consumer_secret VARCHAR(255),
    jwt_secret VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User permissions table
CREATE TABLE IF NOT EXISTS user_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES wp_users(id) ON DELETE CASCADE,
    permission_name VARCHAR(100) NOT NULL,
    permission_value BOOLEAN DEFAULT false,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER REFERENCES wp_users(id),
    UNIQUE(user_id, permission_name)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_wp_users_username ON wp_users(username);
CREATE INDEX IF NOT EXISTS idx_wp_users_email ON wp_users(email);
CREATE INDEX IF NOT EXISTS idx_wp_users_wp_user_id ON wp_users(wp_user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_token ON auth_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires ON auth_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_wp_subscriptions_user_id ON wp_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_wp_subscriptions_status ON wp_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_wp_subscriptions_consumer_secret ON wp_subscriptions(consumer_secret);
CREATE INDEX IF NOT EXISTS idx_api_logs_user_id ON api_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_api_logs_created_at ON api_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_wp_sites_url ON wp_sites(site_url);
CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id);
