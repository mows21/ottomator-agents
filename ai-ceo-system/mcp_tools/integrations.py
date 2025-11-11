"""
MCP Integrations for AI CEO System

Connect AI CEO to real-world tools and services for actual execution.
"""

import os
from typing import Dict, Any, List, Optional
import httpx
import json


class StripeIntegration:
    """Stripe payment processing integration"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('STRIPE_API_KEY')
        self.base_url = "https://api.stripe.com/v1"

    async def create_product(self, name: str, description: str, price: float) -> Dict[str, Any]:
        """Create a product in Stripe"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # Create product
        async with httpx.AsyncClient() as client:
            product_response = await client.post(
                f"{self.base_url}/products",
                headers=headers,
                data={
                    "name": name,
                    "description": description
                }
            )

            product = product_response.json()

            # Create price
            price_response = await client.post(
                f"{self.base_url}/prices",
                headers=headers,
                data={
                    "product": product['id'],
                    "unit_amount": int(price * 100),  # Convert to cents
                    "currency": "usd"
                }
            )

            price_data = price_response.json()

            return {
                "product_id": product['id'],
                "price_id": price_data['id'],
                "name": name,
                "price": price
            }

    async def create_payment_link(self, price_id: str) -> str:
        """Create a payment link"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/payment_links",
                headers=headers,
                json={
                    "line_items": [{"price": price_id, "quantity": 1}]
                }
            )

            data = response.json()
            return data.get('url', '')


class AirtableIntegration:
    """Airtable database integration for CRM and data storage"""

    def __init__(self, api_key: Optional[str] = None, base_id: Optional[str] = None):
        self.api_key = api_key or os.getenv('AIRTABLE_API_KEY')
        self.base_id = base_id or os.getenv('AIRTABLE_BASE_ID')
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}"

    async def create_record(self, table_name: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Create a record in Airtable"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{table_name}",
                headers=headers,
                json={"fields": fields}
            )

            return response.json()

    async def get_records(self, table_name: str, filter_formula: Optional[str] = None) -> List[Dict]:
        """Get records from Airtable"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        params = {}
        if filter_formula:
            params["filterByFormula"] = filter_formula

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{table_name}",
                headers=headers,
                params=params
            )

            data = response.json()
            return data.get('records', [])


class GumroadIntegration:
    """Gumroad integration for selling digital products"""

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.getenv('GUMROAD_ACCESS_TOKEN')
        self.base_url = "https://api.gumroad.com/v2"

    async def create_product(
        self,
        name: str,
        description: str,
        price: float,
        download_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a product on Gumroad"""

        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        data = {
            "name": name,
            "description": description,
            "price": int(price * 100),  # Cents
        }

        if download_url:
            data["url"] = download_url

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/products",
                headers=headers,
                json=data
            )

            return response.json()

    async def get_sales(self, after: Optional[str] = None) -> List[Dict]:
        """Get sales data"""

        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        params = {}
        if after:
            params["after"] = after

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/sales",
                headers=headers,
                params=params
            )

            data = response.json()
            return data.get('sales', [])


class EmailIntegration:
    """Email integration for customer communication"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('SENDGRID_API_KEY')
        self.base_url = "https://api.sendgrid.com/v3"

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None
    ) -> bool:
        """Send an email"""

        from_email = from_email or os.getenv('FROM_EMAIL', 'noreply@example.com')

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": from_email},
            "subject": subject,
            "content": [{"type": "text/html", "value": html_content}]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mail/send",
                headers=headers,
                json=payload
            )

            return response.status_code == 202


class GitHubIntegration:
    """GitHub integration for code deployment"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"

    async def create_repository(self, name: str, description: str, private: bool = False) -> Dict[str, Any]:
        """Create a GitHub repository"""

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        payload = {
            "name": name,
            "description": description,
            "private": private
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/user/repos",
                headers=headers,
                json=payload
            )

            return response.json()

    async def create_file(
        self,
        repo_owner: str,
        repo_name: str,
        file_path: str,
        content: str,
        commit_message: str
    ) -> Dict[str, Any]:
        """Create a file in a repository"""

        import base64

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        content_encoded = base64.b64encode(content.encode()).decode()

        payload = {
            "message": commit_message,
            "content": content_encoded
        }

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/repos/{repo_owner}/{repo_name}/contents/{file_path}",
                headers=headers,
                json=payload
            )

            return response.json()


class AnalyticsIntegration:
    """Analytics tracking for revenue and metrics"""

    def __init__(self):
        self.data_file = "ai-ceo-system/data/analytics.json"
        self.data = self.load_data()

    def load_data(self) -> List[Dict]:
        """Load analytics data"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return []

    def save_data(self):
        """Save analytics data"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def track_event(self, event_type: str, properties: Dict[str, Any]):
        """Track an analytics event"""
        from datetime import datetime

        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "properties": properties
        }

        self.data.append(event)
        self.save_data()

    def get_revenue_today(self) -> float:
        """Get total revenue for today"""
        from datetime import datetime

        today = datetime.now().date().isoformat()

        revenue = sum(
            event['properties'].get('amount', 0)
            for event in self.data
            if event['type'] == 'sale'
            and event['timestamp'].startswith(today)
        )

        return revenue

    def get_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get metrics for the last N days"""
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(days=days)

        recent_events = [
            event for event in self.data
            if datetime.fromisoformat(event['timestamp']) > cutoff
        ]

        sales = [e for e in recent_events if e['type'] == 'sale']
        total_revenue = sum(e['properties'].get('amount', 0) for e in sales)

        return {
            "total_events": len(recent_events),
            "total_sales": len(sales),
            "total_revenue": total_revenue,
            "avg_order_value": total_revenue / len(sales) if sales else 0,
            "days": days
        }


# Helper functions for easy integration

async def setup_product_on_stripe(name: str, description: str, price: float) -> Dict[str, Any]:
    """Quick setup of a product on Stripe"""
    stripe = StripeIntegration()
    product = await stripe.create_product(name, description, price)
    payment_link = await stripe.create_payment_link(product['price_id'])

    return {
        **product,
        "payment_link": payment_link
    }


async def setup_product_on_gumroad(name: str, description: str, price: float) -> Dict[str, Any]:
    """Quick setup of a product on Gumroad"""
    gumroad = GumroadIntegration()
    product = await gumroad.create_product(name, description, price)

    return product


def track_sale(amount: float, product_name: str, customer_email: Optional[str] = None):
    """Track a sale in analytics"""
    analytics = AnalyticsIntegration()
    analytics.track_event("sale", {
        "amount": amount,
        "product": product_name,
        "customer": customer_email
    })
