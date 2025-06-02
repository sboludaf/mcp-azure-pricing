# Azure Pricing MCP Server

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project provides a Model Context Protocol (MCP) server that allows you to programmatically query Azure resource pricing. The server provides a structured workflow to retrieve pricing information from the Azure Retail Prices API.

## Features

- Query Azure pricing data through a simple, structured workflow
- Get real-time pricing information from the Azure Retail Prices API
- Navigate through Azure service families, service names, and products
- Calculate monthly costs for Azure resources

## System Requirements

- Python 3.8 or higher
- Internet connection to access the Azure Retail Prices API
- Permission to install Python packages
- No Azure account or credentials required (uses public pricing API)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/azure-pricing-mcp.git
   cd azure-pricing-mcp
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   ```
   * Windows:
     ```bash
     .venv\Scripts\activate
     ```
   * macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The MCP server provides a structured four-step workflow for accessing Azure pricing information:

1. **Get service families** - Retrieve the list of available Azure service families
2. **Get service names** - Get service names within a specific family
3. **Get products** - Get products associated with a service
4. **Calculate monthly costs** - Calculate the monthly cost for a specific product

## Starting the MCP Server

```bash
source .venv/bin/activate  # Activate the virtual environment
python azure_pricing_mcp_server.py
```

The server will start at `http://0.0.0.0:8080` by default.

### Available Endpoints

- `GET /sse`: Server-Sent Events endpoint for MCP communication
- `GET /tools`: Lists the available tools in the MCP server

### MCP Client Configuration

To configure an MCP client to connect to this server, add the following to your `mcp_config.json` file:

```json
"azure-pricing": {
  "serverUrl": "http://localhost:8080/sse"
}
```

This configuration tells the MCP client to connect to the local server on port 8080 using the SSE endpoint. Make sure the URL matches the address and port your server is running on.

## MCP Tools

The server provides four main tools that form a logical workflow for querying Azure pricing:

### 1. list_service_families

**Description**: Lists all available service families in Azure according to Microsoft's official documentation.

**Example usage**:
```python
result = mcp.tool("list_service_families")
service_families = result["service_families"]
print(f"Found {len(service_families)} service families")
```

### 2. get_service_names

**Description**: Gets all unique service names within a specified service family.

**Parameters**:
- `service_family`: The service family to query (e.g., 'Compute', 'Storage')
- `region`: Azure region (default: 'westeurope')
- `max_results`: Maximum number of results to process

**Example usage**:
```python
result = mcp.tool("get_service_names", {
    "service_family": "Compute",
    "region": "westeurope"
})
service_names = result["service_names"]
print(f"Found {len(service_names)} service names in Compute family")
```

### 3. get_products

**Description**: Gets product names from a specific service family.

**Parameters**:
- `service_family`: The service family to query
- `region`: Azure region (default: 'westeurope')
- `type`: Price type (optional, e.g., 'Consumption', 'Reservation')
- `service_name`: Service name to filter by (optional)
- `product_name_contains`: Filter products whose name contains this text (optional)
- `limit`: Maximum number of products to return (optional)

**Example usage**:
```python
result = mcp.tool("get_products", {
    "service_family": "Compute",
    "service_name": "Virtual Machines",
    "product_name_contains": "Standard_D",
    "limit": 10
})
products = result["product_names"]
print(f"Found {len(products)} matching products")
```

### 4. get_monthly_cost

**Description**: Calculates the monthly cost of a specific Azure product.

**Parameters**:
- `product_name`: Exact name of the product (e.g., 'Azure App Service Premium v3 Plan')
- `region`: Azure region (default: 'westeurope')
- `monthly_hours`: Number of hours per month (default: 730)
- `type`: Price type (optional, e.g., 'Consumption')

**Example usage**:
```python
result = mcp.tool("get_monthly_cost", {
    "product_name": "Virtual Machines D2 v3",
    "region": "westeurope",
    "monthly_hours": 730
})
total_cost = result["total_monthly_cost"]
print(f"Monthly cost: {total_cost} {result['currency']}")
```

## Full Example: Pricing Workflow

Here's a complete Python example that demonstrates the four-step workflow to get pricing information:

```python
import requests
import json

# Configure the MCP server URL
MCP_SERVER = "http://localhost:8080/sse"

# Function to call MCP tools
def call_mcp_tool(tool_name, params=None):
    data = {
        "type": "tool_call",
        "id": "client-123",
        "name": tool_name
    }
    if params:
        data["parameters"] = params
    
    response = requests.post(MCP_SERVER, json=data)
    return response.json().get("content", {})

# STEP 1: Get all service families
service_families = call_mcp_tool("list_service_families")
print(f"Available service families: {len(service_families['service_families'])}")
print(service_families['service_families'][:5])  # Print first 5 families

# STEP 2: Get service names for Compute family
service_names = call_mcp_tool("get_service_names", {
    "service_family": "Compute",
    "region": "westeurope"
})
print(f"\nService names in Compute family: {len(service_names['service_names'])}")
print(service_names['service_names'][:5])  # Print first 5 service names

# STEP 3: Get products for Virtual Machines
products = call_mcp_tool("get_products", {
    "service_family": "Compute",
    "service_name": "Virtual Machines",
    "product_name_contains": "Standard_D2",
    "limit": 5
})
print(f"\nMatching products: {len(products['product_names'])}")
print(products['product_names'])  # Print all matching products

# STEP 4: Calculate monthly cost for a specific product
if products['product_names']:
    cost_result = call_mcp_tool("get_monthly_cost", {
        "product_name": products['product_names'][0],
        "region": "westeurope",
        "monthly_hours": 730
    })
    print(f"\nMonthly cost for {products['product_names'][0]}:")
    print(f"Total: {cost_result['total_monthly_cost']} {cost_result['currency']}")
    
    # Print breakdown of costs if available
    if 'products' in cost_result:
        print("\nCost breakdown:")
        for item in cost_result['products'][:3]:  # Show first 3 cost components
            print(f"- {item['meter_name']}: {item['monthly_cost']} {item['currency']}")
```

This example demonstrates how to:
1. List all Azure service families
2. Get service names within the Compute family
3. Find products containing "Standard_D2" in Virtual Machines
4. Calculate the monthly cost for the first matching product

## Error Handling

The MCP server includes a robust error handling system that:

- Provides descriptive error messages when resources cannot be found
- Properly handles Azure API errors
- Logs detailed information for debugging purposes

### Common Error Scenarios

- **Product not found**: When a product name doesn't exist in the specified region
- **Service family not found**: When an invalid service family is specified
- **API rate limits**: When the Azure Retail Prices API rate limits are exceeded
- **Network errors**: When the server cannot connect to the Azure API

## Limitations

* Prices are estimates based on public information from the Azure Retail Prices API
* Does not include all possible discounts, account-specific offers, or additional costs like taxes or support
* The Azure Retail Prices API has rate limits that can affect performance with a high volume of requests
* Prices may vary depending on the region and currency selected
* Not all Azure resources are available in all regions

## Contributing

Contributions are welcome! Here's how you can contribute to this project:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

* Azure Retail Prices API for providing the pricing data
* FastAPI and Starlette for the web server framework
* The Model Context Protocol (MCP) for enabling AI-first interactions

```python
import requests

# Configuración del servidor MCP
MCP_SERVER = "http://127.0.0.1:8080"

# Datos del recurso a consultar
resource = {
    "name": "Servidor Web Básico",
    "service_name": "Virtual Machines",
    "region": "westeurope",
    "sku_name": "Standard_B1ls",
    "quantity": 2,
    "usage_hours_per_month": 730,
    "currency_code": "EUR"
}

# Realizar la consulta
response = requests.post(
    f"{MCP_SERVER}/get_pricing_report",
    json={"resources": [resource]}
)

# Procesar la respuesta
if response.status_code == 200:
    result = response.json()
    print(f"Coste total estimado: {result['total_cost']} {result['currency']}")
    print("Informe detallado:", result['report'])
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Ejemplo 2: Análisis de Múltiples Recursos

```python
import json

# Cargar configuración desde archivo
with open('infrastructure_config.json') as f:
    resources = json.load(f)

# Enviar solicitud al servidor MCP
response = requests.post(
    f"{MCP_SERVER}/get_pricing_report",
    json={"resources": resources}
)

# Guardar el informe en un archivo
if response.status_code == 200:
    result = response.json()
    with open('informe_costes.md', 'w') as f:
        f.write(result['report'])
    print("Informe generado correctamente en 'informe_costes.md'")
else:
    print(f"Error al generar el informe: {response.text}")
```

### Ejemplo 3: Manejo de Errores

```python
try:
    response = requests.post(
        f"{MCP_SERVER}/get_pricing_report",
        json={"resources": [{"invalid": "config"}]},
        timeout=10
    )
    response.raise_for_status()
    print(response.json())
except requests.exceptions.HTTPError as e:
    print(f"Error HTTP: {e}")
except requests.exceptions.RequestException as e:
    print(f"Error de conexión: {e}")
```
