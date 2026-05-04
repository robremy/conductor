#!/usr/bin/env python3
"""
Conductor Startup Test - Simulates the agent startup checks
without making actual API calls or requiring secrets.
"""

import os
from pathlib import Path

def log(msg): print(f"🎛️ {msg}")

def simulate_missing_groq_key():
    """Simulate missing GROQ_API_KEY check"""
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key or groq_key == "dummy":
        log("❌ Missing GROQ_API_KEY detected")
        print("\n📝 Would comment on issue:")
        print("❌ **Missing GROQ_API_KEY**")
        print("To use Conductor, you need a Groq API key:")
        print("1. Go to [console.groq.com](https://console.groq.com)")
        print("2. Create a new API key")
        print("3. Add it as `GROQ_API_KEY` in repository secrets")
        print("4. Re-trigger this issue")
        return False
    return True

def simulate_missing_agents_md():
    """Simulate missing AGENTS.md check"""
    if not Path("AGENTS.md").exists():
        log("❌ Missing AGENTS.md detected")
        print("\n📝 Would comment on issue:")
        print("❌ **Missing AGENTS.md**")
        print("Conductor requires an `AGENTS.md` file to understand your project.")
        print("Please create `AGENTS.md` in your repository root with project details, tech stack, and test commands.")
        print("\nExample:")
        print("```")
        print("## Project")
        print("My awesome project")
        print("")
        print("## Techstack")
        print("- Backend: Python")
        print("- Tests: pytest")
        print("")
        print("## Test Command")
        print("pytest")
        print("```")
        print("Once created, re-trigger this issue.")
        return False
    return True

def simulate_project_detection():
    """Simulate project type detection"""
    lines = []
    for path in Path(".").rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        lines.append(path.as_posix())

    conductor_files = {'.github/', 'AGENTS.md', 'README.md', '.gitignore', '.vscode/'}
    non_conductor = [line for line in lines if not any(cf in line for cf in conductor_files)]

    if len(non_conductor) == 0:
        log("🔍 Detected: NEW PROJECT")
        print("📝 Would comment: 🎛️ **New Project Detected**")
        print("This appears to be a new project. I will generate the complete initial structure based on AGENTS.md and your issue description.")
        return "new"
    else:
        log("🔍 Detected: EXISTING PROJECT")
        print("📝 Would proceed with incremental changes")
        return "existing"

def simulate_startup():
    """Simulate the full startup sequence"""
    log("Coding Agent startup test initiated")
    print("=" * 50)

    # Check for required secrets
    if not simulate_missing_groq_key():
        log("❌ Startup failed: Missing GROQ_API_KEY")
        return False

    # Check for required files
    if not simulate_missing_agents_md():
        log("❌ Startup failed: Missing AGENTS.md")
        return False

    # Detect project type
    project_type = simulate_project_detection()

    log("✅ All checks passed - would proceed with code generation")
    print(f"\n🚀 Would generate code for: {project_type.upper()} PROJECT")
    return True

# Configuration (same as real agent)
EXCLUDED_DIRS = {".git", "node_modules", ".next", "dist", "build", "__pycache__"}

if __name__ == "__main__":
    print("🎛️ Conductor Startup Test")
    print("This simulates what happens when the coding agent starts")
    print("Testing with current environment and files...\n")

    success = simulate_startup()

    print("\n" + "=" * 50)
    if success:
        print("✅ TEST PASSED: Agent would proceed with code generation")
    else:
        print("❌ TEST FAILED: Agent would exit with guidance comments")

    print("\n💡 To test with different scenarios:")
    print("   - Remove AGENTS.md temporarily")
    print("   - Set GROQ_API_KEY=dummy")
    print("   - Clear non-Conductor files for new project simulation")