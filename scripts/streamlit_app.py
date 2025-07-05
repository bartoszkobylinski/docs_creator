import os
import ast
import json
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional

# Import our enhanced patcher
from scripts.patcher import (
    apply_docitem_patch, 
    validate_docstring_syntax,
    get_item_file_path
)

# OpenAI client setup (optional)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    st.warning("OpenAI package not installed. LLM features will be disabled.")

# ————————————— Configuration ————————————— #
st.set_page_config(
    page_title="FastAPI Documentation Assistant", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ————————————— Helper Functions ————————————— #

@st.cache_data
def load_items(json_path: str) -> pd.DataFrame:
    """Load DocItems from JSON report."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        
        # Add computed columns
        df["has_doc"] = (
            df["docstring"].fillna("").str.strip().astype(bool)
            | df["description"].fillna("").str.strip().astype(bool)
        )
        
        # Add file path column
        df["file_path"] = df.apply(lambda row: get_item_file_path(row.to_dict()), axis=1)
        
        return df
    except Exception as e:
        st.error(f"Error loading JSON: {str(e)}")
        return pd.DataFrame()

def extract_function_source(file_path: str, lineno: int) -> str:
    """Extract the full source code of a function/class at given line."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            src = f.read()
        
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.lineno == lineno:
                seg = ast.get_source_segment(src, node)
                return seg or ""
        return ""
    except Exception as e:
        return f"Error reading source: {str(e)}"

def generate_docstring_with_openai(file_path: str, lineno: int, item_data: Dict[str, Any]) -> Optional[str]:
    """Generate docstring using OpenAI API."""
    if not OPENAI_AVAILABLE:
        return None
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Get function source
        code = extract_function_source(file_path, lineno)
        if not code:
            return None
        
        # Build context-aware prompt
        method_type = item_data.get('method', 'FUNCTION')
        qualname = item_data.get('qualname', 'unknown')
        
        prompt = f"""
You are a Python documentation expert. Write a comprehensive PEP-257 compliant docstring for this {method_type.lower()}:

Function/Class: {qualname}
Type: {method_type}

Code:
```python
{code}
```

Requirements:
1. Write ONLY the docstring content (no triple quotes)
2. Follow PEP-257 conventions
3. Include a brief one-line summary
4. Add detailed description if complex
5. Document all parameters with types
6. Document return value and type
7. Document any exceptions raised
8. For FastAPI endpoints, include API-specific details

Return only the docstring text, no other content.
"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt.strip()}],
            temperature=0.2,
            max_tokens=1000
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        st.error(f"OpenAI API error: {str(e)}")
        return None

def create_docstring_preview(docstring: str, method_type: str) -> str:
    """Create a preview of how the docstring will look in code."""
    if not docstring.strip():
        return "# No docstring"
    
    if method_type == "MODULE":
        return f'"""\n{docstring}\n"""'
    else:
        # Add proper indentation for functions/classes
        lines = docstring.strip().split('\n')
        indented = '\n'.join(f'    {line}' if line.strip() else '' for line in lines)
        return f'    """\n    {indented}\n    """'

# ————————————— UI State Management ————————————— #

def init_session_state():
    """Initialize session state variables."""
    if 'selected_item_idx' not in st.session_state:
        st.session_state.selected_item_idx = 0
    if 'current_docstring' not in st.session_state:
        st.session_state.current_docstring = ""
    if 'llm_suggestion' not in st.session_state:
        st.session_state.llm_suggestion = ""
    if 'show_llm_suggestion' not in st.session_state:
        st.session_state.show_llm_suggestion = False

# ————————————— Main Application ————————————— #

def main():
    init_session_state()
    
    st.title("🚀 FastAPI Documentation Assistant")
    st.markdown("*Analyze, edit, and enhance your FastAPI project documentation with AI assistance*")
    
    # ————————————— Sidebar Configuration ————————————— #
    with st.sidebar:
        st.header("📂 Configuration")
        
        # Report file selection
        report_path = st.text_input(
            "Report JSON Path", 
            value="comprehensive_report.json",
            help="Path to the JSON report generated by the scanner"
        )
        
        # Base path for relative file paths
        base_path = st.text_input(
            "Project Base Path",
            value=".",
            help="Base directory for resolving relative file paths"
        )
        
        # OpenAI configuration
        st.header("🤖 AI Assistant")
        openai_enabled = st.checkbox(
            "Enable OpenAI Suggestions", 
            value=OPENAI_AVAILABLE,
            disabled=not OPENAI_AVAILABLE,
            help="Generate docstring suggestions using OpenAI GPT-4"
        )
        
        if openai_enabled and not os.getenv("OPENAI_API_KEY"):
            st.warning("⚠️ Set OPENAI_API_KEY environment variable to use AI features")
    
    # ————————————— Load and Validate Data ————————————— #
    if not report_path or not os.path.exists(report_path):
        st.warning(f"📄 Report file not found: {report_path}")
        st.info("1. Run the scanner to generate a report\n2. Specify the correct path above")
        return
    
    df = load_items(report_path)
    if df.empty:
        st.error("No data loaded from report file")
        return
    
    # ————————————— Filters and Summary ————————————— #
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📊 Documentation Overview")
        
        # Method type filter
        methods = ["All"] + sorted(df["method"].unique().tolist())
        selected_methods = st.multiselect(
            "Filter by Type",
            methods,
            default=["All"] if "All" in methods else methods[:5]
        )
        
        # Documentation status filter
        doc_filter = st.radio(
            "Documentation Status",
            ["All Items", "Missing Documentation", "Has Documentation"],
            horizontal=True
        )
    
    with col2:
        # Summary metrics
        total_items = len(df)
        documented_items = df["has_doc"].sum()
        coverage_pct = (documented_items / total_items * 100) if total_items > 0 else 0
        
        st.metric("Total Items", total_items)
        st.metric("Documented", f"{documented_items} ({coverage_pct:.1f}%)")
        st.metric("Missing Docs", total_items - documented_items)
    
    # Apply filters
    filtered_df = df.copy()
    
    if "All" not in selected_methods:
        filtered_df = filtered_df[filtered_df["method"].isin(selected_methods)]
    
    if doc_filter == "Missing Documentation":
        filtered_df = filtered_df[~filtered_df["has_doc"]]
    elif doc_filter == "Has Documentation":
        filtered_df = filtered_df[filtered_df["has_doc"]]
    
    # ————————————— Data Table ————————————— #
    st.header("📋 Documentation Items")
    
    if filtered_df.empty:
        st.info("No items match the current filters")
        return
    
    # Create display dataframe
    display_df = filtered_df[[
        "module", "qualname", "method", "has_doc", 
        "coverage_score", "quality_score"
    ]].copy()
    
    display_df["coverage_score"] = display_df["coverage_score"].round(1)
    display_df["quality_score"] = display_df["quality_score"].round(1)
    
    # Show the table
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "has_doc": st.column_config.CheckboxColumn("📝 Has Doc"),
            "coverage_score": st.column_config.ProgressColumn(
                "Coverage %", 
                min_value=0, 
                max_value=100
            ),
            "quality_score": st.column_config.ProgressColumn(
                "Quality %", 
                min_value=0, 
                max_value=100
            )
        }
    )
    
    # ————————————— Item Editor ————————————— #
    st.header("✏️ Documentation Editor")
    
    # Item selection
    if not filtered_df.empty:
        # Create selection options
        selection_options = [
            f"{idx}: {row['qualname']} [{row['method']}] - {row['module']}"
            for idx, row in filtered_df.iterrows()
        ]
        
        selected_idx = st.selectbox(
            "Select Item to Edit",
            range(len(selection_options)),
            format_func=lambda i: selection_options[i],
            key="item_selector"
        )
        
        # Get selected item data
        actual_idx = filtered_df.iloc[selected_idx].name
        item = filtered_df.loc[actual_idx]
        item_dict = item.to_dict()
        
        # ————————————— Item Details ————————————— #
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**📁 Item Information**")
            st.markdown(f"**Module:** `{item.module}`")
            st.markdown(f"**Name:** `{item.qualname}`")
            st.markdown(f"**Type:** `{item.method}`")
            st.markdown(f"**File:** `{item.file_path}`")
            st.markdown(f"**Line:** `{item.lineno}`")
            
            # Coverage information
            if pd.notna(item.coverage_score):
                st.markdown(f"**Coverage:** {item.coverage_score:.1f}%")
            if pd.notna(item.quality_score):
                st.markdown(f"**Quality:** {item.quality_score:.1f}%")
        
        with col2:
            st.markdown("**🔍 Source Preview**")
            source_preview = item.first_lines or "No source preview available"
            st.code(source_preview, language="python", line_numbers=True)
        
        # ————————————— Docstring Editor ————————————— #
        st.markdown("---")
        
        # Current docstring
        current_doc = item.docstring or ""
        
        # Editor tabs
        tab1, tab2, tab3 = st.tabs(["✍️ Manual Edit", "🤖 AI Assistant", "👀 Preview"])
        
        with tab1:
            st.markdown("**Edit Docstring Manually**")
            
            # Manual docstring editor
            new_docstring = st.text_area(
                "Docstring Content",
                value=current_doc,
                height=200,
                help="Enter the docstring content (without triple quotes)",
                key="manual_docstring"
            )
            
            # Validation
            if new_docstring.strip():
                validation = validate_docstring_syntax(new_docstring)
                if validation["valid"]:
                    st.success("✅ Docstring syntax is valid")
                else:
                    st.error(f"❌ {validation['message']}")
        
        with tab2:
            st.markdown("**AI-Powered Docstring Generation**")
            
            if not openai_enabled:
                st.info("Enable OpenAI in the sidebar to use this feature")
            else:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("🎯 Generate Suggestion", type="primary"):
                        with st.spinner("Generating docstring suggestion..."):
                            suggestion = generate_docstring_with_openai(
                                item.file_path, 
                                item.lineno, 
                                item_dict
                            )
                            if suggestion:
                                st.session_state.llm_suggestion = suggestion
                                st.session_state.show_llm_suggestion = True
                
                # Show suggestion if available
                if st.session_state.show_llm_suggestion and st.session_state.llm_suggestion:
                    st.markdown("**🤖 AI Suggestion:**")
                    
                    suggestion_text = st.text_area(
                        "Review and edit the AI suggestion",
                        value=st.session_state.llm_suggestion,
                        height=200,
                        key="ai_suggestion"
                    )
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("✅ Accept Suggestion"):
                            new_docstring = suggestion_text
                            st.success("AI suggestion accepted!")
                    
                    with col2:
                        if st.button("❌ Reject Suggestion"):
                            st.session_state.show_llm_suggestion = False
                            st.session_state.llm_suggestion = ""
                            st.info("Suggestion rejected")
        
        with tab3:
            st.markdown("**📖 Docstring Preview**")
            
            # Determine which docstring to preview
            preview_doc = ""
            if 'new_docstring' in locals():
                preview_doc = new_docstring
            elif st.session_state.show_llm_suggestion and 'suggestion_text' in locals():
                preview_doc = suggestion_text
            else:
                preview_doc = current_doc
            
            if preview_doc.strip():
                preview_code = create_docstring_preview(preview_doc, item.method)
                st.code(preview_code, language="python")
            else:
                st.info("No docstring to preview")
        
        # ————————————— Save Actions ————————————— #
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Determine final docstring to save
            final_docstring = ""
            if 'new_docstring' in locals():
                final_docstring = new_docstring
            elif st.session_state.show_llm_suggestion and 'suggestion_text' in locals():
                final_docstring = suggestion_text
            
            if st.button("💾 Save Docstring", type="primary"):
                if final_docstring.strip():
                    # Apply the patch
                    result = apply_docitem_patch(
                        item_dict, 
                        final_docstring,
                        create_backup_file=True,
                        base_path=base_path
                    )
                    
                    if result["success"]:
                        st.success(f"✅ {result['message']}")
                        if result["backup_path"]:
                            st.info(f"💾 Backup created: {result['backup_path']}")
                        
                        # Clear session state
                        st.session_state.show_llm_suggestion = False
                        st.session_state.llm_suggestion = ""
                        
                        # Suggest rerun to refresh data
                        st.info("🔄 Refresh the page to see updated coverage metrics")
                    else:
                        st.error(f"❌ {result['message']}")
                else:
                    st.warning("⚠️ Cannot save empty docstring")
        
        with col2:
            if st.button("🔄 Reset to Original"):
                st.session_state.show_llm_suggestion = False
                st.session_state.llm_suggestion = ""
                st.info("Reset to original docstring")
        
        with col3:
            if st.button("⏭️ Next Undocumented"):
                # Find next undocumented item
                undocumented = filtered_df[~filtered_df["has_doc"]]
                if not undocumented.empty:
                    next_idx = undocumented.index[0]
                    st.session_state.selected_item_idx = next_idx
                    st.experimental_rerun()
                else:
                    st.info("🎉 All items in current filter are documented!")

if __name__ == "__main__":
    main()