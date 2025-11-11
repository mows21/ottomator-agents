"""
Basic functionality test script (no dependencies required).
Run this to verify core components work before full setup.
"""

import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_templates_exist():
    """Test that all templates are present"""
    templates_dir = Path(__file__).parent / "templates"
    expected_templates = [
        "email_notification.json",
        "database_query.json",
        "api_call.json",
        "web_scraper.json",
        "file_processing.json",
        "slack_notification.json",
        "data_transformation.json",
        "scheduled_task.json",
        "webhook_receiver.json",
        "multi_step_pipeline.json"
    ]

    print("Testing template files...")
    for template_name in expected_templates:
        template_path = templates_dir / template_name
        assert template_path.exists(), f"Template {template_name} not found"

        # Test JSON is valid
        with open(template_path) as f:
            data = json.load(f)
            assert "nodes" in data, f"{template_name} missing 'nodes'"
            assert "connections" in data, f"{template_name} missing 'connections'"
            assert "metadata" in data, f"{template_name} missing 'metadata'"

        print(f"  ✓ {template_name}")

    print(f"✅ All {len(expected_templates)} templates validated")

def test_project_structure():
    """Test that project structure is complete"""
    print("\nTesting project structure...")

    required_files = [
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
        "Dockerfile",
        "docker-compose.yml",
        "IMPLEMENTATION_PLAN.md"
    ]

    for file_name in required_files:
        file_path = Path(__file__).parent / file_name
        assert file_path.exists(), f"Required file {file_name} not found"
        print(f"  ✓ {file_name}")

    required_dirs = [
        "templates",
        "generator",
        "api",
        "ui",
        "database",
        "tests",
        "docs",
        "examples"
    ]

    for dir_name in required_dirs:
        dir_path = Path(__file__).parent / dir_name
        assert dir_path.exists(), f"Required directory {dir_name} not found"
        print(f"  ✓ {dir_name}/")

    print("✅ Project structure complete")

def test_code_files():
    """Test that core code files exist"""
    print("\nTesting code files...")

    code_files = [
        "generator/template_matcher.py",
        "generator/workflow_agent.py",
        "api/n8n_client.py",
        "api/mcp_server.py",
        "ui/app.py",
        "database/schema.sql",
        "tests/test_generator.py"
    ]

    for file_path in code_files:
        full_path = Path(__file__).parent / file_path
        assert full_path.exists(), f"Code file {file_path} not found"
        print(f"  ✓ {file_path}")

    print("✅ All core code files present")

def main():
    """Run all basic tests"""
    print("=" * 60)
    print("AI Workflow Composer - Basic Functionality Test")
    print("=" * 60)

    try:
        test_templates_exist()
        test_project_structure()
        test_code_files()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Configure .env file with your API keys")
        print("3. Start n8n: docker run -p 5678:5678 n8nio/n8n")
        print("4. Run API server: uvicorn api.mcp_server:app --reload")
        print("5. Run UI: streamlit run ui/app.py")

        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
