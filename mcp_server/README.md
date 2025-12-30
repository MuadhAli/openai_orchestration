# Insurance MCP Server

This MCP server provides database tools for querying and updating insurance data.

## Available Tools

### Query Tools
- `query_agents` - Query insurance agents by ID or region
- `query_customers` - Query customers by ID, agent, or email
- `query_policies` - Query policies by ID, customer, type, or status
- `query_claims` - Query claims by ID, policy, or status
- `query_payments` - Query payments by ID, policy, or status

### Update Tools
- `update_claim_status` - Update claim status (approved, denied, pending, etc.)
- `update_policy_status` - Update policy status (active, expired, cancelled, etc.)

## How It Works

The orchestrator automatically routes queries:
- **Insurance queries** → MCP tools (queries about agents, policies, claims, etc.)
- **Normal chat** → Standard OpenAI chat

## Testing

Once deployed, try these queries:
- "Show me all agents in the North region"
- "What policies does customer 123 have?"
- "List all pending claims"
- "Update claim 456 status to approved"
- "What's the weather?" (routes to normal chat)
