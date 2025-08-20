-- Utility functions for WordPress Authentication Manager

-- Function to clean expired sessions
CREATE OR REPLACE FUNCTION clean_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM auth_sessions 
    WHERE expires_at < CURRENT_TIMESTAMP OR is_active = false;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to update user last activity
CREATE OR REPLACE FUNCTION update_user_activity(user_session_token VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE auth_sessions 
    SET last_used_at = CURRENT_TIMESTAMP 
    WHERE session_token = user_session_token AND is_active = true;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to get active subscriptions for a user
CREATE OR REPLACE FUNCTION get_active_subscriptions(user_id_param INTEGER)
RETURNS TABLE(
    subscription_id VARCHAR,
    product_name VARCHAR,
    status VARCHAR,
    end_date TIMESTAMP,
    amount DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.subscription_id,
        s.product_name,
        s.status,
        s.end_date,
        s.amount
    FROM wp_subscriptions s
    WHERE s.user_id = user_id_param 
    AND s.status = 'active'
    AND (s.end_date IS NULL OR s.end_date > CURRENT_TIMESTAMP)
    ORDER BY s.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to log API requests
CREATE OR REPLACE FUNCTION log_api_request(
    user_id_param INTEGER,
    endpoint_param VARCHAR,
    method_param VARCHAR,
    status_code_param INTEGER,
    response_time_param INTEGER DEFAULT NULL,
    error_message_param TEXT DEFAULT NULL,
    request_data_param JSONB DEFAULT NULL,
    response_data_param JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO api_logs (
        user_id, endpoint, method, status_code, 
        response_time_ms, error_message, request_data, response_data
    ) VALUES (
        user_id_param, endpoint_param, method_param, status_code_param,
        response_time_param, error_message_param, request_data_param, response_data_param
    );
END;
$$ LANGUAGE plpgsql;

-- Function to validate JWT token format
CREATE OR REPLACE FUNCTION is_valid_jwt_format(token TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- JWT should have exactly 3 parts separated by dots
    RETURN array_length(string_to_array(token, '.'), 1) = 3;
END;
$$ LANGUAGE plpgsql;
