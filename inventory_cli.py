from inventory import Product

def main():
    products = {}
    
    while True:
        print("\nInventory Management System")
        print("1. Add Product")
        print("2. Record Sale")
        print("3. Get Forecast")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            id = input("Enter product ID: ")
            name = input("Enter product name: ")
            shelf_life = int(input("Enter shelf life (days): "))
            products[id] = Product(id, name, shelf_life)
            print(f"Product {name} added successfully!")
            
        elif choice == "2":
            id = input("Enter product ID: ")
            if id in products:
                quantity = int(input("Enter quantity sold: "))
                products[id].add_sale(quantity)
                print(f"Sale recorded for {quantity} units of {products[id].name}")
            else:
                print("Product not found!")
                
        elif choice == "3":
            id = input("Enter product ID: ")
            if id in products:
                days = int(input("Enter number of days to forecast: "))
                product = products[id]
                forecast = product.get_forecast(days)
                recommended_order = product.get_recommended_order(days)
                print(f"\nForecast for next {days} days:")
                print(f"- Predicted sales: {forecast} units")
                print(f"- Recommended order: {recommended_order} units")
            else:
                print("Product not found!")
                
        elif choice == "4":
            print("Exiting...")
            break
            
        else:
            print("Invalid choice! Please try again.")

if __name__ == "__main__":
    main()
