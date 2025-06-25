import os
import ast
import json
import openai
import streamlit as st
import pandas as pd

from scripts.patcher import apply_docstring_patch

# ————————————— Globals ————————————— #
openai.api_key = os.getenv("OPENAI_APIKEY", "")

@st.cache_data
def load_items(json_path: str) -> pd.DataFrame:
    data = json.loads(open(json_path, "r").read())
    df = pd.DataFrame(data)
    df["has_doc"] = (
        df["docstring"].fillna("").str.strip().astype(bool)
        | df["description"].fillna("").str.strip().astype(bool)
    )
    return df

def extract_function_source(file_path: str, lineno: int) -> str:
    """
    Read `file_path`, locate the FunctionDef or AsyncFunctionDef
    whose .lineno == lineno, and return its full source.
    """
    src = open(file_path, "r").read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.lineno == lineno:
            seg = ast.get_source_segment(src, node)
            return seg or ""
    return ""

def generate_docstring(file_path: str, lineno: int) -> str:
    """
    Fetch the full function code at (file_path, lineno) and ask the LLM
    to return ONLY a PEP257 docstring. Do NOT rename arguments or alter code.
    """
    code = extract_function_source(file_path, lineno)
    prompt = f"""
        You are a Python expert. Below is the complete source of a function (including decorators).
        Write a PEP-257 compliant triple-quoted docstring for it.
        **Do NOT change the function name, its arguments, or any code.**
        **Return ONLY** the docstring (triple-quoted), no extra text.
        ```python
        {code}
        """
    resp = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt.strip()}],
    temperature=0.0,
    )
    return resp.choices[0].message.content.strip()

# ————————————— Main —————————————
def main():
    st.set_page_config(page_title="Doc Coverage + LLM Assist", layout="wide")
    st.title("📝 Documentation Coverage Dashboard")
    report_path = st.text_input("Report JSON path", "advanced_report.json")
    if not report_path:
        st.info("Enter a valid report JSON path above.")
        return
    if not os.path.exists(report_path):
        st.error(f"File not found: {report_path}")
        return

    df = load_items(report_path)

    # Sidebar filters
    st.sidebar.header("Filters")
    methods = sorted(df["method"].unique())
    selected = st.sidebar.multiselect("Select method(s)", methods, default=methods)
    df = df[df["method"].isin(selected)]
    if st.sidebar.checkbox("Show undocumented only", value=False):
        df = df[~df["has_doc"]]

    # Summary metrics
    total = len(df)
    covered = df["has_doc"].sum()
    pct = (covered / total * 100) if total else 0.0
    c1, c2, c3 = st.columns(3)
    c1.metric("Total items", total)
    c2.metric("Documented items", f"{covered} ({pct:.1f}%)")
    c3.metric("Coverage", f"{pct:.1f}%")

    # Data table
    st.dataframe(
        df[["module", "qualname", "method", "path", "has_doc"]],
        use_container_width=True
    )

    # Inspector & LLM Assist
    with st.expander("🔍 Inspect & Edit"):
        idx = st.selectbox(
            "Choose row",
            df.index,
            format_func=lambda i: f"{i}: {df.at[i,'qualname']} [{df.at[i,'method']}]"
        )
        item = df.loc[idx]

        st.markdown(f"**Module:** `{item.module}`")
        st.markdown(f"**Function/Class:** `{item.qualname}`")
        st.markdown(f"**Path:** `{item.path}`")
        st.markdown(f"**Method:** `{item.method}`")

        st.markdown("**Source snippet:**")
        st.code(item.first_lines or "*(none)*", language="python")

        original = item.docstring or ""
        new_doc = st.text_area("Docstring (edit below)", value=original, height=180)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✍️ Generate via LLM"):
                with st.spinner("Generating docstring…"):
                    generated = generate_docstring(item.path, item.lineno)
                new_doc = st.text_area("Docstring (edit below)", value=generated, key="generated")
        with col2:
            if st.button("💾 Save to code"):
                apply_docstring_patch(item.path, item.lineno, new_doc)
                st.success("✅ Docstring patched into source!")
                st.experimental_rerun()

if __name__ == "__main__":
    main()