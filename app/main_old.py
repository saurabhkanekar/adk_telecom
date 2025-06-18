import asyncio

# Import the coordinator agent
from coordinator_agent.agent import coordinator_agent
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from utils import add_user_query_to_history, call_agent_async


import copy
from setup_state import  set_state_info, initial_state

load_dotenv()

# ===== PART 1: Initialize In-Memory Session Service =====
# Using in-memory storage for this example (non-persistent)
session_service = InMemorySessionService()
 

# ===== PART 2: Define Initial State =====
# This will be used when creating a new session
# initial_state = {
#     "customer_id": 1,  # Will be populated when customer is identified
#     "customer_info": "",  # Will store customer details
#     "plan_id": None,  # Will store the customer's plan ID
#     "interaction_history": [],  # Will track conversation history
# }
__initial_state = {
    "customer_id": None,  # Will be populated when customer is identified
    "customer_info": None,  # Will store customer details
    "plan_id": None,  # Will store the customer's plan ID
    "plan_name": None,  # Will store the plan name
    "plan_details": None,  # Will store detailed plan information
    "interaction_history": [],  # Will track conversation history
}





async def main_async():
    # Setup constants
    APP_NAME = "Airtel Customer Support"
    USER_ID = "airtel_customer"

    # Prefill state with customer information
    test_phone = "9765822200"
    prefilled_state = copy.deepcopy(__initial_state)
    initial_state = set_state_info(prefilled_state, phone=test_phone)

    # ===== PART 3: Session Creation =====
    # Create a new session with initial state
    new_session = session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        state=initial_state,
    )
    SESSION_ID = new_session.id
    print(f"Created new session: {SESSION_ID}")

    # ===== PART 4: Agent Runner Setup =====
    # Create a runner with the coordinator agent
    runner = Runner(
        agent=coordinator_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # ===== PART 5: Interactive Conversation Loop =====
    print("\nWelcome to Airtel Customer Support Chat!")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        # Get user input
        user_input = input("You: ")

        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit"]:
            print("Ending conversation. Goodbye!")
            break

        # Update interaction history with the user's query
        add_user_query_to_history(
            session_service, APP_NAME, USER_ID, SESSION_ID, user_input
        )

        # Process the user query through the agent
        await call_agent_async(runner, USER_ID, SESSION_ID, user_input)

    # ===== PART 6: State Examination =====
    # Show final session state
    # final_session = session_service.get_session(
    #     app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    # )
    # print("\nFinal Session State:")
    # for key, value in final_session.state.items():
    #     print(f"{key}: {value}")


def main():
    """Entry point for the application."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
