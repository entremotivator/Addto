import os
import time
import streamlit as st
from supabase import create_client, Client
import psycopg2


# ----------------------------
# Supabase + Postgres Helpers
# ----------------------------

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
        if supabase_url.startswith('https://'):
            project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')

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

        cursor.execute(script_content)
        conn.commit()

        cursor.close()
        conn.close()
        return True, f"✅ {script_name} executed successfully"

    except psycopg2.Error as e:
        return False, f"❌ PostgreSQL Error in {script_name}: {str(e)}"
    except Exception as e:
        return False, f"❌ Error in {script_name}: {str(e)}"


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


# ----------------------------
# SQL Script Loader
# ----------------------------

def get_sql_scripts(folder="."):
    """
    Load SQL scripts from the SAME directory as App.py into a dict {filename: content}.
    Sorted by filename to ensure correct order.
    """
    scripts = {}
    folder_path = os.path.abspath(folder)

    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith(".sql"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                scripts[filename] = f.read()

    return scripts


# ----------------------------
# Streamlit UI
# ----------------------------

def main():
    st.set_page_config(
        page_title="Supabase Schema Setup",
        page_icon="🗄️",
        layout="wide"
    )

    st.title("🗄️ WordPress Auth Manager - Supabase Schema Setup")
    st.markdown("Automatically set up your Supabase database schema for the WordPress Authentication Manager")

    # Sidebar
    st.sidebar.header("🔗 Supabase Connection")

    supabase_url = st.sidebar.text_input(
        "Supabase Project URL:",
        placeholder="https://your-project.supabase.co"
    )

    anon_key = st.sidebar.text_input(
        "Supabase Anon Key:",
        placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        type="password"
    )

    db_password = st.sidebar.text_input(
        "Database Password:",
        placeholder="Your postgres user password",
        type="password"
    )

    st.sidebar.divider()
    consumer_secret = st.sidebar.text_input(
        "Consumer Secret:",
        placeholder="cs_your_consumer_secret_here",
        type="password"
    )

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
        if not scripts:
            st.warning("⚠️ No SQL scripts found in this folder")
        else:
            for script_name, script_content in scripts.items():
                with st.expander(f"📄 {script_name}", expanded=False):
                    st.code(
                        script_content[:500] + "..." if len(script_content) > 500 else script_content,
                        language="sql"
                    )

    with col2:
        st.header("🚀 Execute Setup")

        if postgres_params:
            if st.button("🔍 Test Connection", use_container_width=True):
                success, message = test_postgres_connection(postgres_params)
                if success:
                    st.success(message)
                else:
                    st.error(message)

            st.divider()

            if st.button("🚀 Setup Complete Schema", use_container_width=True, type="primary"):
                scripts = get_sql_scripts()
                if not scripts:
                    st.error("❌ No SQL scripts found to execute")
                else:
                    progress_bar = st.progress(0)
                    status_container = st.container()

                    with status_container:
                        st.write("**Execution Log:**")

                    for i, (script_name, script_content) in enumerate(scripts.items()):
                        progress = (i + 1) / len(scripts)
                        progress_bar.progress(progress)

                        success, message = execute_sql_script_direct(postgres_params, script_content, script_name)

                        with status_container:
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                                break  # stop on first error

                        time.sleep(0.5)

                    if success:
                        st.balloons()
                        st.success("🎉 Schema setup completed successfully!")

            st.divider()

            st.subheader("Run Individual Scripts")
            scripts = get_sql_scripts()
            for script_name, script_content in scripts.items():
                if st.button(f"Run {script_name}", use_container_width=True):
                    success, message = execute_sql_script_direct(postgres_params, script_content, script_name)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

        else:
            st.warning("⚠️ Please provide all connection details in the sidebar")

    st.divider()
    st.markdown("""
    ### 📚 Next Steps
    1. Put your `.sql` files in the **same folder** as `App.py`
    2. Add your **Supabase URL and Anon Key**
    3. Add your **Database Password** (postgres user password)
    4. Test the connection
    5. Run the schema setup
    6. Verify the tables in Supabase dashboard
    """)


if __name__ == "__main__":
    main()

