#!/usr/bin/env python3
"""
Data Visualization Components
===========================

Streamlit visualizations for real estate data analysis.

Author: Lucas P
Date: July 6, 2025
"""

import os
import json
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Union, Optional, Any, Tuple
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import folium_static
import joblib
from pathlib import Path

# Set theme for seaborn plots
sns.set_theme(style="whitegrid")


class RealEstateDataVisualizer:
    """
    Visualization components for real estate data using Streamlit.
    
    This class provides interactive visualizations for real estate data
    analysis, including price distributions, location maps, and property
    feature comparisons.
    """
    
    def __init__(self, data: Optional[pd.DataFrame] = None):
        """
        Initialize the visualizer with optional data.
        
        Args:
            data: DataFrame containing real estate data (optional)
        """
        self.data = data
    
    def load_data(self, file_path: Union[str, Path]) -> None:
        """
        Load data from a CSV or pickle file.
        
        Args:
            file_path: Path to the data file
        """
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.csv':
            self.data = pd.read_csv(file_path)
        elif file_path.suffix.lower() in ['.pkl', '.pickle']:
            self.data = pd.read_pickle(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        st.success(f"Loaded {len(self.data)} records from {file_path}")
    
    def show_data_overview(self) -> None:
        """
        Display an overview of the data.
        """
        if self.data is None:
            st.error("No data loaded. Please load data first.")
            return
        
        st.header("Data Overview")
        
        # Display data info
        st.subheader("Dataset Information")
        data_info = {
            "Number of properties": len(self.data),
            "Number of columns": len(self.data.columns),
        }
        
        # Add some statistics if price column exists
        if 'price' in self.data.columns:
            data_info.update({
                "Average price": f"{self.data['price'].mean():,.2f}",
                "Median price": f"{self.data['price'].median():,.2f}",
                "Price range": f"{self.data['price'].min():,.2f} - {self.data['price'].max():,.2f}"
            })
        
        # Display as a dataframe for better formatting
        st.dataframe(pd.DataFrame(list(data_info.items()), columns=["Metric", "Value"]))
        
        # Display sample data
        st.subheader("Sample Data")
        st.dataframe(self.data.head(10))
        
        # Display column info
        st.subheader("Column Information")
        col_info = pd.DataFrame({
            "Column": self.data.columns,
            "Type": self.data.dtypes.values,
            "Missing Values": self.data.isna().sum().values,
            "Missing (%)": (self.data.isna().sum().values / len(self.data) * 100).round(2)
        })
        st.dataframe(col_info)
    
    def show_price_analysis(self, price_col: str = 'price') -> None:
        """
        Display price analysis visualizations.
        
        Args:
            price_col: Name of the price column
        """
        if self.data is None:
            st.error("No data loaded. Please load data first.")
            return
            
        if price_col not in self.data.columns:
            st.error(f"Price column '{price_col}' not found in data.")
            return
        
        st.header("Price Analysis")
        
        # Create tabs for different visualizations
        tab1, tab2, tab3, tab4 = st.tabs(["Distribution", "By Location", "By Features", "Price Trends"])
        
        with tab1:
            st.subheader("Price Distribution")
            
            # Price histogram
            fig = px.histogram(
                self.data,
                x=price_col,
                nbins=50,
                title="Distribution of Property Prices",
                labels={price_col: "Price"},
                opacity=0.7
            )
            fig.update_layout(bargap=0.2)
            st.plotly_chart(fig, use_container_width=True)
            
            # Price statistics
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Mean", f"{self.data[price_col].mean():,.2f}")
            col2.metric("Median", f"{self.data[price_col].median():,.2f}")
            col3.metric("Std Dev", f"{self.data[price_col].std():,.2f}")
            col4.metric("Min", f"{self.data[price_col].min():,.2f}")
            col5.metric("Max", f"{self.data[price_col].max():,.2f}")
            
            # Box plot
            fig = px.box(
                self.data,
                y=price_col,
                title="Price Box Plot",
                labels={price_col: "Price"}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.subheader("Price by Location")
            
            # Check if location columns exist
            location_cols = [col for col in ['city', 'district', 'neighborhood', 'zone'] if col in self.data.columns]
            
            if not location_cols:
                st.warning("No location columns found in data.")
            else:
                # Select location column for analysis
                location_col = st.selectbox("Select location field", location_cols)
                
                # Group by location and calculate statistics
                location_stats = self.data.groupby(location_col)[price_col].agg(['mean', 'median', 'count']).reset_index()
                location_stats = location_stats.sort_values('count', ascending=False).head(20)
                
                # Create bar chart
                fig = px.bar(
                    location_stats,
                    x=location_col,
                    y='mean',
                    title=f"Average Price by {location_col.title()}",
                    labels={location_col: location_col.title(), 'mean': 'Average Price'},
                    text='count',
                    color='median',
                    color_continuous_scale="Viridis"
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
                
                # Display data table
                st.dataframe(location_stats)
        
        with tab3:
            st.subheader("Price by Property Features")
            
            # Find numeric and categorical columns
            numeric_cols = [col for col in self.data.columns if pd.api.types.is_numeric_dtype(self.data[col]) and col != price_col]
            cat_cols = [col for col in self.data.columns if pd.api.types.is_categorical_dtype(self.data[col]) or 
                         pd.api.types.is_object_dtype(self.data[col])]
            
            if numeric_cols:
                st.subheader("Price vs. Numeric Features")
                # Select feature for scatter plot
                num_feature = st.selectbox("Select feature for correlation", numeric_cols)
                
                # Create scatter plot
                fig = px.scatter(
                    self.data,
                    x=num_feature,
                    y=price_col,
                    title=f"Price vs. {num_feature}",
                    opacity=0.5,
                    trendline="ols"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Display correlation
                corr = self.data[[price_col, num_feature]].corr().iloc[0, 1]
                st.info(f"Correlation between {price_col} and {num_feature}: {corr:.4f}")
            
            if cat_cols:
                st.subheader("Price by Categories")
                # Select categorical feature
                cat_feature = st.selectbox("Select categorical feature", cat_cols)
                
                # Check if the feature has too many categories
                value_counts = self.data[cat_feature].value_counts()
                if len(value_counts) > 15:
                    # Take top N categories
                    top_categories = value_counts.head(15).index.tolist()
                    filtered_data = self.data[self.data[cat_feature].isin(top_categories)]
                    st.info(f"Showing only top 15 categories out of {len(value_counts)}")
                else:
                    filtered_data = self.data
                
                # Create box plot
                fig = px.box(
                    filtered_data,
                    x=cat_feature,
                    y=price_col,
                    title=f"Price Distribution by {cat_feature}",
                    labels={cat_feature: cat_feature.title(), price_col: "Price"}
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            st.subheader("Price Trends")
            
            # Check if date column exists
            date_cols = [col for col in self.data.columns if 'date' in col.lower() or 'time' in col.lower()]
            
            if not date_cols:
                st.warning("No date/time columns found in data.")
            else:
                # Select date column
                date_col = st.selectbox("Select date column", date_cols)
                
                # Convert to datetime if needed
                if not pd.api.types.is_datetime64_dtype(self.data[date_col]):
                    try:
                        self.data[date_col] = pd.to_datetime(self.data[date_col])
                    except:
                        st.error(f"Could not convert {date_col} to datetime format.")
                        return
                
                # Group by date period
                period = st.selectbox("Select time period", ["Day", "Week", "Month", "Quarter", "Year"])
                
                # Resample data based on period
                if period == "Day":
                    time_group = self.data[date_col].dt.date
                elif period == "Week":
                    time_group = self.data[date_col].dt.isocalendar().week
                elif period == "Month":
                    time_group = self.data[date_col].dt.to_period('M')
                elif period == "Quarter":
                    time_group = self.data[date_col].dt.to_period('Q')
                else:
                    time_group = self.data[date_col].dt.year
                
                # Group data
                trend_data = self.data.groupby(time_group)[price_col].agg(['mean', 'median', 'count']).reset_index()
                
                # Create line chart
                fig = px.line(
                    trend_data,
                    x=date_col,
                    y=['mean', 'median'],
                    title=f"Price Trends by {period}",
                    labels={date_col: period, 'value': 'Price'},
                    markers=True
                )
                fig.update_layout(legend_title_text="Metric")
                st.plotly_chart(fig, use_container_width=True)
                
                # Create volume chart
                fig = px.bar(
                    trend_data,
                    x=date_col,
                    y='count',
                    title=f"Number of Properties by {period}",
                    labels={date_col: period, 'count': 'Count'}
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def show_location_map(
        self, 
        lat_col: str = 'latitude', 
        lon_col: str = 'longitude',
        price_col: str = 'price',
        title: str = 'Property Locations'
    ) -> None:
        """
        Display an interactive map of property locations.
        
        Args:
            lat_col: Name of the latitude column
            lon_col: Name of the longitude column
            price_col: Name of the price column
            title: Title for the map
        """
        if self.data is None:
            st.error("No data loaded. Please load data first.")
            return
            
        if lat_col not in self.data.columns or lon_col not in self.data.columns:
            st.error(f"Location columns '{lat_col}' and/or '{lon_col}' not found in data.")
            return
        
        st.header(title)
        
        # Filter out missing coordinates
        map_data = self.data.dropna(subset=[lat_col, lon_col])
        
        if len(map_data) == 0:
            st.error("No valid coordinate data found.")
            return
        
        st.info(f"Showing {len(map_data)} properties with valid coordinates.")
        
        # Determine map center
        center_lat = map_data[lat_col].mean()
        center_lon = map_data[lon_col].mean()
        
        # Create map visualization options
        map_type = st.radio("Map visualization type:", ["Markers", "Heat Map", "Cluster"])
        
        # Create base map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        # Add appropriate layer based on selection
        if map_type == "Heat Map":
            # Create heat map data
            heat_data = [[row[lat_col], row[lon_col]] for _, row in map_data.iterrows()]
            HeatMap(heat_data).add_to(m)
            
        elif map_type == "Cluster":
            # Create marker cluster
            marker_cluster = MarkerCluster().add_to(m)
            
            # Add markers to cluster
            for _, row in map_data.iterrows():
                popup_text = f"Price: {row.get(price_col, 'N/A')}"
                # Add any available property info
                for col in ['address', 'type', 'rooms', 'surface', 'floor']:
                    if col in map_data.columns:
                        popup_text += f"<br>{col.title()}: {row.get(col, 'N/A')}"
                        
                folium.Marker(
                    location=[row[lat_col], row[lon_col]],
                    popup=folium.Popup(popup_text, max_width=300)
                ).add_to(marker_cluster)
                
        else:  # Markers
            # Create color scale
            if price_col in map_data.columns:
                # Normalize prices for color scale
                min_price = map_data[price_col].min()
                max_price = map_data[price_col].max()
                norm = plt.Normalize(min_price, max_price)
                
                # Sample 100 points to display (to avoid overcrowding)
                if len(map_data) > 100:
                    display_data = map_data.sample(100)
                    st.info("Displaying a sample of 100 properties to avoid overcrowding the map.")
                else:
                    display_data = map_data
                
                # Add markers
                for _, row in display_data.iterrows():
                    price = row.get(price_col)
                    if pd.notna(price):
                        # Create color based on price
                        color = plt.cm.viridis(norm(price))
                        rgb_color = f'#{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}'
                        
                        popup_text = f"Price: {price:,.2f}"
                        # Add any available property info
                        for col in ['address', 'type', 'rooms', 'surface', 'floor']:
                            if col in map_data.columns:
                                popup_text += f"<br>{col.title()}: {row.get(col, 'N/A')}"
                        
                        folium.CircleMarker(
                            location=[row[lat_col], row[lon_col]],
                            radius=8,
                            popup=folium.Popup(popup_text, max_width=300),
                            color=rgb_color,
                            fill=True,
                            fill_color=rgb_color
                        ).add_to(m)
            else:
                # Add simple markers without color scaling
                for _, row in map_data.iterrows():
                    folium.CircleMarker(
                        location=[row[lat_col], row[lon_col]],
                        radius=5,
                        color='blue',
                        fill=True
                    ).add_to(m)
        
        # Display the map
        folium_static(m)
    
    def show_feature_distributions(self, max_cols: int = 6) -> None:
        """
        Display distributions of features.
        
        Args:
            max_cols: Maximum number of columns to display
        """
        if self.data is None:
            st.error("No data loaded. Please load data first.")
            return
        
        st.header("Feature Distributions")
        
        # Find numeric columns
        numeric_cols = [col for col in self.data.columns 
                        if pd.api.types.is_numeric_dtype(self.data[col])]
        
        if not numeric_cols:
            st.warning("No numeric columns found in data.")
            return
        
        # Let user select columns
        selected_cols = st.multiselect(
            "Select columns to visualize", 
            numeric_cols,
            default=numeric_cols[:min(3, len(numeric_cols))]
        )
        
        if not selected_cols:
            st.info("Please select at least one column to visualize.")
            return
        
        # Select visualization type
        viz_type = st.radio("Visualization type:", ["Histogram", "Box Plot", "Violin Plot"])
        
        # Create plots
        fig = plt.figure(figsize=(12, 4 * ((len(selected_cols) + max_cols - 1) // max_cols)))
        
        for i, col in enumerate(selected_cols):
            ax = plt.subplot((len(selected_cols) + max_cols - 1) // max_cols, min(max_cols, len(selected_cols)), i + 1)
            
            if viz_type == "Histogram":
                sns.histplot(self.data[col].dropna(), kde=True, ax=ax)
                ax.set_title(f"Distribution of {col}")
            elif viz_type == "Box Plot":
                sns.boxplot(x=self.data[col].dropna(), ax=ax)
                ax.set_title(f"Box Plot of {col}")
            else:  # Violin Plot
                sns.violinplot(x=self.data[col].dropna(), ax=ax)
                ax.set_title(f"Violin Plot of {col}")
        
        plt.tight_layout()
        st.pyplot(fig)
    
    def show_feature_correlations(self) -> None:
        """
        Display correlation matrix of numeric features.
        """
        if self.data is None:
            st.error("No data loaded. Please load data first.")
            return
        
        st.header("Feature Correlations")
        
        # Find numeric columns
        numeric_cols = [col for col in self.data.columns 
                        if pd.api.types.is_numeric_dtype(self.data[col])]
        
        if len(numeric_cols) < 2:
            st.warning("Not enough numeric columns for correlation analysis.")
            return
        
        # Let user select columns
        selected_cols = st.multiselect(
            "Select columns for correlation analysis", 
            numeric_cols,
            default=numeric_cols[:min(5, len(numeric_cols))]
        )
        
        if len(selected_cols) < 2:
            st.info("Please select at least two columns for correlation analysis.")
            return
        
        # Calculate correlation matrix
        corr_matrix = self.data[selected_cols].corr()
        
        # Create heatmap
        fig = plt.figure(figsize=(10, 8))
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(
            corr_matrix,
            mask=mask,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            square=True,
            linewidths=0.5
        )
        plt.title("Feature Correlation Matrix")
        st.pyplot(fig)
        
        # Display correlation table
        st.subheader("Correlation Table")
        st.dataframe(corr_matrix.style.background_gradient(cmap="coolwarm"))
        
        # Show strongest correlations
        st.subheader("Top 10 Strongest Correlations")
        # Unstack correlation matrix and get absolute values
        corrs = corr_matrix.unstack()
        # Remove self-correlations
        corrs = corrs[corrs < 1.0]
        # Get absolute values and sort
        abs_corrs = corrs.abs().sort_values(ascending=False)
        # Take top 10
        top_corrs = abs_corrs.head(10)
        
        # Create a dataframe for display
        top_corrs_df = pd.DataFrame({
            "Features": [f"{idx[0]} & {idx[1]}" for idx in top_corrs.index],
            "Correlation": [corrs[idx] for idx in top_corrs.index]
        })
        
        st.dataframe(top_corrs_df)
    
    def show_ml_model_analysis(self, model_path: str, feature_names: Optional[List[str]] = None) -> None:
        """
        Display analysis of a trained ML model.
        
        Args:
            model_path: Path to the saved model file
            feature_names: List of feature names (optional)
        """
        st.header("Machine Learning Model Analysis")
        
        try:
            # Load model
            model = joblib.load(model_path)
            st.success(f"Successfully loaded model from {model_path}")
            
            # Extract feature importance if available
            if hasattr(model, 'feature_importances_'):
                st.subheader("Feature Importance")
                
                if feature_names is None:
                    # Try to extract from model
                    if hasattr(model, 'feature_names_in_'):
                        feature_names = model.feature_names_in_
                    else:
                        # Create dummy names
                        feature_names = [f"Feature_{i}" for i in range(len(model.feature_importances_))]
                
                # Create feature importance dataframe
                importance_df = pd.DataFrame({
                    'Feature': feature_names,
                    'Importance': model.feature_importances_
                }).sort_values('Importance', ascending=False)
                
                # Display as bar chart
                fig = px.bar(
                    importance_df,
                    x='Importance',
                    y='Feature',
                    orientation='h',
                    title="Feature Importance",
                    labels={'Importance': 'Importance Score', 'Feature': 'Feature Name'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Display as table
                st.dataframe(importance_df)
                
            elif hasattr(model, 'coef_'):
                st.subheader("Feature Coefficients")
                
                if feature_names is None:
                    # Try to extract from model
                    if hasattr(model, 'feature_names_in_'):
                        feature_names = model.feature_names_in_
                    else:
                        # Create dummy names
                        feature_names = [f"Feature_{i}" for i in range(len(model.coef_))]
                
                # Get coefficients (reshape if needed)
                coefs = model.coef_
                if len(coefs.shape) > 1 and coefs.shape[0] == 1:
                    coefs = coefs.flatten()
                
                # Create coefficients dataframe
                coef_df = pd.DataFrame({
                    'Feature': feature_names,
                    'Coefficient': coefs
                }).sort_values('Coefficient', ascending=False)
                
                # Display as bar chart
                fig = px.bar(
                    coef_df,
                    x='Coefficient',
                    y='Feature',
                    orientation='h',
                    title="Feature Coefficients",
                    labels={'Coefficient': 'Coefficient Value', 'Feature': 'Feature Name'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Display as table
                st.dataframe(coef_df)
            
            # Display model parameters if available
            if hasattr(model, 'get_params'):
                st.subheader("Model Parameters")
                params = model.get_params()
                # Flatten nested parameters
                flat_params = {}
                for key, value in params.items():
                    if isinstance(value, dict):
                        for nested_key, nested_value in value.items():
                            flat_params[f"{key}.{nested_key}"] = nested_value
                    else:
                        flat_params[key] = value
                
                # Convert to dataframe for display
                params_df = pd.DataFrame(list(flat_params.items()), columns=["Parameter", "Value"])
                st.dataframe(params_df)
                
        except Exception as e:
            st.error(f"Error loading or analyzing model: {e}")
    
    def create_interactive_dashboard(self) -> None:
        """
        Create an interactive dashboard with all visualizations.
        """
        if self.data is None:
            st.error("No data loaded. Please load data first.")
            return
        
        st.title("Real Estate Data Dashboard")
        
        # Sidebar for controls
        with st.sidebar:
            st.header("Dashboard Controls")
            
            # Add filters
            st.subheader("Filters")
            
            # Price filter if available
            if 'price' in self.data.columns:
                min_price = float(self.data['price'].min())
                max_price = float(self.data['price'].max())
                price_range = st.slider(
                    "Price Range",
                    min_value=min_price,
                    max_value=max_price,
                    value=(min_price, max_price)
                )
                filtered_data = self.data[(self.data['price'] >= price_range[0]) & 
                                         (self.data['price'] <= price_range[1])]
            else:
                filtered_data = self.data
            
            # Location filter if available
            location_cols = [col for col in ['city', 'district', 'neighborhood', 'zone'] if col in self.data.columns]
            if location_cols:
                location_col = st.selectbox("Filter by location field", location_cols)
                locations = ['All'] + sorted(filtered_data[location_col].unique().tolist())
                selected_location = st.selectbox(f"Select {location_col}", locations)
                
                if selected_location != 'All':
                    filtered_data = filtered_data[filtered_data[location_col] == selected_location]
            
            # Property type filter if available
            if 'type' in self.data.columns:
                property_types = ['All'] + sorted(filtered_data['type'].unique().tolist())
                selected_type = st.selectbox("Property Type", property_types)
                
                if selected_type != 'All':
                    filtered_data = filtered_data[filtered_data['type'] == selected_type]
            
            # Room filter if available
            if 'rooms' in self.data.columns:
                room_values = sorted(filtered_data['rooms'].dropna().unique().tolist())
                if room_values:
                    selected_rooms = st.multiselect(
                        "Number of Rooms",
                        ['All'] + room_values,
                        default=['All']
                    )
                    
                    if 'All' not in selected_rooms:
                        filtered_data = filtered_data[filtered_data['rooms'].isin(selected_rooms)]
            
            # Surface area filter if available
            if 'surface' in self.data.columns:
                min_surface = float(filtered_data['surface'].min())
                max_surface = float(filtered_data['surface'].max())
                surface_range = st.slider(
                    "Surface Area (m²)",
                    min_value=min_surface,
                    max_value=max_surface,
                    value=(min_surface, max_surface)
                )
                filtered_data = filtered_data[(filtered_data['surface'] >= surface_range[0]) & 
                                             (filtered_data['surface'] <= surface_range[1])]
            
            # Display filter summary
            st.info(f"Showing {len(filtered_data)} out of {len(self.data)} properties")
        
        # Create a temporary visualizer with the filtered data
        temp_viz = RealEstateDataVisualizer(filtered_data)
        
        # Main content
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Overview",
            "Price Analysis",
            "Location Map",
            "Feature Distribution",
            "Correlations"
        ])
        
        with tab1:
            temp_viz.show_data_overview()
            
        with tab2:
            temp_viz.show_price_analysis()
            
        with tab3:
            temp_viz.show_location_map()
            
        with tab4:
            temp_viz.show_feature_distributions()
            
        with tab5:
            temp_viz.show_feature_correlations()


def create_streamlit_app():
    """
    Create a Streamlit application for the real estate data visualizer.
    """
    st.set_page_config(
        page_title="Real Estate Data Explorer",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("Real Estate Data Explorer")
    st.subheader("Interactive visualization of real estate data")
    
    # Initialize visualizer
    visualizer = RealEstateDataVisualizer()
    
    # Sidebar for data loading
    with st.sidebar:
        st.header("Data Source")
        
        # Option to load from file
        upload_option = st.radio(
            "Select data source:",
            ["Upload CSV File", "Use Sample Data", "Load Saved File"]
        )
        
        if upload_option == "Upload CSV File":
            uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
            if uploaded_file is not None:
                try:
                    data = pd.read_csv(uploaded_file)
                    visualizer.data = data
                    st.success(f"Loaded {len(data)} records")
                except Exception as e:
                    st.error(f"Error loading file: {e}")
        
        elif upload_option == "Use Sample Data":
            # Create sample data for demonstration
            st.info("Loading sample real estate data...")
            
            # Create synthetic data
            np.random.seed(42)
            n_samples = 200
            
            # Generate basic features
            data = pd.DataFrame({
                'price': np.random.lognormal(12, 0.5, n_samples),
                'surface': np.random.lognormal(4.5, 0.4, n_samples),
                'rooms': np.random.randint(1, 6, n_samples),
                'bathrooms': np.random.randint(1, 4, n_samples),
                'floor': np.random.randint(0, 10, n_samples),
                'year_built': np.random.randint(1950, 2025, n_samples),
                'energy_class': np.random.choice(['A', 'B', 'C', 'D', 'E', 'F', 'G'], n_samples),
                'has_parking': np.random.choice([True, False], n_samples),
                'has_elevator': np.random.choice([True, False], n_samples),
                'latitude': 41.902782 + np.random.normal(0, 0.02, n_samples),
                'longitude': 12.496365 + np.random.normal(0, 0.02, n_samples),
            })
            
            # Add derived features
            data['price_per_sqm'] = data['price'] / data['surface']
            
            # Add categorical features
            data['city'] = 'Rome'
            data['zone'] = np.random.choice([
                'Centro Storico', 'Trastevere', 'Testaccio', 'Prati',
                'San Giovanni', 'EUR', 'Parioli', 'Trieste'
            ], n_samples)
            
            data['type'] = np.random.choice([
                'Apartment', 'Villa', 'Townhouse', 'Studio', 'Penthouse'
            ], n_samples)
            
            data['condition'] = np.random.choice([
                'New', 'Excellent', 'Good', 'To be renovated', 'Under construction'
            ], n_samples)
            
            # Add date feature
            start_date = pd.to_datetime('2023-01-01')
            end_date = pd.to_datetime('2025-07-01')
            date_range = (end_date - start_date).days
            random_days = np.random.randint(0, date_range, n_samples)
            data['listing_date'] = start_date + pd.to_timedelta(random_days, unit='D')
            
            visualizer.data = data
            st.success(f"Loaded {len(data)} sample records")
        
        else:  # "Load Saved File"
            file_path = st.text_input("Enter path to saved CSV file:")
            if file_path and st.button("Load File"):
                try:
                    visualizer.load_data(file_path)
                except Exception as e:
                    st.error(f"Error loading file: {e}")
    
    # Main content
    if visualizer.data is not None:
        # Navigation
        nav_option = st.radio(
            "Navigation:",
            ["Dashboard", "Data Explorer", "Price Analysis", "Location Map", "Feature Analysis"]
        )
        
        if nav_option == "Dashboard":
            visualizer.create_interactive_dashboard()
            
        elif nav_option == "Data Explorer":
            visualizer.show_data_overview()
            
        elif nav_option == "Price Analysis":
            visualizer.show_price_analysis()
            
        elif nav_option == "Location Map":
            visualizer.show_location_map()
            
        else:  # "Feature Analysis"
            tab1, tab2 = st.tabs(["Distributions", "Correlations"])
            with tab1:
                visualizer.show_feature_distributions()
            with tab2:
                visualizer.show_feature_correlations()
    else:
        st.info("Please load data from the sidebar to get started.")
        

if __name__ == "__main__":
    create_streamlit_app()
