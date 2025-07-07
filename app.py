import streamlit as st
from inventory import Product
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configure Streamlit page
st.set_page_config(
    page_title="AI Inventory Management",
    layout="wide"
)

# Initialize session state
if 'products' not in st.session_state:
    st.session_state.products = {}

# Helper functions
def add_product(product_id, name, shelf_life):
    if product_id in st.session_state.products:
        st.error(f"Product with ID {product_id} already exists!")
        return False
    st.session_state.products[product_id] = Product(product_id, name, shelf_life)
    st.success(f"Product {name} added successfully!")
    return True

def record_sale(product_id, quantity):
    if product_id not in st.session_state.products:
        st.error(f"Product {product_id} not found!")
        return False
    st.session_state.products[product_id].add_sale(quantity)
    st.success(f"Sale recorded for {quantity} units of {st.session_state.products[product_id].name}")
    return True

def get_forecast(product_id, days):
    if product_id not in st.session_state.products:
        st.error(f"Product {product_id} not found!")
        return None
    
    product = st.session_state.products[product_id]
    forecast = product.get_forecast(days)
    recommended_order = product.get_recommended_order(days)
    
    return {
        'forecast': forecast,
        'recommended_order': recommended_order,
        'current_inventory': product.inventory,
        'shelf_life': product.shelf_life_days
    }

def get_sales_history(product_id):
    if product_id not in st.session_state.products:
        return []
    return st.session_state.products[product_id].sales_history

# Streamlit app
def main():
    # Main title and description
    st.title("AI-Powered Inventory Management System")
    st.markdown(
        """
        Manage your inventory efficiently with AI-powered forecasting.
        Track sales, predict future demand, and reduce waste.
        """
    )
    
    # Sidebar
    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Add Product", "Record Sale", "Forecast"])
    
    # Main content
    if page == "Dashboard":
        st.header("Dashboard")
        
        if not st.session_state.products:
            st.warning("No products added yet!")
            return
            
        # Show product summary
        st.subheader("Product Summary")
        summary_data = []
        for product in st.session_state.products.values():
            summary_data.append({
                'Product': product.name,
                'Current Inventory': product.inventory,
                'Shelf Life (days)': product.shelf_life_days,
                'Recent Sales': sum(s[1] for s in product.sales_history[-7:])
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df)
        
        # Show sales history chart
        if any(product.sales_history for product in st.session_state.products.values()):
            st.subheader("Sales History")
            all_sales = []
            for product in st.session_state.products.values():
                for date, quantity in product.sales_history:
                    all_sales.append({
                        'Date': date,
                        'Quantity': quantity,
                        'Product': product.name
                    })
            
            sales_df = pd.DataFrame(all_sales)
            
            # Create a more detailed chart
            fig = go.Figure()
            
            # Add traces for each product
            for product in st.session_state.products.values():
                product_sales = sales_df[sales_df['Product'] == product.name]
                if not product_sales.empty:
                    fig.add_trace(go.Scatter(
                        x=product_sales['Date'],
                        y=product_sales['Quantity'],
                        name=product.name,
                        mode='lines+markers',
                        line=dict(width=2),
                        marker=dict(size=8)
                    ))
            
            # Update layout
            fig.update_layout(
                title='Sales History by Product',
                xaxis_title='Date',
                yaxis_title='Quantity Sold',
                legend_title='Products',
                hovermode='x unified',
                margin=dict(l=50, r=50, t=50, b=50),
                height=500
            )
            
            # Add range slider
            fig.update_layout(
                xaxis=dict(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1,
                                 label="1m",
                                 step="month",
                                 stepmode="backward"),
                            dict(count=6,
                                 label="6m",
                                 step="month",
                                 stepmode="backward"),
                            dict(count=1,
                                 label="YTD",
                                 step="year",
                                 stepmode="todate"),
                            dict(count=1,
                                 label="1y",
                                 step="year",
                                 stepmode="backward"),
                            dict(step="all")
                        ])
                    ),
                    rangeslider=dict(
                        visible=True
                    ),
                    type="date"
                )
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
    elif page == "Add Product":
        st.header("Add New Product")
        
        with st.form("add_product_form"):
            product_id = st.text_input("Product ID", "P1")
            name = st.text_input("Product Name", "Apple")
            shelf_life = st.number_input("Shelf Life (days)", min_value=1, value=7)
            
            if st.form_submit_button("Add Product"):
                add_product(product_id, name, shelf_life)
                
    elif page == "Record Sale":
        st.header("Record Sale")
        
        if not st.session_state.products:
            st.warning("No products added yet!")
            return
            
        with st.form("record_sale_form"):
            product_id = st.selectbox("Select Product", list(st.session_state.products.keys()))
            quantity = st.number_input("Quantity Sold", min_value=1, value=1)
            
            if st.form_submit_button("Record Sale"):
                record_sale(product_id, quantity)
                
    elif page == "Forecast":
        st.header("Generate Forecast")
        
        if not st.session_state.products:
            st.warning("No products added yet!")
            return
            
        with st.form("forecast_form"):
            product_id = st.selectbox("Select Product", list(st.session_state.products.keys()))
            days = st.number_input("Days to Forecast", min_value=1, value=7)
            
            if st.form_submit_button("Generate Forecast"):
                result = get_forecast(product_id, days)
                if result:
                    st.subheader("Forecast Results")
                    st.write(f"Predicted sales for next {days} days: {result['forecast']} units")
                    st.write(f"Current inventory: {result['current_inventory']} units")
                    st.write(f"Recommended order quantity: {result['recommended_order']} units")
                    st.write(f"Product shelf life: {result['shelf_life']} days")
                    
                    # Show detailed sales history for this product
                    sales_history = get_sales_history(product_id)
                    if sales_history:
                        sales_df = pd.DataFrame(sales_history, columns=['Date', 'Quantity'])
                        
                        # Create a detailed chart
                        fig = go.Figure()
                        
                        # Add line and markers
                        fig.add_trace(go.Scatter(
                            x=sales_df['Date'],
                            y=sales_df['Quantity'],
                            mode='lines+markers',
                            line=dict(width=2),
                            marker=dict(size=8)
                        ))
                        
                        # Add trend line
                        if len(sales_df) > 2:
                            trend = px.scatter(sales_df, x='Date', y='Quantity', trendline='ols').data[1]
                            fig.add_trace(
                                go.Scatter(
                                    x=trend['x'],
                                    y=trend['y'],
                                    name='Trend Line',
                                    line=dict(color='red', dash='dash')
                                )
                            )
                        
                        # Update layout
                        fig.update_layout(
                            title=f'Sales History for {st.session_state.products[product_id].name}',
                            xaxis_title='Date',
                            yaxis_title='Quantity Sold',
                            hovermode='x unified',
                            margin=dict(l=50, r=50, t=50, b=50),
                            height=400
                        )
                        
                        # Add range slider
                        fig.update_layout(
                            xaxis=dict(
                                rangeslider=dict(
                                    visible=True
                                ),
                                type="date"
                            )
                        )
                        
                        # Display the chart
                        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
