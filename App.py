import streamlit as st
from supabase import create_client, Client
import os
from urllib.parse import urlparse

def create_supabase_client(url: str, anon_key: str) -> Client:
    """Create Supabase client with URL and anon key"""
    try:
        supabase: Client = create_client(url, anon_key)
        return supabase
    except Exception as e:
        st.error(f"Failed to create Supabase client: {str(e)}")
        return None

def execute_sql_script(supabase: Client, script_content: str, script_name: str):
    """Execute SQL script using Supabase client and return results"""
    try:
        result = supabase.rpc('execute_sql', {'sql_query': script_content}).execute()
        return True, f"✅ {script_name} executed successfully"
    except Exception as e:
        try:
            # Split script into individual statements
            statements = [stmt.strip() for stmt in script_content.split(';') if stmt.strip()]
            for statement in statements:
                if statement:
                    supabase.postgrest.session.post(
                        f"{supabase.url}/rest/v1/rpc/execute_sql",
                        json={"sql": statement},
                        headers=supabase.postgrest.auth.session.headers
                    )
            return True, f"✅ {script_name} executed successfully"
        except Exception as fallback_error:
            return False, f"❌ Error in {script_name}: {str(fallback_error)}"

def parse_supabase_url(database_url):
    """Parse Supabase database URL to extract connection parameters"""
    parsed = urlparse(database_url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path[1:],  # Remove leading slash
        'user': parsed.username,
        'password': parsed.password
    }

def get_sql_scripts():
    """Define all SQL scripts content"""
    scripts = {
        "01_create_tables.sql": """
-- WordPress Authentication Manager Database Schema
-- Create main tables for the application

-- Users table for WordPress authentication
CREATE TABLE IF NOT EXISTS wp_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    user_status INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Authentication sessions table
CREATE TABLE IF NOT EXISTS auth_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES wp_users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    consumer_key VARCHAR(255),
    consumer_secret VARCHAR(255),
    wp_site_url TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES wp_users(id) ON DELETE CASCADE,
    subscription_id VARCHAR(255) UNIQUE NOT NULL,
    plan_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    consumer_secret VARCHAR(255) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- WordPress sites table
CREATE TABLE IF NOT EXISTS wp_sites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES wp_users(id) ON DELETE CASCADE,
    site_url TEXT NOT NULL,
    site_name VARCHAR(255),
    consumer_key VARCHAR(255),
    consumer_secret VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User permissions table
CREATE TABLE IF NOT EXISTS user_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES wp_users(id) ON DELETE CASCADE,
    permission_name VARCHAR(100) NOT NULL,
    permission_value BOOLEAN DEFAULT FALSE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    granted_by INTEGER REFERENCES wp_users(id) ON DELETE SET NULL,
    UNIQUE(user_id, permission_name)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_auth_sessions_token ON auth_sessions(token);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_active ON auth_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_api_logs_user_id ON api_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_api_logs_created_at ON api_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_wp_sites_user_id ON wp_sites(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id);
""",

        "02_insert_sample_data.sql": """
-- Insert sample data for testing

-- Sample users
INSERT INTO wp_users (username, email, display_name, user_status) VALUES
('admin', 'admin@example.com', 'Administrator', 1),
('testuser', 'test@example.com', 'Test User', 1),
('demo', 'demo@example.com', 'Demo User', 0)
ON CONFLICT (username) DO NOTHING;

-- Sample WordPress sites
INSERT INTO wp_sites (user_id, site_url, site_name, consumer_key, consumer_secret) VALUES
(1, 'https://aipropiq.com', 'AI Propiq', 'ck_sample_key_123', 'cs_sample_secret_456'),
(2, 'https://example.com', 'Example Site', 'ck_test_key_789', 'cs_test_secret_012')
ON CONFLICT DO NOTHING;

-- Sample permissions
INSERT INTO user_permissions (user_id, permission_name, permission_value, granted_by) VALUES
(1, 'manage_subscriptions', TRUE, 1),
(1, 'view_analytics', TRUE, 1),
(1, 'manage_users', TRUE, 1),
(2, 'view_subscriptions', TRUE, 1),
(2, 'view_analytics', FALSE, 1)
ON CONFLICT (user_id, permission_name) DO NOTHING;

-- Sample subscriptions
INSERT INTO subscriptions (user_id, subscription_id, plan_name, status, start_date, end_date, consumer_secret, metadata) VALUES
(1, 'sub_123456789', 'Premium Plan', 'active', NOW() - INTERVAL '30 days', NOW() + INTERVAL '335 days', 'cs_premium_secret_123', '{"features": ["api_access", "premium_support"]}'),
(2, 'sub_987654321', 'Basic Plan', 'active', NOW() - INTERVAL '15 days', NOW() + INTERVAL '350 days', 'cs_basic_secret_456', '{"features": ["basic_access"]}')
ON CONFLICT (subscription_id) DO NOTHING;
""",

        "03_create_functions.sql": """
-- Utility functions for the WordPress Authentication Manager

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM auth_sessions 
    WHERE expires_at < NOW() OR (last_used_at < NOW() - INTERVAL '30 days');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to update user activity
CREATE OR REPLACE FUNCTION update_user_activity(session_token TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE auth_sessions 
    SET last_used_at = NOW() 
    WHERE token = session_token AND is_active = TRUE;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to validate JWT token format
CREATE OR REPLACE FUNCTION is_valid_jwt_format(token TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if token has exactly 3 parts separated by dots
    RETURN array_length(string_to_array(token, '.'), 1) = 3;
END;
$$ LANGUAGE plpgsql;

-- Function to get user subscription by consumer secret
CREATE OR REPLACE FUNCTION get_subscription_by_secret(secret TEXT)
RETURNS TABLE(
    subscription_id VARCHAR(255),
    user_id INTEGER,
    plan_name VARCHAR(255),
    status VARCHAR(50),
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT s.subscription_id, s.user_id, s.plan_name, s.status, s.start_date, s.end_date
    FROM subscriptions s
    WHERE s.consumer_secret = secret AND s.status = 'active';
END;
$$ LANGUAGE plpgsql;

-- Function to log API requests
CREATE OR REPLACE FUNCTION log_api_request(
    p_user_id INTEGER,
    p_endpoint VARCHAR(500),
    p_method VARCHAR(10),
    p_status_code INTEGER,
    p_response_time_ms INTEGER DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL,
    p_request_data JSONB DEFAULT NULL,
    p_response_data JSONB DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    log_id INTEGER;
BEGIN
    INSERT INTO api_logs (user_id, endpoint, method, status_code, response_time_ms, error_message, request_data, response_data)
    VALUES (p_user_id, p_endpoint, p_method, p_status_code, p_response_time_ms, p_error_message, p_request_data, p_response_data)
    RETURNING id INTO log_id;
    
    RETURN log_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get active session by token
CREATE OR REPLACE FUNCTION get_active_session(session_token TEXT)
RETURNS TABLE(
    session_id INTEGER,
    user_id INTEGER,
    username VARCHAR(255),
    wp_site_url TEXT,
    consumer_key VARCHAR(255),
    consumer_secret VARCHAR(255)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id,
        a.user_id,
        u.username,
        a.wp_site_url,
        a.consumer_key,
        a.consumer_secret
    FROM auth_sessions a
    JOIN wp_users u ON a.user_id = u.id
    WHERE a.token = session_token 
    AND a.is_active = TRUE 
    AND (a.expires_at IS NULL OR a.expires_at > NOW());
END;
$$ LANGUAGE plpgsql;
""",

        "04_create_views.sql": """
-- Useful views for the WordPress Authentication Manager

-- View for active user sessions
CREATE OR REPLACE VIEW active_sessions AS
SELECT 
    a.id as session_id,
    u.username,
    u.email,
    a.wp_site_url,
    a.consumer_key,
    a.created_at as session_created,
    a.last_used_at,
    a.expires_at,
    CASE 
        WHEN a.expires_at IS NULL THEN 'No Expiry'
        WHEN a.expires_at > NOW() THEN 'Valid'
        ELSE 'Expired'
    END as session_status
FROM auth_sessions a
JOIN wp_users u ON a.user_id = u.id
WHERE a.is_active = TRUE;

-- View for subscription summary
CREATE OR REPLACE VIEW subscription_summary AS
SELECT 
    u.username,
    u.email,
    s.subscription_id,
    s.plan_name,
    s.status,
    s.start_date,
    s.end_date,
    CASE 
        WHEN s.end_date > NOW() THEN 'Active'
        WHEN s.end_date <= NOW() THEN 'Expired'
        ELSE 'Unknown'
    END as subscription_status,
    EXTRACT(DAYS FROM (s.end_date - NOW())) as days_remaining
FROM subscriptions s
JOIN wp_users u ON s.user_id = u.id;

-- View for API usage statistics
CREATE OR REPLACE VIEW api_usage_stats AS
SELECT 
    u.username,
    COUNT(*) as total_requests,
    COUNT(CASE WHEN al.status_code BETWEEN 200 AND 299 THEN 1 END) as successful_requests,
    COUNT(CASE WHEN al.status_code >= 400 THEN 1 END) as failed_requests,
    AVG(al.response_time_ms) as avg_response_time,
    MAX(al.created_at) as last_request_at,
    DATE_TRUNC('day', al.created_at) as request_date
FROM api_logs al
LEFT JOIN wp_users u ON al.user_id = u.id
WHERE al.created_at >= NOW() - INTERVAL '30 days'
GROUP BY u.username, DATE_TRUNC('day', al.created_at)
ORDER BY request_date DESC;

-- View for user permissions summary
CREATE OR REPLACE VIEW user_permissions_summary AS
SELECT 
    u.username,
    u.email,
    STRING_AGG(
        CASE WHEN up.permission_value THEN up.permission_name END, 
        ', '
    ) as granted_permissions,
    COUNT(CASE WHEN up.permission_value THEN 1 END) as total_permissions
FROM wp_users u
LEFT JOIN user_permissions up ON u.id = up.user_id
GROUP BY u.id, u.username, u.email;

-- View for WordPress sites with user info
CREATE OR REPLACE VIEW wp_sites_with_users AS
SELECT 
    ws.id as site_id,
    u.username,
    u.email,
    ws.site_url,
    ws.site_name,
    ws.consumer_key,
    ws.is_active,
    ws.last_sync_at,
    ws.created_at as site_added_at,
    COUNT(a.id) as active_sessions
FROM wp_sites ws
JOIN wp_users u ON ws.user_id = u.id
LEFT JOIN auth_sessions a ON ws.user_id = a.user_id AND a.is_active = TRUE
GROUP BY ws.id, u.username, u.email, ws.site_url, ws.site_name, ws.consumer_key, ws.is_active, ws.last_sync_at, ws.created_at;
"""
    }
    return scripts

def main():
    st.set_page_config(
        page_title="Supabase Schema Setup",
        page_icon="🗄️",
        layout="wide"
    )
    
    st.title("🗄️ WordPress Auth Manager - Supabase Schema Setup")
    st.markdown("Automatically set up your Supabase database schema for the WordPress Authentication Manager")
    
    # Sidebar for connection details
    st.sidebar.header("🔗 Supabase Connection")
    
    # Supabase connection parameters
    supabase_url = st.sidebar.text_input(
        "Supabase Project URL:",
        placeholder="https://your-project.supabase.co",
        help="Find this in your Supabase project settings"
    )
    
    anon_key = st.sidebar.text_input(
        "Supabase Anon Key:",
        placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        type="password",
        help="Find this in your Supabase project settings under API > anon public"
    )
    
    st.sidebar.divider()
    st.sidebar.subheader("🔑 API Configuration")
    consumer_secret = st.sidebar.text_input(
        "Consumer Secret:",
        placeholder="cs_your_consumer_secret_here",
        type="password",
        help="Consumer secret for subscription API access"
    )
    
    # Create Supabase client if credentials provided
    supabase_client = None
    if supabase_url and anon_key:
        supabase_client = create_supabase_client(supabase_url, anon_key)
        if supabase_client:
            st.sidebar.success("✅ Supabase client created successfully")
        else:
            st.sidebar.error("❌ Failed to create Supabase client")
    else:
        st.sidebar.warning("⚠️ Please provide Supabase URL and Anon Key")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📋 Schema Setup Steps")
        
        scripts = get_sql_scripts()
        script_descriptions = {
            "01_create_tables.sql": "Create main database tables (users, sessions, subscriptions, etc.)",
            "02_insert_sample_data.sql": "Insert sample data for testing",
            "03_create_functions.sql": "Create utility functions for database operations",
            "04_create_views.sql": "Create helpful views for data analysis"
        }
        
        for script_name, description in script_descriptions.items():
            with st.expander(f"📄 {script_name}", expanded=False):
                st.write(description)
                st.code(scripts[script_name][:500] + "..." if len(scripts[script_name]) > 500 else scripts[script_name], language="sql")
    
    with col2:
        st.header("🚀 Execute Setup")
        
        if supabase_client:
            st.success("✅ Ready to execute")
            
            # Test connection button
            if st.button("🔍 Test Connection", use_container_width=True):
                try:
                    # Test connection by trying to fetch from auth.users (should work with anon key)
                    result = supabase_client.table('auth.users').select('count').limit(1).execute()
                    st.success("✅ Supabase connection successful!")
                except Exception as e:
                    st.error(f"❌ Connection test failed: {str(e)}")
            
            st.divider()
            
            if consumer_secret:
                st.info(f"🔑 Consumer Secret configured for subscription API")
            else:
                st.warning("⚠️ Consumer Secret not provided - subscription API may not work")
            
            # Execute all scripts button
            if st.button("🚀 Setup Complete Schema", use_container_width=True, type="primary"):
                progress_bar = st.progress(0)
                status_container = st.container()
                
                try:
                    scripts = get_sql_scripts()
                    total_scripts = len(scripts)
                    
                    with status_container:
                        st.write("**Execution Log:**")
                        
                    for i, (script_name, script_content) in enumerate(scripts.items()):
                        progress = (i + 1) / total_scripts
                        progress_bar.progress(progress)
                        
                        success, message = execute_sql_script(supabase_client, script_content, script_name)
                        
                        with status_container:
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                    
                    st.balloons()
                    st.success("🎉 Schema setup completed successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Setup failed: {str(e)}")
            
            st.divider()
            
            # Individual script execution
            st.subheader("Individual Scripts")
            scripts = get_sql_scripts()
            
            for script_name in scripts.keys():
                if st.button(f"Run {script_name}", use_container_width=True):
                    try:
                        success, message = execute_sql_script(supabase_client, scripts[script_name], script_name)
                        
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"❌ Failed to execute {script_name}: {str(e)}")
        
        else:
            st.warning("⚠️ Please provide Supabase URL and Anon Key in the sidebar")
    
    st.divider()
    st.markdown("""
    ### 📚 Next Steps
    1. **Add your Supabase URL and Anon Key** in the sidebar
    2. **Add Consumer Secret** for subscription API access
    3. **Run the schema setup** using the buttons above
    4. **Verify the tables** were created in your Supabase dashboard
    5. **Use the WordPress Auth Manager** with your new database schema
    
    ### 🔧 Troubleshooting
    - Ensure your Supabase project is active and accessible
    - Verify the Project URL format: `https://your-project.supabase.co`
    - Check that the Anon Key is copied correctly from your project settings
    - Consumer Secret is required for subscription API endpoint access
    
    ### 🔑 API Endpoint Configuration
    - **Subscription API**: `https://aipropiq.com/wp-json/wsp-route/v1/wsp-view-subscription`
    - **Method**: GET
    - **Required Parameter**: `consumer_secret` (configured in sidebar)
    """)

if __name__ == "__main__":
    main()
