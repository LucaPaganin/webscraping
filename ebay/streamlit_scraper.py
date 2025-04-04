import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import plotly.express as px
import re # Import regular expression library for price cleaning
import logging # Importa il modulo logging
from helpers import (
    run_ebay_scraper, 
    run_vinted_scraper,
    extract_keywords, 
    detect_language, 
    SAVE_DIR
)
from streamlit_chatbot import chatbot_page

def plot_subpage(df: pd.DataFrame, data_source: str):
    mean_price = df['Prezzo'].mean()
    max_price = df['Prezzo'].max()
    min_price = df['Prezzo'].min()
    median_price = df['Prezzo'].median()
    std_dev_price = df['Prezzo'].std()
    
    st.subheader(f"📈 Analisi dei Prezzi da {data_source}")

    metrics = {
        "Prezzo Medio": f"€ {mean_price:,.2f}",
        "Prezzo Mediano": f"€ {median_price:,.2f}",
        "Deviazione Standard Prezzi": f"€ {std_dev_price:,.2f}",
        "Prezzo Minimo": f"€ {min_price:,.2f}",
        "Prezzo Massimo": f"€ {max_price:,.2f}"
    }

    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        with col:
            st.metric(label, value)

    st.metric("Numero di Record", len(df))
    # Create the histogram
    fig = px.histogram(df, x='Prezzo', nbins=30,
                       title="Distribuzione dei Prezzi Filtrati",
                       labels={'Prezzo': 'Prezzo (€)'},
                       opacity=0.8,
                       color_discrete_sequence=px.colors.qualitative.Pastel)

    # Generate x values for the Gaussian curve
    x_values = np.linspace(df['Prezzo'].min(), df['Prezzo'].max(), 500)
    y_values = norm.pdf(x_values, mean_price, std_dev_price)

    # Normalize the Gaussian curve to match the histogram scale
    y_values *= len(df) * (df['Prezzo'].max() - df['Prezzo'].min()) / 30

    # Add the Gaussian curve to the figure
    fig.add_scatter(x=x_values, y=y_values, mode='lines', name='Curva Gaussiana', line=dict(color='blue'))
    
    if not df.empty:
        mean_price = df['Prezzo'].mean()
        median_price = df['Prezzo'].median()

        fig.add_vline(x=mean_price, line_dash="dash", line_color="red", annotation_text=f"Media: {mean_price:.2f}€")
        fig.add_vline(x=median_price, line_dash="dot", line_color="green", 
                    annotation_text=f"Mediana: {median_price:.2f}€", annotation_position="bottom")
        
        std_dev_price = df['Prezzo'].std()
        fig.add_vline(x=mean_price - 1 * std_dev_price, line_dash="dash", line_color="gold", 
                    annotation_text=f"Media - 1σ: {mean_price - 1 * std_dev_price:.2f}€", annotation_position="top")
        fig.add_vline(x=mean_price + 1 * std_dev_price, line_dash="dash", line_color="gold", 
                    annotation_text=f"Media + 1σ: {mean_price + 1 * std_dev_price:.2f}€", annotation_position="top")
        fig.add_vline(x=mean_price + 2 * std_dev_price, line_dash="dash", line_color="blue", 
                    annotation_text=f"Media + 2σ: {mean_price + 2 * std_dev_price:.2f}€", annotation_position="top")
        fig.add_vline(x=mean_price + 3 * std_dev_price, line_dash="dash", line_color="purple", 
                    annotation_text=f"Media + 3σ: {mean_price + 3 * std_dev_price:.2f}€", annotation_position="top")
            
            
    st.plotly_chart(fig, use_container_width=True)

def scraping_page():
    """Page logic for Scraping and Analysis."""
    st.header("🔍 Scraping e Analisi")
    st.title("📊 Web Scraper & Analisi Prezzi")
    st.markdown("""
    Questa applicazione effettua lo scraping dei risultati di ricerca da vari siti web,
    salva i dati in un file CSV e visualizza un'analisi dei prezzi.
    """)

    # --- Input Section ---
    website = st.selectbox("Seleziona il sito web da cui effettuare lo scraping:", ["eBay", "Vinted"])
    query = st.text_input("Inserisci la query di ricerca:", placeholder="Es: scheda video nvidia")
    max_pages_to_scrape = st.slider("Numero massimo di pagine da analizzare:", min_value=1, max_value=100, value=10, step=1,
                                    help="Imposta quante pagine di risultati vuoi analizzare. Più pagine richiedono più tempo.")
    start_button = st.button("Avvia Ricerca / Carica Dati")
    force_rerun = st.checkbox("Forza nuovo scraping anche se il file esiste", value=False, 
                              help="Seleziona per forzare un nuovo scraping anche se il file CSV esiste già.")
    start_search_url = st.text_input("URL di ricerca (opzionale):", placeholder="Es: https://www.ebay.it/sch/i.html?_nkw=scheda+video+nvidia")
    
    sanitized_query = "".join(c if c.isalnum() else "_" for c in query)
    filename = SAVE_DIR / f"{website}_{sanitized_query}.csv"

    if start_button and query:
        if not force_rerun and filename.exists():
            st.write(f"Il file '{filename}' esiste già. Seleziona 'Forza nuovo scraping' per sovrascrivere.")
            results_df = pd.read_csv(filename)
            st.write(f"**Dati caricati da '{filename}'!**")
        else:
            with st.spinner(f"Elaborazione per '{query}' su {website}... Attendere prego."):
                if website == "eBay":
                    results_df = run_ebay_scraper(query, max_pages_to_scrape, start_search_url=start_search_url)
                elif website == "Vinted":
                    results_df = run_vinted_scraper(query, max_pages_to_scrape, start_search_url=start_search_url)

        if results_df is not None and not results_df.empty:
            st.write(f"**Dati estratti con successo da {website}!**")
            st.write(f"Numero di record estratti: {len(results_df)}")
            st.write("Applico rilevamento lingua dei titoli...")
            results_df['Lingua'] = results_df['Titolo'].apply(detect_language)
            
            st.write("Salvo i dati in un file CSV...")
            try:
                results_df.to_csv(filename, index=False)
                st.success(f"Dati salvati con successo in '{filename}'")
            except Exception as e:
                st.error(f"Impossibile salvare il file CSV '{filename}': {e}")

            plot_subpage(results_df, website)

            st.subheader(f"📄 Tabella dei Risultati per '{query}' su {website}")

            st.dataframe(results_df, use_container_width=True, hide_index=True)

    elif start_button and not query:
        st.warning("Per favore, inserisci una query di ricerca.")

def filter_analysis_subpage(df: pd.DataFrame, data_source: str):
    """Subpage logic for eBay Analysis."""
    st.subheader(f"🔍 Analisi dati estratti da {data_source}")
    st.write(f"Questa sezione è dedicata all'analisi dei dati estratti da {data_source}.")
    st.write(f"Numero di record caricati: {len(df)}")
    if "Lingua" not in df.columns:
        st.write(f"Applico rilevamento lingua dei titoli...")
        df['Lingua'] = df['Titolo'].apply(detect_language)
    else:
        st.write(f"Colonna 'Lingua' già presente. Non applico rilevamento lingua.")
    
    if data_source == "eBay":    
        # Extract the last part of the URL before the query string and create a new column 'id_inserzione'
        df['id_inserzione'] = df['Link'].apply(lambda x: x.split('?')[0].split('/')[-1] if isinstance(x, str) else None)
        # Drop duplicates based on the 'id_inserzione' column
        df.drop_duplicates(subset=['id_inserzione'], inplace=True)
        filter_columns = ["Titolo", "Sottotitolo", "Lingua"]
    elif data_source == "Vinted":
        # Drop duplicates based on the 'id_inserzione' column
        df.drop_duplicates(subset=['Link'], inplace=True)
        filter_columns = ["Titolo", "Brand", "Condizione", "Lingua"]
    
    
    
    
    st.markdown(f"**Dati unici dopo rimozione duplicati:** {len(df)} record")
    st.subheader(f"📄 Tabella dei Dati Caricati: {len(df)} record")

    st.dataframe(df, use_container_width=True, hide_index=True)
    
    min_price = float(df['Prezzo'].min())
    max_price = float(df['Prezzo'].max())

    st.subheader("📊 Filtri e Grafici")
    st.write("Applica filtri per analizzare i dati in modo più dettagliato.")
    st.write("Puoi filtrare per prezzo, parole chiave nel titolo e altre caratteristiche.")
    
    col1, col2 = st.columns(2)
    with col1:
        min_price = st.number_input(
            "Prezzo Minimo (€):", 
            min_value=float(df['Prezzo'].min()), 
            max_value=float(df['Prezzo'].max()), 
            value=float(df['Prezzo'].min()), 
            step=1.0
        )
    with col2:
        max_price = st.number_input(
            "Prezzo Massimo (€):", 
            min_value=float(df['Prezzo'].min()), 
            max_value=float(df['Prezzo'].max()), 
            value=float(df['Prezzo'].max()), 
            step=1.0
        )
    
    df = df[(df['Prezzo'] >= min_price) & (df['Prezzo'] <= max_price)]
    
    return filter_dataframe_by_keywords(df, filter_columns)

def filter_dataframe_by_keywords(df: pd.DataFrame, filter_columns) -> pd.DataFrame:
    """Filter DataFrame by keywords in string columns."""

    st.subheader("🔍 Filtri per Parole Chiave")
    with st.expander("🔧 Mostra/Nascondi Filtri per Parole Chiave"):
        filter_inputs = {}
        for column in filter_columns:
            col1, col2 = st.columns(2)
            with col1:
                keyword_filter = st.text_input(
                    f"Filtra per Parole Chiave in **{column}**:", 
                    placeholder="Inserisci una o più parole chiave separate da spazi",
                    key=f"keyword_filter_{column}"
                )
                filt_type = st.radio(
                    f"Tipo di filtro per **{column}**:",
                    options=["And", "Or"],
                    key=f"include_filter_type_{column}",
                )
                filter_inputs[f"{column}_include"] = {
                    "keywords": keyword_filter,
                    "type": filt_type
                }
            
            with col2:
                exclude_keyword_filter = st.text_input(
                    f"Escludi Parole Chiave in **{column}**:", 
                    placeholder="Inserisci una o più parole chiave separate da spazi",
                    key=f"exclude_keyword_filter_{column}"
                )
                
                filt_type = st.radio(
                    f"Tipo di filtro per **{column}**:",
                    options=["And", "Or"],
                    key=f"exclude_filter_type_{column}",
                )
                filter_inputs[f"{column}_exclude"] = {
                    "keywords": exclude_keyword_filter,
                    "type": filt_type
                }

    # Applica i filtri al dataframe
    filtered_df = df.copy()
    for column in filter_columns:
        include_keywords = extract_keywords(filter_inputs[f"{column}_include"]["keywords"])
        exclude_keywords = extract_keywords(filter_inputs[f"{column}_exclude"]["keywords"])
        
        if include_keywords:
            if filter_inputs[f"{column}_include"]["type"] == "And":
                filtered_df = filtered_df[
                    filtered_df[column].str.lower().apply(
                        lambda value: all(keyword in value for keyword in include_keywords) if isinstance(value, str) else False
                    )
                ]
            else:
                filtered_df = filtered_df[
                    filtered_df[column].str.lower().apply(
                        lambda value: any(keyword in value for keyword in include_keywords) if isinstance(value, str) else False
                    )
                ]
        if exclude_keywords:
            if filter_inputs[f"{column}_exclude"]["type"] == "And":
                filtered_df = filtered_df[
                    filtered_df[column].str.lower().apply(
                        lambda value: not any(keyword in value for keyword in exclude_keywords) if isinstance(value, str) else True
                    )
                ]
            else:
                filtered_df = filtered_df[
                    filtered_df[column].str.lower().apply(
                        lambda value: not all(keyword in value for keyword in exclude_keywords) if isinstance(value, str) else True
                    )
                ]

    return filtered_df

def analysis_and_filters_page():
    """Page logic for Analysis and Filters."""
    st.header("📂 Analisi e Filtri")
    uploaded_file = st.file_uploader("Carica un file CSV con i dati da analizzare:", type=["csv"])
    data_source = st.selectbox("Seleziona l'origine dei dati:", ["eBay", "Vinted"], help="Scegli l'origine dei dati per l'analisi.")
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            if 'Prezzo' in df.columns:
                df['Prezzo'] = pd.to_numeric(df['Prezzo'], errors='coerce')
                df.dropna(subset=['Prezzo'], inplace=True)
            st.success("File caricato con successo!")
            
            filtered_df = filter_analysis_subpage(df, data_source)
            
            
            st.write(f"Risultati filtrati: {len(filtered_df)} su {len(df)} totali ({100*len(filtered_df)/len(df):.2f}%)")
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            plot_subpage(filtered_df, data_source)
            
        except Exception as e:
            st.error(f"Errore durante il caricamento o l'elaborazione del file: {e}")

PAGES = {
    "🔍 Scraping e Analisi": scraping_page,
    "📊 Analisi e Filtri": analysis_and_filters_page,
    "🤖 Chatbot": chatbot_page
}

# --- Multi-page Setup with Streamlit Pages Dropdown ---
st.set_page_config(layout="wide")  # Use wider layout
st.sidebar.title("Navigazione")
page = st.sidebar.selectbox("Seleziona una pagina:", PAGES.keys())
st.sidebar.markdown("---")

# --- Page Routing ---
selected_page = PAGES[page]
selected_page()

