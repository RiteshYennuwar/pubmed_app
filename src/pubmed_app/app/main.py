import streamlit as st

from pubmed_app.services import SearchService

st.set_page_config(
    page_title="PubMed Article Search",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Main container */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Card style for articles */
    .article-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #4CAF50;
    }
    
    .article-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
    }
    
    .article-meta {
        font-size: 0.85rem;
        color: #666;
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1.5rem;
        color: white;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
    }
    
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    st.title("PubMed")
    
    # Database stats
    st.markdown("### Database Stats")
    try:
        search_service = SearchService()
        stats = search_service.get_stats()
        
        st.metric("Total Articles", stats["total_articles"])
        st.metric("Year Range", stats["year_range"])
        st.metric("Journals", stats["total_journals"])
    except Exception as e:
        st.error("Database not connected")
        st.caption(f"Run: `pubmed db init`")

st.title("🔬 PubMed Research Explorer")
st.markdown("Search, explore, and analyze biomedical research articles from PubMed.")

st.markdown("---")

# Quick stats row
col1, col2, col3, col4 = st.columns(4)

try:
    search_service = SearchService()
    stats = search_service.get_stats()
    filter_options = search_service.get_filter_options()
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['total_articles']:,}</div>
            <div class="stat-label">Total Articles</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['total_journals']}</div>
            <div class="stat-label">Journals</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(filter_options.get('years', []))}</div>
            <div class="stat-label">Years Covered</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(filter_options.get('mesh_terms', []))}</div>
            <div class="stat-label">MeSH Terms</div>
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error("Database connection failed. Please initialize the database.")
    st.code("pubmed db init", language="bash")
    st.stop()

st.markdown("---")

st.markdown("## Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Search")
    st.markdown("""
    Search articles by:
    - Keywords in title/abstract
    - Publication year
    - Journal name
    - Author name
    - MeSH terms
    """)
    if st.button("Go to Search", key="btn_search"):
        st.switch_page("pages/1_Search.py")

with col2:
    st.markdown("### Article Details")
    st.markdown("""
    View full article information:
    - Title and abstract
    - Authors with affiliations
    - Journal information
    - MeSH terms
    - Link to PubMed
    """)
    if st.button("Browse Articles", key="btn_details"):
        st.switch_page("pages/2_Details.py")

with col3:
    st.markdown("### Ask Questions")
    st.markdown("""
    Natural language queries:
    - "How many cancer articles?"
    - "Top journals by article count"
    - "Articles by author Smith"
    - AI converts to SQL
    """)
    if st.button("Ask a Question", key="btn_qa"):
        st.switch_page("pages/3_QA.py")

st.markdown("---")

st.markdown("## Recent Articles")

try:
    from pubmed_app.services import ArticleService
    article_service = ArticleService()
    recent = article_service.get_recent_articles(limit=5)
    
    if recent:
        for article in recent:
            with st.container():
                st.markdown(f"""
                <div class="article-card">
                    <div class="article-title">{article.title}</div>
                    <div class="article-meta">
                        📰 {article.journal_name or 'Unknown Journal'} | 
                        📅 {article.publication_year or 'N/A'} | 
                        🔗 PMID: {article.pmid}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No articles in database. Run ETL to fetch articles:")
        st.code('pubmed etl --topic "your research topic" --max-results 100', language="bash")

except Exception as e:
    st.error(f"Error loading articles: {e}")

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Built with ❤️ using Streamlit | Data from PubMed/NCBI"
    "</div>",
    unsafe_allow_html=True
)