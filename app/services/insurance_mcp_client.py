"""Insurance MCP Client"""
import os
import json
import logging
import mysql.connector
from mysql.connector import Error
from typing import Dict, Any, List
import time

logger = logging.getLogger(__name__)

class InsuranceMCPClient:
    """Client for insurance database operations."""
    
    def __init__(self):
        self.db_config = {
            "host": os.getenv("DB_HOST", "mysql"),
            "port": int(os.getenv("DB_PORT", 3306)),
            "user": os.getenv("DB_USER", "chatuser"),
            "password": os.getenv("DB_PASSWORD", "chatpassword"),
            "database": os.getenv("INSURANCE_DB_NAME", "insurance_db"),  # Use insurance_db for insurance tables
            "autocommit": False,
            "connect_timeout": 10,
            "buffered": True
        }
    
    def get_db_connection(self, max_retries=3, retry_delay=2):
        """Create database connection with retry logic."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to MySQL at {self.db_config['host']}:{self.db_config['port']} (attempt {attempt + 1}/{max_retries})")
                conn = mysql.connector.connect(**self.db_config)
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

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Return OpenAI function calling schema."""
        return [
            {"type": "function", "function": {"name": "query_agents", "description": "Query insurance agents", "parameters": {"type": "object", "properties": {"agent_id": {"type": "integer"}, "region": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "query_customers", "description": "Query customers", "parameters": {"type": "object", "properties": {"customer_id": {"type": "integer"}, "agent_id": {"type": "integer"}, "email": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "query_policies", "description": "Query policies", "parameters": {"type": "object", "properties": {"policy_id": {"type": "integer"}, "customer_id": {"type": "integer"}, "policy_type": {"type": "string"}, "status": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "query_claims", "description": "Query claims", "parameters": {"type": "object", "properties": {"claim_id": {"type": "integer"}, "policy_id": {"type": "integer"}, "status": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "query_payments", "description": "Query payments", "parameters": {"type": "object", "properties": {"payment_id": {"type": "integer"}, "policy_id": {"type": "integer"}, "status": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "update_claim_status", "description": "Update claim status", "parameters": {"type": "object", "properties": {"claim_id": {"type": "integer"}, "status": {"type": "string"}}, "required": ["claim_id", "status"]}}},
            {"type": "function", "function": {"name": "update_policy_status", "description": "Update policy status", "parameters": {"type": "object", "properties": {"policy_id": {"type": "integer"}, "status": {"type": "string"}}, "required": ["policy_id", "status"]}}}
        ]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool call against the database."""
        conn = None
        cursor = None
        try:
            logger.info(f"Calling tool: {tool_name} with arguments: {arguments}")
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            results = None
            
            if tool_name == "query_agents":
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
                logger.info(f"Query returned {len(results)} agent(s)")
                
            elif tool_name == "query_customers":
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
                logger.info(f"Query returned {len(results)} customer(s)")
                
            elif tool_name == "query_policies":
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
                logger.info(f"Query returned {len(results)} policy/policies")
                
            elif tool_name == "query_claims":
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
                logger.info(f"Query returned {len(results)} claim(s)")
                
            elif tool_name == "query_payments":
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
                logger.info(f"Query returned {len(results)} payment(s)")
                
            elif tool_name == "update_claim_status":
                if not arguments.get("claim_id") or not arguments.get("status"):
                    results = {"error": "claim_id and status are required"}
                else:
                    query = "UPDATE Claims SET status = %s WHERE claim_id = %s"
                    cursor.execute(query, (arguments["status"], arguments["claim_id"]))
                    conn.commit()
                    results = {"success": True, "message": f"Claim {arguments['claim_id']} updated to {arguments['status']}"}
                    logger.info(f"Updated claim {arguments['claim_id']} to status {arguments['status']}")
                
            elif tool_name == "update_policy_status":
                if not arguments.get("policy_id") or not arguments.get("status"):
                    results = {"error": "policy_id and status are required"}
                else:
                    query = "UPDATE Policies SET status = %s WHERE policy_id = %s"
                    cursor.execute(query, (arguments["status"], arguments["policy_id"]))
                    conn.commit()
                    results = {"success": True, "message": f"Policy {arguments['policy_id']} updated to {arguments['status']}"}
                    logger.info(f"Updated policy {arguments['policy_id']} to status {arguments['status']}")
                
            else:
                results = {"error": f"Unknown tool: {tool_name}"}
                logger.warning(f"Unknown tool requested: {tool_name}")
            
            if results is None:
                results = {"error": "No results returned from query"}
            
            return json.dumps(results, indent=2, default=str)
            
        except mysql.connector.Error as e:
            error_msg = f"MySQL error calling tool {tool_name}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg, "error_code": e.errno if hasattr(e, 'errno') else None})
        except Exception as e:
            error_msg = f"Error calling tool {tool_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return json.dumps({"error": error_msg})
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
                logger.debug("Database connection closed")
