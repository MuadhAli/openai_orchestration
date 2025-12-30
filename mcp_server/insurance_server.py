"""
MCP Server for Insurance Database Operations
"""
import os
import json
import logging
import time
from typing import Any
import mysql.connector
from mysql.connector import Error
from mcp.server import Server
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "mysql"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "chatuser"),
    "password": os.getenv("DB_PASSWORD", "chatpassword"),
    "database": os.getenv("INSURANCE_DB_NAME", "insurance_db"),  # Use insurance_db for insurance tables
    "autocommit": False,
    "connect_timeout": 10,
    "buffered": True
}

app = Server("insurance-db")

def get_db_connection(max_retries=3, retry_delay=2):
    """Create database connection with retry logic."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to MySQL at {DB_CONFIG['host']}:{DB_CONFIG['port']} (attempt {attempt + 1}/{max_retries})")
            conn = mysql.connector.connect(**DB_CONFIG)
            logger.info("Successfully connected to MySQL database")
            return conn
        except Error as e:
            logger.error(f"Database connection error (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise Exception(f"Failed to connect to database after {max_retries} attempts: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to database: {str(e)}")
            raise

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available insurance database tools."""
    return [
        Tool(
            name="query_agents",
            description="Query insurance agents. Optional filters: agent_id, region",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "integer", "description": "Filter by agent ID"},
                    "region": {"type": "string", "description": "Filter by region"}
                }
            }
        ),
        Tool(
            name="query_customers",
            description="Query customers. Optional filters: customer_id, agent_id, email",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer"},
                    "agent_id": {"type": "integer"},
                    "email": {"type": "string"}
                }
            }
        ),
        Tool(
            name="query_policies",
            description="Query insurance policies. Optional filters: policy_id, customer_id, policy_type, status",
            inputSchema={
                "type": "object",
                "properties": {
                    "policy_id": {"type": "integer"},
                    "customer_id": {"type": "integer"},
                    "policy_type": {"type": "string"},
                    "status": {"type": "string"}
                }
            }
        ),
        Tool(
            name="query_claims",
            description="Query insurance claims. Optional filters: claim_id, policy_id, status",
            inputSchema={
                "type": "object",
                "properties": {
                    "claim_id": {"type": "integer"},
                    "policy_id": {"type": "integer"},
                    "status": {"type": "string"}
                }
            }
        ),
        Tool(
            name="query_payments",
            description="Query payments. Optional filters: payment_id, policy_id, status",
            inputSchema={
                "type": "object",
                "properties": {
                    "payment_id": {"type": "integer"},
                    "policy_id": {"type": "integer"},
                    "status": {"type": "string"}
                }
            }
        ),
        Tool(
            name="update_claim_status",
            description="Update the status of an insurance claim",
            inputSchema={
                "type": "object",
                "properties": {
                    "claim_id": {"type": "integer", "description": "Claim ID to update"},
                    "status": {"type": "string", "description": "New status"}
                },
                "required": ["claim_id", "status"]
            }
        ),
        Tool(
            name="update_policy_status",
            description="Update the status of an insurance policy",
            inputSchema={
                "type": "object",
                "properties": {
                    "policy_id": {"type": "integer"},
                    "status": {"type": "string"}
                },
                "required": ["policy_id", "status"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    conn = None
    cursor = None
    try:
        logger.info(f"Calling tool: {name} with arguments: {arguments}")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        results = None
        
        if name == "query_agents":
            query = "SELECT * FROM Agents WHERE 1=1"
            params = []
            if arguments.get("agent_id"):
                query += " AND agent_id = %s"
                params.append(arguments["agent_id"])
            if arguments.get("region"):
                query += " AND region = %s"
                params.append(arguments["region"])
            cursor.execute(query, params)
            results = cursor.fetchall()
            
        elif name == "query_customers":
            query = "SELECT * FROM Customers WHERE 1=1"
            params = []
            if arguments.get("customer_id"):
                query += " AND customer_id = %s"
                params.append(arguments["customer_id"])
            if arguments.get("agent_id"):
                query += " AND agent_id = %s"
                params.append(arguments["agent_id"])
            if arguments.get("email"):
                query += " AND email = %s"
                params.append(arguments["email"])
            cursor.execute(query, params)
            results = cursor.fetchall()
            
        elif name == "query_policies":
            query = "SELECT * FROM Policies WHERE 1=1"
            params = []
            if arguments.get("policy_id"):
                query += " AND policy_id = %s"
                params.append(arguments["policy_id"])
            if arguments.get("customer_id"):
                query += " AND customer_id = %s"
                params.append(arguments["customer_id"])
            if arguments.get("policy_type"):
                query += " AND policy_type = %s"
                params.append(arguments["policy_type"])
            if arguments.get("status"):
                query += " AND status = %s"
                params.append(arguments["status"])
            cursor.execute(query, params)
            results = cursor.fetchall()
            
        elif name == "query_claims":
            query = "SELECT * FROM Claims WHERE 1=1"
            params = []
            if arguments.get("claim_id"):
                query += " AND claim_id = %s"
                params.append(arguments["claim_id"])
            if arguments.get("policy_id"):
                query += " AND policy_id = %s"
                params.append(arguments["policy_id"])
            if arguments.get("status"):
                query += " AND status = %s"
                params.append(arguments["status"])
            cursor.execute(query, params)
            results = cursor.fetchall()
            
        elif name == "query_payments":
            query = "SELECT * FROM Payments WHERE 1=1"
            params = []
            if arguments.get("payment_id"):
                query += " AND payment_id = %s"
                params.append(arguments["payment_id"])
            if arguments.get("policy_id"):
                query += " AND policy_id = %s"
                params.append(arguments["policy_id"])
            if arguments.get("status"):
                query += " AND status = %s"
                params.append(arguments["status"])
            cursor.execute(query, params)
            results = cursor.fetchall()
            
        elif name == "update_claim_status":
            query = "UPDATE Claims SET status = %s WHERE claim_id = %s"
            cursor.execute(query, (arguments["status"], arguments["claim_id"]))
            conn.commit()
            results = {"success": True, "message": f"Claim {arguments['claim_id']} updated to {arguments['status']}"}
            
        elif name == "update_policy_status":
            query = "UPDATE Policies SET status = %s WHERE policy_id = %s"
            cursor.execute(query, (arguments["status"], arguments["policy_id"]))
            conn.commit()
            results = {"success": True, "message": f"Policy {arguments['policy_id']} updated to {arguments['status']}"}
            
        else:
            results = {"error": f"Unknown tool: {name}"}
            logger.warning(f"Unknown tool requested: {name}")
        
        if results is None:
            results = {"error": "No results returned from query"}
        
        return [TextContent(type="text", text=json.dumps(results, indent=2, default=str))]
        
    except mysql.connector.Error as e:
        error_msg = f"MySQL error calling tool {name}: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=json.dumps({"error": error_msg, "error_code": e.errno if hasattr(e, 'errno') else None}))]
    except Exception as e:
        error_msg = f"Error calling tool {name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": error_msg}))]
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            logger.debug("Database connection closed")


if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    
    asyncio.run(main())
