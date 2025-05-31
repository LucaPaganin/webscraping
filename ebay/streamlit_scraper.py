import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import plotly.express as px
import re  # Import regular expression library for price cleaning
import logging  # Import logging module
from helpers import (
    run_ebay_scraper, 
    run_vinted_scraper,
    extract_keywords,
    store_data_in_session,
    get_data_from_session,
    clear_session_data,
    has_session_data
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
    fig.add_scatter(x=x_values, y=y_values, mode='lines', name='Gaussian Curve', line=dict(color='blue'))

    # Add vertical lines for mean, median, and standard deviation
    fig.add_vline(x=mean, line_dash="dash", line_color="red", 
                  annotation_text=f"Mean: {mean:.2f}")
    fig.add_vline(x=median, line_dash="dot", line_color="green", 
                  annotation_text=f"Median: {median:.2f}", annotation_position="bottom")
    
    fig.add_vline(x=mean - 1 * std_dev, line_dash="dash", line_color="gold", 
                  annotation_text=f"Mean - 1σ: {mean - 1 * std_dev:.2f}", annotation_position="top")
    fig.add_vline(x=mean + 1 * std_dev, line_dash="dash", line_color="gold", 
                  annotation_text=f"Mean + 1σ: {mean + 1 * std_dev:.2f}", annotation_position="top")
    fig.add_vline(x=mean + 3 * std_dev, line_dash="dash", line_color="purple", 
                  annotation_text=f"Mean + 3σ: {mean + 3 * std_dev:.2f}", annotation_position="top")
    
    # Add vertical lines for 25th and 75th percentiles
    percentile_25 = np.percentile(df[column], 25)
    percentile_75 = np.percentile(df[column], 75)
    fig.add_vline(x=percentile_25, line_dash="dot", line_color="orange", 
                  annotation_text=f"25th Percentile: {percentile_25:.2f}", annotation_position="bottom")
    fig.add_vline(x=percentile_75, line_dash="dot", line_color="orange", 
                  annotation_text=f"75th Percentile: {percentile_75:.2f}", annotation_position="bottom")

    return fig

def plot_subpage(df: pd.DataFrame, data_source: str):
    mean_price = df['Price'].mean()
    max_price = df['Price'].max()
    min_price = df['Price'].min()
    median_price = df['Price'].median()
    std_dev_price = df['Price'].std()
    
    st.subheader(f"📈 Price Analysis from {data_source}")

    metrics = {
        "Average Price": f"€ {mean_price:,.2f}",
        "Median Price": f"€ {median_price:,.2f}",
        "Price Standard Deviation": f"€ {std_dev_price:,.2f}",
        "Minimum Price": f"€ {min_price:,.2f}",
        "Maximum Price": f"€ {max_price:,.2f}"
    }

    st.subheader("📊 Price Statistics")
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        with col:
            st.metric(label, value)
    st.subheader("📊 Percentiles")
    percentiles = {
        "**25th** Percentile": f"€ {np.percentile(df['Price'], 25):,.2f}",
        "**50th** Percentile": f"€ {np.percentile(df['Price'], 50):,.2f}",
        "**75th** Percentile": f"€ {np.percentile(df['Price'], 75):,.2f}",
        "**90th** Percentile": f"€ {np.percentile(df['Price'], 90):,.2f}",
        "**95th** Percentile": f"€ {np.percentile(df['Price'], 95):,.2f}",
        "**99th** Percentile": f"€ {np.percentile(df['Price'], 99):,.2f}"
    }
    cols = st.columns(len(percentiles))
    for col, (label, value) in zip(cols, percentiles.items()):
        with col:
            st.metric(label, value)

    st.metric("Number of Records", len(df))
            
    st.subheader("📊 Price Distribution")
    fig = histogram_with_gaussian(df, 'Price', "Price Distribution")
    st.plotly_chart(fig, use_container_width=True)
    
    if data_source == "Vinted":
        cols = st.columns(2)
        
        with cols[0]:
            st.subheader("🔨 Condition Distribution")
            condition_counts = df['Condition'].value_counts()
            fig_condition_pie = px.pie(
                condition_counts,
                values=condition_counts.values,
                names=condition_counts.index,
                title="Condition Distribution in Data",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_condition_pie, use_container_width=True)

        with cols[1]:
            st.subheader("📈 Price vs Favorites Correlation")
            if 'Price' in df.columns and 'Favorites' in df.columns:
                fig_scatter = px.scatter(
                    df,
                    x='Price',
                    y='Favorites',
                    title="Correlation between Price and Favorites",
                    labels={'Price': 'Price (€)', 'Favorites': 'Number of Favorites'},
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.warning("The columns 'Price' and 'Favorites' are not present in the data.")
    
        if 'Favorites' in df.columns:
            st.subheader("📊 Favorites Distribution")
            fig_favorites_hist = histogram_with_gaussian(df, 'Favorites', "Favorites Distribution")
            st.plotly_chart(fig_favorites_hist, use_container_width=True)
        else:
            st.warning("The column 'Favorites' is not present in the data.")
    
    

def scraping_page():
    """Page logic for Scraping and Analysis."""
    st.header("🔍 Scraping and Analysis")
    st.title("📊 Web Scraper & Price Analysis")
    st.markdown("""
    This application performs scraping of search results from various websites,
    stores the data in session state, and displays a price analysis.
    """)

    # --- Input Section ---
    website = st.selectbox("Select the website to scrape from:", ["eBay", "Vinted"])
    query = st.text_input("Enter the search query:", placeholder="E.g.: NVIDIA graphics card")
    max_pages_to_scrape = st.number_input("Maximum number of pages to analyze:", min_value=1, max_value=100, value=10,
                                    help="Set how many pages of results you want to analyze. More pages take more time.")
    start_button = st.button("Start Search / Load Data")
    force_rerun = st.checkbox("Force new scraping", value=False, 
                              help="Select to force new scraping and override any existing session data.")
    start_search_url = st.text_input("Search URL (optional):", placeholder="E.g.: https://www.ebay.com/sch/i.html?_nkw=nvidia+graphics+card")
    
    # Display current session data info if available
    if has_session_data():
        session_df, metadata = get_data_from_session()
        st.info(f"📊 Session data available: {metadata.get('num_records', 0)} records from {metadata.get('website', 'Unknown')} "
               f"search for '{metadata.get('query', 'Unknown')}' (scraped at {metadata.get('timestamp', 'Unknown')})")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Session Data"):
                clear_session_data()
                st.rerun()
        with col2:
            if st.button("Use Session Data for Analysis"):
                st.session_state['use_session_data'] = True
                st.success("Session data will be used in Analysis page!")

    if start_button and query:
        # Check if we should use existing session data or scrape new data
        if not force_rerun and has_session_data():
            session_df, metadata = get_data_from_session()
            if metadata.get('query') == query and metadata.get('website') == website:
                st.write(f"Using existing session data for '{query}' on {website}.")
                results_df = session_df
                st.write(f"**Data loaded from session state!**")
            else:
                st.write("Query or website changed. Starting new scraping...")
                with st.spinner(f"Processing for '{query}' on {website}... Please wait."):
                    if website == "eBay":
                        results_df = run_ebay_scraper(query, max_pages_to_scrape, start_search_url=start_search_url)
                    elif website == "Vinted":
                        results_df = run_vinted_scraper(query, max_pages_to_scrape, start_search_url=start_search_url)
        else:
            with st.spinner(f"Processing for '{query}' on {website}... Please wait."):
                if website == "eBay":
                    results_df = run_ebay_scraper(query, max_pages_to_scrape, start_search_url=start_search_url)
                elif website == "Vinted":
                    results_df = run_vinted_scraper(query, max_pages_to_scrape, start_search_url=start_search_url)

        if results_df is not None and not results_df.empty:
            st.write(f"**Data successfully extracted from {website}!**")
            st.write(f"Number of records extracted: {len(results_df)}")

            # Rename columns to standardized format
            results_df.rename(columns={
                'Titolo': 'Title',
                'Sottotitolo': 'Subtitle',
                'Prezzo': 'Price',
                'Prezzo con spedizione': 'Price with Shipping',
                'Link': 'Link',
                'Brand': 'Brand',
                'Condizione': 'Condition',
                'Preferiti': 'Favorites',
                'Note': 'Notes'
            }, inplace=True)
            
            # Store data in session state instead of saving to CSV
            store_data_in_session(results_df, query, website, max_pages_to_scrape)

            plot_subpage(results_df, website)

            st.subheader(f"📄 Results Table for '{query}' on {website}")

            st.dataframe(results_df, use_container_width=True, hide_index=True, 
                         column_config={"Link": st.column_config.LinkColumn()})

    elif start_button and not query:
        st.warning("Please enter a search query.")

def filter_analysis_subpage(df: pd.DataFrame, data_source: str):
    """Subpage logic for Analysis."""
    st.subheader(f"🔍 Analysis of extracted data from {data_source}")
    st.write(f"This section is dedicated to analyzing the data extracted from {data_source}.")
    st.write(f"Number of records loaded: {len(df)}")
    
    if data_source == "eBay":    
        # Extract the last part of the URL before the query string and create a new column 'listing_id'
        df['listing_id'] = df['Link'].apply(lambda x: x.split('?')[0].split('/')[-1] if isinstance(x, str) else None)
        # Drop duplicates based on the 'listing_id' column
        df.drop_duplicates(subset=['listing_id'], inplace=True)
        filter_columns = ["Title", "Subtitle"]
    elif data_source == "Vinted":
        # Drop duplicates based on the 'Link' column
        df.drop_duplicates(subset=['Link'], inplace=True)
        filter_columns = ["Title", "Brand", "Condition"]

    st.markdown(f"**Unique data after removing duplicates:** {len(df)} records")
    st.subheader(f"📄 Loaded Data Table: {len(df)} records")

    st.dataframe(df, use_container_width=True, hide_index=True, 
                 column_config={"Link": st.column_config.LinkColumn()})
    
    min_price = float(df['Price'].min())
    max_price = float(df['Price'].max())

    st.subheader("📊 Filters and Charts")
    st.write("Apply filters to analyze the data in more detail.")
    st.write("You can filter by price, keywords in the title, and other characteristics.")
    
    col1, col2 = st.columns(2)
    with col1:
        min_price = st.number_input(
            "Minimum Price (€):", 
            min_value=float(df['Price'].min()), 
            max_value=float(df['Price'].max()), 
            value=float(df['Price'].min()), 
            step=1.0
        )
    with col2:
        max_price = st.number_input(
            "Maximum Price (€):", 
            min_value=float(df['Price'].min()), 
            max_value=float(df['Price'].max()), 
            value=float(df['Price'].max()), 
            step=1.0
        )
    
    df = df[(df['Price'] >= min_price) & (df['Price'] <= max_price)]
    
    if data_source == "Vinted":
        fav_cols = st.columns(2)
        with fav_cols[0]:
            min_favorites = st.number_input(
                "Minimum number of favorites:", 
                min_value=0, 
                max_value=int(df['Favorites'].max()), 
                value=0
            )
        with fav_cols[1]:
            max_favorites = st.number_input(
                "Maximum number of favorites:", 
                min_value=0, 
                max_value=int(df['Favorites'].max()), 
                value=int(df['Favorites'].max())
            )
        
        df = df[(df["Favorites"] >= min_favorites) & (df["Favorites"] <= max_favorites)]
    
    return filter_dataframe_by_keywords(df, filter_columns)

def filter_dataframe_by_keywords(df: pd.DataFrame, filter_columns) -> pd.DataFrame:
    """Filter DataFrame by keywords in string columns."""

    st.subheader("🔍 Keyword Filters")
    with st.expander("🔧 Show/Hide Keyword Filters"):
        filter_inputs = {}
        for column in filter_columns:
            col1, col2 = st.columns(2)
            with col1:
                keyword_filter = st.text_input(
                    f"Filter by Keywords in **{column}**:", 
                    placeholder="Enter one or more keywords separated by spaces",
                    key=f"keyword_filter_{column}"
                )
                filt_type = st.radio(
                    f"Filter type for **{column}**:",
                    options=["And", "Or"],
                    key=f"include_filter_type_{column}",
                )
                filter_inputs[f"{column}_include"] = {
                    "keywords": keyword_filter,
                    "type": filt_type
                }
            
            with col2:
                exclude_keyword_filter = st.text_input(
                    f"Exclude Keywords in **{column}**:", 
                    placeholder="Enter one or more keywords separated by spaces",
                    key=f"exclude_keyword_filter_{column}"
                )
                
                filt_type = st.radio(
                    f"Filter type for **{column}**:",
                    options=["And", "Or"],
                    key=f"exclude_filter_type_{column}",
                )
                filter_inputs[f"{column}_exclude"] = {
                    "keywords": exclude_keyword_filter,
                    "type": filt_type
                }

    # Apply filters to the dataframe
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
    st.header("📂 Analysis and Filters")
    
    # Check for session data first
    session_df, metadata = get_data_from_session()
    has_session = has_session_data()
    
    if has_session:
        st.success(f"📊 Session data available: {metadata.get('num_records', 0)} records from {metadata.get('website', 'Unknown')} "
                  f"search for '{metadata.get('query', 'Unknown')}'")
        
        # Option to use session data or upload CSV
        data_choice = st.radio(
            "Choose data source:",
            options=["Use Session Data", "Upload CSV File"],
            help="Session data comes from the scraping page, or you can upload your own CSV file."
        )
        
        if data_choice == "Use Session Data":
            df = session_df.copy()
            data_source = metadata.get('website', 'Unknown')
            
            if 'Price' in df.columns:
                df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
                df.dropna(subset=['Price'], inplace=True)
            
            st.write(f"**Using session data from {data_source}!**")
            st.write(f"Query: '{metadata.get('query', 'Unknown')}' | Records: {len(df)} | Scraped: {metadata.get('timestamp', 'Unknown')}")
            
            filtered_df = filter_analysis_subpage(df, data_source)
            
            st.write(f"Filtered results: {len(filtered_df)} out of {len(df)} total ({100*len(filtered_df)/len(df):.2f}%)")
            st.dataframe(filtered_df, 
                         use_container_width=True, 
                         hide_index=True, 
                         column_config={"Link": st.column_config.LinkColumn()})

            plot_subpage(filtered_df, data_source)
            return
      # CSV upload section (when no session data or user chooses to upload)
    if not has_session:
        st.info("No session data available. Please run a search on the scraping page first, or upload a CSV file below.")
        
    uploaded_file = st.file_uploader("Upload a CSV file with the data to analyze:", type=["csv"])
    data_source = st.selectbox("Select the data source:", ["eBay", "Vinted"], help="Choose the data source for analysis.")
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            if 'Price' in df.columns:
                df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
                df.dropna(subset=['Price'], inplace=True)
            st.success("File successfully uploaded! Using uploaded data.")
            
            filtered_df = filter_analysis_subpage(df, data_source)
            
            st.write(f"Filtered results: {len(filtered_df)} out of {len(df)} total ({100*len(filtered_df)/len(df):.2f}%)")
            st.dataframe(filtered_df, 
                         use_container_width=True, 
                         hide_index=True, 
                         column_config={"Link": st.column_config.LinkColumn()})

            plot_subpage(filtered_df, data_source)
            
        except Exception as e:
            st.error(f"Error during file upload or processing: {e}")
    elif not has_session:
        st.warning("Please upload a CSV file or run a search on the scraping page first.")

PAGES = {
    "🔍 Scraping and Analysis": scraping_page,
    "📊 Analysis and Filters": analysis_and_filters_page
}

# --- Multi-page Setup with Streamlit Pages Dropdown ---
st.set_page_config(layout="wide")  # Use wider layout
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select a page:", PAGES.keys())
st.sidebar.markdown("---")

# --- Page Routing ---
selected_page = PAGES[page]
selected_page()
