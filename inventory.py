from datetime import datetime, timedelta

class Product:
    def __init__(self, id, name, shelf_life_days):
        self.id = id
        self.name = name
        self.shelf_life_days = shelf_life_days
        self.inventory = 0
        self.sales_history = []

    def add_sale(self, quantity):
        self.sales_history.append((datetime.now(), quantity))
        self.inventory -= quantity

    def get_forecast(self, days):
        # Enhanced forecasting logic
        if not self.sales_history:
            return 0
            
        # Get sales data for the last 30 days if available
        recent_sales = self.sales_history[-30:]
        if not recent_sales:
            return 0
            
        # Calculate daily average sales
        total_sales = sum(s[1] for s in recent_sales)
        avg_sales = total_sales / len(recent_sales)
        
        # Consider trend (increase/decrease in recent sales)
        if len(recent_sales) >= 14:  # Need at least 2 weeks of data
            first_half = sum(s[1] for s in recent_sales[:len(recent_sales)//2])
            second_half = sum(s[1] for s in recent_sales[len(recent_sales)//2:])
            trend_factor = second_half / first_half if first_half > 0 else 1
            
            # Adjust forecast based on trend
            avg_sales *= trend_factor
            
        # Add buffer based on shelf life
        buffer_factor = 1.1  # 10% buffer
        if days > self.shelf_life_days:
            buffer_factor = 1.2  # Increase buffer for longer periods
            
        # Calculate forecast for requested days
        forecast = int(avg_sales * days * buffer_factor)
        
        return max(1, forecast)  # Ensure at least 1 unit is forecasted

    def get_recommended_order(self, days):
        forecast = self.get_forecast(days)
        
        # Consider current inventory and shelf life
        current_stock_days = self.inventory / (forecast / days) if forecast > 0 else 0
        
        # If current stock will last longer than requested period, no order needed
        if current_stock_days >= days:
            return 0
            
        # Calculate recommended order considering shelf life
        recommended_order = forecast - self.inventory
        
        # Ensure we don't order too much that would exceed shelf life
        max_order = forecast * (self.shelf_life_days / days)
        recommended_order = min(recommended_order, max_order)
        
        return max(0, int(recommended_order))

# Example usage
if __name__ == "__main__":
    # Create a product
    apple = Product("A1", "Apple", 7)
    
    # Add some sales
    apple.add_sale(10)
    apple.add_sale(15)
    apple.add_sale(12)
    
    # Get forecast for next 7 days
    forecast = apple.get_forecast(7)
    recommended_order = apple.get_recommended_order(7)
    
    print(f"Forecast for next 7 days: {forecast} units")
    print(f"Recommended order: {recommended_order} units")
