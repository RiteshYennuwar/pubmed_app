import streamlit as st

from pubmed_app.services import ArticleService, SearchService


st.set_page_config(
    page_title="Article Details - PubMed Explorer",
    page_icon="📄",
    layout="wide",
)

st.title("📄 Article Details")

article_service = ArticleService()
search_service = SearchService()


selected_pmid = st.session_state.get("selected_pmid", "")

col1, col2 = st.columns([3, 1])
with col1:
    pmid = st.text_input(
        "Enter PMID",
        value=selected_pmid,
        placeholder="e.g., 12345678",
        help="Enter a PubMed ID to view article details"
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    fetch_clicked = st.button("Fetch Article", type="primary")

with st.expander("Or select from recent articles"):
    recent_articles = article_service.get_recent_articles(limit=10)
    
    if recent_articles:
        for article in recent_articles:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{article.title[:70]}{'...' if len(article.title) > 70 else ''}**")
                st.caption(f"PMID: {article.pmid} | {article.publication_year or 'N/A'}")
            with col2:
                if st.button("Select", key=f"select_{article.pmid}"):
                    st.session_state["selected_pmid"] = article.pmid
                    st.rerun()
    else:
        st.info("No articles in database")

st.markdown("---")

if pmid:
    article = article_service.get_article_by_pmid(pmid.strip())
    
    if article:
        st.markdown(f"## {article.title}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Year", article.publication_year or "N/A")
        with col2:
            st.metric("Journal", article.journal_name or "Unknown")
        with col3:
            st.metric("PMID", article.pmid)
        
        st.markdown("---")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Abstract")
            if article.abstract:
                st.markdown(article.abstract)
            else:
                st.info("No abstract available for this article.")
            
            st.markdown("### Authors")
            if article.authors:
                for i, author in enumerate(article.authors, 1):
                    author_str = f"**{i}. {author.last_name}"
                    if author.first_name:
                        author_str += f", {author.first_name}"
                    author_str += "**"
                    
                    if author.affiliation:
                        author_str += f" — _{author.affiliation}_"
                    
                    st.markdown(author_str)
            else:
                st.info("No author information available.")
        
        with col2:
            st.markdown("### MeSH Terms")
            if article.mesh_terms:
                for term in article.mesh_terms:
                    st.markdown(f"• {term}")
            else:
                st.info("No MeSH terms available.")
            
            st.markdown("---")
            
            st.markdown("### External Links")
            
            pubmed_url = article_service.get_pubmed_url(article.pmid)
            st.link_button(
                "View on PubMed",
                pubmed_url,
                use_container_width=True
            )
        
        st.markdown("---")
        
        st.markdown("### Related Articles")
        
        tab1, tab2 = st.tabs(["Same Journal", "Similar Topics"])
        
        with tab1:
            if article.journal_name:
                related_journal = search_service.search_articles(
                    journal=article.journal_name,
                    limit=5
                )
                related_journal = [a for a in related_journal if a.pmid != article.pmid]
                
                if related_journal:
                    for rel in related_journal[:5]:
                        st.markdown(f"• **{rel.title[:80]}{'...' if len(rel.title) > 80 else ''}** ({rel.publication_year or 'N/A'})")
                else:
                    st.info("No other articles from this journal.")
            else:
                st.info("Journal information not available.")
        
        with tab2:
            if article.mesh_terms:
                related_mesh = search_service.search_articles(
                    mesh_term=article.mesh_terms[0],
                    limit=6
                )
                related_mesh = [a for a in related_mesh if a.pmid != article.pmid]
                
                if related_mesh:
                    for rel in related_mesh[:5]:
                        st.markdown(f"• **{rel.title[:80]}{'...' if len(rel.title) > 80 else ''}** ({rel.publication_year or 'N/A'})")
                else:
                    st.info("No related articles found.")
            else:
                st.info("No MeSH terms to find related articles.")
    
    else:
        st.error(f"Article with PMID '{pmid}' not found in database.")
        st.info("Make sure the PMID exists and has been loaded via ETL.")

else:
    st.info("Enter a PMID above to view article details, or select from recent articles.")

    st.markdown("### Database Overview")
    
    try:
        stats = search_service.get_stats()
        filter_options = search_service.get_filter_options()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Articles", stats["total_articles"])
        with col2:
            st.metric("Journals", stats["total_journals"])
        with col3:
            st.metric("Year Range", stats["year_range"])
        
        st.markdown("### Top MeSH Terms")
        mesh_terms = filter_options.get("mesh_terms", [])[:10]
        if mesh_terms:
            cols = st.columns(5)
            for i, term in enumerate(mesh_terms):
                with cols[i % 5]:
                    st.markdown(f"• {term}")
    except Exception as e:
        st.error(f"Error loading stats: {e}")