import asyncio
import copy
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from manager.agent import coordinator_agent
from setup_state import set_state_info

# Load environment variables
load_dotenv()

# ===== CONSTANTS =====
APP_NAME = "Airtel Customer Support"

# ===== INITIAL STATE TEMPLATE =====
__initial_state = {
    "customer_info": None,
    "plan_details": None, 
    "interaction_history": [],
}

# ===== GLOBAL SERVICES =====
session_service = InMemorySessionService()

# ===== ACTIVE CONNECTIONS TRACKING =====
active_connections: Dict[str, WebSocket] = {}

# ===== UTILITY FUNCTIONS (FROM utils.py) =====
def update_interaction_history(session_service, app_name, user_id, session_id, entry):
    """Add an entry to the interaction history in state."""
    try:
        session = session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

        interaction_history = session.state.get("interaction_history", [])

        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        interaction_history.append(entry)

        updated_state = session.state.copy()
        updated_state["interaction_history"] = interaction_history

        session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state=updated_state,
        )
    except Exception as e:
        print(f"Error updating interaction history: {e}")


def add_user_query_to_history(session_service, app_name, user_id, session_id, query):
    """Add a user query to the interaction history."""
    update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {
            "action": "user_query",
            "query": query,
        },
    )


def add_agent_response_to_history(
    session_service, app_name, user_id, session_id, agent_name, response
):
    """Add an agent response to the interaction history."""
    update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {
            "action": "agent_response",
            "agent": agent_name,
            "response": response,
        },
    )


def display_state(session_service, app_name, user_id, session_id, label="Current State"):
    """Display the current session state in a formatted way."""
    try:
        session = session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

        print(f"\n{'-' * 10} {label} {'-' * 10}")
        
        customer_id = session.state.get("customer_id", "Not identified")
        print(f"👤 Customer ID: {customer_id}")

        customer_info = session.state.get("customer_info", "No customer info available")
        if isinstance(customer_info, dict) and customer_info:
            print("🧑‍💼 Customer Info:")
            for key, value in customer_info.items():
                print(f"  - {key}: {value}")
        else:
            print("🧑‍💼 Customer Info: Not available")

        plan_id = session.state.get("plan_id", "No plan assigned")
        print(f"💳 Plan ID: {plan_id}")

        plan_name = session.state.get("plan_name", "No plan name available")
        print(f"📦 Plan Name: {plan_name}")

        plan_details = session.state.get("plan_details", "No details available")
        if isinstance(plan_details, dict) and plan_details:
            print("📃 Plan Details:")
            for detail_key, detail_value in plan_details.items():
                print(f"  - {detail_key}: {detail_value}")
        else:
            print("📃 Plan Details: Not available")

        interaction_history = session.state.get("interaction_history", [])
        if interaction_history:
            print("📝 Interaction History:")
            for idx, interaction in enumerate(interaction_history, 1):
                if isinstance(interaction, dict):
                    action = interaction.get("action", "interaction")
                    timestamp = interaction.get("timestamp", "unknown time")

                    if action == "user_query":
                        query = interaction.get("query", "")
                        print(f'  {idx}. User query at {timestamp}: "{query}"')
                    elif action == "agent_response":
                        agent = interaction.get("agent", "unknown")
                        response = interaction.get("response", "")
                        if len(response) > 100:
                            response = response[:97] + "..."
                        print(f'  {idx}. {agent} response at {timestamp}: "{response}"')
                    else:
                        details = ", ".join(
                            f"{k}: {v}"
                            for k, v in interaction.items()
                            if k not in ["action", "timestamp"]
                        )
                        print(
                            f"  {idx}. {action} at {timestamp}"
                            + (f" ({details})" if details else "")
                        )
                else:
                    print(f"  {idx}. {interaction}")
        else:
            print("📝 Interaction History: None")

        print("-" * (22 + len(label)))
    except Exception as e:
        print(f"Error displaying state: {e}")


# ===== SESSION MANAGEMENT =====
def initialize_chat_session(customer_id: str) -> str:
    """Initialize a new chat session for a customer."""
    session_id = str(uuid.uuid4())
    
    try:
        # Initialize state with customer data
        prefilled_state = copy.deepcopy(__initial_state)
        initial_state = set_state_info(prefilled_state, customer_id=customer_id)
        print(f"✅ Successfully loaded customer data for customer_id: {customer_id}")
    except Exception as e:
        print(f"⚠️  Could not load customer data for customer_id {customer_id}: {e}")
        # Fallback state
        initial_state = copy.deepcopy(__initial_state)
        initial_state.update({
            "customer_id": customer_id,
            "customer_info": {"error": "Customer data not available"},
            "plan_id": "unknown",
            "plan_name": "No plan information available",
            "plan_details": {"error": "Plan data not available"}
        })

    # Create session
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=customer_id,
        session_id=session_id,
        state=initial_state,
    )
    
    print(f"🆕 Created new session: {session_id} for customer: {customer_id}")
    return session_id


async def process_agent_response_async(runner, customer_id: str, session_id: str, query: str) -> Optional[str]:
    """Process agent response asynchronously (similar to call_agent_async from utils.py)."""
    content = types.Content(role="user", parts=[types.Part(text=query)])
    print(f"\n🔄 Processing Query: {query}")
    
    final_response_text = None
    agent_name = None

    # Display state before processing
    display_state(session_service, APP_NAME, customer_id, session_id, "State BEFORE processing")

    try:
        async for event in runner.run_async(
            user_id=customer_id, session_id=session_id, new_message=content
        ):
            if event.author:
                agent_name = event.author

            if event.is_final_response():
                if (
                    event.content
                    and event.content.parts
                    and hasattr(event.content.parts[0], "text")
                    and event.content.parts[0].text
                ):
                    final_response_text = event.content.parts[0].text.strip()
                    print(f"\n✅ AGENT RESPONSE: {final_response_text}\n")
                break

    except Exception as e:
        print(f"❌ ERROR during agent run: {e}")
        final_response_text = f"Error processing your request: {str(e)}"

    # Add agent response to history
    if final_response_text and agent_name:
        add_agent_response_to_history(
            session_service, APP_NAME, customer_id, session_id, agent_name, final_response_text
        )

    # Display state after processing
    display_state(session_service, APP_NAME, customer_id, session_id, "State AFTER processing")
    print(f"{'='*50}")

    return final_response_text


# ===== FASTAPI APP =====
app = FastAPI(title="Airtel Customer Support Chat")

# Serve static files if needed
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_chat_page():
    """Serve a simple chat interface."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Airtel Customer Support</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .chat-container { max-width: 800px; margin: 0 auto; }
            .messages { height: 400px; border: 1px solid #ccc; overflow-y: auto; padding: 10px; margin: 10px 0; }
            .message { margin: 5px 0; padding: 5px; }
            .user-message { background-color: #e3f2fd; text-align: right; }
            .agent-message { background-color: #f3e5f5; }
            .system-message { background-color: #fff3e0; font-style: italic; }
            input[type="text"] { width: 70%; padding: 10px; }
            button { padding: 10px 20px; margin-left: 10px; }
            .connection-info { background-color: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <h1>🛜 Airtel Customer Support Chat</h1>
            
            <div class="connection-info">
                <h3>Connect to Chat</h3>
                <input type="text" id="customerId" placeholder="Enter your Customer ID" />
                <button onclick="connect()">Connect</button>
                <button onclick="disconnect()">Disconnect</button>
                <div id="connectionStatus">Status: Disconnected</div>
            </div>
            
            <div id="messages" class="messages"></div>
            
            <div>
                <input type="text" id="messageInput" placeholder="Type your message..." disabled />
                <button onclick="sendMessage()" disabled id="sendBtn">Send</button>
            </div>
        </div>

        <script>
            let ws = null;
            let sessionId = null;
            let customerId = null;

            function connect() {
                customerId = document.getElementById('customerId').value;
                if (!customerId) {
                    alert('Please enter a Customer ID');
                    return;
                }
                
                ws = new WebSocket(`ws://localhost:8000/chat/${customerId}`);
                
                ws.onopen = function(event) {
                    document.getElementById('connectionStatus').textContent = `Status: Connected (Customer: ${customerId})`;
                    document.getElementById('messageInput').disabled = false;
                    document.getElementById('sendBtn').disabled = false;
                    addMessage('system', `Connected as Customer ID: ${customerId}`);
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    if (data.type === 'agent_response') {
                        addMessage('agent', data.message);
                    } else if (data.type === 'session_info') {
                        sessionId = data.session_id;
                        addMessage('system', `Session ID: ${sessionId}`);
                    } else if (data.type === 'error') {
                        addMessage('system', `Error: ${data.message}`);
                    }
                };
                
                ws.onclose = function(event) {
                    document.getElementById('connectionStatus').textContent = 'Status: Disconnected';
                    document.getElementById('messageInput').disabled = true;
                    document.getElementById('sendBtn').disabled = true;
                    addMessage('system', 'Connection closed');
                };
                
                ws.onerror = function(error) {
                    addMessage('system', `Connection error: ${error}`);
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                }
            }
            
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (message && ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({type: 'user_message', message: message}));
                    addMessage('user', message);
                    input.value = '';
                }
            }
            
            function addMessage(type, message) {
                const messages = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}-message`;
                messageDiv.textContent = message;
                messages.appendChild(messageDiv);
                messages.scrollTop = messages.scrollHeight;
            }
            
            // Send message on Enter key
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.websocket("/chat/{customer_id}")
async def websocket_chat(websocket: WebSocket, customer_id: str):
    """WebSocket endpoint for customer chat."""
    await websocket.accept()
    
    try:
        # Initialize session
        session_id = initialize_chat_session(customer_id)
        active_connections[session_id] = websocket
        
        # Create runner
        runner = Runner(
            agent=coordinator_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )
        
        # Send session info to client
        await websocket.send_text(json.dumps({
            "type": "session_info",
            "session_id": session_id,
            "customer_id": customer_id
        }))
        
        print(f"👋 Customer {customer_id} connected with session {session_id}")
        
        # Display initial state
        display_state(session_service, APP_NAME, customer_id, session_id, "Initial Session State")
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data["type"] == "user_message":
                user_message = message_data["message"]
                
                # Add to interaction history
                add_user_query_to_history(
                    session_service, APP_NAME, customer_id, session_id, user_message
                )
                
                print(f"📝 User message: {user_message}")
                
                # Process with agent
                agent_response = await process_agent_response_async(
                    runner, customer_id, session_id, user_message
                )
                
                # Send response back
                if agent_response:
                    await websocket.send_text(json.dumps({
                        "type": "agent_response",
                        "message": agent_response
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "No response from agent"
                    }))
                    
    except WebSocketDisconnect:
        print(f"👋 Customer {customer_id} disconnected")
    except Exception as e:
        print(f"❌ Error in websocket chat: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Server error: {str(e)}"
            }))
        except:
            pass
    finally:
        # Cleanup
        if session_id in active_connections:
            del active_connections[session_id]
        
        # Display final state
        try:
            display_state(session_service, APP_NAME, customer_id, session_id, "Final Session State")
        except:
            pass


@app.get("/sessions")
async def list_active_sessions():
    """List all active chat sessions."""
    return {
        "active_sessions": len(active_connections),
        "sessions": list(active_connections.keys())
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Airtel Customer Support Chat"}

from fastapi import  Depends
from typing import Optional
from config.database_config import DatabaseConfig  # Update with your actual module
from fastapi.responses import JSONResponse

db = DatabaseConfig()

@app.get("/conversation_analytics")
def fetch_conversation_analytics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    intent: Optional[str] = Query(None, description="Filter by intent type")
):
    base_query = "SELECT * FROM conversation_analytics"
    filters = []
    params = []

    # Add WHERE clauses conditionally
    if user_id:
        filters.append("user_id = %s")
        params.append(user_id)

    if intent:
        filters.append("intent::text ILIKE %s")
        params.append(f"%{intent}%")  # Allow partial matches (e.g., "Tech")

    if filters:
        base_query += " WHERE " + " AND ".join(filters)

    base_query += " ORDER BY datetime DESC"

    result = db.execute_query(base_query, tuple(params))
    if "error" in result:
        return JSONResponse(status_code=500, content={"error": result["error"]})

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)