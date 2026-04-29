
import streamlit as st
import json
import time
import pandas as pd

from scrapers import scrape_cnn, scrape_detik, scrape_kompas, scrape_wikipedia, scrape_tribun
from semantic.converter import build_rdf_graph, to_jsonld, to_turtle, run_sparql, get_schema_type


# ─── Page Config ─────────────────────────────────────────────
st.set_page_config(
    page_title="Scraping Web Semantic",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
    }

    .hero-container {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        border-radius: 20px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .hero-container h1 {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .hero-container p {
        color: #a0aec0;
        font-size: 1.05rem;
        margin: 0;
    }

    .controls-container {
        background: rgba(30,30,60,0.5);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 2rem;
    }

    .source-card {
        background: linear-gradient(145deg, rgba(30,30,60,0.9), rgba(20,20,40,0.95));
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .source-card:hover {
        border-color: rgba(102, 126, 234, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.15);
    }
    .source-card h3 {
        font-size: 1.2rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 0.3rem;
    }
    .source-card .source-meta {
        color: #718096;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    .source-card .badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.4rem;
    }
    .badge-items {
        background: rgba(102, 126, 234, 0.2);
        color: #667eea;
    }
    .badge-type {
        background: rgba(236, 72, 153, 0.2);
        color: #ec4899;
    }

    .stat-box {
        background: linear-gradient(145deg, rgba(30,30,60,0.8), rgba(20,20,40,0.9));
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 1.2rem 1rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-box .stat-number {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-box .stat-label {
        color: #718096;
        font-size: 0.85rem;
        margin-top: 0.3rem;
    }

    /* Hide Sidebar completely */
    [data-testid="collapsedControl"] {
        display: none;
    }

    .footer {
        text-align: center;
        padding: 2rem 0 1rem 0;
        color: #4a5568;
        font-size: 0.85rem;
        border-top: 1px solid rgba(255,255,255,0.05);
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)


# ─── Source Definitions ──────────────────────────────────────
SOURCES = {
    "cnn": {
        "name": "CNN.com",
        "url": "https://edition.cnn.com",
        "description": "Berita internasional dari CNN (Cable News Network)",
        "scraper": scrape_cnn,
    },
    "detik": {
        "name": "Detik.com",
        "url": "https://www.detik.com",
        "description": "Portal berita terkini Indonesia — Detik.com",
        "scraper": scrape_detik,
    },
    "kompas": {
        "name": "Kompas.com",
        "url": "https://www.kompas.com",
        "description": "Berita terpercaya dari Kompas.com",
        "scraper": scrape_kompas,
    },
    "wikipedia": {
        "name": "Wikipedia.org",
        "url": "https://en.wikipedia.org",
        "description": "Artikel ensiklopedia dari Wikipedia",
        "scraper": scrape_wikipedia,
    },
    "tribun": {
        "name": "Tribunnews.com",
        "url": "https://www.tribunnews.com",
        "description": "Berita terkini dari jaringan Tribunnews",
        "scraper": scrape_tribun,
    },
}


# ─── Session State ───────────────────────────────────────────
if "scraped_data" not in st.session_state:
    st.session_state.scraped_data = {}
if "rdf_graphs" not in st.session_state:
    st.session_state.rdf_graphs = {}
if "scrape_times" not in st.session_state:
    st.session_state.scrape_times = {}


# ─── Helper Functions ────────────────────────────────────────
def do_scrape(source_key: str):
    """Execute scraping for a specific source."""
    source = SOURCES[source_key]
    start_time = time.time()
    data = source["scraper"]()
    elapsed = time.time() - start_time

    st.session_state.scraped_data[source_key] = data
    st.session_state.scrape_times[source_key] = elapsed

    if data:
        graph = build_rdf_graph(data, source_key)
        st.session_state.rdf_graphs[source_key] = graph

    return data


def do_scrape_all():
    """Execute scraping for all sources."""
    progress = st.progress(0, text="Memulai ekstraksi...")
    total = len(SOURCES)

    for i, (key, source) in enumerate(SOURCES.items()):
        progress.progress((i) / total, text=f"Mengekstraksi {source['name']}...")
        do_scrape(key)
        progress.progress((i + 1) / total, text=f"✅ {source['name']} selesai!")

    progress.progress(1.0, text="✅ Semua sumber berhasil diekstrak!")
    time.sleep(0.5)
    progress.empty()


# ─── Page: Dashboard ─────────────────────────────────────────

# Hero
st.markdown("""
<div class="hero-container">
    <h1>Scraping Web Semantic</h1>
    <p>Scraping Dalam 5 Website Yang Berbeda</p>
</div>
""", unsafe_allow_html=True)


# ─── Controls (Moved from Sidebar) ───────────────────────────
st.markdown("### Kontrol Scraping")
with st.container():
    st.markdown('<div class="controls-container">', unsafe_allow_html=True)
    
    col_main, col_indiv = st.columns([1, 2])
    
    with col_main:
        st.markdown("**Scraping Keseluruhan**")
        if st.button("Scraping Semua Sumber", use_container_width=True, type="primary"):
            do_scrape_all()
            st.rerun()
            
    with col_indiv:
        st.markdown("**Scraping Individual**")
        # Buat 5 kolom untuk tombol individual
        cols = st.columns(5)
        for i, (key, source) in enumerate(SOURCES.items()):
            with cols[i]:
                if st.button(source['name'], key=f"btn_{key}", use_container_width=True):
                    with st.spinner(f"Mengekstraksi {source['name']}..."):
                        do_scrape(key)
                    st.rerun()
                    
    st.markdown('</div>', unsafe_allow_html=True)


# ─── Stats Row (Removed Rata-rata Waktu) ───────────────────────
total_items = sum(len(d) for d in st.session_state.scraped_data.values())
total_sources = len(st.session_state.scraped_data)
total_triples = sum(len(g) for g in st.session_state.rdf_graphs.values())

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="stat-box"><div class="stat-number">{total_sources}</div><div class="stat-label">Sumber Scraping</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="stat-box"><div class="stat-number">{total_items}</div><div class="stat-label">Total Data</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="stat-box"><div class="stat-number">{total_triples}</div><div class="stat-label">Tripel RDF</div></div>', unsafe_allow_html=True)


# ─── Source Cards ────────────────────────────────────────────
if not st.session_state.scraped_data:
    st.info("Klik 'Scraping Semua Sumber' atau pilih salah satu sumber di atas untuk memulai scraping")

for key, source in SOURCES.items():
    data = st.session_state.scraped_data.get(key, [])
    schema_type = get_schema_type(key)
    items_count = len(data)

    card_html = f'<div class="source-card"><h3>{source["name"]}</h3><div class="source-meta">{source["description"]}</div><div><span class="badge badge-items">{items_count} data</span><span class="badge badge-type">skema:{schema_type}</span></div></div>'
    st.markdown(card_html, unsafe_allow_html=True)


# ─── Summary Table ───────────────────────────────────────────
if st.session_state.scraped_data:
    st.markdown("---")
    st.markdown("### Ringkasan Jumlah Data yang Diekstrak")
    summary_data = []
    for key, source in SOURCES.items():
        data = st.session_state.scraped_data.get(key, [])
        triples = len(st.session_state.rdf_graphs.get(key, []))
        summary_data.append({
            "Sumber": source["name"],
            "URL": source["url"],
            "Jumlah Data": len(data),
            "Tripel RDF": triples,
        })
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    # Grand total
    grand_total = sum(len(d) for d in st.session_state.scraped_data.values())
    st.success(f"**Total keseluruhan data yang berhasil diekstrak: {grand_total} data** dari {len(st.session_state.scraped_data)} website")

    st.markdown("---")
    st.markdown("### 📰 Daftar Berita Terbaru")
    
    from datetime import datetime, timedelta
    import re
    now = datetime.now()
    all_news = []
    
    for key, source in SOURCES.items():
        data_list = st.session_state.scraped_data.get(key, [])
        for i, item in enumerate(data_list):
            item_copy = item.copy()
            item_copy["_source_name"] = source["name"]
            item_copy["_source_color"] = source.get("color", "#667eea")
            
            # Extract or simulate timestamp
            date_str = str(item.get("date", "")).lower()
            timestamp = now - timedelta(minutes=i * 15 + (len(source["name"]) % 5)) # Fallback sequential time
            
            if "menit" in date_str and "lalu" in date_str:
                num = re.search(r'\d+', date_str)
                if num: timestamp = now - timedelta(minutes=int(num.group()))
            elif "jam" in date_str and "lalu" in date_str:
                num = re.search(r'\d+', date_str)
                if num: timestamp = now - timedelta(hours=int(num.group()))
                
            item_copy["_timestamp"] = timestamp
            item_copy["formatted_date"] = timestamp.strftime("%d %b %Y, %H:%M WIB")
            all_news.append(item_copy)
            
    # Urutkan dari yang terbaru (timestamp paling besar) ke yang terlama
    all_news.sort(key=lambda x: x["_timestamp"], reverse=True)
    
    for news in all_news:
        date_badge = f'<span style="color:#a0aec0; font-size:0.8rem; margin-right:10px;">📅 {news["formatted_date"]}</span>'
        cat_badge = f'<span style="background:rgba(255,255,255,0.1); padding:2px 8px; border-radius:10px; font-size:0.75rem; color:#e2e8f0;">{news.get("category", "Umum").title()}</span>'
        
        st.markdown(f"""
<div style="background:rgba(30,30,60,0.6); border-left:4px solid {news['_source_color']}; padding:15px; border-radius:8px; margin-bottom:12px; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.01)'" onmouseout="this.style.transform='scale(1)'">
    <div style="margin-bottom:8px;">
        <span style="color:{news['_source_color']}; font-weight:bold; font-size:0.85rem; margin-right:10px;">{news['_source_name']}</span>
        {date_badge}
        {cat_badge}
    </div>
    <a href="{news.get('url', '#')}" target="_blank" style="color:#e2e8f0; font-size:1.15rem; font-weight:600; text-decoration:none; display:block; margin-bottom:6px;">{news.get('title', 'Tanpa Judul')}</a>
    <p style="color:#a0aec0; font-size:0.9rem; margin-top:0; margin-bottom:0; line-height:1.5;">{news.get('summary', '')}</p>
</div>
""", unsafe_allow_html=True)


# ─── Footer ──────────────────────────────────────────────────
st.markdown('<div class="footer">Scraping Web Semantic <br> Muh.Albyansyah Qaishar Porosi <br> E1E124071 </div>', unsafe_allow_html=True)
