-- Useful views for WordPress Authentication Manager

-- View for active user sessions
CREATE OR REPLACE VIEW active_user_sessions AS
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    u.display_name,
    s.session_token,
    s.wp_site_url,
    s.auth_method,
    s.expires_at,
    s.last_used_at,
    EXTRACT(EPOCH FROM (s.expires_at - CURRENT_TIMESTAMP))/3600 as hours_until_expiry
FROM wp_users u
JOIN auth_sessions s ON u.id = s.user_id
WHERE s.is_active = true 
AND s.expires_at > CURRENT_TIMESTAMP;

-- View for subscription summary
CREATE OR REPLACE VIEW subscription_summary AS
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    COUNT(s.id) as total_subscriptions,
    COUNT(CASE WHEN s.status = 'active' THEN 1 END) as active_subscriptions,
    COUNT(CASE WHEN s.status = 'cancelled' THEN 1 END) as cancelled_subscriptions,
    SUM(CASE WHEN s.status = 'active' THEN s.amount ELSE 0 END) as total_active_amount,
    MAX(s.end_date) as latest_expiry_date
FROM wp_users u
LEFT JOIN wp_subscriptions s ON u.id = s.user_id
GROUP BY u.id, u.username, u.email;

-- View for API usage statistics
CREATE OR REPLACE VIEW api_usage_stats AS
SELECT 
    u.username,
    DATE(l.created_at) as date,
    COUNT(*) as total_requests,
    COUNT(CASE WHEN l.status_code >= 200 AND l.status_code < 300 THEN 1 END) as successful_requests,
    COUNT(CASE WHEN l.status_code >= 400 THEN 1 END) as error_requests,
    AVG(l.response_time_ms) as avg_response_time,
    MAX(l.response_time_ms) as max_response_time
FROM api_logs l
LEFT JOIN wp_users u ON l.user_id = u.id
GROUP BY u.username, DATE(l.created_at)
ORDER BY date DESC;

-- View for user permissions summary
CREATE OR REPLACE VIEW user_permissions_summary AS
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    STRING_AGG(
        CASE WHEN p.permission_value THEN p.permission_name END, 
        ', ' ORDER BY p.permission_name
    ) as granted_permissions,
    COUNT(CASE WHEN p.permission_value THEN 1 END) as total_permissions
FROM wp_users u
LEFT JOIN user_permissions p ON u.id = p.user_id
GROUP BY u.id, u.username, u.email;
