from loyalty_platform.api.members import members_bp
from loyalty_platform.api.tiers import tiers_bp
from loyalty_platform.api.activities import activities_bp
from loyalty_platform.api.campaigns import campaigns_bp
from loyalty_platform.api.rewards import rewards_bp
from loyalty_platform.api.analytics import analytics_bp

__all__ = [
    "members_bp",
    "tiers_bp",
    "activities_bp",
    "campaigns_bp",
    "rewards_bp",
    "analytics_bp",
]
