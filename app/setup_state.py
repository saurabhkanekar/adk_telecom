import copy
from datetime import datetime
from typing import Optional, Dict, Any

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
from config.customer_service_tools import CustomerServiceTools

# Create the tools
tools = CustomerServiceTools()


# Define initial state structure
initial_state = {
    "customer_id": None,  # Will be populated when customer is identified
    "customer_info": None,  # Will store customer details
    "plan_id": None,  # Will store the customer's plan ID
    "plan_name": None,  # Will store the plan name
    "plan_details": None,  # Will store detailed plan information
    "interaction_history": [],  # Will track conversation history
}


def set_state_info(
    state: Dict[str, Any],
    customer_id: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Find a customer by email or phone and update the state with customer information.

    Args:
        state: The current state dictionary to update
        email (Optional[str]): Email address of the customer.
        phone (Optional[str]): Phone number of the customer.

    Returns:
        Dict[str, Any]: Updated state dictionary with customer information
    """
    customer_data = None
    if customer_id:
        customer_data = tools.get_user_profile(customer_id)

    # If customer found, update state with customer info
    if customer_data:
        state["customer_info"] = {
            "customer_id" : customer_data.get("user_id"),
            "first_name": customer_data.get("first_name"),
            "last_name": customer_data.get("last_name"),
            "phone_number": customer_data.get("phone_number"),
            "email": customer_data.get("email"),
            "user_type": customer_data.get("user_type"),
        }
        state["plan_details"] = {
            "plan_id" :  customer_data.get("plan_id"),
            "plan_name" :  customer_data.get("plan_name"),
            "data_limit_gb": customer_data.get("data"),
            "voice_minutes": customer_data.get("calls"),
            "sms_allowance": customer_data.get("msgs"),
            "monthly_fee": customer_data.get("price"),
            "plan_description": customer_data.get("description"),
            "plan_start": customer_data.get("current_plan_start"),
            "plan_end": customer_data.get("current_plan_end"),
        }

    return state


if __name__ == "__main__":
    prefilled_state = copy.deepcopy(initial_state)

    test_phone = "9765822200"
    prefilled_state = set_state_info(prefilled_state, phone=test_phone)
    print(prefilled_state)
