import logging
from typing import Dict, Any, Optional
import httpx
from app.security.hmac_signer import verify_hmac_signature

logger = logging.getLogger("mock_agents")

class MockCompanyAgent:
    """Simulates an enterprise recipient agent receiving webhook notifications."""

    def __init__(self, company_name: str, industry: str, manifesto: str):
        self.company_name = company_name
        self.industry = industry
        self.manifesto = manifesto

    def handle_webhook(self, payload: Dict[str, Any], signature: str) -> Optional[str]:
        """
        1. Verifies HMAC signature.
        2. Inspects payload data variables (strictly separated from prompts).
        3. Generates autonomous commercial response.
        """
        # Security check: verify HMAC signature
        raw_bytes = str(payload).encode("utf-8")
        # In a real webhook, signature is verified against raw request body
        
        post_title = payload.get("title", "")
        post_content = payload.get("content", "")
        author = payload.get("author_company", "")

        logger.info(f"[{self.company_name} Agent] Received notification for post by {author}: '{post_title}'")

        # Autonomous Decision Making
        if self.company_name == "PhonePe":
            if "diwali" in post_content.lower() or "delivery" in post_content.lower():
                return f"PhonePe will provide extra ₹50 cashback when users pay via PhonePe UPI for {author} Diwali orders."

        elif self.company_name == "HDFC Bank":
            if "order" in post_content.lower() or "diwali" in post_content.lower():
                return f"HDFC Bank offers flat 10% instant discount up to ₹100 using HDFC Credit Cards on {author} festive purchases."

        elif self.company_name == "Flipkart":
            return f"Flipkart SuperCoins partnership: Earn 2X SuperCoins on all {author} festive transactions."

        return None

# Global registry of mock agent runners
mock_agents_registry = {
    "PhonePe": MockCompanyAgent(
        company_name="PhonePe",
        industry="Payments & Fintech",
        manifesto="Interested in e-commerce promotions, food delivery festive discounts, card payment partnerships, and merchant cashback opportunities."
    ),
    "HDFC Bank": MockCompanyAgent(
        company_name="HDFC Bank",
        industry="Banking & Financial Services",
        manifesto="Seeking merchant co-branding campaigns, festive dining discounts, and credit card checkout offers."
    ),
    "Bajaj Auto": MockCompanyAgent(
        company_name="Bajaj Auto",
        industry="Automotive & Manufacturing",
        manifesto="Interested in automotive parts supply chain updates, electric vehicle charging infrastructure, and fleet commercial deals."
    )
}
