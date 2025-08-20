import os
import time
import streamlit as st
from supabase import create_client, Client

# ----------------------------
# Supabase Helpers
# ----------------------------

def create_supabase_client(url: str, anon_key: str) -> Client:
    try:
        return create_client(url, anon_key)
    except Exception as e:
        st.error(f"Failed to create Supabase client: {str(e)}")
        return None


def ensure_run_sql_function(supabase: Client):
    """Ensure the run_sql function exists in Supabase"""
    sql_function = """
    create or replace function public.run_sql(query text)
    returns void
    language plpgsql
    as $$
    begin
      execute query;
    end;
    $$;
    """
    try:
        supabase.rpc("run_sql", {"query": sql_function}).execute()
    except Exception:
        # If function doesn’t exist yet, try raw table creation call as fallback
        pass


def execute_sql_with_supabase(supabase: Client, script_content: str, script_name: str):
    """Execute SQL script line by line via Supabase run_sql"""
    try:
        # split on ; but ignore empty lines
        statements = [s.strip() for s in script_content.split(";") if s.strip()]
        for stmt in statements:
            supabase.rpc("run_sql", {"query": stmt}).execute()
        return True, f"✅ {script_name} executed successfully"
    except Exception as e:
        return False, f"❌ Error in {script_name}: {str(e)}"


def get_sql_scripts(folder="."):
    scripts = {}
    for filename in sorted(os.listdir(folder)):
        if filename.endswith(".sql"):
            with open(os.path.join(folder, filename), "r", encoding="utf-8") as f:
                scripts[filename] = f.read()
    return scripts


# ----------------------------
# Streamlit UI
# ----------------------------

def main():
    st.set_page_config(page_title="Supabase Schema Setup", page_icon="🗄️", layout="wide")
    st.title("🗄️ Supabase Schema Setup Tool")

    # Sidebar
    st.sidebar.header("🔗 Supabase Connection")
    supabase_url = st.sidebar.text_input("Supabase Project URL:", placeholder="https://your-project.supabase.co")
    anon_key = st.sidebar.text_input("Supabase Anon Key:", placeholder="eyJhbGciOiJI...", type="password")

    supabase_client = None
    if supabase_url and anon_key:
        supabase_client = create_supabase_client(supabase_url, anon_key)
        if supabase_client:
            st.sidebar.success("✅ Supabase client ready")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📋 Schema Setup Steps")
        scripts = get_sql_scripts()
        if not scripts:
            st.warning("⚠️ No SQL scripts found in this folder")
        else:
            for script_name, content in scripts.items():
                with st.expander(f"📄 {script_name}"):
                    st.code(content[:500] + "..." if len(content) > 500 else content, language="sql")

    with col2:
        st.header("🚀 Execute Setup")

        if supabase_client:
            if st.button("Run Full Setup", use_container_width=True, type="primary"):
                ensure_run_sql_function(supabase_client)

                scripts = get_sql_scripts()
                progress_bar = st.progress(0)
                status_container = st.container()

                for i, (script_name, script_content) in enumerate(scripts.items()):
                    progress = (i + 1) / len(scripts)
                    progress_bar.progress(progress)

                    success, message = execute_sql_with_supabase(supabase_client, script_content, script_name)

                    with status_container:
                        st.write(message)
                        if not success:
                            break
                    time.sleep(0.2)

                if success:
                    st.balloons()
                    st.success("🎉 Schema setup completed!")

        else:
            st.warning("⚠️ Please connect to Supabase first")


if __name__ == "__main__":
    main()
