#!/usr/bin/env python3
"""
FastAPI Documentation Assistant - Complete Workflow
==================================================

This script demonstrates the complete workflow for analyzing and improving
FastAPI project documentation using the enhanced scanner and Streamlit dashboard.

Usage:
1. Run scanner to analyze your FastAPI project
2. Launch Streamlit dashboard to edit docstrings
3. Use AI assistance for generating professional docstrings
"""

import os
import subprocess
import sys

def run_scanner(project_path="project", output_file="comprehensive_report.json"):
    """Run the FastAPI scanner to analyze the project."""
    print("🔍 Scanning FastAPI project for documentation analysis...")
    
    try:
        from fastdoc.scanner import scan_file
        import json
        
        all_items = []
        for root, _, files in os.walk(project_path):
            for fn in files:
                if fn.endswith('.py'):
                    try:
                        file_path = os.path.join(root, fn)
                        items = scan_file(file_path)
                        all_items.extend(items)
                        print(f"  ✓ Scanned {len(items)} items from {file_path}")
                    except Exception as e:
                        print(f"  ❌ Error scanning {fn}: {e}")
        
        # Save comprehensive report
        with open(output_file, 'w') as f:
            json.dump([item.__dict__ for item in all_items], f, indent=2)
        
        print(f"\n✅ Generated report with {len(all_items)} items -> {output_file}")
        
        # Show summary
        from collections import Counter
        method_counts = Counter(item.method for item in all_items)
        documented_count = sum(1 for item in all_items if item.docstring)
        coverage_pct = (documented_count / len(all_items) * 100) if all_items else 0
        
        print(f"\n📊 Documentation Summary:")
        print(f"   Total items: {len(all_items)}")
        print(f"   Documented: {documented_count} ({coverage_pct:.1f}%)")
        print(f"   Missing docs: {len(all_items) - documented_count}")
        
        print(f"\n📋 Items by type:")
        for method, count in method_counts.most_common():
            print(f"   {method}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scanner failed: {e}")
        return False

def launch_dashboard():
    """Launch the Streamlit dashboard for interactive editing."""
    print("\n🚀 Launching FastAPI Documentation Assistant Dashboard...")
    print("   The dashboard will open in your browser automatically.")
    print("   Features available:")
    print("   • 📊 Documentation coverage analysis")
    print("   • ✏️ Interactive docstring editing")  
    print("   • 🤖 AI-powered docstring generation")
    print("   • 💾 Automatic backup and patching")
    print("   • 🔍 Source code preview")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "scripts/streamlit_app.py",
            "--theme.base", "light"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard closed by user")
    except Exception as e:
        print(f"❌ Failed to launch dashboard: {e}")

def setup_environment():
    """Check and setup the environment."""
    print("🔧 Checking environment setup...")
    
    # Check required packages
    required_packages = ["streamlit", "pandas"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package} (missing)")
    
    if missing_packages:
        print(f"\n⚠️  Install missing packages: pip install {' '.join(missing_packages)}")
        return False
    
    # Check OpenAI setup (optional)
    if os.getenv("OPENAI_API_KEY"):
        print("  ✓ OpenAI API key configured")
        try:
            from openai import OpenAI
            print("  ✓ OpenAI package available")
        except ImportError:
            print("  ⚠️  OpenAI package not installed (optional)")
            print("     Install with: pip install openai")
    else:
        print("  ⚠️  OPENAI_API_KEY not set (optional)")
        print("     Set environment variable to enable AI features")
    
    return True

def main():
    """Main workflow."""
    print("=" * 60)
    print("🚀 FastAPI Documentation Assistant")
    print("=" * 60)
    
    if not setup_environment():
        print("\n❌ Environment setup incomplete. Please install required packages.")
        return
    
    print("\n" + "=" * 60)
    print("STEP 1: Project Analysis")
    print("=" * 60)
    
    # Check if report already exists
    if os.path.exists("comprehensive_report.json"):
        choice = input("\n📄 Report file already exists. Regenerate? (y/N): ").lower()
        if choice not in ['y', 'yes']:
            print("   Using existing report file")
        else:
            if not run_scanner():
                return
    else:
        if not run_scanner():
            return
    
    print("\n" + "=" * 60)
    print("STEP 2: Interactive Documentation Editor")
    print("=" * 60)
    
    input("\n🎯 Press ENTER to launch the documentation dashboard...")
    launch_dashboard()

if __name__ == "__main__":
    main()