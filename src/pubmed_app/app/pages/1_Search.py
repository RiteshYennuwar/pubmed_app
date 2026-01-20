import streamlit as st
import pandas as pd

from pubmed_app import services
from pubmed_app.services import SearchService, ExportService


st.set_page_config(
    page_title="Search - PubMed Explorer",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Search Articles")
st.markdown("Search the PubMed database using various filters.")

search_service = SearchService()
export_service = ExportService()

try:
    filter_options = search_service.get_filter_options()
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

with st.sidebar:
    st.header("Filters")
    
    keyword = st.text_input(
        "Keyword",
        placeholder="Search in title & abstract...",
        help="Full-text search in article titles and abstracts"
    )
    
    st.markdown("#### Publication Year")
    year_options = ["All"] + [str(y) for y in filter_options.get("years", [])]
    selected_year = st.selectbox("Year", year_options)
    
    use_year_range = st.checkbox("Use year range instead")
    year_from, year_to = None, None
    if use_year_range and filter_options.get("years"):
        min_year = min(filter_options["years"])
        max_year = max(filter_options["years"])
        year_from, year_to = st.slider(
            "Year range",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year)
        )
    
    st.markdown("#### Journal")
    journal_options = ["All"] + filter_options.get("journals", [])
    selected_journal = st.selectbox("Journal", journal_options)
    
    author = st.text_input(
        "Author (last name)",
        placeholder="e.g., Smith"
    )
    
    st.markdown("#### MeSH Term")
    mesh_options = ["All"] + filter_options.get("mesh_terms", [])
    selected_mesh = st.selectbox("MeSH Term", mesh_options)
    
    limit = st.slider("Max results", 10, 200, 50)
    
    search_clicked = st.button("Search", type="primary", use_container_width=True)    

    if st.button("Clear Filters", use_container_width=True):
        st.rerun()

search_params = {"limit": limit}

if keyword:
    search_params["keyword"] = keyword

if selected_year != "All" and not use_year_range:
    search_params["year"] = int(selected_year)

if use_year_range and year_from and year_to:
    search_params["year_from"] = year_from
    search_params["year_to"] = year_to

if selected_journal != "All":
    search_params["journal"] = selected_journal

if author:
    search_params["author_name"] = author

if selected_mesh != "All":
    search_params["mesh_term"] = selected_mesh

articles = search_service.search_articles(**search_params)

st.markdown("---")

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"### Results ({len(articles)} articles)")
with col2:
    if articles:
        export_format = st.selectbox("Export as", ["CSV", "JSON"], label_visibility="collapsed")

if articles:
    if export_format == "CSV":
        csv_data = export_service.to_csv(articles)
        st.download_button(
            label="Download",
            data=csv_data,
            file_name="pubmed_search_results.csv",
            mime="text/csv",
        )
    else:
        json_data = export_service.to_json(articles)
        st.download_button(
            label="Download",
            data=json_data,
            file_name="pubmed_search_results.json",
            mime="application/json",
        )

st.markdown("---")

if not articles:
    st.info("No articles found. Try adjusting your search filters.")
else:
    view_mode = st.radio(
        "View mode",
        ["Cards", "Table"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if view_mode == "Cards":
        for article in articles:
            with st.container():
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    st.markdown(f"**{article.title}**")
                    
                    meta_parts = []
                    if article.journal_name:
                        meta_parts.append(f"{article.journal_name}")
                    if article.publication_year:
                        meta_parts.append(f"{article.publication_year}")
                    meta_parts.append(f"PMID: {article.pmid}")
                    
                    st.caption(" | ".join(meta_parts))
                    
                    if article.abstract:
                        preview = article.abstract[:300] + "..." if len(article.abstract) > 300 else article.abstract
                        with st.expander("Show abstract"):
                            st.write(article.abstract)
                
                with col2:
                    if st.button("View Details", key=f"view_{article.pmid}"):
                        st.session_state["selected_pmid"] = article.pmid
                        st.switch_page("pages/2_Details.py")
                    
                    st.link_button(
                        "PubMed",
                        f"https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/",
                        use_container_width=True
                    )
                
                st.markdown("---")
    
    else:
        df = pd.DataFrame([
            {
                "PMID": a.pmid,
                "Title": a.title[:80] + "..." if len(a.title) > 80 else a.title,
                "Journal": a.journal_name or "N/A",
                "Year": a.publication_year or "N/A",
            }
            for a in articles
        ])
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "PMID": st.column_config.TextColumn("PMID", width="small"),
                "Title": st.column_config.TextColumn("Title", width="large"),
                "Journal": st.column_config.TextColumn("Journal", width="medium"),
                "Year": st.column_config.NumberColumn("Year", width="small", format="%d"),
            }
        )
        
        st.caption("💡 Enter a PMID below to view full details")
        pmid_input = st.text_input("Enter PMID", label_visibility="collapsed", placeholder="e.g., 12345678")
        if pmid_input:
            st.session_state["selected_pmid"] = pmid_input
            st.switch_page("pages/2_Details.py")