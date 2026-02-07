import os
from typing import Any, Dict, List

import stripe
from supabase import Client

from logger import logger

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class TreatsService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    async def give_treat(
        self, from_user_id: str, photo_id: str, amount: int
    ) -> Dict[str, Any]:
        """Give treats to a photo owner."""
        try:
            # Atomic transaction via RPC
            # This handles:
            # 1. Check photo existence
            # 2. Check self-treat (cannot give to self)
            # 3. Check balance
            # 4. Atomic balance update (give/take)
            # 5. Atomic stats update
            # 6. Transaction log
            res = self.supabase.rpc("give_treat_atomic", {
                "p_from_user_id": from_user_id, 
                "p_photo_id": photo_id, 
                "p_amount": amount
            }).execute()
            
            result = res.data
            
            if not result.get("success"):
                raise ValueError(result.get("error", "Unknown error"))
                
            # Trigger Notification (Fire and forget, or log error but don't fail transaction)
            # We need to know who the receiver was to send notification. 
            # The RPC didn't return to_user_id, but we can fetch it or update RPC to return it.
            # To keep RPC simple, we can fetch owner here or just let the client handle it?
            # Better: Fetch owner to send notification.
            # actually, let's just fetch it quickly, it's a read.
            # Or we can just include to_user_id in RPC return?
            # Let's check RPC again... I didn't return to_user_id.
            # I can query it easily.
            
            try:
                # Get photo owner for notification
                photo_res = self.supabase.table("cat_photos").select("user_id").eq("id", photo_id).single().execute()
                if photo_res.data:
                    to_user_id = photo_res.data["user_id"]
                    
                    # Get actor name
                    actor_res = self.supabase.table("users").select("name").eq("id", from_user_id).single().execute()
                    actor_name = actor_res.data.get("name") if actor_res.data else "Someone"
                    
                    self.supabase.table("notifications").insert({
                            "user_id": to_user_id,
                            "actor_id": from_user_id,
                            "type": "treat",
                            "title": "Treats Received!",
                            "message": f"{actor_name} sent you {amount} treat(s)! 🍬",
                            "resource_id": photo_id,
                            "resource_type": "photo"
                    }).execute()
            except Exception as e:
                logger.error(f"Failed to send treat notification: {e}")

            return {"success": True, "message": f"Gave {amount} treats", "new_balance": result.get("new_balance")}
            
        except Exception as e:
            logger.error(f"Give treat failed: {e}")
            raise e
    
    async def purchase_treats_checkout(
        self, user_id: str, package: str, price_id: str,
        success_url: str, cancel_url: str
    ) -> Dict[str, str]:
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": user_id, "type": "treat_purchase", "package": package},
            payment_intent_data={"metadata": {"user_id": user_id, "package": package}}
        )
        return {
            "checkout_url": checkout_session.url or "",
            "session_id": checkout_session.id
        }
    
    async def get_balance(self, user_id: str) -> Dict[str, Any]:
        user_res = self.supabase.table("users").select("treat_balance").eq("id", user_id).single().execute()
        balance = user_res.data["treat_balance"] if user_res.data else 0
        
        # Get recent transactions - Join logic might be needed to get photo info/user names for real app
        # For MVP returning raw data
        trans_res = self.supabase.table("treats_transactions").select("*").or_(f"from_user_id.eq.{user_id},to_user_id.eq.{user_id}").order("created_at", desc=True).limit(10).execute()
        
        return {
            "balance": balance,
            "recent_transactions": trans_res.data
        }

    async def get_leaderboard(self) -> List[Dict[str, Any]]:
        # Return top receivers (Most Spoiled Cats owners)
        res = self.supabase.table("users").select("id, name, username, picture, total_treats_received").order("total_treats_received", desc=True).limit(10).execute()
        return res.data
