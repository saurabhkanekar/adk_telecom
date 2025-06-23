import asyncio
import base64
import copy
import json
import os
from pathlib import Path
from typing import AsyncIterable
from datetime import datetime

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, Query, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.events.event import Event
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import \
    InMemorySessionService
from google.genai import types
from manager.agent import coordinator_agent
from setup_state import set_state_info

#
# ADK Streaming
#

# Load Gemini API Key
load_dotenv()

APP_NAME = "NexTel Customer Support"
USER_ID = "101"
__initial_state = {  # Will be populated when customer is identified
    "customer_info": None,  # Will store customer details  # Will store the plan name
    "plan_details": None,  # Will store detailed plan information
    "interaction_history": [],  # Will track conversation history
}
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
session_service = InMemorySessionService()

# ===== UTILITY FUNCTIONS FROM UTILS.PY =====
def update_interaction_history(session_service, app_name, user_id, session_id, entry):
    """Add an entry to the interaction history in state."""
    try:
        # Get current session
        session = session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

        # Get current interaction history
        interaction_history = session.state.get("interaction_history", [])

        # Add timestamp if not already present
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Add the entry to interaction history
        interaction_history.append(entry)

        # Create updated state
        updated_state = session.state.copy()
        updated_state["interaction_history"] = interaction_history

        # Create a new session with updated state
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
        
        # Handle the customer ID
        customer_id = session.state.get("customer_id", "Not identified")
        print(f"👤 Customer ID: {customer_id}")

        # Handle the customer info
        customer_info = session.state.get("customer_info", "No customer info available")
        if isinstance(customer_info, dict) and customer_info:
            print("🧑‍💼 Customer Info:")
            for key, value in customer_info.items():
                print(f"  - {key}: {value}")
        else:
            print("🧑‍💼 Customer Info: Not available")

        # Handle the plan ID
        plan_id = session.state.get("plan_id", "No plan assigned")
        print(f"💳 Plan ID: {plan_id}")

        # Handle the plan name
        plan_name = session.state.get("plan_name", "No plan name available")
        print(f"📦 Plan Name: {plan_name}")

        # Handle the plan details
        plan_details = session.state.get("plan_details", "No details available")
        if isinstance(plan_details, dict) and plan_details:
            print("📃 Plan Details:")
            for detail_key, detail_value in plan_details.items():
                print(f"  - {detail_key}: {detail_value}")
        else:
            print("📃 Plan Details: Not available")

        # Handle interaction history
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
                        # Truncate very long responses for display
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

def start_agent_session(session_id, is_audio=False):
    """Starts an agent session"""
    prefilled_state = copy.deepcopy(__initial_state)
    initial_state = set_state_info(prefilled_state, customer_id="101")
    
    # Create a Session
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=session_id,
        session_id=session_id,  # Add session_id parameter
        state=initial_state,
    )

    # Create a Runner
    runner = Runner(
        app_name=APP_NAME,
        agent=coordinator_agent,
        session_service=session_service,
    )

    # Set response modality
    modality = "AUDIO" if is_audio else "TEXT"

    # Create speech config with voice settings
    speech_config = types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
        )
    )

    # Create run config with basic settings
    config = {"response_modalities": [modality]}
    
    # Only add speech config for audio mode
    if is_audio:
        config["speech_config"] = speech_config
        config["output_audio_transcription"] = {}

    run_config = RunConfig(**config)

    # Create a LiveRequestQueue for this session
    live_request_queue = LiveRequestQueue()

    # Start agent session
    live_events = runner.run(#run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )
    return live_events, live_request_queue, runner

async def agent_to_client_messaging(
    websocket: WebSocket, 
    live_events: AsyncIterable[Event | None],
    session_id: str,
    runner: Runner
):
    """Agent to client communication with history tracking"""
    current_response = ""
    agent_name = None
    
    while True:
        async for event in live_events:
            if event is None:
                continue

            # Capture agent name
            if event.author:
                agent_name = event.author

            # If the turn complete or interrupted, send it and save to history
            if event.turn_complete or event.interrupted:
                # Save the complete response to history if we have one
                if current_response.strip() and agent_name:
                    add_agent_response_to_history(
                        session_service,
                        APP_NAME,
                        session_id,
                        session_id,
                        agent_name,
                        current_response.strip()
                    )
                    
                    # Display state after processing
                    display_state(
                        session_service,
                        APP_NAME,
                        session_id,
                        session_id,
                        "State AFTER processing"
                    )
                    print(f"{'='*50}")
                
                # Reset for next interaction
                current_response = ""
                
                message = {
                    "turn_complete": event.turn_complete,
                    "interrupted": event.interrupted,
                }
                await websocket.send_text(json.dumps(message))
                print(f"[AGENT TO CLIENT]: {message}")
                continue

            # Read the Content and its first Part
            part = event.content and event.content.parts and event.content.parts[0]
            if not part:
                continue

            # Make sure we have a valid Part
            if not isinstance(part, types.Part):
                continue

            # Handle text content
            if part.text:
                # Accumulate the response text
                if event.partial:
                    current_response += part.text
                else:
                    # This is the final complete response
                    current_response = part.text
                
                # Send text if it's a partial response (streaming)
                if event.partial:
                    message = {
                        "mime_type": "text/plain",
                        "data": part.text,
                        "role": "model",
                    }
                    await websocket.send_text(json.dumps(message))
                    print(f"[AGENT TO CLIENT]: text/plain: {part.text}")

            # Handle audio content (if needed)
            is_audio = (
                part.inline_data
                and part.inline_data.mime_type
                and part.inline_data.mime_type.startswith("audio/pcm")
            )
            if is_audio:
                audio_data = part.inline_data and part.inline_data.data
                if audio_data:
                    message = {
                        "mime_type": "audio/pcm",
                        "data": base64.b64encode(audio_data).decode("ascii"),
                        "role": "model",
                    }
                    await websocket.send_text(json.dumps(message))
                    print(f"[AGENT TO CLIENT]: audio/pcm: {len(audio_data)} bytes.")

async def client_to_agent_messaging(
    websocket: WebSocket, 
    live_request_queue: LiveRequestQueue,
    session_id: str
):
    """Client to agent communication with history tracking"""
    while True:
        # Decode JSON message
        message_json = await websocket.receive_text()
        message = json.loads(message_json)
        mime_type = message["mime_type"]
        data = message["data"]
        role = message.get("role", "user")

        # Send the message to the agent
        if mime_type == "text/plain":
            # Add user query to history
            add_user_query_to_history(
                session_service,
                APP_NAME,
                session_id,
                session_id,
                data
            )
            
            # Display state before processing
            display_state(
                session_service,
                APP_NAME,
                session_id,
                session_id,
                "State BEFORE processing"
            )
            
            # Send a text message
            content = types.Content(role=role, parts=[types.Part.from_text(text=data)])
            live_request_queue.send_content(content=content)
            print(f"[CLIENT TO AGENT]: {data}")
            
        elif mime_type == "audio/pcm":
            # Send audio data
            decoded_data = base64.b64decode(data)
            live_request_queue.send_realtime(
                types.Blob(data=decoded_data, mime_type=mime_type)
            )
            print(f"[CLIENT TO AGENT]: audio/pcm: {len(decoded_data)} bytes")
        else:
            raise ValueError(f"Mime type not supported: {mime_type}")

#
# FastAPI web app
#

app = FastAPI()

STATIC_DIR = Path("static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    """Serves the index.html"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    is_audio: str = Query(...),
):
    """Client websocket endpoint with chat history functionality"""

    # Wait for client connection
    await websocket.accept()
    print(f"Client #{session_id} connected, audio mode: {is_audio}")

    # Start agent session
    live_events, live_request_queue, runner = start_agent_session(
        session_id, is_audio == "true"
    )

    # Start tasks with enhanced functionality
    agent_to_client_task = asyncio.create_task(
        agent_to_client_messaging(websocket, live_events, session_id, runner)
    )
    client_to_agent_task = asyncio.create_task(
        client_to_agent_messaging(websocket, live_request_queue, session_id)
    )
    
    try:
        await asyncio.gather(agent_to_client_task, client_to_agent_task)
    except Exception as e:
        print(f"Error in websocket communication: {e}")
    finally:
        # Display final state when client disconnects
        try:
            display_state(
                session_service,
                APP_NAME,
                session_id,
                session_id,
                "Final Session State"
            )
        except Exception as e:
            print(f"Error displaying final state: {e}")
        
        print(f"Client #{session_id} disconnected")