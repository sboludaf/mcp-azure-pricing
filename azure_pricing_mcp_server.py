import logging
import logging.config
import uvicorn
import requests
from typing import List, Dict, Any

# MCP imports
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from starlette.endpoints import HTTPEndpoint

# Import configuration
from config import settings, logging_config

# Configure logging
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

# Configure debug mode based on settings
if settings.MCP_DEBUG:
    logger.setLevel(logging.DEBUG)
    logger.debug("DEBUG mode activated")

def log(message: str, level: str = "info"):
    """Helper function for consistent logging."""
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message)

# Create MCP server
mcp = FastMCP("Azure Pricing MCP")

@mcp.tool(description="""
    [STEP 1] List all available service families in Azure.
    
    This endpoint returns the official list of service families available in Azure
    according to Microsoft's official documentation.
    
    This should be the FIRST STEP in the pricing query workflow:
    1. First, get the list of service families with list_service_families
    2. Then, get service names with get_service_names
    3. Next, get products with get_products
    4. Finally, calculate monthly costs with get_monthly_cost
    
    Official reference: https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices#supported-servicefamily-values
    
    Returns:
        dict: Dictionary with the list of service families and the total number of items
    """)
def list_service_families():
    # Official list of service families according to Microsoft documentation
    official_service_families = [
        "Analytics",
        "Azure Arc",
        "Azure Communication Services",
        "Azure Security",
        "Azure Stack",
        "Compute",
        "Containers",
        "Data",
        "Databases",
        "Developer Tools",
        "Dynamics",
        "Gaming",
        "Integration",
        "Internet of Things",
        "Management and Governance",
        "Microsoft Syntex",
        "Mixed Reality",
        "Networking",
        "Other",
        "Power Platform",
        "Quantum Computing",
        "Security",
        "Storage",
        "Telecommunications",
        "Web",
        "Windows Virtual Desktop"
    ]
    
    log("Returning official list of Azure service families")
    return {
        "service_families": official_service_families,
        "count": len(official_service_families),
        "source": "official_documentation",
        "reference": "https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices#supported-servicefamily-values"
    }

@mcp.tool(description="""
    [STEP 3] Get product names from a specific service family.
    
    This endpoint returns a list of product names (productName) that belong to
    the specified service family, without including all the complete details of each product.
    
    This is the THIRD STEP in the pricing query workflow:
    1. First, get the list of service families with list_service_families
    2. Then, get service names with get_service_names
    3. Now, use this tool to get specific products
    4. Finally, calculate monthly costs with get_monthly_cost
    
    Args:
        service_family (str): The service family to query (e.g. 'Compute', 'Storage', 'Networking')
        region (str): Azure region (default: 'westeurope')
        type (str, optional): Price type (e.g. 'Consumption', 'Reservation')
        service_name (str, optional): Service name to filter by (e.g. 'Virtual Machines', 'Storage Accounts')
        product_name_contains (str, optional): Filter products whose name contains this text (e.g. 'Redis', 'SQL')
        limit (int, optional): Maximum number of products to return (default: 0, which means no limit)
    """)
def get_products(service_family, region="westeurope", type="", service_name="", product_name_contains="", limit=0):
    # Ensure parameters are of the correct type
    service_family = str(service_family)
    region = str(region)
    type = str(type)
    service_name = str(service_name)
    product_name_contains = str(product_name_contains)
    limit = int(limit) if not isinstance(limit, int) else limit
    
    log_message = f"Getting products for family {service_family} in region {region}"
    if service_name:
        log_message += f", filtered by service '{service_name}'"
    if product_name_contains:
        log_message += f", filtered by products containing '{product_name_contains}'"
    if limit > 0:
        log_message += f", limited to {limit} results"
    log(log_message)
    
    # API Configuration
    AZURE_PRICE_API = "https://prices.azure.com/api/retail/prices"
    API_VERSION = "2023-01-01-preview"
    
    # Build query parameters
    filter_params = f"serviceFamily eq '{service_family}'"
    if region:
        filter_params += f" and armRegionName eq '{region}'"
    if type:
        filter_params += f" and type eq '{type}'"
    if service_name:
        filter_params += f" and serviceName eq '{service_name}'"
    
    params = {
        'api-version': API_VERSION,
        '$filter': filter_params
    }
    
    # We don't set a limit to get all available results
    # The API can automatically paginate if there are many results
    
    try:
        # Make the request to the Azure API
        log(f"Querying API with filter: {filter_params}")
        response = requests.get(AZURE_PRICE_API, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Check if the response is empty
        items = result.get("Items", [])
        if len(items) == 0:
            log(f"No products found for the specified criteria: {filter_params}", "warning")
            return {
                "product_names": [],
                "count": 0,
                "total_products": 0,
                "total_products_processed": 0,
                "was_limited": False,
                "limit_applied": limit if limit > 0 else None,
                "status": "success",
                "message": f"No products found for family '{service_family}' with the applied filters.",
                "filter_applied": filter_params,
                "product_name_filter": product_name_contains if product_name_contains else None
            }
        
        # Check if there are more pages
        next_page_link = result.get("NextPageLink")
        all_items = items
        page_count = 1
        max_pages = 3  # Reasonable page limit to avoid too many calls
        
        # Continue getting more pages if there is a NextPageLink
        while next_page_link and page_count < max_pages:
            log(f"Getting additional page {page_count + 1}: {next_page_link}")
            try:
                next_response = requests.get(next_page_link)
                next_response.raise_for_status()
                next_result = next_response.json()
                
                # Add items from the next page
                next_items = next_result.get("Items", [])
                all_items.extend(next_items)
                
                # Update for the next iteration
                next_page_link = next_result.get("NextPageLink")
                page_count += 1
            except Exception as e:
                log(f"Error getting additional page: {str(e)}", "error")
                break
        
        # Filter by product name if specified
        if product_name_contains:
            filtered_items = [item for item in all_items if product_name_contains.lower() in item.get("productName", "").lower()]
            log(f"Filtering: from {len(all_items)} products, {len(filtered_items)} contain '{product_name_contains}'")
            all_items = filtered_items
        
        # Extract product names
        product_names = list(set(item.get("productName", "") for item in all_items if item.get("productName")))
        product_names.sort()  # Sort alphabetically
        
        # Limit results if specified
        if limit > 0 and len(product_names) > limit:
            limited_product_names = product_names[:limit]
            log(f"Limiting results: showing {len(limited_product_names)} of {len(product_names)} total products")
            was_limited = True
        else:
            limited_product_names = product_names
            was_limited = False
        
        # Return product names
        log(f"Retrieved {len(limited_product_names)} unique product names from {len(all_items)} total products across {page_count} pages")
        return {
            "product_names": limited_product_names,
            "count": len(limited_product_names),
            "total_products": len(product_names),
            "total_products_processed": len(all_items),
            "was_limited": was_limited,
            "limit_applied": limit if limit > 0 else None,
            "status": "success",
            "filter_applied": filter_params,
            "product_name_filter": product_name_contains if product_name_contains else None
        }
        
    except requests.exceptions.RequestException as e:
        log(f"Error connecting to Azure API: {str(e)}", "error")
        return {
            "error": f"Error connecting to API: {str(e)}",
            "status": "error"
        }

@mcp.tool(description="""
    [STEP 2] Get all unique service names within a service family.
    
    This endpoint returns a list of all unique service names that belong
    to the specified service family. For the 'Compute' family, which has many results,
    an optimized strategy is used to limit overhead.
    
    This is the SECOND STEP in the pricing query workflow:
    1. First, get the list of service families with list_service_families
    2. Then, use this tool to get the service names within that family
    3. Next, get specific products with get_products
    4. Finally, calculate monthly costs with get_monthly_cost
    
    Args:
        service_family (str): The service family to query (e.g. 'Compute', 'Storage', 'Networking')
        region (str): Azure region (default: 'westeurope')
        max_results (int): Maximum number of results to process (for 'Compute')
    """)
def get_service_names(service_family, region="westeurope", max_results=500):
    # Ensure parameters are of the correct type
    service_family = str(service_family)
    region = str(region)
    max_results = int(max_results)
    
    log(f"Getting unique service names for family {service_family} in region {region}")
    
    # Special handling for 'Compute' which has many results
    if service_family.lower() == "compute":
        log(f"Using optimized approach for Compute family, limiting to {max_results} results")
        
        # API Configuration
        AZURE_PRICE_API = "https://prices.azure.com/api/retail/prices"
        API_VERSION = "2023-01-01-preview"
        
        # Build query parameters with a specific top to optimize
        filter_params = f"serviceFamily eq '{service_family}'"
        if region:
            filter_params += f" and armRegionName eq '{region}'"
        
        params = {
            'api-version': API_VERSION,
            '$filter': filter_params,
            '$top': min(int(max_results), 1000)  # Maximum 1000 allowed by the API
        }
        
        try:
            # Make the request to the Azure API
            log(f"Querying API with optimized filter: {filter_params}")
            response = requests.get(AZURE_PRICE_API, params=params)
            response.raise_for_status()
            result = response.json()
            
            # Check if the response is empty
            items = result.get("Items", [])
            if len(items) == 0:
                log(f"No products found for the specified criteria: {filter_params}", "warning")
                return {
                    "service_family": service_family,
                    "service_names": [],
                    "count": 0,
                    "is_complete": True,
                    "status": "success",
                    "message": f"No products found for family '{service_family}' in region '{region}'.",
                    "filter_applied": filter_params
                }
            
            # Extract unique service names
            service_names = list(set(item.get("serviceName", "") for item in items if item.get("serviceName")))
            service_names.sort()  # Sort alphabetically
            
            return {
                "service_family": service_family,
                "service_names": service_names,
                "count": len(service_names),
                "is_complete": False,  # Indicate that it might not be the complete list
                "region": region,
                "note": f"Optimized results for Compute family, limited to {len(items)} products"
            }
            
        except requests.exceptions.RequestException as e:
            log(f"Error connecting to Azure API: {str(e)}", "error")
            return {
                "error": f"Error connecting to API: {str(e)}",
                "status": "error"
            }
    
    # For other families, we get all products and extract service names
    try:
        # Use existing get_products function
        products_result = get_products(service_family, region)
        
        # Check if response is empty or has an error
        if products_result.get("status") == "error" or products_result.get("count", 0) == 0:
            log(f"No products found for family {service_family}", "warning")
            return {
                "service_family": service_family,
                "service_names": [],
                "count": 0,
                "is_complete": True,
                "status": "success",
                "message": products_result.get("message", f"No products found for family '{service_family}' in region '{region}'."),
                "filter_applied": products_result.get("filter_applied", "")
            }
        
        # Since get_products now returns only product names, we need to make another call
        # to the API to get the service names.
        log(f"Querying API to get service names for {service_family}")
        
        # API Configuration
        AZURE_PRICE_API = "https://prices.azure.com/api/retail/prices"
        API_VERSION = "2023-01-01-preview"
        
        # API Configuration
        filter_params = f"serviceFamily eq '{service_family}'"
        if region:
            filter_params += f" and armRegionName eq '{region}'"
        
        params = {
            'api-version': API_VERSION,
            '$filter': filter_params,
            '$top': 100  # Limit to 100 results to get a reasonable sample
        }
        
        try:
            # Make the request to the Azure API
            log(f"Querying API with filter: {filter_params}")
            response = requests.get(AZURE_PRICE_API, params=params)
            response.raise_for_status()
            result = response.json()
            
            # Extract unique service names
            items = result.get("Items", [])
            service_names = list(set(item.get("serviceName", "") for item in items if item.get("serviceName")))
            service_names.sort()  # Sort alphabetically
        except Exception as e:
            log(f"Error getting service names: {str(e)}", "error")
            return {
                "service_family": service_family,
                "service_names": [],
                "count": 0,
                "is_complete": True,
                "status": "error",
                "message": f"Error getting service names: {str(e)}"
            }
        
        return {
            "service_family": service_family,
            "service_names": service_names,
            "count": len(service_names),
            "is_complete": products_result.get("NextPageLink") is None,  # Indicate if it's the complete list
            "region": region,
            "processed_items": len(items)
        }
        
    except Exception as e:
        log(f"Error getting service names: {str(e)}", "error")
        return {
            "error": f"Error getting service names: {str(e)}",
            "status": "error"
        }

@mcp.tool(description="""
    [STEP 4] Calculate the monthly cost of a specific Azure product.
    
    This endpoint queries the Azure Retail Prices API to get the hourly price
    of a specific product and calculates its monthly cost based on the number of hours.
    
    This is the FINAL STEP in the pricing query workflow:
    1. First, get the list of service families with list_service_families
    2. Then, get service names with get_service_names
    3. Next, get specific products with get_products
    4. Finally, use this tool to calculate the monthly cost of the selected product
    
    IMPORTANT: You must use the EXACT product name as it appears in the results of get_products.
    
    Args:
        product_name (str): Exact name of the product (e.g. 'Azure App Service Premium v3 Plan')
        region (str): Azure region (default: 'westeurope')
        monthly_hours (int): Number of hours per month (default: 730, which is approximately one month)
        type (str, optional): Price type (e.g. 'Consumption', 'Reservation')
    """)
def get_monthly_cost(product_name, region="westeurope", monthly_hours=730, type="Consumption"):
    # Ensure parameters are of the correct type
    product_name = str(product_name)
    region = str(region)
    type = str(type)
    monthly_hours = int(monthly_hours) if not isinstance(monthly_hours, int) else monthly_hours
    
    # API Configuration
    AZURE_PRICE_API = "https://prices.azure.com/api/retail/prices"
    API_VERSION = "2023-01-01-preview"
    
    filter_params = f"productName eq '{product_name}' and armRegionName eq '{region}'"
    if type:
        filter_params += f" and type eq '{type}'"
    
    params = {
        'api-version': API_VERSION,
        '$filter': filter_params,
    }
    
    try:
        # Make the request to the Azure API
        log(f"Querying API to get the price of {product_name} in {region}")
        response = requests.get(AZURE_PRICE_API, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Extract relevant items
        items = result.get("Items", [])
        
        if len(items) == 0:
            log(f"No products found for: {product_name}", "warning")
            return {
                "product_name": product_name,
                "region": region,
                "status": "error",
                "message": f"Product '{product_name}' not found in region '{region}'.",
                "filter_applied": filter_params
            }
        
        # Prepare the response with costs
        products_costs = []
        total_monthly_cost = 0
        
        for item in items:
            # Extract relevant information
            sku_name = item.get("skuName", "")
            meter_name = item.get("meterName", "")
            retail_price = item.get("retailPrice", 0)
            currency = item.get("currencyCode", "USD")
            unit_of_measure = item.get("unitOfMeasure", "")
            
            # Calculate monthly cost
            monthly_cost = retail_price * monthly_hours if "Hour" in unit_of_measure else retail_price
            total_monthly_cost += monthly_cost
            
            # Add to the costs list
            products_costs.append({
                "sku_name": sku_name,
                "meter_name": meter_name,
                "retail_price": retail_price,
                "unit_of_measure": unit_of_measure,
                "monthly_cost": monthly_cost,
                "currency": currency
            })
        
        # Sort by monthly cost in descending order
        products_costs.sort(key=lambda x: x["monthly_cost"], reverse=True)
        
        return {
            "product_name": product_name,
            "region": region,
            "monthly_hours": monthly_hours,
            "products": products_costs,
            "total_monthly_cost": total_monthly_cost,
            "currency": items[0].get("currencyCode", "USD") if items else "USD",
            "count": len(products_costs),
            "status": "success"
        }
        
    except requests.exceptions.RequestException as e:
        log(f"Error connecting to Azure API: {str(e)}", "error")
        return {
            "product_name": product_name,
            "region": region,
            "status": "error",
            "error": f"Error connecting to API: {str(e)}"
        }


# Endpoint to list available tools in the MCP
class ToolsEndpoint(HTTPEndpoint):
    """
    Endpoint to list available tools in the MCP.
    
    This endpoint returns information about all registered tools
    in the MCP, including their names, descriptions, and expected parameters.
    """
    async def get(self, request):
        tools = mcp.list_tools()
        return JSONResponse(tools)

# Create the Starlette application with routes
app = Starlette(routes=[
    Mount("/", app=mcp.sse_app()),
    Route("/tools", ToolsEndpoint)
])

# Create the FastAPI application with Model Context Protocol
def get_application():
    """Create and return the Starlette application."""
    return app

if __name__ == "__main__":
    log(f"Starting MCP server at http://{settings.MCP_HOST}:{settings.MCP_PORT}")
    log(f"SSE Endpoint: http://{settings.MCP_HOST}:{settings.MCP_PORT}/sse")
    log(f"Tools Endpoint: http://{settings.MCP_HOST}:{settings.MCP_PORT}/tools")
    log(f"Debug mode: {'ON' if settings.MCP_DEBUG else 'OFF'}")
    log(f"Auto-reload: {'ENABLED' if settings.MCP_RELOAD else 'DISABLED'}")
    
    # Configure uvicorn
    uvicorn_config = {
        "app": "azure_pricing_mcp_server:get_application",
        "host": settings.MCP_HOST,
        "port": settings.MCP_PORT,
        "reload": settings.MCP_RELOAD,
        "log_level": "debug" if settings.MCP_DEBUG else settings.LOG_LEVEL.lower()
    }
    
    logger.debug(f"Uvicorn configuration: {uvicorn_config}")
    
    if settings.MCP_DEBUG:
        logger.debug("DEBUG mode enabled for uvicorn")
    
    uvicorn.run(**uvicorn_config)
