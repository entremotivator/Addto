-- Sample data for WordPress Authentication Manager
-- Insert default WordPress site configuration

INSERT INTO wp_sites (site_url, site_name, api_base_url, consumer_key, consumer_secret, jwt_secret) 
VALUES (
    'https://aipropiq.com',
    'AI Propiq',
    'https://aipropiq.com/wp-json',
    'your_consumer_key_here',
    'your_consumer_secret_here',
    'your_jwt_secret_here'
) ON CONFLICT (site_url) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- Insert sample user (replace with actual data)
INSERT INTO wp_users (username, email, display_name, wp_user_id, consumer_key, consumer_secret)
VALUES (
    'admin',
    'admin@aipropiq.com',
    'Administrator',
    1,
    'your_consumer_key_here',
    'your_consumer_secret_here'
) ON CONFLICT (username) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- Insert default permissions
INSERT INTO user_permissions (user_id, permission_name, permission_value)
SELECT 
    u.id,
    perm.name,
    true
FROM wp_users u
CROSS JOIN (
    VALUES 
    ('view_subscriptions'),
    ('manage_users'),
    ('access_api_logs'),
    ('manage_sites')
) AS perm(name)
WHERE u.username = 'admin'
ON CONFLICT (user_id, permission_name) DO NOTHING;
