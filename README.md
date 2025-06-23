# Stateful Multi-Agent System for Airtel Network Provider

This example demonstrates how to create a stateful multi-agent system for an Airtel network provider customer support service, combining the power of persistent state management with specialized agent delegation. This approach creates intelligent agent systems that remember customer information across interactions while leveraging specialized domain expertise.

## What is a Stateful Multi-Agent System?

A Stateful Multi-Agent System combines two powerful patterns:

1. **State Management**: Persisting information about customers and conversations across interactions
2. **Multi-Agent Architecture**: Distributing tasks among specialized agents based on their expertise

The result is a sophisticated agent ecosystem that can:
- Remember customer information and interaction history
- Route queries to the most appropriate specialized agent
- Provide personalized responses based on past interactions
- Maintain context across multiple agent delegates

This example implements a customer service system for an Airtel network provider, where specialized agents handle different aspects of customer support while sharing a common state.

## Project Structure

```
app/
│
├── manager/           # Main agent package
│   ├── __init__.py              # Required for Python package
│   ├── agent.py                 # Root coordinator agent definition
│   └── sub_agents/              # Specialized agents
│       ├── recharge_billing_agent/   # Handles recharge, billing and invoice queries
├       └── faq_agents/               # rag agents    
│       ├── tech_support_agent/       # Handles tech support queries
│       └── plan_enquiry_agent/       # Handles plan, addon related enquiry
|        
├── config/                       # Configuration files
│   ├── database_config.py        # Database configuration
│   └── customer_service_tools.py # Tools for customer service
│
├── chat_server.py               # Application entry point with session setup (Web)
├── utils.py                     # Helper functions for state management
└── README.md                    # This documentation
```

## Key Components

### 1. Session Management

The example uses `InMemorySessionService` to store session state:

```python
session_service = InMemorySessionService()

def initialize_state():
    """Initialize the session state with default values."""
    return {
        "customer_id": None,  # Will be populated when customer is identified
        "customer_info": None,  # Will store customer details
        "plan_id": None,  # Will store the customer's plan ID
        "interaction_history": [],  # Will track conversation history
    }

# Create a new session with initial state
session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    state=initialize_state(),
)
```

### 2. State Sharing Across Agents

All agents in the system can access the same session state, enabling:
- Coordinator agent to track interaction history and customer identification
- Billing agent to access customer information for invoice queries
- Subscription agent to check customer's current plan and recommend alternatives
- All agents to personalize responses based on customer information

### 3. Multi-Agent Delegation

The coordinator agent routes queries to specialized sub-agents:

```python
coordinator_agent = Agent(
    name="coordinator_agent",
    model="gemini-2.0-flash",
    description="Coordinator agent for Airtel network provider",
    instruction="""
    You are the primary coordinator agent for Airtel network provider customer service.
    Your role is to help customers with their queries and direct them to the appropriate specialized agent.
    
    # ... detailed instructions ...
    
    """,
    sub_agents=[billing_agent, subscription_agent],
    tools=[
        tools.find_customer_by_phone,
        tools.find_customer_by_email
    ],
)
```

## How It Works

1. **Initial Session Creation**:
   - A new session is created with default state values
   - Session state is initialized with empty customer information

2. **Customer Identification**:
   - The coordinator agent asks for the customer's phone number or email
   - Customer information is retrieved and stored in the state
   - This information becomes available to all agents

3. **Query Routing**:
   - The coordinator agent analyzes the customer query and decides which specialist should handle it
   - Specialized agents receive the full state context when delegated to

4. **State Updates**:
   - When customer information is found, it's stored in the state
   - These updates are available to all agents for future interactions

5. **Personalized Responses**:
   - Agents tailor responses based on customer information and previous interactions
   - Different paths are taken based on the customer's subscription plan

## Getting Started

### Setup

1. Activate the virtual environment from the root directory:
```bash
# macOS/Linux:
source ../.venv/bin/activate
# Windows CMD:
..\.venv\Scripts\activate.bat
# Windows PowerShell:
..\.venv\Scripts\Activate.ps1
```

2. Make sure your Google API key is set in the `.env` file:
```
GOOGLE_API_KEY=your_api_key_here
```

### Running the Example

To run the stateful multi-agent example:

```bash
uvicorn chat_server:app --host 0.0.0.0 --port 8000 --reload
```

This will:
1. Initialize a new session with default state
2. Start an interactive conversation with the coordinator agent
3. Track all interactions in the session state
4. Allow specialized agents to handle specific queries

### Example Conversation Flow

Try this conversation flow to test the system:

1. **Start with a general query**:
   - "I want to check my current plan"
   - (Coordinator agent will ask for identification)

2. **Provide identification**:
   - "My phone number is 9876543210"
   - (Coordinator will look up customer and update state)

3. **Ask about billing**:
   - "I want to see my recent invoices"
   - (Coordinator agent will route to billing agent)

4. **Ask about subscription plans**:
   - "What other plans do you offer?"
   - (Coordinator agent will route to subscription agent)

Notice how the system remembers your customer information across different specialized agents!

## Advanced Features

### 1. Interaction History Tracking

The system maintains a history of interactions to provide context:

```python
# Update interaction history with the user's query
add_user_query_to_history(
    session_service, APP_NAME, USER_ID, SESSION_ID, user_input
)
```

### 2. Customer Identification

The system implements customer lookup by phone or email:

```
Before providing any account-specific information, ensure the customer has been properly identified
using their phone number or email address.
```

### 3. State-Based Personalization

All agents tailor responses based on session state:

```
Tailor your responses based on the customer's information and previous interactions.
When the customer hasn't been identified yet, ask for their phone number or email to look them up.
```

## Production Considerations

For a production implementation, consider:

1. **Persistent Storage**: Replace `InMemorySessionService` with `DatabaseSessionService` to persist state across application restarts
2. **User Authentication**: Implement proper user authentication to securely identify customers
3. **Error Handling**: Add robust error handling for agent failures and state corruption
4. **Monitoring**: Implement logging and monitoring to track system performance

# run
- web- adk web
- Fastapi - localhost/docs - adk api_server 
- terminal adk run multi_tool_agent 
