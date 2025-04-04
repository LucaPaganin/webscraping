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

def histogram_with_gaussian(df: pd.DataFrame, column: str, title: str):
    """Create a histogram with a Gaussian curve overlay."""
    mean = df[column].mean()
    std_dev = df[column].std()
    median = df[column].median()

    # Create the histogram
    fig = px.histogram(df, x=column, nbins=30, title=title,
                       labels={column: column},
                       opacity=0.8,
                       color_discrete_sequence=px.colors.qualitative.Pastel)

    # Generate x values for the Gaussian curve
    x_values = np.linspace(df[column].min(), df[column].max(), 500)
    y_values = norm.pdf(x_values, mean, std_dev)

    # Normalize the Gaussian curve to match the histogram scale
    y_values *= len(df) * (df[column].max() - df[column].min()) / 30

    # Add the Gaussian curve to the figure
    fig.add_scatter(x=x_values, y=y_values, mode='lines', name='Curva Gaussiana', line=dict(color='blue'))

    # Add vertical lines for mean, median, and standard deviation
    fig.add_vline(x=mean, line_dash="dash", line_color="red", 
                  annotation_text=f"Media: {mean:.2f}")
    fig.add_vline(x=median, line_dash="dot", line_color="green", 
                  annotation_text=f"Mediana: {median:.2f}", annotation_position="bottom")
    
    fig.add_vline(x=mean - 1 * std_dev, line_dash="dash", line_color="gold", 
                  annotation_text=f"Media - 1σ: {mean - 1 * std_dev:.2f}", annotation_position="top")
    fig.add_vline(x=mean + 1 * std_dev, line_dash="dash", line_color="gold", 
                  annotation_text=f"Media + 1σ: {mean + 1 * std_dev:.2f}", annotation_position="top")
    fig.add_vline(x=mean + 3 * std_dev, line_dash="dash", line_color="purple", 
                  annotation_text=f"Media + 3σ: {mean + 3 * std_dev:.2f}", annotation_position="top")
    
    # Add vertical lines for 25th and 75th percentiles
    percentile_25 = np.percentile(df[column], 25)
    percentile_75 = np.percentile(df[column], 75)
    fig.add_vline(x=percentile_25, line_dash="dot", line_color="orange", 
                  annotation_text=f"25° Percentile: {percentile_25:.2f}", annotation_position="bottom")
    fig.add_vline(x=percentile_75, line_dash="dot", line_color="orange", 
                  annotation_text=f"75° Percentile: {percentile_75:.2f}", annotation_position="bottom")

    return fig

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

    st.subheader("📊 Statistiche dei Prezzi")
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        with col:
            st.metric(label, value)
    st.subheader("📊 Percentili")
    percentiles = {
        "**25°** Percentile": f"€ {np.percentile(df['Prezzo'], 25):,.2f}",
        "**50°** Percentile": f"€ {np.percentile(df['Prezzo'], 50):,.2f}",
        "**75°** Percentile": f"€ {np.percentile(df['Prezzo'], 75):,.2f}",
        "**90°** Percentile": f"€ {np.percentile(df['Prezzo'], 90):,.2f}",
        "**95°** Percentile": f"€ {np.percentile(df['Prezzo'], 95):,.2f}",
        "**99°** Percentile": f"€ {np.percentile(df['Prezzo'], 99):,.2f}"
    }
    cols = st.columns(len(percentiles))
    for col, (label, value) in zip(cols, percentiles.items()):
        with col:
            st.metric(label, value)

    st.metric("Numero di Record", len(df))
            
    st.subheader("📊 Distribuzione dei Prezzi")
    fig = histogram_with_gaussian(df, 'Prezzo', "Distribuzione dei Prezzi")
    st.plotly_chart(fig, use_container_width=True)
    
    if data_source == "Vinted":
        cols = st.columns(3)
        
        with cols[0]:
            st.subheader("👅 Distribuzione delle Lingue")
            language_counts = df['Lingua'].value_counts()
            fig_pie = px.pie(
                language_counts,
                values=language_counts.values,
                names=language_counts.index,
                title="Distribuzione delle Lingue nei Dati",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with cols[1]:
            st.subheader("🔨 Distribuzione delle Condizioni")
            condition_counts = df['Condizione'].value_counts()
            fig_condition_pie = px.pie(
                condition_counts,
                values=condition_counts.values,
                names=condition_counts.index,
                title="Distribuzione delle Condizioni nei Dati",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_condition_pie, use_container_width=True)
        
        with cols[2]:
            st.subheader("📈 Correlazione Prezzo vs Preferiti")
            if 'Prezzo' in df.columns and 'Preferiti' in df.columns:
                fig_scatter = px.scatter(
                    df,
                    x='Prezzo',
                    y='Preferiti',
                    title="Correlazione tra Prezzo e Preferiti",
                    labels={'Prezzo': 'Prezzo (€)', 'Preferiti': 'Numero di Preferiti'},
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.warning("Le colonne 'Prezzo' e 'Preferiti' non sono presenti nei dati.")
    
        if 'Preferiti' in df.columns:
            st.subheader("📊 Distribuzione dei Preferiti")
            fig_favorites_hist = histogram_with_gaussian(df, 'Preferiti', "Distribuzione dei Preferiti")
            st.plotly_chart(fig_favorites_hist, use_container_width=True)
        else:
            st.warning("La colonna 'Preferiti' non è presente nei dati.")
    
    

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
    max_pages_to_scrape = st.number_input("Numero massimo di pagine da analizzare:", min_value=1, max_value=100, value=10,
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

            st.dataframe(results_df, use_container_width=True, hide_index=True, 
                         column_config={"Link": st.column_config.LinkColumn()})

    elif start_button and not query:
        st.warning("Per favore, inserisci una query di ricerca.")

def filter_analysis_subpage(df: pd.DataFrame, data_source: str):
    """Subpage logic for Analysis."""
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

    st.dataframe(df, use_container_width=True, hide_index=True, 
                 column_config={"Link": st.column_config.LinkColumn()})
    
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
    
    if data_source == "Vinted":
        fav_cols = st.columns(2)
        with fav_cols[0]:
            min_favorites = st.number_input(
                "Minimo numero di preferiti:", 
                min_value=0, 
                max_value=int(df['Preferiti'].max()), 
                value=0
            )
        with fav_cols[1]:
            max_favorites = st.number_input(
                "Massimo numero di preferiti:", 
                min_value=0, 
                max_value=int(df['Preferiti'].max()), 
                value=int(df['Preferiti'].max())
            )
        
        df = df[(df["Preferiti"] >= min_favorites) & (df["Preferiti"] <= max_favorites)]
    
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
            st.dataframe(filtered_df, 
                         use_container_width=True, 
                         hide_index=True, 
                         column_config={"Link": st.column_config.LinkColumn()})

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

