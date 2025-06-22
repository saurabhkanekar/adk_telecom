from datetime import date, timedelta, datetime
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
        print(result)
        if result and len(result["data"]) > 0:
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

    def get_last_transactions(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Fetches the last 5 transaction records for a user.

        Args:
            user_id (int): ID of the user.

        Returns:
            List of Dicts with transaction details, or None if no records found.
        """
        query = """
        SELECT 
            t.trans_id,
            t.transaction_type,
            t.status,
            t.transaction_date,
            t.amount_paid,
            COALESCE(p.plan_name, a.addon_type) AS item_name,
            COALESCE(p.price, a.price) AS item_price
        FROM transactions t
        LEFT JOIN plans p ON t.plan_id = p.plan_id
        LEFT JOIN addons a ON t.addon_id = a.addon_id
        WHERE t.user_id = %s
        ORDER BY t.transaction_date DESC
        LIMIT 5
        """
        transaction_info = self.db.execute_query(query, (user_id,))
        if transaction_info:
            return str(transaction_info["data"])
        else:
            return "Error fetching transaction info!"

    def recharge_user_with_wallet(self, user_id: int, new_plan_id: int, tool_context: ToolContext) -> str:
        """
        Recharges (or changes plan) for a user. Prepaid users are charged from wallet, 
        postpaid users are updated without deduction.

        Args:
            user_id (int): ID of the user.
            new_plan_id (int): ID of the new plan.

        Returns:
            str: Descriptive status message.
        """
        
        # Fetch user details including type and current plan
        user_query = """
        SELECT id, user_type, status, plan_id, current_plan_start
        FROM users WHERE id = %s
        """
        user = self.db.execute_query(user_query, (user_id,))
        if not user:
            return "User not found."
        user = user["data"][0]
        if user["status"] != "active":
            return "User is not active."
        
        user_type = user["user_type"]
        old_plan_id = user["plan_id"]
        current_plan_start = user["current_plan_start"]

        # Fetch new plan
        plan_query = "SELECT plan_id, plan_name, duration, price FROM plans WHERE plan_id = %s"
        new_plan = self.db.execute_query(plan_query, (new_plan_id,))
        if not new_plan:
            return "New plan not found."
        new_plan = new_plan["data"][0]
        plan_name = new_plan["plan_name"]
        plan_price = float(new_plan["price"])
        plan_duration = new_plan["duration"]
        
        # PREPAID flow
        if user_type == "prepaid":
            # Wallet
            wallet_query = "SELECT balance FROM wallet WHERE user_id = %s"
            wallet = self.db.execute_query(wallet_query, (user_id,))
            if not wallet:
                return "Wallet not found."
            wallet = wallet["data"][0]
            balance = wallet["balance"]
            refund_amount = 0.00
            
            # Calculate refund
            if old_plan_id:
                old_plan_query = "SELECT price, duration FROM plans WHERE plan_id = %s"
                old_plan = self.db.execute_query(old_plan_query, (old_plan_id,))
                if old_plan and current_plan_start:
                    old_plan = old_plan["data"][0]
                    total_days = old_plan["duration"]
                    days_used = (date.today() - current_plan_start).days
                    days_remaining = max(total_days - days_used, 0)
                    refund_amount = round((days_remaining / total_days) * float(old_plan["price"]), 2)

            
            net_amount = plan_price - refund_amount

            if net_amount > 0:
                if balance < net_amount:
                    return f"Insufficient wallet balance. Required: ₹{net_amount:.2f}, Available: ₹{balance:.2f}"
                # Deduct from wallet
                update_wallet_query = """
                UPDATE wallet SET balance = balance - %s, last_updated = CURRENT_TIMESTAMP WHERE user_id = %s
                """
                self.db.execute_update(update_wallet_query, (net_amount, user_id))
            elif net_amount < 0:
                refund_to_wallet = abs(net_amount)
                # Credit to wallet
                update_wallet_query = """
                UPDATE wallet SET balance = balance + %s, last_updated = CURRENT_TIMESTAMP WHERE user_id = %s
                """
                self.db.execute_update(update_wallet_query, (refund_to_wallet, user_id))
            
            
            # Update user plan
            new_start = date.today()
            new_end = new_start + timedelta(days=plan_duration)
            update_user_query = """
            UPDATE users SET plan_id = %s, current_plan_start = %s, current_plan_end = %s WHERE id = %s
            """
            self.db.execute_update(update_user_query, (new_plan_id, new_start, new_end, user_id))
            
            # Insert transaction
            txn_query = """
            INSERT INTO transactions (user_id, plan_id, transaction_type, status, transaction_date, amount_paid)
            VALUES (%s, %s, 'recharge', 'success', CURRENT_TIMESTAMP, %s)
            """
            self.db.execute_update(txn_query, (user_id, new_plan_id, net_amount))
            
            interaction_history = tool_context.state.get("interaction_history")
            new_state = { 
                "customer_info": None, 
                "plan_details": None,
                "interaction_history": interaction_history, 
            }
            if user_id:
                user_data = self.get_user_profile(user_id)

            # If customer found, update state with customer info
            if user_data:
                new_state["customer_info"] = {
                    "customer_id" : user_data.get("user_id"),
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "phone_number": user_data.get("phone_number"),
                    "email": user_data.get("email"),
                    "user_type": user_data.get("user_type"),
                }
                new_state["plan_details"] = {
                    "plan_id" :  user_data.get("plan_id"),
                    "plan_name" :  user_data.get("plan_name"),
                    "data_limit_gb": user_data.get("data"),
                    "voice_minutes": user_data.get("calls"),
                    "sms_allowance": user_data.get("msgs"),
                    "monthly_fee": user_data.get("price"),
                    "plan_description": user_data.get("description"),
                    "plan_start": user_data.get("current_plan_start"),
                    "plan_end": user_data.get("current_plan_end"),
                }
            tool_context.state["customer_info"] = new_state["customer_info"]
            tool_context.state["plan_details"] = new_state["plan_details"]
            
            if net_amount > 0:
                payment_message = f"₹{net_amount:.2f} deducted (₹{refund_amount:.2f} refunded)."
            elif net_amount < 0:
                payment_message = f"Plan downgraded. ₹{abs(net_amount):.2f} refunded to wallet (₹{refund_amount:.2f} total refund)."
            else:
                payment_message = f"No amount charged. Plan refund and cost are equal (₹{refund_amount:.2f})."
            return payment_message

        # POSTPAID flow
        elif user_type == "postpaid":
            # Immediate plan update (can be changed to next billing cycle if needed)
            new_start = date.today()
            new_end = new_start + timedelta(days=plan_duration)
            update_user_query = """
            UPDATE users SET plan_id = %s, current_plan_start = %s, current_plan_end = %s WHERE id = %s
            """
            self.db.execute_update(update_user_query, (new_plan_id, new_start, new_end, user_id))

            # Log transaction (no amount deducted)
            txn_query = """
            INSERT INTO transactions (user_id, plan_id, transaction_type, status, transaction_date, amount_paid)
            VALUES (%s, %s, 'recharge', 'success', CURRENT_TIMESTAMP, 0.00)
            """
            self.db.execute_update(txn_query, (user_id, new_plan_id))

            interaction_history = tool_context.state.get("interaction_history")
            new_state = { 
                "customer_info": None, 
                "plan_details": None,
                "interaction_history": interaction_history, 
            }
            if user_id:
                user_data = self.get_user_profile(user_id)

            # If customer found, update state with customer info
            if user_data:
                new_state["customer_info"] = {
                    "customer_id" : user_data.get("user_id"),
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "phone_number": user_data.get("phone_number"),
                    "email": user_data.get("email"),
                    "user_type": user_data.get("user_type"),
                }
                new_state["plan_details"] = {
                    "plan_id" :  user_data.get("plan_id"),
                    "plan_name" :  user_data.get("plan_name"),
                    "data_limit_gb": user_data.get("data"),
                    "voice_minutes": user_data.get("calls"),
                    "sms_allowance": user_data.get("msgs"),
                    "monthly_fee": user_data.get("price"),
                    "plan_description": user_data.get("description"),
                    "plan_start": user_data.get("current_plan_start"),
                    "plan_end": user_data.get("current_plan_end"),
                }
            tool_context.state = new_state

            return f"Postpaid plan changed to '{plan_name}'. No immediate charge. Will be billed in next cycle."

        else:
            return f"Unknown user type: {user_type}"

    def purchase_addon(self, user_id: int, addon_id: int) -> str:
        """
        Purchases an addon for a user by deducting the amount from their wallet.

        Args:
            user_id (int): ID of the user.
            addon_id (int): ID of the addon to purchase.

        Returns:
            str: Status message.
        """

        # 1. Validate user exists
        user_query = "SELECT id, status FROM users WHERE id = %s"
        user = self.db.execute_query(user_query, (user_id,))
        if not user:
            return "User not found or inactive."
        user = user["data"][0]
        if user["status"] != "active":
            return "User not found or inactive."

        # 2. Get addon details
        addon_query = """
        SELECT addon_id, addon_type, price
        FROM addons
        WHERE addon_id = %s
        """
        addon = self.db.execute_query(addon_query, (addon_id,))
        if not addon:
            return "Addon not found."
        addon = addon["data"][0]
        addon_price = float(addon["price"])
        addon_type = addon["addon_type"]

        # 3. Get wallet balance
        wallet_query = "SELECT balance FROM wallet WHERE user_id = %s"
        wallet = self.db.execute_query(wallet_query, (user_id,))
        if not wallet:
            return "Wallet not found."
        wallet = wallet["data"][0]
        balance = float(wallet["balance"])
        if balance < addon_price:
            return f"Insufficient balance. Addon price is ₹{addon_price:.2f}, available balance is ₹{balance:.2f}"

        # 4. Deduct from wallet
        update_wallet_query = """
        UPDATE wallet
        SET balance = balance - %s, last_updated = CURRENT_TIMESTAMP
        WHERE user_id = %s
        """
        self.db.execute_update(update_wallet_query, (addon_price, user_id))

        # 5. Insert into user_addons (28-day default validity)
        added_on = datetime.now().date()
        expiry_date = added_on + timedelta(days=28)  # Can be customized per addon

        insert_user_addon_query = """
        INSERT INTO user_addons (user_id, addon_id, added_on, expiry_date)
        VALUES (%s, %s, %s, %s)
        """
        self.db.execute_update(insert_user_addon_query, (user_id, addon_id, added_on, expiry_date))

        # 6. Log transaction
        txn_query = """
        INSERT INTO transactions (user_id, addon_id, transaction_type, status, transaction_date, amount_paid)
        VALUES (%s, %s, 'addon_purchase', 'success', CURRENT_TIMESTAMP, %s)
        """
        self.db.execute_update(txn_query, (user_id, addon_id, addon_price))

        return f"Addon '{addon_type}' purchased successfully. ₹{addon_price:.2f} deducted. Valid until {expiry_date}."

    def check_wallet_balance(self, user_id: int) -> str:
        """
        Checks the current wallet balance for a user.

        Args:
            user_id (int): ID of the user.

        Returns:
            str: Message with balance or appropriate error.
        """

        # Validate user
        user_query = "SELECT id, status FROM users WHERE id = %s"
        user = self.db.execute_query(user_query, (user_id,))
        if not user:
            return "User not found."
        user = user["data"][0]
        if user["status"] != "active":
            return "User is inactive."

        # Get wallet balance
        wallet_query = "SELECT balance FROM wallet WHERE user_id = %s"
        wallet = self.db.execute_query(wallet_query, (user_id,))
        if not wallet:
            return "Wallet not found."
        wallet = wallet["data"][0]
        balance = float(wallet["balance"])
        return f"Wallet balance for user {user_id} is ₹{balance:.2f}."
