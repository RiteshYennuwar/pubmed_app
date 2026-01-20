import streamlit as st
import pandas as pd

from pubmed_app.services import LLMService
from pubmed_app.config import settings


st.set_page_config(
    page_title="Q&A - PubMed Explorer",
    page_icon="💬",
    layout="wide",
)

st.title("💬 Ask Questions")
st.markdown("Ask questions about the PubMed database in natural language. AI will convert your question to SQL.")

llm_service = LLMService()


if not llm_service.is_available():
    st.error("⚠️ OpenAI API key not configured")
    st.markdown("""
    To use the Q&A feature, add your OpenAI API key to `.env`:
    
    ```
    OPENAI_API_KEY=sk-your-api-key-here
    ```
    
    Then restart the application.
    """)
    st.stop()

st.markdown("### Example Questions")

example_questions = [
    "How many articles are in the database?",
    "Which journals have the most articles?",
    "Show me articles about cancer from 2023",
    "Find articles by author Smith",
    "What are the most common MeSH terms?",
    "List articles from Nature Medicine",
    "How many articles per year?",
    "Find articles about machine learning",
]

cols = st.columns(4)
for i, question in enumerate(example_questions):
    with cols[i % 4]:
        if st.button(question, key=f"example_{i}", use_container_width=True):
            st.session_state["qa_question"] = question

st.markdown("---")
st.markdown("### Your Question")

default_question = st.session_state.get("qa_question", "")

question = st.text_area(
    "Ask a question",
    value=default_question,
    placeholder="e.g., How many articles about diabetes were published in 2023?",
    height=100,
    label_visibility="collapsed"
)

col1, col2 = st.columns([1, 4])
with col1:
    ask_clicked = st.button("Ask", type="primary", use_container_width=True)
with col2:
    if st.button("Clear", use_container_width=True):
        st.session_state["qa_question"] = ""
        st.rerun()

if ask_clicked and question:
    with st.spinner("Thinking..."):
        result = llm_service.ask(question)
    
    st.markdown("---")
    
    st.markdown("### Generated SQL")
    if result.get("sql_query"):
        st.code(result["sql_query"], language="sql")
    else:
        st.error("Failed to generate SQL query")
    
    if result.get("error"):
        st.error(f"Error: {result['error']}")
    
    if result.get("results") is not None:
        st.markdown("### Results")
        
        results = result["results"]
        
        if len(results) == 0:
            st.info("Query returned no results.")
        
        elif len(results) == 1 and len(results[0]) == 1:
            key = list(results[0].keys())[0]
            value = results[0][key]
            st.metric(key.replace("_", " ").title(), value)
        
        else:
            df = pd.DataFrame(results)
            
            st.caption(f"Showing {len(df)} rows")
            
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name="query_results.csv",
                mime="text/csv",
            )

st.markdown("---")

with st.expander("📚 Tips & Database Schema"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Tips for Better Questions
        
        **Be specific:**
        - ❌ "Show me articles"
        - ✅ "Show me 10 articles about cancer"
        
        **Mention fields:**
        - ❌ "Find recent papers"
        - ✅ "Find articles from 2023"
        
        **Use clear criteria:**
        - ❌ "Popular journals"
        - ✅ "Journals with most articles"
        """)
    
    with col2:
        st.markdown("""
        ### Database Schema
        
        **articles**: id, pmid, title, abstract, publication_year, journal_id
        
        **journals**: id, name, issn
        
        **authors**: id, last_name, first_name, affiliation
        
        **mesh_terms**: id, descriptor
        
        **article_authors**: article_id, author_id, author_position
        
        **article_mesh**: article_id, mesh_id
        """)

if "query_history" not in st.session_state:
    st.session_state["query_history"] = []

if ask_clicked and question and result.get("sql_query"):

    st.session_state["query_history"].append({
        "question": question,
        "sql": result["sql_query"],
        "success": result.get("error") is None
    })
    st.session_state["query_history"] = st.session_state["query_history"][-10:]

if st.session_state.get("query_history"):
    with st.expander("📜 Query History"):
        for i, item in enumerate(reversed(st.session_state["query_history"])):
            status = "✅" if item["success"] else "❌"
            st.markdown(f"{status} **{item['question']}**")
            st.code(item["sql"], language="sql")
            st.markdown("---")