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
    
    # def get_customer_invoices(self, customer_id: int) -> Dict[str, Any]:
    #     """
    #     Retrieve all invoices for a specific customer with their basic information.

    #     Args:
    #       customer_id (int): The unique customer ID from the customers table

    #     Returns:
    #       Dict containing:
    #       - success (bool): Whether the query was successful
    #       - data (list): List of invoice records with customer details
    #       - error (str): Error message if query failed

    #     """
    #     query = """
    #     SELECT i.*, c.first_name, c.last_name, c.email
    #     FROM invoices i
    #     JOIN customers c ON i.customer_id = c.customer_id
    #     WHERE i.customer_id = %s
    #     ORDER BY i.invoice_date DESC
    #     LIMIT 5
    #     """
    #     return self.db.execute_query(query, (customer_id,))

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
