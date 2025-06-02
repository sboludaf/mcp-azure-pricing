#!/usr/bin/env python3
import requests
import json
import sys

def test_api_call(service_family, region="westeurope", type="", service_name=""):
    """
    Prueba directa de la API de Azure Retail Prices con los parámetros especificados.
    """
    print(f"Consultando API para familia: {service_family}, región: {region}, tipo: {type}, servicio: {service_name}")
    
    # Configuración de la API
    AZURE_PRICE_API = "https://prices.azure.com/api/retail/prices"
    API_VERSION = "2023-01-01-preview"
    
    # Construir los parámetros de la consulta
    filter_params = f"serviceFamily eq '{service_family}'"
    if region:
        filter_params += f" and armRegionName eq '{region}'"
    if type:
        filter_params += f" and type eq '{type}'"
    if service_name:
        filter_params += f" and serviceName eq '{service_name}'"
    
    params = {
        'api-version': API_VERSION,
        '$filter': filter_params,
        '$top': 10  # Limitamos a 10 resultados para la prueba
    }
    
    print(f"Filtro: {filter_params}")
    
    try:
        # Realizar la petición a la API
        response = requests.get(AZURE_PRICE_API, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Mostrar información sobre los resultados
        items = result.get("Items", [])
        print(f"Se encontraron {len(items)} productos")
        
        # Mostrar los primeros 3 resultados
        for i, item in enumerate(items[:3]):
            print(f"\nProducto {i+1}:")
            print(f"  Nombre: {item.get('productName', 'N/A')}")
            print(f"  Servicio: {item.get('serviceName', 'N/A')}")
            print(f"  SKU: {item.get('skuName', 'N/A')}")
            print(f"  Región: {item.get('armRegionName', 'N/A')}")
            print(f"  Precio: {item.get('retailPrice', 'N/A')} {item.get('currencyCode', '')}")
        
        return result
    
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API: {str(e)}")
        return None

if __name__ == "__main__":
    # Procesar argumentos de línea de comandos
    service_family = sys.argv[1] if len(sys.argv) > 1 else "Networking"
    region = sys.argv[2] if len(sys.argv) > 2 else "westeurope"
    service_name = sys.argv[3] if len(sys.argv) > 3 else "Virtual Network"
    type_param = sys.argv[4] if len(sys.argv) > 4 else ""
    
    # Llamar a la función de prueba
    test_api_call(service_family, region, type_param, service_name)
