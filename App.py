import streamlit as st
from supabase import create_client, Client
import psycopg2
from urllib.parse import urlparse
import time

def create_supabase_client(url: str, anon_key: str) -> Client:
    """Create Supabase client with URL and anon key"""
    try:
        supabase: Client = create_client(url, anon_key)
        return supabase
    except Exception as e:
        st.error(f"Failed to create Supabase client: {str(e)}")
        return None

def get_postgres_connection_from_supabase_url(supabase_url: str, password: str):
    """Extract PostgreSQL connection details from Supabase URL"""
    try:
        # Convert Supabase URL to PostgreSQL connection URL
        if supabase_url.startswith('https://'):
            project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
            
            # Supabase PostgreSQL connection details
            conn_params = {
                'host': f'db.{project_ref}.supabase.co',
                'port': 5432,
                'database': 'postgres',
                'user': 'postgres',
                'password': password,
                'sslmode': 'require'
            }
            return conn_params
    except Exception as e:
        st.error(f"Failed to parse Supabase URL: {str(e)}")
        return None

def execute_sql_script_direct(conn_params: dict, script_content: str, script_name: str):
    """Execute SQL script using direct PostgreSQL connection"""
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Execute the script
        cursor.execute(script_content)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True, f"✅ {script_name} executed successfully"
        
    except psycopg2.Error as e:
        return False, f"❌ PostgreSQL Error in {script_name}: {str(e)}"
    except Exception as e:
        return False, f"❌ Error in {script_name}: {str(e)}"

def test_supabase_connection(supabase_client: Client):
    """Test Supabase connection with timeout"""
    try:
        with st.spinner("Testing connection..."):
            # Simple test - try to access auth schema
            result = supabase_client.table('auth.users').select('count').limit(0).execute()
            return True, "Connection successful"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def test_postgres_connection(conn_params: dict):
    """Test direct PostgreSQL connection"""
    try:
        with st.spinner("Testing PostgreSQL connection..."):
            conn = psycopg2.connect(**conn_params)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            cursor.close()
            conn.close()
            return True, f"PostgreSQL connection successful: {version[0][:50]}..."
    except Exception as e:
        return False, f"PostgreSQL connection failed: {str(e)}"


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
    
    db_password = st.sidebar.text_input(
        "Database Password:",
        placeholder="Your postgres user password",
        type="password",
        help="Your Supabase database password (postgres user)"
    )
    
    st.sidebar.divider()
    st.sidebar.subheader("🔑 API Configuration")
    consumer_secret = st.sidebar.text_input(
        "Consumer Secret:",
        placeholder="cs_your_consumer_secret_here",
        type="password",
        help="Consumer secret for subscription API access"
    )
    
    # Create connections
    supabase_client = None
    postgres_params = None
    
    if supabase_url and anon_key:
        supabase_client = create_supabase_client(supabase_url, anon_key)
        if supabase_client:
            st.sidebar.success("✅ Supabase client created")
        else:
            st.sidebar.error("❌ Failed to create Supabase client")
    
    if supabase_url and db_password:
        postgres_params = get_postgres_connection_from_supabase_url(supabase_url, db_password)
        if postgres_params:
            st.sidebar.success("✅ PostgreSQL params configured")
        else:
            st.sidebar.error("❌ Failed to configure PostgreSQL")
    
    if not (supabase_url and anon_key and db_password):
        st.sidebar.warning("⚠️ Please provide all connection details")
    
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
        
        if postgres_params:
            st.success("✅ Ready to execute")
            
            if st.button("🔍 Test Connection", use_container_width=True):
                success, message = test_postgres_connection(postgres_params)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
            
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
                        
                        success, message = execute_sql_script_direct(postgres_params, script_content, script_name)
                        
                        with status_container:
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                                break  # Stop on first error
                        
                        # Small delay to show progress
                        time.sleep(0.5)
                    
                    if success:  # Only show balloons if all scripts succeeded
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
                        success, message = execute_sql_script_direct(postgres_params, scripts[script_name], script_name)
                        
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"❌ Failed to execute {script_name}: {str(e)}")
        
        else:
            st.warning("⚠️ Please provide all connection details in the sidebar")
    
    st.divider()
    st.markdown("""
    ### 📚 Next Steps
    1. **Add your Supabase URL and Anon Key** in the sidebar
    2. **Add your Database Password** (postgres user password)
    3. **Add Consumer Secret** for subscription API access
    4. **Test the connection** using the Test Connection button
    5. **Run the schema setup** using the buttons above
    6. **Verify the tables** were created in your Supabase dashboard
    
    ### 🔧 Troubleshooting
    - Ensure your Supabase project is active and accessible
    - Verify the Project URL format: `https://your-project.supabase.co`
    - Check that the Anon Key is copied correctly from your project settings
    - Database password is your postgres user password from Supabase settings
    - Consumer Secret is required for subscription API endpoint access
    
    ### 🔑 API Endpoint Configuration
    - **Subscription API**: `https://aipropiq.com/wp-json/wsp-route/v1/wsp-view-subscription`
    - **Method**: GET
    - **Required Parameter**: `consumer_secret` (configured in sidebar)
    """)

if __name__ == "__main__":
    main()
