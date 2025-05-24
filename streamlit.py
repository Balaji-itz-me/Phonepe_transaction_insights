import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
import numpy as np
import seaborn as sns
from plotly.subplots import make_subplots

# Set page configuration
st.set_page_config(
    page_title="PhonePe Pulse Data Analysis",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to improve appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #6739B7;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #9063CD;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-container {
        background-color: #EFE9F7;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #6739B7;
    }
    .metric-label {
        font-size: 1rem;
        color: #666;
    }
    .stButton>button {
        background-color: #6739B7;
        color: white;
    }
    .stButton>button:hover {
        background-color: #5A2CA0;
    }
</style>
""", unsafe_allow_html=True)

# Database connection function
@st.cache_resource
def create_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",  
            password="1234",  
            database="phonepe_transaction_insights"  
        )
        if conn.is_connected():
            return conn
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

# Execute SQL query function
def execute_query(conn, query):
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results
    except Error as e:
        st.error(f"Error executing query: {e}")
        return []

# Header with logo and title
def display_header():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="main-header">PhonePe Pulse Data Analysis</div>', unsafe_allow_html=True)
    
    st.markdown("""
    This dashboard presents analytical insights from the PhonePe Pulse dataset, showing transaction patterns,
    user behaviors, and market trends across India. Explore different sections using the sidebar navigation.
    """)
    st.divider()

# Display key metrics in a dashboard format
def display_key_metrics(conn):
    st.markdown('<div class="sub-header">Key Metrics</div>', unsafe_allow_html=True)
    
    # Execute queries for key metrics
    total_transactions = execute_query(conn, "SELECT SUM(count) as total FROM aggregated_transaction")
    total_amount = execute_query(conn, "SELECT SUM(amount) as total FROM aggregated_transaction")
    total_users = execute_query(conn, "SELECT SUM(registered_users) as total FROM aggregated_user")
    
    # Display metrics in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{total_transactions[0]["total"]:,}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Total Transactions</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">₹{total_amount[0]["total"]/10000000:,.2f}Cr</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Total Transaction Amount</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{total_users[0]["total"]:,}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Registered Users</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Transaction Analysis
def transaction_analysis(conn):
    st.markdown('<div class="sub-header">Transaction Analysis</div>', unsafe_allow_html=True)
    
    # Query options
    query_options = {
        "Quarterly Transaction Growth": """
            SELECT year, quarter, SUM(count) as total_transactions, 
            SUM(amount) as total_amount
            FROM aggregated_transaction
            GROUP BY year, quarter
            ORDER BY year, quarter
        """,
        "Top 10 States by Transaction Volume": """
            SELECT state, SUM(count) as total_transactions
            FROM aggregated_transaction
            GROUP BY state
            ORDER BY total_transactions DESC
            LIMIT 10
        """,
        "Top 10 Districts by Transaction Amount": """
            SELECT district, SUM(transaction_amount) as total_amount
            FROM map_transaction
            GROUP BY district
            ORDER BY total_amount DESC
            LIMIT 10
        """,
        "Transaction Type Distribution": """
            SELECT transaction_type, SUM(count) as total_transactions,
            SUM(amount) as total_amount
            FROM aggregated_transaction
            GROUP BY transaction_type
            ORDER BY total_transactions DESC
        """,
        "Year-on-Year Growth": """
            SELECT year, SUM(count) as total_transactions,
            SUM(amount) as total_amount
            FROM aggregated_transaction
            GROUP BY year
            ORDER BY year
        """
    }
    
    # Select analysis type
    selected_query = st.selectbox("Select Analysis Type", list(query_options.keys()))
    
    # Execute selected query
    results = execute_query(conn, query_options[selected_query])
    
    if not results:
        st.warning("No data available for this analysis.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Display results based on query type
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.dataframe(df, use_container_width=True)
    
    with col2:
        if selected_query == "Quarterly Transaction Growth":
            # Create quarter-year labels
            df['period'] = df['year'].astype(str) + ' Q' + df['quarter'].astype(str)
            
            # Create a dual-axis chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df['period'],
                y=df['total_transactions'],
                name='Transaction Count',
                marker_color='rgb(103, 57, 183)'
            ))
            fig.add_trace(go.Scatter(
                x=df['period'],
                y=df['total_amount'],
                name='Transaction Amount (₹)',
                marker_color='rgb(255, 161, 90)',
                yaxis='y2'
            ))
            fig.update_layout(
                title='Quarterly Transaction Growth',
                xaxis=dict(title='Quarter'),
                yaxis=dict(title='Transaction Count', side='left'),
                yaxis2=dict(title='Transaction Amount (₹)', side='right', overlaying='y', showgrid=False),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        elif selected_query == "Top 10 States by Transaction Volume":
            fig = px.bar(
                df,
                x='state',
                y='total_transactions',
                title='Top 10 States by Transaction Volume',
                color='total_transactions',
                color_continuous_scale=px.colors.sequential.Purples
            )
            fig.update_layout(xaxis_title='State', yaxis_title='Total Transactions')
            st.plotly_chart(fig, use_container_width=True)
            
        elif selected_query == "Top 10 Districts by Transaction Amount":
            fig = px.bar(
                df,
                x='district',
                y='total_amount',
                title='Top 10 Districts by Transaction Amount',
                color='total_amount',
                color_continuous_scale=px.colors.sequential.Purples
            )
            fig.update_layout(xaxis_title='District', yaxis_title='Total Amount (₹)')
            st.plotly_chart(fig, use_container_width=True)
            
        elif selected_query == "Transaction Type Distribution":
            fig = px.pie(
                df,
                values='total_transactions',
                names='transaction_type',
                title='Transaction Type Distribution',
                color_discrete_sequence=px.colors.sequential.Purples
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
            # Also show amount distribution
            fig2 = px.pie(
                df,
                values='total_amount',
                names='transaction_type',
                title='Transaction Amount Distribution by Type',
                color_discrete_sequence=px.colors.sequential.Purples_r
            )
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig2, use_container_width=True)
            
        elif selected_query == "Year-on-Year Growth":
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df['year'].astype(str),
                y=df['total_transactions'],
                name='Transaction Count',
                marker_color='rgb(103, 57, 183)'
            ))
            fig.add_trace(go.Scatter(
                x=df['year'].astype(str),
                y=df['total_amount'],
                name='Transaction Amount (₹)',
                marker_color='rgb(255, 161, 90)',
                yaxis='y2'
            ))
            fig.update_layout(
                title='Year-on-Year Growth',
                xaxis=dict(title='Year'),
                yaxis=dict(title='Transaction Count', side='left'),
                yaxis2=dict(title='Transaction Amount (₹)', side='right', overlaying='y', showgrid=False),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

# User Analysis
def user_analysis(conn):
    st.markdown('<div class="sub-header">User Analysis</div>', unsafe_allow_html=True)
    
    # Query options
    query_options = {
        "Top 10 States by Registered Users": """
            SELECT state, SUM(registered_users) as total_users
            FROM aggregated_user
            GROUP BY state
            ORDER BY total_users DESC
            LIMIT 10
        """,
        "Top 10 Districts by App Opens": """
            SELECT district, SUM(app_opens) as total_app_opens
            FROM map_user
            GROUP BY district
            ORDER BY total_app_opens DESC
            LIMIT 10
        """,
        "User Brand Distribution": """
            SELECT brand, SUM(device_count) as user_count
            FROM aggregated_user
            GROUP BY brand
            ORDER BY user_count DESC
        """,
        "User Growth by Quarter": """
            SELECT year, quarter, SUM(registered_users) as new_users
            FROM aggregated_user
            GROUP BY year, quarter
            ORDER BY year, quarter
        """,
        "States with Highest User Engagement": """
            SELECT state, SUM(registered_users) as total_users, 
            SUM(app_opens) as total_app_opens,
            SUM(app_opens)/ SUM(registered_users) as engagement_ratio
            FROM aggregated_user 
            GROUP BY state
            ORDER BY engagement_ratio DESC
            LIMIT 10
        """
    }
    
    # Select analysis type
    selected_query = st.selectbox("Select Analysis Type", list(query_options.keys()), key="user_analysis")
    
    # Execute selected query
    results = execute_query(conn, query_options[selected_query])
    
    if not results:
        st.warning("No data available for this analysis.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Display results based on query type
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.dataframe(df, use_container_width=True)
    
    with col2:
        if selected_query == "Top 10 States by Registered Users":
            # Option 4: Sunburst Chart
            plot_df = df.copy()
            # Add a central node for all states
            plot_df['country'] = 'India'
        
            fig = px.sunburst(
                plot_df,
                path=['country', 'state'],  # Hierarchy levels
                values='total_users',
                color='total_users',
                color_continuous_scale='Purples',
                title='Top 10 States by Registered Users'
            )
        
            fig.update_layout(height=600)
        
            st.plotly_chart(fig, use_container_width=True)
        
            
        elif selected_query == "Top 10 Districts by App Opens":
            fig = px.bar(
                df,
                x='district',
                y='total_app_opens',
                title='Top 10 Districts by App Opens',
                color='total_app_opens',
                color_continuous_scale=px.colors.sequential.Purples
            )
            fig.update_layout(xaxis_title='District', yaxis_title='Total App Opens')
            st.plotly_chart(fig, use_container_width=True)
            
        elif selected_query == "User Brand Distribution":
            # Show top 10 brands for better visualization
            top_brands = df.head(10)
            others = pd.DataFrame({
                'brand': ['Others'],
                'user_count': [df[10:]['user_count'].sum() if len(df) > 10 else 0]
            })
            plot_df = pd.concat([top_brands, others])
            
            fig = px.pie(
                plot_df,
                values='user_count',
                names='brand',
                title='User Device Brand Distribution',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
        elif selected_query == "User Growth by Quarter":
            # Create quarter-year labels
            df['period'] = df['year'].astype(str) + ' Q' + df['quarter'].astype(str)
            
            fig = px.line(
                df,
                x='period',
                y='new_users',
                title='User Growth by Quarter',
                markers=True
            )
            fig.update_traces(line_color='rgb(103, 57, 183)', line_width=3)
            fig.update_layout(xaxis_title='Quarter', yaxis_title='New Registered Users')
            st.plotly_chart(fig, use_container_width=True)
            
        elif selected_query == "States with Highest User Engagement":
            # Convert engagement_ratio to numeric
            df['engagement_ratio'] = pd.to_numeric(df['engagement_ratio'], errors='coerce')
    
            # Create scatter plot
            fig = px.scatter(
                df,
                x='total_users',
                y='total_app_opens',
                size='engagement_ratio',
                hover_data=['state'],
                title="User Engagement by State",
                labels={
                    'total_users': 'Total Registered Users',
                    'total_app_opens': 'App Opens',
                    'engagement_ratio': 'Engagement Ratio'
                },
                log_x=True,  # Set x-axis to log scale
                log_y=True   # Set y-axis to log scale
            )
    
            # Update layout
            fig.update_layout(
                xaxis_title='Total Users (log scale)', 
                yaxis_title='Total App Opens (log scale)',
                coloraxis_colorbar_title='Engagement Ratio'
            )
    
            # Display the plot
            st.plotly_chart(fig, use_container_width=True)

# Geographical Analysis
def geographical_analysis(conn):
    st.markdown('<div class="sub-header">Geographical Analysis</div>', unsafe_allow_html=True)
    
    # Year and quarter selection for filtering
    col1, col2 = st.columns(2)
    with col1:
        year = st.selectbox("Select Year", [2018, 2019, 2020, 2021, 2022, 2023, 2024], index=4)
    with col2:
        quarter = st.selectbox("Select Quarter", [1, 2, 3, 4], index=3)
    
    # Analysis type selection - Added Insurance
    analysis_type = st.radio(
        "Select Analysis Type",
        ["Transaction Count", "Transaction Amount", "Registered Users", "App Opens", "Insurance Policies", "Insurance Amount"]
    )
    
    # Build query based on selection
    if analysis_type in ["Transaction Count", "Transaction Amount"]:
        query = f"""
            SELECT state, 
                  {'SUM(count) as value' if analysis_type == "Transaction Count" else 'SUM(amount) as value'}
            FROM {'aggregated_transaction' if analysis_type in ["Transaction Count", "Transaction Amount"] else 'map_transaction'}
            WHERE year = {year} AND quarter = {quarter}
            GROUP BY state
        """
    elif analysis_type in ["Registered Users", "App Opens"]:  # User-based metrics
        query = f"""
            SELECT state, 
                  {'SUM(registered_users) as value' if analysis_type == "Registered Users" else 'SUM(app_opens) as value'}
            FROM {'aggregated_user' if analysis_type == "Registered Users" else 'map_user'}
            WHERE year = {year} AND quarter = {quarter}
            GROUP BY state
        """
    else:  # Insurance metrics
        
        query = f"""
            SELECT state, 
                  {'SUM(count) as value' if analysis_type == "Insurance Policies" else 'SUM(amount) as value'}
            FROM aggregated_insurance
            WHERE year = {year} AND quarter = {quarter}
            GROUP BY state
        """
    
    # Execute query
    results = execute_query(conn, query)
    
    if not results:
        st.warning("No data available for this analysis.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Display aggregate metrics
    total_value = df['value'].sum()
    
    # Format based on analysis type
    if analysis_type in ["Transaction Amount", "Insurance Amount"]:
        # Convert to crores for large amounts
        formatted_value = f"₹{total_value/10000000:.2f} Cr"
    elif analysis_type in ["Transaction Count", "Insurance Policies", "Registered Users"]:
        formatted_value = f"{total_value:,.0f}"
    else:  # App Opens
        formatted_value = f"{total_value:,.0f}"
    
    st.metric(f"Total {analysis_type}", formatted_value)
    
    # Create India map with proper state names
    fig = px.choropleth(
        df,
        geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson",
        featureidkey='properties.ST_NM',
        locations='state',  # Use the mapped state names
        color='value',
        color_continuous_scale='Purples' if not analysis_type.startswith("Insurance") else 'Teal',
        title=f'{analysis_type} by State - {year} Q{quarter}'
    )
    fig.update_geos(fitbounds="locations", visible=False)
    
    # Display map
    st.plotly_chart(fig, use_container_width=True)
    
    # Create tabs for additional visualizations
    tab1, tab2 = st.tabs(["Data Table", "Bar Chart"])
    
    with tab1:
        # Add the state_mapped column to display and sort by value
        display_df = df[['state', 'value']].sort_values('value', ascending=False)
        
        # Rename columns for better readability
        display_df.columns = ['State', 'Value']
        
        # Format values based on analysis type
        if analysis_type in ["Transaction Amount", "Insurance Amount"]:
            # Format as currency
            display_df['Value'] = display_df['Value'].apply(lambda x: f"₹{x:,.2f}")
        
        st.dataframe(display_df, use_container_width=True)
    
    with tab2:
        # Create bar chart of top 10 states
        top_states = df.sort_values('value', ascending=False).head(10)
        
        fig = px.bar(
            top_states,
            x='state',
            y='value',
            title=f'Top 10 States by {analysis_type} - {year} Q{quarter}',
            color='value',
            color_continuous_scale='Purples' if not analysis_type.startswith("Insurance") else 'Teal',
            text_auto='.2s' if analysis_type in ["Transaction Amount", "Insurance Amount"] else True
        )
        
        # Set axis labels
        fig.update_layout(
            xaxis_title="State",
            yaxis_title=analysis_type,
            xaxis={'categoryorder':'total descending'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # If insurance data is selected, show additional insurance-specific analysis
    if analysis_type.startswith("Insurance"):
        st.subheader("Insurance Trends")
        
        # Query to get trend data
        trend_query = f"""
            SELECT year, quarter, SUM({'count' if analysis_type == "Insurance Policies" else 'amount'}) as value
            FROM aggregated_insurance
            GROUP BY year, quarter
            ORDER BY year, quarter
        """
        
        trend_results = execute_query(conn, trend_query)
        
        if trend_results:
            trend_df = pd.DataFrame(trend_results)
            
            # Create time period labels
            trend_df['period'] = trend_df.apply(lambda x: f"{x['year']} Q{x['quarter']}", axis=1)
            
            # Create line chart
            fig = px.line(
                trend_df,
                x='period',
                y='value',
                title=f'{analysis_type} Trend Over Time',
                markers=True
            )
            
            st.plotly_chart(fig, use_container_width=True)

def business_case_studies(conn):
    st.markdown('<div class="sub-header">Business Case Studies</div>', unsafe_allow_html=True)
    
    # Define business case studies with descriptions and multiple SQL queries
    case_studies = {
        "1. Decoding Transaction Dynamics on PhonePe": {
            "description": "Analyzing patterns and trends in user transactions to uncover key insights driving PhonePe's digital payment ecosystem.",
            "queries": {
                "State-wise Transaction Trends": {
                    "query": """
                        SELECT 
                            state,
                            year,
                            quarter,
                            SUM(count) AS total_transactions,
                            SUM(amount) AS total_transaction_value
                        FROM 
                            aggregated_transaction
                        GROUP BY 
                            state, year, quarter
                        ORDER BY 
                            state, year, quarter;
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "state", "y_col": "total_transaction_value", "title": "State-wise Transaction Trends"}
                },
                "Quarter-wise Transaction Trends": {
                    "query": """
                        SELECT 
                            quarter,
                            SUM(amount) AS total_value,
                            SUM(count) AS total_count
                        FROM 
                            aggregated_transaction
                        GROUP BY 
                            quarter
                        ORDER BY 
                            quarter ASC;
                    """,
                    "viz_type": "dual_axis",
                    "viz_params": {"x_col": "quarter", "y_col1": "total_count", "y_col2": "total_value", "title": "Quarter-wise Transaction Trends","y_title1": "Transaction Count","y_title2": "Transaction Value (₹)"}
                },
                "Payment Category-wise Trends": {
                    "query": """
                        SELECT 
                            transaction_type,
                            SUM(amount) AS total_value,
                            SUM(count) AS total_count
                        FROM 
                            aggregated_transaction
                        GROUP BY 
                            transaction_type
                        ORDER BY 
                            total_value DESC;
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "transaction_type", "y_col": "total_value", "title": "Payment Category-wise Trends"}
                },
                "State + Quarter Combination Analysis": {
                    "query": """
                        SELECT 
                            state,
                            year,
                            quarter,
                            SUM(amount) AS total_value,
                            SUM(count) AS total_count
                        FROM 
                            aggregated_transaction
                        GROUP BY 
                            state, quarter,year
                        ORDER BY 
                            state, quarter,year;
                    """,
                    "viz_type": "group_bar_1",
                    "viz_params": {"x_col": "state", "y_col": "total_value", "color": "year", "title": "Transaction Values by State, Year and Quarter"}
                }
            },
            "insights": """
                - Digital Commerce Leadership: Average transaction of ₹1.47K with Merchant Payments dominating indicates PhonePe has become essential infrastructure for everyday retail, from street vendors to small businesses across India.
                - Economic Hub Concentration: Top states (Maharashtra, Karnataka, UP) align with major economic centers, while remote regions (Mizoram, Lakshadweep, Andaman) show significant growth potential in underserved markets.
                - Mainstream Adoption: The moderate transaction value suggests successful penetration beyond urban elites into middle-class daily commerce, replacing cash for routine purchases and bill payments.
            """
        },
        "2. User Engagement and Growth Strategy": {
            "description": "Identifying user behavior patterns and strategic levers to enhance engagement, retention, and overall growth on the PhonePe platform.",
            "queries": {
                "State-wise Total Registered Users and App Opens": {
                    "query": """
                        SELECT 
                            state,
                            SUM(registered_users) AS total_registered_users,
                            SUM(app_opens) AS total_app_opens
                        FROM 
                            aggregated_user
                        GROUP BY 
                            state
                        ORDER BY 
                            total_registered_users DESC;
                        
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "state", "y_col": "total_registered_users", "title": "State-wise Total Registered Users and App Opens"}
                },
                "District-wise Total Registered Users": {
                    "query": """
                       SELECT 
                            state,
                            district,
                            SUM(registered_users) AS total_registered_users
                        FROM 
                            map_user
                        GROUP BY 
                            state, district
                        ORDER BY 
                            total_registered_users DESC
                        LIMIT 10;
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "district", "y_col": "total_registered_users", "title": "District-wise Total Registered Users"}
                },
                "Top 10 States with Highest App Opens": {
                    "query": """
                        SELECT 
                            state,
                            SUM(app_opens) AS total_app_opens
                        FROM 
                            aggregated_user
                        GROUP BY 
                            state
                        ORDER BY 
                            total_app_opens DESC
                        LIMIT 10;
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "state", "y_col": "total_app_opens", "title": "Top 10 States with Highest App Opens"}
                },
                "States with Low Registered Users but High App Opens": {
                    "query": """
                        SELECT 
                            state,
                            SUM(registered_users) AS total_registered_users,
                            SUM(app_opens) AS total_app_opens,
                            (SUM(app_opens) - SUM(registered_users)) AS gap
                        FROM 
                            aggregated_user
                        GROUP BY 
                            state
                        HAVING 
                            gap > 0
                        ORDER BY 
                            gap DESC
                        LIMIT 10;
                    """,
                    "viz_type": "group_bar",
                    "viz_params": {"x_col": "state", "y_cols": ["total_registered_users", "total_app_opens"],"title": "Top 10 States: App Opens vs Registered Users Gap","color_name": "Metric"}
                }
            },
            "insights": """
                - States like Maharashtra, Uttar Pradesh, and Karnataka have the highest number of registered users and app opens, indicating strong engagement
                - Lower-performing states could be targeted for marketing campaigns
                - Districts like Bangalore Urban and Pune dominate user registration, suggesting dense urban adoption
                - States like Maharashtra and Karnataka show the maximum app activity, reflecting higher user engagement and potential for upselling services
            """
        },

        "3. Insurance Engagement Analysis": {
            "description": "Analyzing user interaction and adoption trends to evaluate the effectiveness and growth potential of insurance services on PhonePe.",
            "queries": {
                "State-wise Total Insurance Transactions and Values": {
                    "query": """
                        SELECT 
                            state,
                            SUM(count) AS total_insurance_transactions,
                            SUM(amount) AS total_insurance_value
                        FROM 
                            aggregated_insurance
                        GROUP BY 
                            state
                        ORDER BY 
                            total_insurance_transactions DESC;
                        
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "state", "y_col": "total_insurance_transactions", "title": "State-wise Total Insurance Transactions and Values"}
                },
                "District-wise Total Insurance Transactions": {
                    "query": """
                        SELECT 
                            state,
                            district,
                            SUM(policy_count) AS total_insurance_transactions,
                            SUM(insured_amount) AS total_insurance_value
                        FROM 
                            map_insurance
                        GROUP BY 
                            state, district
                        ORDER BY 
                            total_insurance_transactions DESC
                        LIMIT 10;
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "district", "y_col": "total_insurance_transactions", "title": "District-wise Total Insurance Transactions"}
                },
                "Top 10 States by Insurance Transaction Value": {
                    "query": """
                        SELECT 
                            state,
                            SUM(amount) AS total_insurance_value
                        FROM 
                            aggregated_insurance
                        GROUP BY 
                            state
                        ORDER BY 
                            total_insurance_value DESC
                        LIMIT 10;
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "state", "y_col": "total_insurance_value", "title": "Top 10 States by Insurance Transaction Value"}
                },
                "Find States with Low Insurance Uptake": {
                    "query": """
                        SELECT 
                            state,
                            SUM(count) AS total_insurance_transactions
                        FROM 
                            aggregated_insurance
                        GROUP BY 
                            state
                        HAVING 
                            SUM(count) < 50000
                        ORDER BY 
                            total_insurance_transactions ASC;
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "state", "y_col": "total_insurance_transactions", "title": "States with Low Insurance Uptake"}
                },
                "State-wise Insurance Penetration (%)": {
                    "query": """
                        SELECT 
                            ins.state,
                            (SUM(ins.amount) / SUM(trx.amount)) * 100 AS insurance_percentage
                        FROM 
                            aggregated_insurance ins
                        JOIN 
                            aggregated_transaction trx 
                        ON 
                            ins.state = trx.state
                        GROUP BY 
                            ins.state
                        ORDER BY 
                            insurance_percentage DESC;
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "state", "y_col": "insurance_percentage", "title": "State-wise Insurance Penetration (%)"}
                }
            },
            "insights": """
                - States like Karnataka, Maharashtra, and Tamil Nadu lead in insurance transactions and value, suggesting higher insurance awareness among users
                - Urban centers like Bangalore Urban and Pune show high insurance engagement, aligning with financial literacy trends
                - States with the highest insurance transaction value represent mature markets; further cross-selling of premium plans can be explored
                - The analysis highlights that states like Lakshadweep, Ladakh, and others have the lowest insurance transaction counts. This indicates a major growth opportunity where PhonePe can target insurance marketing campaigns, customized offerings, or awareness programs to increase insurance penetration
                - States with low insurance penetration (e.g., Andra Pradesh and Madhya Pradesh) represent significant opportunities for insurance marketing and user education
            """
        },

        "4.Transaction Analysis Across States and Districts": {
            "description": "Examining regional transaction trends to uncover geographic patterns, usage intensity, and growth opportunities across Indian states and districts on PhonePe.",
            "queries": {
                "Top States by Total Transaction Value": {
                    "query": """
                        SELECT 
                            state,
                            SUM(count) AS total_transactions,
                            SUM(amount) AS total_transaction_value
                        FROM 
                            aggregated_transaction
                        GROUP BY 
                            state
                        ORDER BY 
                            total_transaction_value DESC
                        LIMIT 10;
                        
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "state", "y_col": "total_transaction_value", "title": "Top States by Total Transaction Value"}
                },
                "Top Districts by Total Transaction Value": {
                    "query": """
                        SELECT 
                            state,
                            district,
                            SUM(transaction_count) AS total_transactions,
                            SUM(transaction_amount) AS total_transaction_value
                        FROM 
                            map_transaction
                        GROUP BY 
                            state, district
                        ORDER BY 
                            total_transaction_value DESC
                        LIMIT 10;
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "district", "y_col": "total_transaction_value", "title": "Top Districts by Total Transaction Value"}
                },
                "Bottom 10 States (Low Transaction Value)": {
                    "query": """
                        SELECT 
                            state,
                            SUM(count) AS total_transactions,
                            SUM(amount) AS total_transaction_value
                        FROM 
                            aggregated_transaction
                        GROUP BY 
                            state
                        ORDER BY 
                            total_transaction_value ASC
                        LIMIT 10;
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "state", "y_col": "total_transaction_value", "title": "Bottom 10 States (Low Transaction Value)"}
                },
                "contribution percentage of a district in state total!": {
                    "query": """
                        SELECT 
                            m.state,
                            m.district,
                            SUM(m.transaction_amount) AS district_total,
                            (SUM(m.transaction_amount) / s.state_total) * 100 AS contribution_percentage
                        FROM 
                            map_transaction m
                        JOIN 
                            (SELECT 
                                state, 
                                SUM(amount) AS state_total 
                            FROM 
                                aggregated_transaction 
                            GROUP BY 
                                state) s
                            ON 
                                m.state = s.state
                            GROUP BY 
                                m.state, m.district, s.state_total
                            ORDER BY 
                                contribution_percentage DESC
                            LIMIT 10;
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "district", "y_col": "contribution_percentage", "title": "contribution percentage of a district in state total"}
                }
            },
            "insights": """
                - States like Maharashtra, Karnataka, and Telangana dominate the transaction value, indicating a mature and digitally active user base
                - Districts like Bengaluru Urban, Pune, and Hyderabad are key transaction hubs — these regions can be leveraged for premium services
                - States like Lakshadweep, Mizoram, and Andaman and Nicobar Island show low transaction volumes, suggesting a potential for targeted marketing campaigns and partnership building
                - Some states show heavy dependence on just 1-2 districts (example: Chandigarh District drives a big chunk of Punjabs transactions). Such states should diversify focus beyond just top cities
            """
        },

        "5.User Registration Analysis": {
            "description": "Analyzing user registration trends to understand adoption patterns, regional growth, and onboarding effectiveness on the PhonePe platform.",
            "queries": {
                "Brand Preference Analysis": {
                    "query": """
                        SELECT 
                            brand,
                            SUM(device_count) as total_devices,
                            ROUND(AVG(device_percentage) * 100, 2) as average_percentage
                        FROM aggregated_user
                        GROUP BY brand
                        ORDER BY total_devices DESC
                        LIMIT 10;
                        
                    """,
                    "viz_type": "bar",
                    "viz_params": {"x_col": "brand", "y_col": "average_percentage", "title": "Top Brands by Registered Users on PhonePe"}
                },
                "Comprehensive Registration Analysis with Multiple Metrics": {
                    "query": """
                        SELECT 
                            m.state,
                            SUM(m.registered_users) as total_registered_users,
                            COUNT(DISTINCT m.district) as districts_count,
                            ROUND(SUM(m.registered_users) / COUNT(DISTINCT m.district), 0) as avg_users_per_district,
                            (SELECT SUM(transaction_count) 
                                FROM map_transaction mt 
                                ) as total_transactions
                        FROM map_user m
                        GROUP BY m.state
                        ORDER BY total_registered_users DESC;
                    """,
                    "viz_type": "combo_bar_line",
                    "viz_params": {"x_col": "state", "y_col_bar": "total_registered_users","y_col_line": "avg_users_per_district","tooltip_cols": ["districts_count", "total_transactions"],"title": "State-wise User Registration with Average per District","y_title_bar": "Total Registered Users","y_title_line": "Avg Users per District"}
                },
                "Year-on-Year Growth in User Registration by State": {
                    "query": """
                        WITH yearly_registrations AS (
                            SELECT 
                                state,
                                year,
                                SUM(registered_users) as yearly_users
                            FROM map_user
                            GROUP BY state, year
                        ),
                        yearly_growth AS (
                            SELECT 
                                current.state,
                                current.year as current_year,
                                current.yearly_users as current_year_users,
                                prev.year as previous_year,
                                prev.yearly_users as previous_year_users,
                                (current.yearly_users - prev.yearly_users) as absolute_growth,
                                CASE 
                                    WHEN prev.yearly_users > 0 
                                    THEN ROUND((current.yearly_users - prev.yearly_users) * 100.0 / prev.yearly_users, 2)
                                    ELSE NULL
                                END as growth_percentage
                            FROM yearly_registrations current
                            LEFT JOIN yearly_registrations prev 
                                ON current.state = prev.state AND current.year = prev.year + 1
                            WHERE prev.yearly_users IS NOT NULL  -- Ensure there's a previous year to compare with
                        )
                        SELECT 
                            state,
                            current_year,
                            previous_year,
                            current_year_users,
                            previous_year_users,
                            absolute_growth,
                            growth_percentage,
                            CASE
                                WHEN growth_percentage > 50 THEN 'High Growth'
                                WHEN growth_percentage > 20 THEN 'Moderate Growth'
                                WHEN growth_percentage > 0 THEN 'Low Growth'
                                WHEN growth_percentage = 0 THEN 'Stagnant'
                                ELSE 'Declining'
                            END as growth_category
                        FROM yearly_growth
                        ORDER BY current_year, growth_percentage DESC;
                    """,
                    "viz_type": "scatter_categories",
                    "viz_params": {"x_col": "growth_percentage", "y_col": "current_year_users","color_col": "growth_category","hover_name": "state","size_col": "absolute_growth","facet_col": "current_year","title": "User Growth Analysis by State and Year"}
                },
                "multi-dimensional cohort analysis of PhonePe user": {
                    "query": """
                        WITH registration_trends AS (
                            -- Get registration data by state, year, quarter
                            SELECT 
                                mu.state,
                                mu.year,
                                mu.quarter,
                                SUM(mu.registered_users) AS total_registrations,
                                SUM(mu.app_opens) AS total_app_opens,
                                COUNT(DISTINCT mu.district) AS active_districts
                            FROM map_user mu
                            GROUP BY mu.state, mu.year, mu.quarter
                        ),
                        transaction_metrics AS (
                            -- Get transaction data by state, year, quarter
                            SELECT 
                                mt.state,
                                mt.year,
                                mt.quarter,
                                SUM(mt.transaction_count) AS total_transactions,
                                SUM(mt.transaction_amount) AS total_amount,
                                SUM(mt.transaction_count)/COUNT(DISTINCT mt.district) AS avg_transactions_per_district
                            FROM map_transaction mt
                            GROUP BY mt.state, mt.year, mt.quarter
                        ),
                        device_distribution AS (
                            -- Get device brand data
                            SELECT 
                                au.state,
                                au.year,
                                au.quarter,
                                au.brand,
                                SUM(au.device_count) AS total_devices,
                                SUM(au.device_count*au.device_percentage)/SUM(au.device_count) AS weighted_percentage
                            FROM aggregated_user au
                            GROUP BY au.state, au.year, au.quarter, au.brand
                        ),
                        dominant_brands AS (
                            -- Find dominant brand per state/period
                            SELECT 
                                state,
                                year,
                                quarter,
                                FIRST_VALUE(brand) OVER (
                                    PARTITION BY state, year, quarter 
                                    ORDER BY total_devices DESC
                                ) AS top_brand,
                                FIRST_VALUE(weighted_percentage) OVER (
                                    PARTITION BY state, year, quarter 
                                    ORDER BY total_devices DESC
                                ) AS top_brand_percentage
                            FROM device_distribution
                        ),
                        insurance_adoption AS (
                            -- Get insurance data where available
                            SELECT
                                mi.state,
                                mi.year, 
                                mi.quarter,
                                SUM(mi.policy_count) AS total_policies,
                                SUM(mi.insured_amount) AS total_insured_amount,
                                COUNT(DISTINCT mi.district) AS districts_with_insurance
                            FROM map_insurance mi
                            GROUP BY mi.state, mi.year, mi.quarter
                        )
                        SELECT
                            -- Basic identifiers
                            rt.state,
                            rt.year,
                            rt.quarter,
                            
                            -- Registration metrics
                            rt.total_registrations,
                            rt.total_app_opens,
                            rt.active_districts,
                            ROUND(rt.total_app_opens/NULLIF(rt.total_registrations, 0), 2) AS app_opens_per_user,
                            
                            -- Transaction metrics
                            tm.total_transactions,
                            tm.total_amount,
                            ROUND(tm.total_transactions/NULLIF(rt.total_registrations, 0), 2) AS transactions_per_user,
                            tm.avg_transactions_per_district,
                            
                            -- Device metrics
                            db.top_brand,
                            ROUND(db.top_brand_percentage * 100, 1) AS top_brand_percentage,
                            
                            -- Insurance metrics
                            ia.total_policies,
                            ia.total_insured_amount,
                            ROUND(ia.total_policies/NULLIF(rt.total_registrations, 0) * 1000, 2) AS policies_per_1000_users,
                            
                            -- Derived/calculated metrics
                            CASE
                                WHEN rt.total_registrations > 1000000 THEN 'Very High'
                                WHEN rt.total_registrations > 500000 THEN 'High'
                                WHEN rt.total_registrations > 100000 THEN 'Medium'
                                ELSE 'Low'
                            END AS registration_tier,
                            
                            CASE
                                WHEN tm.total_transactions/NULLIF(rt.total_registrations, 0) > 5 THEN 'Highly Engaged'
                                WHEN tm.total_transactions/NULLIF(rt.total_registrations, 0) > 2 THEN 'Moderately Engaged'
                                WHEN tm.total_transactions/NULLIF(rt.total_registrations, 0) > 0 THEN 'Slightly Engaged'
                                ELSE 'Not Engaged'
                            END AS engagement_level,
                            
                            -- Market penetration metric (comparing districts with any activity vs districts with insurance)
                            ROUND(ia.districts_with_insurance/NULLIF(rt.active_districts, 0) * 100, 1) AS insurance_district_coverage_percent
                            
                        FROM registration_trends rt
                        LEFT JOIN transaction_metrics tm 
                            ON rt.state = tm.state AND rt.year = tm.year AND rt.quarter = tm.quarter
                        LEFT JOIN (
                            SELECT DISTINCT state, year, quarter, top_brand, top_brand_percentage
                            FROM dominant_brands
                        ) db 
                            ON rt.state = db.state AND rt.year = db.year AND rt.quarter = db.quarter
                        LEFT JOIN insurance_adoption ia 
                            ON rt.state = ia.state AND rt.year = ia.year AND rt.quarter = ia.quarter
                        WHERE rt.year BETWEEN 2018 AND 2024  -- Adjust years as needed
                        ORDER BY 
                            rt.year DESC, 
                            rt.quarter DESC, 
                            rt.total_registrations DESC;
                    """,
                    "viz_type": "advanced_bubble",
                    "viz_params": {
                        "x_col": "transactions_per_user", 
                        "y_col": "total_registrations",
                        "size_col": "total_amount",
                        "color_col": "engagement_level",
                        "hover_name": "state",
                        "animation_col": "year",
                        "animation_group": "state",
                        "facet_col": "quarter",
                        "title": "State Performance Dashboard: Engagement vs Registration"
                    }
                }
            },
            "insights": """
                - High users but low avg per district       --  Spread thin    --     User concentration is low; marketing can focus on dense areas
                - High users, high transactions      --          Good conversion  --   Indicates strong onboarding and active users
                - High districts, low total users    --          Untapped potential --   Launch district-focused campaigns
                - Low/Negative growth -- Stagnation — investigate reasons (e.g., saturation, competition)
                - Growth category -- Segment states for tailored marketing (e.g., retention in low-growth vs. onboarding in high-growth)
            """
        }
       
    }
    
    # Create a selection dropdown for the case studies
    selected_case = st.selectbox("Select a Business Case Study", list(case_studies.keys()))
    
    # Display the selected case study
    st.markdown("### " + selected_case)
    st.write(case_studies[selected_case]["description"])
    
    # Create tabs for different queries within the case study
    query_tabs = st.tabs(list(case_studies[selected_case]["queries"].keys()))
    
    # Process each query in its own tab
    for i, (query_name, query_info) in enumerate(case_studies[selected_case]["queries"].items()):
        with query_tabs[i]:
            st.subheader(query_name)
            
            # Run the query
            try:
                df = pd.read_sql_query(query_info["query"], conn)
                st.dataframe(df)
                
                # Create visualization based on the specified type
                if not df.empty:
                    st.subheader("Visualization")
                    viz_type = query_info["viz_type"]
                    params = query_info["viz_params"]
                    
                    if viz_type == "choropleth" and "state" in df.columns:
                        fig = px.choropleth_mapbox(
                            df, 
                            geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson", 
                            locations='state', 
                            featureidkey='properties.ST_NM',
                            color=params["color_col"],
                            color_continuous_scale="Viridis",
                            mapbox_style="carto-positron",
                            zoom=3, center={"lat": 20.5937, "lon": 78.9629},
                            opacity=0.7,
                            title=params["title"]
                        )
                        st.plotly_chart(fig)
                    
                    elif viz_type == "bar":
                        fig = px.bar(
                            df, 
                            x=params["x_col"], 
                            y=params["y_col"], 
                            title=params["title"]
                        )
                        st.plotly_chart(fig)

                    elif viz_type == "advanced_bubble":
                        # Create an animated bubble chart with facets
                        fig = px.scatter(
                            df,
                            x=params["x_col"],
                            y=params["y_col"],
                            size=params["size_col"],
                            color=params["color_col"],
                            hover_name=params["hover_name"],
                            animation_frame=params.get("animation_col"),
                            animation_group=params.get("animation_group"),
                            facet_col=params.get("facet_col"),
                            size_max=60,
                            title=params["title"],
                            labels={
                                col: col.replace('_', ' ').title() 
                                for col in [params["x_col"], params["y_col"], params["size_col"], params["color_col"]]
                            },
                            color_discrete_map={
                                'Highly Engaged': '#1a9850',     # Green
                                'Moderately Engaged': '#91cf60', # Light green
                                'Slightly Engaged': '#fee08b',   # Light yellow
                                'Not Engaged': '#d73027'         # Red
                            },
                            height=600
                        )
                        
                        # Customize hover information
                        hover_template = (
                            "<b>%{hovertext}</b><br><br>" +
                            "Transactions per User: %{x:.2f}<br>" +
                            "Total Registrations: %{y:,.0f}<br>" +
                            "Transaction Amount: ₹%{marker.size:,.0f}<br>" +
                            "Engagement: %{customdata[3]}<br><br>" +  # Store engagement_level in customdata
                            
                            "<extra></extra>"
                        )

                        # And update the customdata to include engagement_level
                        fig.update_traces(
                            customdata=df[[
                                "top_brand", 
                                "top_brand_percentage", 
                                "policies_per_1000_users",
                                params["color_col"]  # engagement_level
                            ]],
                            hovertemplate=hover_template
                        )
                        
                        # Add reference quadrant lines
                        fig.add_shape(type="line", x0=df[params["x_col"]].median(), y0=0, 
                                    x1=df[params["x_col"]].median(), y1=df[params["y_col"]].max()*1.05,
                                    line=dict(color="gray", width=1, dash="dash"))
                        
                        fig.add_shape(type="line", x0=0, y0=df[params["y_col"]].median(), 
                                    x1=df[params["x_col"]].max()*1.05, y1=df[params["y_col"]].median(),
                                    line=dict(color="gray", width=1, dash="dash"))
                        
                        # Add quadrant labels
                        annotations = [
                            dict(x=df[params["x_col"]].max()*0.25, y=df[params["y_col"]].max()*0.85, 
                                text="High Registration<br>Low Engagement", showarrow=False, 
                                font=dict(size=10, color="gray")),
                            dict(x=df[params["x_col"]].max()*0.75, y=df[params["y_col"]].max()*0.85, 
                                text="High Registration<br>High Engagement", showarrow=False, 
                                font=dict(size=10, color="gray")),
                            dict(x=df[params["x_col"]].max()*0.25, y=df[params["y_col"]].max()*0.15, 
                                text="Low Registration<br>Low Engagement", showarrow=False, 
                                font=dict(size=10, color="gray")),
                            dict(x=df[params["x_col"]].max()*0.75, y=df[params["y_col"]].max()*0.15, 
                                text="Low Registration<br>High Engagement", showarrow=False, 
                                font=dict(size=10, color="gray"))
                        ]
                        fig.update_layout(annotations=annotations)
                        
                        # Improve layout
                        fig.update_layout(
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            margin=dict(l=20, r=20, t=60, b=20)
                        )
                        
                        st.plotly_chart(fig)

                    elif viz_type == "combo_bar_line":
                        # Create figure with secondary y-axis
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
    
                        # Add bar chart on primary y-axis
                        fig.add_trace(
                            go.Bar(
                                x=df[params["x_col"]],
                                y=df[params["y_col_bar"]],
                                name=params.get("y_title_bar", params["y_col_bar"]),
                                marker_color='rgb(55, 83, 109)'
                            ),
                            secondary_y=False
                        )
    
                        # Add line chart on secondary y-axis
                        fig.add_trace(
                            go.Scatter(
                                x=df[params["x_col"]],
                                y=df[params["y_col_line"]],
                                name=params.get("y_title_line", params["y_col_line"]),
                                marker_color='rgb(200, 50, 50)',
                                mode='lines+markers'
                            ),
                            secondary_y=True
                        )
    
                        # Add hover data if specified
                        if "tooltip_cols" in params:
                            hovertemplate = "<b>%{x}</b><br><br>"
                            hovertemplate += f"{params.get('y_title_bar', params['y_col_bar'])}: %{{y:,.0f}}<br>"
        
                            for col in params["tooltip_cols"]:
                                if col in df.columns:
                                    fig.update_traces(
                                        customdata=df[params["tooltip_cols"]],
                                        selector=dict(type='bar')
                                    )
                
                                    idx = params["tooltip_cols"].index(col)
                                    hovertemplate += f"{col.replace('_', ' ').title()}: %{{customdata[{idx}]:,.0f}}<br>"
                
                            hovertemplate += "<extra></extra>"
                            fig.update_traces(hovertemplate=hovertemplate, selector=dict(type='bar'))
    
                        # Update layout
                        fig.update_layout(
                            title_text=params["title"],
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            margin=dict(l=20, r=20, t=60, b=20),
                            xaxis=dict(
                                title=params["x_col"].replace('_', ' ').title(),
                                categoryorder='total descending'  # Sorts by bar height
                            )
                        )
    
                        # Update y-axes titles
                        fig.update_yaxes(
                            title_text=params.get("y_title_bar", params["y_col_bar"]), 
                            secondary_y=False
                        )
                        fig.update_yaxes(
                            title_text=params.get("y_title_line", params["y_col_line"]), 
                            secondary_y=True
                        )
    
                        st.plotly_chart(fig)

                    elif viz_type == "dual_axis":
                         # Create a figure with primary Y-axis
                        fig = go.Figure()
    
                        # Add first trace - line for count
                        fig.add_trace(go.Scatter(
                            x=df[params["x_col"]],
                            y=df[params["y_col1"]],
                            name=params["y_col1"].replace('_', ' ').title(),
                            mode='lines+markers',
                            line=dict(color='#1f77b4', width=3),
                            marker=dict(size=8)
                        ))
    
                        # Add second trace - line for value on secondary y-axis
                        fig.add_trace(go.Scatter(
                            x=df[params["x_col"]],
                            y=df[params["y_col2"]],
                            name=params["y_col2"].replace('_', ' ').title(),
                            mode='lines+markers',
                            line=dict(color='#ff7f0e', width=3),
                            marker=dict(size=8),
                            yaxis="y2"
                        ))
    
                        # Set up the layout with a secondary y-axis
                        fig.update_layout(
                            title=params["title"],
                            xaxis_title=params["x_col"].replace('_', ' ').title(),
                            yaxis=dict(
                                title=params.get("y_title1", params["y_col1"].replace('_', ' ').title()),
                                side="left",
                                showgrid=True
                            ),
                            yaxis2=dict(
                                title=params.get("y_title2", params["y_col2"].replace('_', ' ').title()),
                                side="right",
                                showgrid=False,
                                overlaying="y"
                            ),
                            legend=dict(x=0.01, y=0.99, bordercolor="Black", borderwidth=1),
                            hovermode="x unified",
                            template="plotly_white"
                        )
    
                        # Add range slider
                        fig.update_layout(
                            xaxis=dict(
                            rangeslider=dict(visible=True),
                            type="category"
                            )
                        )
    
                        st.plotly_chart(fig, use_container_width=True)

                    elif viz_type == "scatter_categories":
                        # Create scatter plot with categorial coloring
                        fig = px.scatter(
                            df,
                            x=params["x_col"],
                            y=params["y_col"],
                            color=params["color_col"],
                            size=params.get("size_col"),
                            hover_name=params.get("hover_name"),
                            facet_col=params.get("facet_col"),
                            title=params["title"],
                            labels={
                                params["x_col"]: params["x_col"].replace('_', ' ').title(),
                                params["y_col"]: params["y_col"].replace('_', ' ').title(),
                                params["color_col"]: params["color_col"].replace('_', ' ').title()
                            },
                            # Define color scheme for growth categories
                            color_discrete_map={
                                'High Growth': '#1a9850',     # Green
                                'Moderate Growth': '#91cf60', # Light green
                                'Low Growth': '#d9ef8b',      # Yellow-green
                                'Stagnant': '#fee08b',        # Light yellow
                                'Declining': '#d73027'        # Red
                            },
                            # Add quadrant lines
                            category_orders={
                                "growth_category": ["High Growth", "Moderate Growth", "Low Growth", "Stagnant", "Declining"]
                            }
                        )
    
                        # Add reference line at 0% growth
                        fig.add_shape(
                            type="line", 
                            x0=0, y0=0, 
                            x1=0, y1=1, 
                            xref="x", yref="paper",
                            line=dict(color="black", width=1, dash="dash")
                        )
    
                        # Improve layout
                        fig.update_layout(
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            margin=dict(l=20, r=20, t=60, b=20)
                        )
    
                        # Add hover data for additional context
                        fig.update_traces(
                            hovertemplate="<b>%{hovertext}</b><br><br>" +
                                        "Growth: %{x:.2f}%<br>" +
                                        "Current Users: %{y:,.0f}<br>" +
                                        "Absolute Growth: %{marker.size:,.0f}<br>" +
                                        "<extra></extra>"
                        )
    
                        st.plotly_chart(fig)
                    
                    elif viz_type == "group_bar_1":
                        fig = px.bar(
                            df, 
                            x=params["x_col"], 
                            y=params["y_col"], 
                            color=params["color"],
                            barmode="group",
                            title=params["title"]
                        )
                        st.plotly_chart(fig)

                    elif viz_type == "group_bar":
                        # Check if we're dealing with the specific case of registered users vs app opens
                        if "y_cols" in params and isinstance(params["y_cols"], list):
                            # For multiple y columns (like registered_users and app_opens)
                            df_melted = pd.melt(
                                df, 
                                id_vars=["state", "gap"] if "gap" in df.columns else ["state"],
                                value_vars=params["y_cols"],
                                var_name="metric", 
                                value_name="value"
                            )
        
                            fig = px.bar(
                                df_melted,
                                x="state",
                                y="value",
                                color="metric",
                                barmode="group",
                                title=params["title"],
                                labels={"value": "Count", "state": "State", "metric": params.get("color_name", "Metric")}
                            )
        
                            # If gap exists, sort by it
                            if "gap" in df.columns:
                                fig.update_layout(xaxis={'categoryorder':'array', 'categoryarray': df.sort_values("gap", ascending=False)["state"]})
        
                            st.plotly_chart(fig)
                        else:
                            # Standard grouped bar chart with a single y column and a color column
                            fig = px.bar(
                                df, 
                                x=params["x_col"], 
                                y=params["y_col"], 
                                color=params.get("color"),
                                title=params["title"],
                                barmode="group"
                            )
                            st.plotly_chart(fig)

                    elif viz_type == "dual_axis_horizontal_bar":
                        # Create the first horizontal bar trace
                        fig = go.Figure()
    
                        # First trace - primary x-axis
                        fig.add_trace(
                            go.Bar(
                                y=df[params["y_col"]],  # This is your category (quarters)
                                x=df[params["x_col1"]], # First measure (total_count)
                                name=params["x_title1"],
                                orientation='h',        # Makes it horizontal
                                marker=dict(color='blue')
                            )
                        )
    
                        # Create a secondary x-axis
                        fig.add_trace(
                            go.Bar(
                                y=df[params["y_col"]],  # Same categories (quarters)
                                x=df[params["x_col2"]], # Second measure (total_value)
                                name=params["x_title2"],
                                orientation='h',        # Makes it horizontal
                                marker=dict(color='red'),
                                xaxis='x2'              # Use secondary x-axis
                            )
                        )
    
                        # Update the layout to include both axes
                        fig.update_layout(
                            title=params["title"],
                            xaxis=dict(
                                title=params["x_title1"],
                                side="bottom",
                                anchor="y"
                            ),
                            xaxis2=dict(
                                title=params["x_title2"],
                                side="top",
                                anchor="y",
                                overlaying="x"
                            ),
                            barmode='group',  # Group the bars
                            legend=dict(orientation="h", y=1.1)  # Horizontal legend at the top
                        )
    
                        st.plotly_chart(fig)
                    
                    elif viz_type == "lineplot":
                        fig = px.line(
                            df, 
                            x=params["x_col"], 
                            y=params["y_col"], 
                            color=params.get("color"),
                            title=params["title"]
                        )
                        st.plotly_chart(fig)
                    
                    elif viz_type == "pie":
                        fig = px.pie(
                            df, 
                            values=params["values"], 
                            names=params["names"], 
                            title=params["title"]
                        )
                        st.plotly_chart(fig)
                    
                    elif viz_type == "scatter":
                        fig = px.scatter(
                            df, 
                            x=params["x_col"], 
                            y=params["y_col"], 
                            color=params.get("color"),
                            size=params.get("size"),
                            title=params["title"]
                        )
                        st.plotly_chart(fig)
                
                # Option to download the data
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Data as CSV",
                    data=csv,
                    file_name=f"{selected_case}_{query_name}.csv",
                    mime='text/csv',
                )
                
            except Exception as e:
                st.error(f"Error executing query: {e}")
    
    # Display overall business insights
    st.subheader("Business Insights")
    st.markdown(case_studies[selected_case]["insights"])

# Main function
def main():
    # Create connection to MySQL database
    conn = create_db_connection()
    if not conn:
        st.error("Failed to connect to the database. Please check your connection settings.")
        return
    
    # Page header
    display_header()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select a page:", [
        "Dashboard", 
        "Transaction Analysis", 
        "User Analysis",
        "Geographical Analysis", 
        "Business Case Studies"
    ])
    
    # Display selected page
    if page == "Dashboard":
        display_key_metrics(conn)
        
        # Add quick insights
        st.markdown('<div class="sub-header">Quick Insights</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Transaction type distribution
            results = execute_query(conn, """
                SELECT transaction_type, SUM(count) as total
                FROM aggregated_transaction
                GROUP BY transaction_type
                ORDER BY total DESC
            """)
            df = pd.DataFrame(results)
            
            fig = px.pie(
                df,
                values='total',
                names='transaction_type',
                title='Transaction Type Distribution',
                color_discrete_sequence=px.colors.sequential.Purples
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Brand distribution
            results = execute_query(conn, """
                SELECT brand, SUM(device_count) as total
                FROM aggregated_user
                GROUP BY brand
                ORDER BY total DESC
                LIMIT 10
            """)
            df = pd.DataFrame(results)
            
            fig = px.bar(
                df,
                x='brand',
                y='total',
                title='Top 10 Device Brands',
                color='total',
                color_continuous_scale='Purples'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Quarterly trends
        results = execute_query(conn, """
            SELECT year, quarter, SUM(count) as transactions, SUM(amount) as amount
            FROM aggregated_transaction
            GROUP BY year, quarter
            ORDER BY year, quarter
        """)
        df = pd.DataFrame(results)
        df['period'] = df['year'].astype(str) + ' Q' + df['quarter'].astype(str)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['period'],
            y=df['transactions'],
            mode='lines+markers',
            name='Transaction Count',
            line=dict(color='rgb(103, 57, 183)', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=df['period'],
            y=df['amount'],
            mode='lines+markers',
            name='Transaction Amount',
            line=dict(color='rgb(255, 161, 90)', width=3),
            yaxis='y2'
        ))
        fig.update_layout(
            title='Quarterly Transaction Trends',
            xaxis=dict(title='Period'),
            yaxis=dict(title='Transaction Count', side='left'),
            yaxis2=dict(title='Transaction Amount (₹)', side='right', overlaying='y', showgrid=False),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    elif page == "Transaction Analysis":
        transaction_analysis(conn)
        
    elif page == "User Analysis":
        user_analysis(conn)
        
    elif page == "Geographical Analysis":
        geographical_analysis(conn)
        
    elif page == "Business Case Studies":
        business_case_studies(conn)
    
    # Footer
    st.divider()

    # Create a two-column layout for the footer
    footer_col1, footer_col2 = st.columns([3, 1])
    
    with footer_col1:
        st.caption("PhonePe Pulse Data Analysis Dashboard - Created with Streamlit")
    
    with footer_col2:
        st.markdown("**Created by:** BALAJI K")
        # Optional: Add social links or additional info
        st.markdown("[GitHub](https://github.com/Balaji-itz-me) | [LinkedIn](https://www.linkedin.com/in/balaji-k-626613157/)")
    
# Run the application
if __name__ == "__main__":
    main()
