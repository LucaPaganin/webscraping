import streamlit as st
import pandas as pd
import plotly.express as px
import re # Import regular expression library for price cleaning
import logging # Importa il modulo logging
from helpers import run_ebay_scraper



# --- Multi-page Setup with Streamlit Pages Dropdown ---
st.set_page_config(layout="wide")  # Use wider layout
st.sidebar.title("Navigazione")
page = st.sidebar.selectbox("Seleziona una pagina:", ["🔍 Scraping e Analisi", "📊 Analisi e Filtri", "🤖 Chatbot"])

def scraping_and_analysis_page():
    """Page logic for Scraping and Analysis."""
    st.header("🔍 Scraping e Analisi")
    st.title("📊 Web Scraper eBay & Analisi Prezzi")
    st.markdown("""
    Questa applicazione effettua lo scraping dei risultati di ricerca da **eBay.it** per una data query,
    salva i dati in un file CSV e visualizza un'analisi dei prezzi.
    """)

    # --- Input Section ---
    query = st.text_input("Inserisci la query di ricerca per eBay:", placeholder="Es: scheda video nvidia")
    max_pages_to_scrape = st.slider("Numero massimo di pagine da analizzare:", min_value=1, max_value=100, value=10, step=1,
                                    help="Imposta quante pagine di risultati vuoi analizzare. Più pagine richiedono più tempo.")
    start_button = st.button("Avvia Ricerca / Carica Dati")
    force_rerun = st.checkbox("Forza nuovo scraping anche se il file esiste", value=False, 
                              help="Seleziona per forzare un nuovo scraping anche se il file CSV esiste già.")
    if start_button and query:
        with st.spinner(f"Elaborazione per '{query}'... Attendere prego."):
            results_df = run_ebay_scraper(query, max_pages_to_scrape, force_rerun)

        if results_df is not None and not results_df.empty:
            st.subheader(f"📈 Analisi dei Prezzi per '{query}'")
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
                                    title=f"Distribuzione dei Prezzi per '{query}'",
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

            st.subheader(f"📄 Tabella dei Risultati per '{query}'")
            results_df_display = results_df.copy()
            if 'Prezzo' in results_df_display.columns:
                results_df_display['Prezzo'] = results_df_display['Prezzo'].apply(lambda x: f"€ {x:,.2f}" if pd.notna(x) else "N/D")
            st.dataframe(results_df_display, use_container_width=True, hide_index=True)
        elif start_button and query:
            st.error("Non è stato possibile ottenere o caricare dati validi per la query specificata.")
    elif start_button and not query:
        st.warning("Per favore, inserisci una query di ricerca.")

def analysis_and_filters_page():
    """Page logic for Analysis and Filters."""
    st.header("📂 Analisi e Filtri")
    uploaded_file = st.file_uploader("Carica un file CSV con i dati da analizzare:", type=["csv"])
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            if 'Prezzo' in df.columns:
                df['Prezzo'] = pd.to_numeric(df['Prezzo'], errors='coerce')
                df.dropna(subset=['Prezzo'], inplace=True)
            st.success("File caricato con successo!")
            
            # Extract the last part of the URL before the query string and create a new column 'id_inserzione'
            df['id_inserzione'] = df['Link'].apply(lambda x: x.split('?')[0].split('/')[-1] if isinstance(x, str) else None)

            # Drop duplicates based on the 'id_inserzione' column
            df.drop_duplicates(subset=['id_inserzione'], inplace=True)
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
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("Filtri per Parole Chiave nel **Titolo**:")
                keyword_filter = st.text_input(
                    "Filtra per Parole Chiave nel Titolo:", 
                    placeholder="Inserisci una o più parole chiave separate da spazi"
                )
                exclude_keyword_filter = st.text_input(
                    "Escludi Parole Chiave nel Titolo:", 
                    placeholder="Inserisci una o più parole chiave separate da spazi"
                )
            
            with col2:
                st.markdown("Filtri per Parole Chiave nel **Sottotitolo**:")
                subtitle_keyword_filter = st.text_input(
                    "Filtra per Parole Chiave nel Sottotitolo:", 
                    placeholder="Inserisci una o più parole chiave separate da spazi"
                )
                exclude_subtitle_keyword_filter = st.text_input(
                    "Escludi Parole Chiave nel Sottotitolo:", 
                    placeholder="Inserisci una o più parole chiave separate da spazi"
                )

            # Applica i filtri al dataframe
            filtered_df = df[(df['Prezzo'] >= min_price) & (df['Prezzo'] <= max_price)]

            def extract_keywords(input_string):
                """Extract keywords from a string, keeping quoted groups together."""
                matches = re.findall(r'"(.*?)"|(\S+)', input_string.lower())
                return [kw[0] or kw[1] for kw in matches]  # Flatten the tuple results

            if keyword_filter:
                keywords = extract_keywords(keyword_filter)
                filtered_df = filtered_df[
                    filtered_df['Titolo'].str.lower().apply(
                        lambda title: all(keyword in title for keyword in keywords)
                    )
                ]
            if exclude_keyword_filter:
                exclude_keywords = extract_keywords(exclude_keyword_filter)
                filtered_df = filtered_df[
                    filtered_df['Titolo'].str.lower().apply(
                        lambda title: not any(keyword in title for keyword in exclude_keywords)
                    )
                ]
            
            if subtitle_keyword_filter:
                subtitle_keywords = extract_keywords(subtitle_keyword_filter)
                filtered_df = filtered_df[
                    filtered_df['Sottotitolo'].str.lower().apply(
                        lambda subtitle: all(keyword in subtitle for keyword in subtitle_keywords)
                    )
                ]
            if exclude_subtitle_keyword_filter:
                exclude_subtitle_keywords = extract_keywords(exclude_subtitle_keyword_filter)
                filtered_df = filtered_df[
                    filtered_df['Sottotitolo'].str.lower().apply(
                        lambda subtitle: not any(keyword in subtitle for keyword in exclude_subtitle_keywords)
                    )
                ]

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

# --- Page Routing ---
if page == "Scraping e Analisi":
    scraping_and_analysis_page()
elif page == "Analisi e Filtri":
    analysis_and_filters_page()
elif page == "Chatbot":
    chatbot_page()
