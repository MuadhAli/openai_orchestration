"""
Orchestrator Service - Routes queries to insurance MCP or normal chat
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.services.insurance_mcp_client import InsuranceMCPClient

logger = logging.getLogger(__name__)

class OrchestratorService:
    """Routes queries intelligently between insurance MCP and normal chat."""
    
    INSURANCE_KEYWORDS = [
        "insurance", "policy", "policies", "claim", "claims", "agent", "agents",
        "customer", "customers", "payment", "payments", "premium", "coverage",
        "policyholder", "insured", "beneficiary", "deductible"
    ]
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.mcp_client = InsuranceMCPClient()
        
    def is_insurance_query(self, message: str) -> bool:
        """Determine if query is insurance-related."""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.INSURANCE_KEYWORDS)
    
    async def route_query(self, message: str, session_id: str, chat_history: list) -> Dict[str, Any]:
        """Route query to appropriate handler."""
        
        if self.is_insurance_query(message):
            logger.info(f"Routing to insurance MCP for session {session_id}")
            return await self.handle_insurance_query(message, chat_history)
        else:
            logger.info(f"Routing to normal chat for session {session_id}")
            return await self.handle_normal_chat(message, chat_history)
    
    async def handle_insurance_query(self, message: str, chat_history: list) -> Dict[str, Any]:
        """Handle insurance queries using MCP tools."""
        
        tools = self.mcp_client.get_tools_schema()
        
        messages = [
            {"role": "system", "content": "You are an insurance assistant with access to database tools. Use them to answer queries accurately."}
        ]
        messages.extend(chat_history[-5:])
        messages.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        if tool_calls:
            messages.append(response_message)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"Calling MCP tool: {function_name} with args: {function_args}")
                function_response = await self.mcp_client.call_tool(function_name, function_args)
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response
                })
            
            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            final_content = second_response.choices[0].message.content
        else:
            final_content = response_message.content
        
        return {
            "content": final_content,
            "type": "insurance",
            "tools_used": [tc.function.name for tc in tool_calls] if tool_calls else []
        }
    
    async def handle_normal_chat(self, message: str, chat_history: list) -> Dict[str, Any]:
        """Handle normal chat queries."""
        
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ]
        messages.extend(chat_history[-10:])
        messages.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        
        return {
            "content": response.choices[0].message.content,
            "type": "normal_chat",
            "tools_used": []
        }
