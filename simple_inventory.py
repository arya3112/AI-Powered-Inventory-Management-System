from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor

app = FastAPI(title="Simple Inventory System")

# Simple in-memory storage
class Product(BaseModel):
    id: str
    name: str
    shelf_life_days: int

class Sales(BaseModel):
    product_id: str
    date: str
    quantity: int

class ForecastRequest(BaseModel):
    product_id: str
    days: int

class ForecastResponse(BaseModel):
    dates: List[str]
    predicted_sales: List[int]
    recommended_order: List[int]

# In-memory storage
data = {
    "products": [],
    "sales": []
}

# Simple ML model
model = RandomForestRegressor(n_estimators=50, random_state=42)

@app.post("/add-product/")
async def add_product(product: Product):
    data["products"].append(product)
    return {"message": "Product added successfully"}

@app.post("/add-sales/")
async def add_sales(sales: Sales):
    data["sales"].append(sales)
    return {"message": "Sales data added successfully"}

@app.post("/forecast/")
async def forecast_sales(request: ForecastRequest):
    try:
        # Prepare data
        sales_df = pd.DataFrame(data["sales"])
        sales_df["date"] = pd.to_datetime(sales_df["date"])
        sales_df["day_of_week"] = sales_df["date"].dt.dayofweek
        
        # Train model
        X = sales_df["day_of_week"].values.reshape(-1, 1)
        y = sales_df["quantity"]
        model.fit(X, y)
        
        # Generate predictions
        today = datetime.now()
        dates = [today + timedelta(days=i) for i in range(request.days)]
        dates_str = [d.strftime("%Y-%m-%d") for d in dates]
        
        # Create features for prediction
        future_features = pd.DataFrame({
            "day_of_week": [d.weekday() for d in dates]
        })
        
        # Predict
        predictions = model.predict(future_features).round().astype(int)
        
        # Calculate recommended order (simple buffer)
        recommended_order = [(p + 10) for p in predictions]  # Add 10 units buffer
        
        return ForecastResponse(
            dates=dates_str,
            predicted_sales=predictions.tolist(),
            recommended_order=recommended_order
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
