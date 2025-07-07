from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import plotly.express as px
import plotly.graph_objects as go
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Inventory Management System")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Product(BaseModel):
    product_id: str
    name: str
    category: str
    unit_cost: float
    shelf_life_days: int

class SalesData(BaseModel):
    product_id: str
    date: str
    quantity: int
    revenue: float

class WeatherData(BaseModel):
    date: str
    temperature: float
    precipitation: float
    humidity: float

class ForecastRequest(BaseModel):
    product_id: str
    start_date: str
    end_date: str
    holidays: List[str]

class ForecastResponse(BaseModel):
    dates: List[str]
    predicted_sales: List[float]
    recommended_order: List[int]
    waste_risk: List[float]

# In-memory storage (replace with database in production)
class InventoryDB:
    def __init__(self):
        self.products = []
        self.sales = []
        self.weather = []
        self.forecasts = {}

    def add_product(self, product: Product):
        self.products.append(product)
        return product

    def add_sales(self, sales: SalesData):
        self.sales.append(sales)
        return sales

    def add_weather(self, weather: WeatherData):
        self.weather.append(weather)
        return weather

db = InventoryDB()

# ML Model
model = RandomForestRegressor(n_estimators=100, random_state=42)

@app.post("/products/", response_model=Product)
async def add_product(product: Product):
    return db.add_product(product)

@app.post("/sales/", response_model=SalesData)
async def add_sales_data(sales: SalesData):
    return db.add_sales(sales)

@app.post("/weather/", response_model=WeatherData)
async def add_weather_data(weather: WeatherData):
    return db.add_weather(weather)

@app.post("/forecast/", response_model=ForecastResponse)
async def get_forecast(request: ForecastRequest):
    try:
        # Convert dates to datetime
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        
        # Prepare historical data
        historical_sales = pd.DataFrame(db.sales)
        historical_weather = pd.DataFrame(db.weather)
        
        # Merge data
        merged_data = pd.merge(historical_sales, historical_weather, on='date', how='left')
        
        # Feature engineering
        merged_data['date'] = pd.to_datetime(merged_data['date'])
        merged_data['day_of_week'] = merged_data['date'].dt.dayofweek
        merged_data['month'] = merged_data['date'].dt.month
        merged_data['is_holiday'] = merged_data['date'].isin(request.holidays).astype(int)
        
        # Train model
        X = merged_data[['temperature', 'precipitation', 'humidity', 'day_of_week', 'month', 'is_holiday']]
        y = merged_data['quantity']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model.fit(X_train, y_train)
        
        # Generate predictions
        dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
        dates_str = [d.strftime("%Y-%m-%d") for d in dates]
        
        # Create future features
        future_features = pd.DataFrame({
            'date': dates_str,
            'day_of_week': [d.weekday() for d in dates],
            'month': [d.month for d in dates],
            'is_holiday': [1 if d.strftime("%Y-%m-%d") in request.holidays else 0 for d in dates]
        })
        
        # Predict
        predictions = model.predict(future_features)
        
        # Calculate recommended order
        recommended_order = []
        waste_risk = []
        for pred in predictions:
            product = next((p for p in db.products if p.product_id == request.product_id), None)
            if product:
                # Calculate recommended order based on predicted sales and shelf life
                recommended = max(0, int(pred * 1.1))  # Add 10% buffer
                recommended_order.append(recommended)
                
                # Calculate waste risk
                waste = max(0, recommended - pred)
                waste_risk.append(waste / recommended if recommended > 0 else 0)
            else:
                recommended_order.append(0)
                waste_risk.append(0)
                
        return ForecastResponse(
            dates=dates_str,
            predicted_sales=predictions.tolist(),
            recommended_order=recommended_order,
            waste_risk=waste_risk
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/", response_model=dict)
async def get_dashboard():
    try:
        # Generate dashboard metrics
        total_sales = sum(s.quantity for s in db.sales)
        total_revenue = sum(s.revenue for s in db.sales)
        
        # Generate sales trend plot
        sales_df = pd.DataFrame(db.sales)
        sales_trend = px.line(
            sales_df, 
            x='date', 
            y='quantity',
            title='Sales Trend'
        )
        
        # Generate waste risk plot
        waste_data = []
        for product in db.products:
            forecast = db.forecasts.get(product.product_id)
            if forecast:
                waste_data.append({
                    'product': product.name,
                    'waste_risk': sum(forecast['waste_risk']) / len(forecast['waste_risk'])
                })
        
        waste_df = pd.DataFrame(waste_data)
        waste_risk_plot = px.bar(
            waste_df,
            x='product',
            y='waste_risk',
            title='Average Waste Risk by Product'
        )
        
        return {
            "total_sales": total_sales,
            "total_revenue": total_revenue,
            "sales_trend": sales_trend.to_html(full_html=False),
            "waste_risk_plot": waste_risk_plot.to_html(full_html=False)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
