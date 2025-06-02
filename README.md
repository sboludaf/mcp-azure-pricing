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
   git clone https://github.com/sboludaf/mcp-azure-pricing.git
   cd mcp-azure-pricing
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

### 2. get_service_names

**Description**: Gets all unique service names within a specified service family.

**Parameters**:
- `service_family`: The service family to query (e.g., 'Compute', 'Storage')
- `region`: Azure region (default: 'westeurope')
- `max_results`: Maximum number of results to process

### 3. get_products

**Description**: Gets product names from a specific service family.

**Parameters**:
- `service_family`: The service family to query
- `region`: Azure region (default: 'westeurope')
- `type`: Price type (optional, e.g., 'Consumption', 'Reservation')
- `service_name`: Service name to filter by (optional)
- `product_name_contains`: Filter products whose name contains this text (optional)
- `limit`: Maximum number of products to return (optional)

### 4. get_monthly_cost

**Description**: Calculates the monthly cost of a specific Azure product.

**Parameters**:
- `product_name`: Exact name of the product (e.g., 'Azure App Service Premium v3 Plan')
- `region`: Azure region (default: 'westeurope')
- `monthly_hours`: Number of hours per month (default: 730)
- `type`: Price type (optional, e.g., 'Consumption')

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