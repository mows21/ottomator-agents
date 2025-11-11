"""
Streamlit UI for AI Workflow Composer.
User-friendly interface for testing workflow generation and execution.
"""

import streamlit as st
import asyncio
import json
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
API_TOKEN = os.getenv("API_BEARER_TOKEN", "your-secure-token-here")

# Initialize session state
if "generation_history" not in st.session_state:
    st.session_state.generation_history = []
if "current_workflow" not in st.session_state:
    st.session_state.current_workflow = None


class WorkflowComposerClient:
    """Client for AI Workflow Composer API"""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            return response.json()

    async def generate_workflow(self, task_description: str,
                              parameters: Dict = None,
                              force_ai: bool = False) -> Dict[str, Any]:
        """Generate workflow"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate-workflow",
                headers=self.headers,
                json={
                    "task_description": task_description,
                    "parameters": parameters or {},
                    "force_ai": force_ai,
                    "user_id": "streamlit_user",
                    "session_id": st.session_state.get("session_id", "default")
                }
            )
            response.raise_for_status()
            return response.json()

    async def create_workflow(self, task_description: str,
                            parameters: Dict = None) -> Dict[str, Any]:
        """Generate and create workflow in n8n"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/create-workflow",
                headers=self.headers,
                json={
                    "task_description": task_description,
                    "parameters": parameters or {},
                    "user_id": "streamlit_user",
                    "session_id": st.session_state.get("session_id", "default")
                }
            )
            response.raise_for_status()
            return response.json()

    async def execute_workflow(self, workflow_id: str,
                              input_data: Dict = None) -> Dict[str, Any]:
        """Execute workflow"""
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/api/execute-workflow",
                headers=self.headers,
                json={
                    "workflow_id": workflow_id,
                    "input_data": input_data,
                    "monitor": True
                }
            )
            response.raise_for_status()
            return response.json()

    async def list_templates(self) -> list:
        """List available templates"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/templates",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()


# Initialize client
client = WorkflowComposerClient(API_BASE_URL, API_TOKEN)


def run_async(coro):
    """Helper to run async functions in Streamlit"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# Page config
st.set_page_config(
    page_title="AI Workflow Composer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .workflow-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
    }
    .success-badge {
        background-color: #10b981;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
    }
    .warning-badge {
        background-color: #f59e0b;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🤖 AI Workflow Composer</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    # Health check
    with st.expander("🏥 System Health", expanded=True):
        if st.button("Check Health"):
            with st.spinner("Checking..."):
                try:
                    health = run_async(client.health_check())
                    if health["n8n_connected"]:
                        st.success("✅ All systems operational")
                    else:
                        st.warning("⚠️ n8n not connected")
                    st.json(health)
                except Exception as e:
                    st.error(f"❌ API not reachable: {e}")

    # Generation options
    st.header("🎯 Generation Options")
    force_ai = st.checkbox("Force AI Generation", value=False,
                          help="Use AI instead of templates")

    # Templates
    with st.expander("📚 Available Templates"):
        try:
            templates = run_async(client.list_templates())
            for template in templates:
                st.write(f"**{template['name']}**")
                st.caption(template['description'])
                st.caption(f"Tags: {', '.join(template['tags'])}")
                st.markdown("---")
        except Exception as e:
            st.error(f"Failed to load templates: {e}")

# Main content tabs
tab1, tab2, tab3 = st.tabs(["🚀 Generate", "📊 History", "📖 Documentation"])

with tab1:
    st.header("Generate Workflow")

    # Task description
    task_description = st.text_area(
        "Describe your workflow:",
        height=150,
        placeholder="Example: Send an email notification to team@company.com when a new user signs up...",
        help="Describe what you want your workflow to do in natural language"
    )

    # Parameters
    with st.expander("🔧 Optional Parameters"):
        st.markdown("Provide specific values for your workflow:")

        param_col1, param_col2 = st.columns(2)

        with param_col1:
            params = {}
            if st.checkbox("Add email parameters"):
                params["sender_email"] = st.text_input("Sender Email")
                params["recipient_email"] = st.text_input("Recipient Email")
                params["email_subject"] = st.text_input("Subject")
                params["email_body"] = st.text_area("Body", height=100)

        with param_col2:
            if st.checkbox("Add URL parameters"):
                params["api_url"] = st.text_input("API URL")
                params["http_method"] = st.selectbox("HTTP Method", ["GET", "POST", "PUT", "DELETE"])

            if st.checkbox("Add database parameters"):
                params["sql_query"] = st.text_area("SQL Query", height=100)

    # Generation buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔧 Generate Workflow", type="primary", use_container_width=True):
            if not task_description:
                st.error("Please provide a task description")
            else:
                with st.spinner("Generating workflow..."):
                    try:
                        result = run_async(client.generate_workflow(
                            task_description,
                            params if params else None,
                            force_ai=force_ai
                        ))

                        st.session_state.current_workflow = result
                        st.session_state.generation_history.append({
                            "timestamp": datetime.now(),
                            "task": task_description,
                            "result": result
                        })

                        st.success("✅ Workflow generated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Generation failed: {str(e)}")

    with col2:
        if st.button("🚀 Generate & Create in n8n", type="secondary", use_container_width=True):
            if not task_description:
                st.error("Please provide a task description")
            else:
                with st.spinner("Generating and creating workflow in n8n..."):
                    try:
                        result = run_async(client.create_workflow(
                            task_description,
                            params if params else None
                        ))

                        st.session_state.current_workflow = result
                        st.session_state.generation_history.append({
                            "timestamp": datetime.now(),
                            "task": task_description,
                            "result": result
                        })

                        st.success(f"✅ Workflow created in n8n! ID: {result['n8n_workflow_id']}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Creation failed: {str(e)}")

    # Display current workflow
    if st.session_state.current_workflow:
        st.markdown("---")
        st.subheader("Generated Workflow")

        workflow = st.session_state.current_workflow

        # Metadata
        meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)

        with meta_col1:
            method_badge = "🧠 AI" if workflow["generation_method"] == "ai_generation" else "📋 Template"
            st.metric("Method", method_badge)

        with meta_col2:
            confidence = workflow["confidence_score"]
            st.metric("Confidence", f"{confidence:.1%}")

        with meta_col3:
            status = workflow["status"]
            st.metric("Status", status.title())

        with meta_col4:
            if workflow.get("n8n_workflow_id"):
                st.metric("n8n ID", workflow["n8n_workflow_id"][:8] + "...")

        # Reasoning
        with st.expander("💭 Generation Reasoning", expanded=True):
            st.info(workflow["reasoning"])

        # Workflow JSON
        with st.expander("📄 Workflow JSON"):
            st.json(workflow["workflow_json"])

        # Actions
        action_col1, action_col2, action_col3 = st.columns(3)

        with action_col1:
            if st.button("📋 Copy JSON", use_container_width=True):
                st.code(json.dumps(workflow["workflow_json"], indent=2), language="json")

        with action_col2:
            if st.download_button(
                "💾 Download JSON",
                data=json.dumps(workflow["workflow_json"], indent=2),
                file_name=f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            ):
                st.success("Downloaded!")

        with action_col3:
            if workflow.get("n8n_workflow_id"):
                if st.button("▶️ Execute Workflow", use_container_width=True):
                    with st.spinner("Executing workflow..."):
                        try:
                            exec_result = run_async(client.execute_workflow(
                                workflow["workflow_id"]
                            ))

                            if exec_result["success"]:
                                st.success("✅ Execution successful!")
                                with st.expander("Execution Results"):
                                    st.json(exec_result)
                            else:
                                st.error(f"❌ Execution failed: {exec_result.get('error')}")
                        except Exception as e:
                            st.error(f"❌ Execution error: {str(e)}")
            else:
                st.button("▶️ Execute Workflow", disabled=True, use_container_width=True,
                         help="Create workflow in n8n first")

with tab2:
    st.header("Generation History")

    if not st.session_state.generation_history:
        st.info("No workflows generated yet. Go to the Generate tab to create one!")
    else:
        for i, entry in enumerate(reversed(st.session_state.generation_history)):
            with st.expander(
                f"#{len(st.session_state.generation_history) - i} - {entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
                expanded=(i == 0)
            ):
                st.write("**Task:**", entry["task"])

                result = entry["result"]
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Method:** {result['generation_method']}")
                    st.write(f"**Confidence:** {result['confidence_score']:.1%}")

                with col2:
                    st.write(f"**Status:** {result['status']}")
                    if result.get("n8n_workflow_id"):
                        st.write(f"**n8n ID:** {result['n8n_workflow_id']}")

                st.write("**Reasoning:**", result["reasoning"])

                if st.button(f"View JSON #{len(st.session_state.generation_history) - i}"):
                    st.json(result["workflow_json"])

with tab3:
    st.header("Documentation")

    st.markdown("""
    ### 🚀 Quick Start

    1. **Describe your workflow** in natural language in the Generate tab
    2. **Optional:** Add specific parameters like emails, URLs, or queries
    3. Click **Generate Workflow** to create the workflow JSON
    4. Click **Generate & Create in n8n** to also create it in n8n
    5. If created in n8n, click **Execute Workflow** to run it

    ### 📋 Templates

    The system includes 10 pre-built templates for common tasks:
    - Email notifications
    - Database queries
    - API calls
    - Web scraping
    - File processing
    - Slack notifications
    - Data transformation
    - Scheduled tasks
    - Webhook receivers
    - Multi-step pipelines

    ### 🧠 Generation Methods

    **Template Matching** (Fast, Reliable)
    - Uses keyword matching to find appropriate templates
    - Best for common, well-defined tasks
    - High confidence (>70%) = automatic selection

    **AI Generation** (Flexible, Intelligent)
    - Uses GPT-4 to generate custom workflows
    - Best for complex or unique requirements
    - Can combine multiple operations

    ### 💡 Tips

    - Be specific in your descriptions
    - Include actual values (emails, URLs) when possible
    - Use the parameters section for structured data
    - Check the confidence score - higher is better
    - Test workflows with sample data first

    ### 🔧 Troubleshooting

    **"API not reachable"**
    - Check that the FastAPI server is running on port 8001
    - Verify your API token in .env file

    **"n8n not connected"**
    - Ensure n8n is running (default: localhost:5678)
    - Check n8n credentials in .env file

    **"Execution failed"**
    - Verify workflow credentials are configured in n8n
    - Check that all required parameters are provided
    - Review the error message for specific issues
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "AI Workflow Composer | Part of ottomator-agents | "
    f"<a href='{API_BASE_URL}/docs' target='_blank'>API Docs</a>"
    "</div>",
    unsafe_allow_html=True
)
