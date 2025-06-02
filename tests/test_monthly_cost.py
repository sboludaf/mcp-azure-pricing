#!/usr/bin/env python3
import requests
import json

def calculate_monthly_cost(product_name, region="westeurope", monthly_hours=730, type="Consumption"):
    """
    Calcula el coste mensual de un producto específico de Azure.
    
    Args:
        product_name: Nombre exacto del producto
        region: Región de Azure
        monthly_hours: Número de horas al mes (por defecto 730)
        type: Tipo de precio
    """
    # Configuración de la API
    AZURE_PRICE_API = "https://prices.azure.com/api/retail/prices"
    API_VERSION = "2023-01-01-preview"
    
    # Construir la consulta
    filter_params = f"productName eq '{product_name}' and armRegionName eq '{region}'"
    if type:
        filter_params += f" and type eq '{type}'"
    
    params = {
        'api-version': API_VERSION,
        '$filter': filter_params
    }
    
    print(f"Consultando API para: {product_name} en {region}")
    print(f"Filtro: {filter_params}")
    
    try:
        # Realizar la petición a la API
        response = requests.get(AZURE_PRICE_API, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Extraer los items relevantes
        items = result.get("Items", [])
        
        if len(items) == 0:
            print(f"No se encontraron productos para: {product_name}")
            return
        
        print(f"Se encontraron {len(items)} variantes del producto.")
        total_monthly_cost = 0
        
        # Mostrar información para cada variante
        for i, item in enumerate(items):
            sku_name = item.get("skuName", "")
            meter_name = item.get("meterName", "")
            retail_price = item.get("retailPrice", 0)
            currency = item.get("currencyCode", "USD")
            unit_of_measure = item.get("unitOfMeasure", "")
            
            # Calcular coste mensual
            monthly_cost = retail_price * monthly_hours if "Hour" in unit_of_measure else retail_price
            total_monthly_cost += monthly_cost
            
            print(f"\nVariante {i+1}:")
            print(f"  SKU: {sku_name}")
            print(f"  Meter: {meter_name}")
            print(f"  Precio por unidad: {retail_price} {currency} por {unit_of_measure}")
            print(f"  Coste mensual estimado: {monthly_cost:.2f} {currency}")
        
        print(f"\nCoste mensual total estimado: {total_monthly_cost:.2f} {currency}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API: {str(e)}")


if __name__ == "__main__":
    import sys
    
    # Valores por defecto
    product_name = "Azure App Service Premium v3 Plan"
    region = "westeurope"
    monthly_hours = 730
    type = "Consumption"
    
    # Procesar argumentos de línea de comandos si se proporcionan
    if len(sys.argv) > 1:
        product_name = sys.argv[1]
    if len(sys.argv) > 2:
        region = sys.argv[2]
    if len(sys.argv) > 3:
        monthly_hours = int(sys.argv[3])
    if len(sys.argv) > 4:
        type = sys.argv[4]
    
    # Calcular el coste mensual
    calculate_monthly_cost(product_name, region, monthly_hours, type)
