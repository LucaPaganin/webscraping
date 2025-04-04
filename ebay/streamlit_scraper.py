import streamlit as st
import pandas as pd
import plotly.express as px
import re # Import regular expression library for price cleaning
import logging # Importa il modulo logging
from helpers import (
    run_ebay_scraper, 
    run_vinted_scraper,
    extract_keywords
)
import os
import requests
from bs4 import BeautifulSoup


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

    if start_button and query:
        with st.spinner(f"Elaborazione per '{query}' su {website}... Attendere prego."):
            if website == "eBay":
                results_df = run_ebay_scraper(query, max_pages_to_scrape, force_rerun)
            elif website == "Vinted":
                results_df = run_vinted_scraper(query, max_pages_to_scrape, force_rerun)

        if results_df is not None and not results_df.empty:
            st.subheader(f"📈 Analisi dei Prezzi per '{query}' su {website}")
            if 'Prezzo' in results_df.columns and pd.api.types.is_numeric_dtype(results_df['Prezzo']) and results_df['Prezzo'].notna().sum() > 0:
                mean_price = results_df['Prezzo'].mean()
                max_price = results_df['Prezzo'].max()
                min_price = results_df['Prezzo'].min()
                median_price = results_df['Prezzo'].median()
                std_dev_price = results_df['Prezzo'].std()

                st.metric("Prezzo Medio", f"€ {mean_price:,.2f}")
                st.metric("Prezzo Mediano", f"€ {median_price:,.2f}")
                st.metric("Deviazione Standard Prezzi", f"€ {std_dev_price:,.2f}")
                st.metric("Prezzo Minimo", f"€ {min_price:,.2f}")
                st.metric("Prezzo Massimo", f"€ {max_price:,.2f}")

                fig = px.histogram(results_df, x='Prezzo', nbins=30,
                                    title=f"Distribuzione dei Prezzi per '{query}' su {website}",
                                    labels={'Prezzo': 'Prezzo (€)'},
                                    opacity=0.8,
                                    color_discrete_sequence=px.colors.qualitative.Pastel)

                fig.add_vline(x=mean_price, line_dash="dash", line_color="red", annotation_text=f"Media: {mean_price:.2f}€")
                fig.add_vline(x=median_price, line_dash="dot", line_color="green", annotation_text=f"Mediana: {median_price:.2f}€")

                fig.update_layout(
                    bargap=0.1,
                    xaxis_title="Prezzo (€)",
                    yaxis_title="Numero di Annunci",
                    title_x=0.5
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("La colonna 'Prezzo' non è presente, non è numerica o non contiene dati validi per generare il grafico.")

            st.subheader(f"📄 Tabella dei Risultati per '{query}' su {website}")
            results_df_display = results_df.copy()
            if 'Prezzo' in results_df_display.columns:
                results_df_display['Prezzo'] = results_df_display['Prezzo'].apply(lambda x: f"€ {x:,.2f}" if pd.notna(x) else "N/D")
            st.dataframe(results_df_display, use_container_width=True, hide_index=True)
        elif start_button and query:
            st.error("Non è stato possibile ottenere o caricare dati validi per la query specificata.")
    elif start_button and not query:
        st.warning("Per favore, inserisci una query di ricerca.")


def filter_analysis_subpage(df: pd.DataFrame, data_source: str):
    """Subpage logic for eBay Analysis."""
    st.subheader(f"🔍 Analisi dati estratti da {data_source}")
    st.write(f"Questa sezione è dedicata all'analisi dei dati estratti da {data_source}.")
    st.write(f"Numero di record caricati: {len(df)}")
    if data_source == "eBay":    
        # Extract the last part of the URL before the query string and create a new column 'id_inserzione'
        df['id_inserzione'] = df['Link'].apply(lambda x: x.split('?')[0].split('/')[-1] if isinstance(x, str) else None)
        # Drop duplicates based on the 'id_inserzione' column
        df.drop_duplicates(subset=['id_inserzione'], inplace=True)
        filter_columns = ["Titolo", "Sottotitolo"]
    elif data_source == "Vinted":
        # Drop duplicates based on the 'id_inserzione' column
        df.drop_duplicates(subset=['Link'], inplace=True)
        filter_columns = ["Titolo", "Brand", "Condizione"]
    
    st.markdown(f"**Dati unici dopo rimozione duplicati:** {len(df)} record")
    st.subheader(f"📄 Tabella dei Dati Caricati: {len(df)} record")

    st.dataframe(df, use_container_width=True, hide_index=True)
    
    min_price = float(df['Prezzo'].min())
    max_price = float(df['Prezzo'].max())

    st.subheader("📊 Filtri e Grafici")
    st.write("Applica filtri per analizzare i dati in modo più dettagliato.")
    st.write("Puoi filtrare per prezzo, parole chiave nel titolo e altre caratteristiche.")
    
    min_price, max_price = st.slider(
        "Filtra per Prezzo (€):", 
        min_value=min_price, 
        max_value=max_price, 
        value=(min_price, max_price),
        step=1.0
    )
    
    df = df[(df['Prezzo'] >= min_price) & (df['Prezzo'] <= max_price)]
    
    # Display minimum and maximum price metrics
    st.metric("Prezzo Minimo Filtrato", f"€ {min_price:,.2f}")
    st.metric("Prezzo Massimo Filtrato", f"€ {max_price:,.2f}")
    
    return filter_dataframe_by_keywords(df, filter_columns)

def filter_dataframe_by_keywords(df: pd.DataFrame, filter_columns) -> pd.DataFrame:
    """Filter DataFrame by keywords in string columns."""

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
            
            
            st.write(f"Risultati filtrati: {len(filtered_df)} su {len(df)} totali")
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            fig = px.histogram(filtered_df, x='Prezzo', nbins=30,
                                title="Distribuzione dei Prezzi Filtrati",
                                labels={'Prezzo': 'Prezzo (€)'},
                                opacity=0.8,
                                color_discrete_sequence=px.colors.qualitative.Pastel)
            if not filtered_df.empty:
                mean_price = filtered_df['Prezzo'].mean()
                median_price = filtered_df['Prezzo'].median()

                fig.add_vline(x=mean_price, line_dash="dash", line_color="red", annotation_text=f"Media: {mean_price:.2f}€")
                fig.add_vline(x=median_price, line_dash="dot", line_color="green", 
                              annotation_text=f"Mediana: {median_price:.2f}€", annotation_position="bottom")
                
                std_dev_price = filtered_df['Prezzo'].std()
                fig.add_vline(x=mean_price - 1 * std_dev_price, line_dash="dash", line_color="gold", 
                              annotation_text=f"Media - 1σ: {mean_price - 1 * std_dev_price:.2f}€", annotation_position="top")
                fig.add_vline(x=mean_price + 1 * std_dev_price, line_dash="dash", line_color="gold", 
                              annotation_text=f"Media + 1σ: {mean_price + 1 * std_dev_price:.2f}€", annotation_position="top")
                fig.add_vline(x=mean_price + 2 * std_dev_price, line_dash="dash", line_color="blue", 
                              annotation_text=f"Media + 2σ: {mean_price + 2 * std_dev_price:.2f}€", annotation_position="top")
                fig.add_vline(x=mean_price + 3 * std_dev_price, line_dash="dash", line_color="purple", 
                              annotation_text=f"Media + 3σ: {mean_price + 3 * std_dev_price:.2f}€", annotation_position="top")
            
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Errore durante il caricamento o l'elaborazione del file: {e}")

def chatbot_page():
    """Placeholder for Chatbot page."""
    st.header("🤖 Chatbot")
    st.write("Questa pagina è in fase di sviluppo. Prossimamente sarà disponibile un chatbot interattivo.")

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

