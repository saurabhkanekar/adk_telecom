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

def set_state_info(state: Dict[str, Any], email: Optional[str] = None, phone: Optional[str] = None) -> Dict[str, Any]:
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
    
    # Try to find customer by email
    if email:
        result = tools.find_customer_by_email(email)
        if result.get("success") and result.get("data"):
            customer_data = result["data"][0]
    
    # If not found by email, try phone
    if not customer_data and phone:
        result = tools.find_customer_by_phone(phone)
        if result.get("success") and result.get("data"):
            customer_data = result["data"][0]
    
    # If customer found, update state with customer info
    if customer_data:
        customer_id = customer_data.get("customer_id")
        state["customer_id"] = customer_id
        state["customer_info"] = customer_data
        
        # Get customer subscription details
        if customer_id:
            subscription_result = tools.get_customer_subscription_details(customer_id)
            if subscription_result.get("success") and subscription_result.get("data"):
                subscription_data = subscription_result["data"][0]
                
                # Update state with plan information
                state["plan_id"] = subscription_data.get("plan_id")
                state["plan_name"] = subscription_data.get("plan_name")
                state["plan_details"] = {
                    "data_limit_gb": subscription_data.get("data_limit_gb"),
                    "voice_minutes": subscription_data.get("voice_minutes"),
                    "sms_allowance": subscription_data.get("sms_allowance"),
                    "monthly_fee": subscription_data.get("monthly_fee"),
                    "description": subscription_data.get("description")
                }
    
    return state

if __name__ == "__main__":
    prefilled_state = copy.deepcopy(initial_state)
    
    test_phone = "9765822200"
    prefilled_state = set_state_info(prefilled_state, phone=test_phone)
    print(prefilled_state)




# # Example usage:
# # To prefill state with a specific customer's information
# def prefill_customer_state() -> Dict[str, Any]:
#     """
#     Prefill the state with a specific customer's information for testing purposes.
    
#     Returns:
#         Dict[str, Any]: Prefilled state with customer information
#     """
#     # Create a copy of the initial state
#     prefilled_state = copy.deepcopy(initial_state)
    
#     # Use a test phone number or email to find a customer
#     test_phone = "+91-9876543210"  # Replace with an actual phone number in your database
#     # test_email = "customer@example.com"  # Alternative: use email instead
    
#     # Set the state information using the test phone/email
#     prefilled_state = set_state_info(prefilled_state, phone=test_phone)
    
#     # If no customer found in database, use hardcoded values for testing
#     if not prefilled_state["customer_id"]:
#         prefilled_state["customer_id"] = 12345
#         prefilled_state["customer_info"] = {
#             "first_name": "Rahul",
#             "last_name": "Sharma",
#             "email": "rahul.sharma@example.com",
#             "phone": test_phone,
#             "address": "123 Main Street, Mumbai, Maharashtra",
#             "registration_date": "2023-01-15"
#         }
#         prefilled_state["plan_id"] = 789
#         prefilled_state["plan_name"] = "Airtel Premium Plus"
#         prefilled_state["plan_details"] = {
#             "data_limit_gb": 100,
#             "voice_minutes": 1500,
#             "sms_allowance": 500,
#             "monthly_fee": 999,
#             "description": "Premium postpaid plan with unlimited 5G data and free Netflix subscription"
#         }
    
#     return prefilled_state
