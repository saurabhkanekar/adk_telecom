from google.adk.tools.tool_context import ToolContext
from config.database_config import DatabaseConfig
from typing import Dict, List, Any,Optional
import json


class CustomerServiceTools:
    def __init__(self):
        self.db = DatabaseConfig()

    # Billing Tools
    def get_customer_invoices(self,  tool_context: ToolContext) -> Dict[str, Any]:
        """
        Retrieve all invoices for a specific customer with their basic information.
      """
        query = """
        SELECT i.*, c.first_name, c.last_name, c.email
        FROM invoices i
        JOIN customers c ON i.customer_id = c.customer_id
        WHERE i.customer_id = %s
        ORDER BY i.invoice_date DESC
        LIMIT 5
        """
        

        customer_id = tool_context.state.get("customer_id")
        print("customer_id=========>", str(customer_id))
        result= self.db.execute_query(query, (customer_id,))
        if "success" in result and result["success"]:
            json_result = self.db.to_json(result)
            print(json_result)
        else:
            print("Error:", result.get("error"))
        return json_result


    def get_payment_history(self, tool_context: ToolContext) -> Dict[str, Any]:
        """
        Get complete payment history for a customer including invoice details.

        Args:
            customer_id (int): The unique customer ID

        Returns:
            Dict containing payment records with associated invoice information
        """
        query = """
        SELECT p.*, i.invoice_date, i.total_amount as invoice_amount
        FROM payments p
        JOIN invoices i ON p.invoice_id = i.invoice_id
        WHERE i.customer_id = %s
        ORDER BY p.payment_date DESC
        LIMIT 5
        """

        customer_id = tool_context.state.get("customer_id")
        print("customer_id=========>", str(customer_id))
        result= self.db.execute_query(query, (customer_id,))
        if "success" in result and result["success"]:
            json_result = self.db.to_json(result)
            print(json_result)
        else:
            print("Error:", result.get("error"))
        return json_result

    # Subscription Tools
    def get_customer_subscription(self, tool_context: ToolContext) -> Dict[str, Any]:
        """
        Retrieve the current active subscription details for a specific customer.

        Args:
            customer_id (int): The unique identifier of the customer.

        Returns:
            Dict[str, Any]: A dictionary containing the customer's active subscription details,
                            including plan information such as name, description, monthly fee,
                            data limit, voice minutes, and SMS allowance.
        """

        query = """
        SELECT s.*, p.name as plan_name, p.description, p.monthly_fee,
               p.data_limit_gb, p.voice_minutes, p.sms_allowance
        FROM subscriptions s
        JOIN plans p ON s.plan_id = p.plan_id
        WHERE s.customer_id = %s AND s.status = 'active'
        """
        customer_id = tool_context.state.get("customer_id")
        print("customer_id=========>", str(customer_id))
        result= self.db.execute_query(query, (customer_id,))
        if "success" in result and result["success"]:
            json_result = self.db.to_json(result)
            print(json_result)
        else:
            print("Error:", result.get("error"))
        return json_result

    def get_available_plans(self, plan_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve a list of available subscription plans, optionally filtered by plan type.

        Args:
            plan_type (str, optional): The type of plan to filter by (e.g., 'prepaid', 'postpaid').
                                    If None, all plans are returned.

        Returns:
            Dict[str, Any]: A dictionary containing the available plans, ordered by monthly fee.
        """

        if plan_type:
            query = "SELECT * FROM plans WHERE plan_type = %s ORDER BY monthly_fee"
            return self.db.execute_query(query, (plan_type,))
        else:
            query = "SELECT * FROM plans ORDER BY monthly_fee"
            return self.db.execute_query(query)

    # General Customer Tools
    def find_customer_by_phone(self, phone: str) -> Dict[str, Any]:
        """
        Find customer by phone number.

        This function searches for a customer in the database using their phone number.

        Args:
            phone (str): The phone number of the customer to search for.

        Returns:
            Dict[str, Any]: A dictionary containing the customer details if found,
                            otherwise an empty dictionary.
        """
        query = "SELECT * FROM customers WHERE phone = %s"
        return self.db.execute_query(query, (phone,))

    def find_customer_by_email(self, email: str) -> Dict[str, Any]:
        """
        Find customer by email
        This function searches for a customer in the database using their email address.

        Args:
          email (str): The email address of the customer to search for.

        Returns:
          Dict[str, Any]: A dictionary containing the customer details if found,
                          otherwise an empty dictionary.
        """
        query = "SELECT * FROM customers WHERE email = %s"
        return self.db.execute_query(query, (email,))

    def get_customer_subscription_details(self, customer_id: int) -> Dict[str, Any]:
        """
        Retrieve the current active subscription details for a specific customer.

        Args:
            customer_id (int): The unique identifier of the customer.

        Returns:
            Dict[str, Any]: A dictionary containing the customer's active subscription details,
                            including plan information such as name, description, monthly fee,
                            data limit, voice minutes, and SMS allowance.
        """

        query = """
        SELECT s.*, p.name as plan_name, p.description, p.monthly_fee,
               p.data_limit_gb, p.voice_minutes, p.sms_allowance
        FROM subscriptions s
        JOIN plans p ON s.plan_id = p.plan_id
        WHERE s.customer_id = %s AND s.status = 'active'
        """
        print("customer_id=========>", str(customer_id))
        result= self.db.execute_query(query, (customer_id,))
        return result
    
    ############### custom new tools ###############
    def get_available_plans(self, ) -> List[Dict[str, Any]]:
        """
        Fetch all available prepaid and postpaid plan options.
        Returns:
            List[Dict]: All available plans.
        """
        plans_query = """
        SELECT 
            plan_id,
            plan_name,
            plan_type,
            price,
            duration,
            calls,
            msgs,
            data,
            description
        FROM plans
        ORDER BY plan_id, plan_type
        """

        plans = self.db.execute_query(plans_query)
        return str(plans)

    def get_available_addons(self, ) -> List[Dict[str, Any]]:
        """
        Fetch all available add-on options.
        Returns:
            List[Dict]: All available addons.
        """
    
        addons_query = """
        SELECT 
            addon_id,
            addon_type,
            price,
            amount,
            description
        FROM addons
        ORDER BY addon_id, addon_type
        """

        addons = self.db.execute_query(addons_query)

        return str(addons)

    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve the full profile of a user, including their current plan details.

        Args:
            user_id (int): The unique identifier of the user.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the user's profile info.
                                      Returns None if user is not found.
        """
        query = """
        SELECT 
            u.id AS user_id,
            u.first_name,
            u.last_name,
            u.phone_number,
            u.email,
            u.address,
            u.user_type,
            u.status,
            u.current_plan_start,
            u.current_plan_end,
            p.plan_id,
            p.plan_name,
            p.description,
            p.price,
            p.calls,
            p.msgs,
            p.data,
            p.duration
        FROM users u
        LEFT JOIN plans p ON u.plan_id = p.plan_id
        WHERE u.id = %s
        """

        result = self.db.execute_query(query, (user_id,))
        
        if result and len(result["data"]) > 0:
            print("@"*10)
            print(result)
            return result["data"][0]
        else:
            return None
        
    def get_current_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:

        """
        Returns the currently active plan for a user from the users table.

        Args:
            user_id (int): ID of the user.

        Returns:
            Dict with plan and user details, or None if not found.
        """
        query = """
        SELECT 
            u.id AS user_id,
            u.first_name,
            u.last_name,
            u.current_plan_start,
            u.current_plan_end,
            p.plan_id,
            p.plan_name,
            p.price,
            p.description,
            p.duration,
            p.calls,
            p.msgs,
            p.data
        FROM users u
        LEFT JOIN plans p ON u.plan_id = p.plan_id
        WHERE u.id = %s AND u.status = 'active'
        """
        plan_result = self.db.execute_query(query, (user_id,))
        query = """
        SELECT 
            ua.addon_id,
            a.addon_type,
            a.price,
            a.description,
            ua.added_on,
            ua.expiry_date
        FROM user_addons ua
        JOIN addons a ON ua.addon_id = a.addon_id
        WHERE ua.user_id = %s
        ORDER BY ua.added_on DESC
        """
        addon_result = self.db.execute_query(query, (user_id,))

        return {"plans":plan_result, "addons":addon_result}

    def get_open_tickets(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all unresolved tickets for the user.

        Args:
            user_id (int): ID of the user.

        Returns:
            List of open tickets.
        """
        query = """
        SELECT ticket_id, description, created_at, status
        FROM tech_support
        WHERE user_id = %s AND status != 'closed'
        ORDER BY created_at DESC
        """
        return self.db.execute_query(query, (user_id,))
    
    def get_ticket_history(self, user_id: int) -> List[Dict[str, Any]]:

        """
        Get full support ticket history.

        Args:
            user_id (int): ID of the user.

        Returns:
            List of all support tickets.
        """
        query = """
        SELECT ticket_id, description, created_at, resolved_at, status
        FROM tech_support
        WHERE user_id = %s
        ORDER BY created_at DESC
        limit 5
        """
        return self.db.execute_query(query, (user_id,))

    def create_support_ticket(self, user_id: int, description: str) -> bool:
        """
        Creates a new support ticket for the user.

        Args:
            user_id (int): ID of the user.
            description (str): Issue description.

        Returns:
            True if ticket created successfully, False if ticket creation failed.
        """
        query = """
        INSERT INTO tech_support (user_id, description, status, created_at)
        VALUES (%s, %s, 'open', CURRENT_TIMESTAMP)
        """
        ticket_creation_status = self.db.execute_update(query, (user_id, description))
        print(ticket_creation_status)
        return ticket_creation_status

    def update_ticket_status(self, ticket_id: int, status: str) -> bool:
        """
        Updates status of a support ticket. If status is 'closed', resolved_at is also set.

        Args:
            ticket_id (int): Ticket ID.
            status (str): New status ('open', 'in_progress', 'closed').

        Returns:
            True if updated successfully.
        """
        if status == 'closed':
            query = """
            UPDATE tech_support
            SET status = %s, resolved_at = CURRENT_TIMESTAMP
            WHERE ticket_id = %s
            """
        else:
            query = """
            UPDATE tech_support
            SET status = %s
            WHERE ticket_id = %s
            """
        return self.db.execute_update(query, (status, ticket_id))