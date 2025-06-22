from google.adk.tools.tool_context import ToolContext
from config.database_config import DatabaseConfig
from typing import Dict, List, Any,Optional
import json


class CustomerServiceTools:
    def __init__(self):
        self.db = DatabaseConfig()

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