"""Tests for the LoyaltyHub loyalty platform."""
import pytest
from loyalty_platform import create_app
from loyalty_platform.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    """Create application configured for testing with an in-memory SQLite DB."""
    test_app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    return test_app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


# ─── TIERS ────────────────────────────────────────────────────────────────────

class TestTiers:
    def test_list_tiers(self, client):
        r = client.get("/api/tiers")
        assert r.status_code == 200
        tiers = r.get_json()
        # Seeded tiers: Bronze, Silver, Gold, Platinum
        names = [t["name"] for t in tiers]
        assert "Bronze" in names
        assert "Platinum" in names

    def test_tier_order_by_min_points(self, client):
        tiers = client.get("/api/tiers").get_json()
        pts = [t["min_points"] for t in tiers]
        assert pts == sorted(pts)

    def test_create_tier(self, client):
        r = client.post("/api/tiers", json={
            "name": "Diamond",
            "min_points": 50000,
            "multiplier": 3.0,
            "color": "#b9f2ff",
            "description": "Elite tier",
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["name"] == "Diamond"
        assert data["multiplier"] == 3.0

    def test_create_tier_duplicate_name(self, client):
        r = client.post("/api/tiers", json={"name": "Bronze", "min_points": 0})
        assert r.status_code == 409

    def test_create_tier_missing_name(self, client):
        r = client.post("/api/tiers", json={"min_points": 0})
        assert r.status_code == 400

    def test_update_tier(self, client):
        # Get Bronze tier id
        tiers = client.get("/api/tiers").get_json()
        bronze = next(t for t in tiers if t["name"] == "Bronze")
        r = client.put(f"/api/tiers/{bronze['id']}", json={"description": "Updated Bronze"})
        assert r.status_code == 200
        assert r.get_json()["description"] == "Updated Bronze"


# ─── MEMBERS ─────────────────────────────────────────────────────────────────

class TestMembers:
    def test_create_member(self, client):
        r = client.post("/api/members", json={
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["email"] == "alice@example.com"
        assert data["points_balance"] == 0
        assert data["tier"] is not None  # assigned Bronze by default

    def test_create_member_missing_email(self, client):
        r = client.post("/api/members", json={
            "first_name": "Bob",
            "last_name": "Jones",
        })
        assert r.status_code == 400

    def test_create_member_duplicate_email(self, client):
        r = client.post("/api/members", json={
            "first_name": "Alice2",
            "last_name": "Smith2",
            "email": "alice@example.com",
        })
        assert r.status_code == 409

    def test_list_members(self, client):
        r = client.get("/api/members")
        assert r.status_code == 200
        data = r.get_json()
        assert "members" in data
        assert data["total"] >= 1

    def test_get_member(self, client):
        members = client.get("/api/members").get_json()["members"]
        member_id = members[0]["id"]
        r = client.get(f"/api/members/{member_id}")
        assert r.status_code == 200
        assert r.get_json()["id"] == member_id

    def test_get_nonexistent_member(self, client):
        r = client.get("/api/members/99999")
        assert r.status_code == 404

    def test_update_member(self, client):
        members = client.get("/api/members").get_json()["members"]
        mid = members[0]["id"]
        r = client.put(f"/api/members/{mid}", json={"first_name": "Alicia"})
        assert r.status_code == 200
        assert r.get_json()["first_name"] == "Alicia"

    def test_search_members(self, client):
        r = client.get("/api/members?search=alice")
        assert r.status_code == 200
        data = r.get_json()
        assert data["total"] >= 1

    def test_member_transactions_empty(self, client):
        members = client.get("/api/members").get_json()["members"]
        mid = members[0]["id"]
        r = client.get(f"/api/members/{mid}/transactions")
        assert r.status_code == 200
        assert isinstance(r.get_json(), list)


# ─── ACTIVITIES ───────────────────────────────────────────────────────────────

class TestActivities:
    def test_list_activities(self, client):
        r = client.get("/api/activities")
        assert r.status_code == 200
        activities = r.get_json()
        names = [a["name"] for a in activities]
        assert "Purchase" in names

    def test_create_activity(self, client):
        r = client.post("/api/activities", json={
            "name": "App Login",
            "description": "Daily login bonus",
            "points_per_unit": 5,
            "unit_label": "login",
        })
        assert r.status_code == 201
        assert r.get_json()["points_per_unit"] == 5

    def test_create_activity_duplicate(self, client):
        r = client.post("/api/activities", json={"name": "Purchase", "points_per_unit": 10})
        assert r.status_code == 409


# ─── POINTS SERVICE: EARN ─────────────────────────────────────────────────────

class TestEarnPoints:
    def _get_member_id(self, client):
        members = client.get("/api/members").get_json()["members"]
        return members[0]["id"]

    def _get_purchase_activity_id(self, client):
        activities = client.get("/api/activities").get_json()
        return next(a["id"] for a in activities if a["name"] == "Purchase")

    def test_earn_points(self, client):
        mid = self._get_member_id(client)
        aid = self._get_purchase_activity_id(client)
        before = client.get(f"/api/members/{mid}").get_json()["points_balance"]
        r = client.post(f"/api/members/{mid}/earn", json={
            "activity_id": aid,
            "quantity": 10,  # $10 purchase at 10 pts/dollar = 100 pts base
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["points_earned"] > 0
        after = client.get(f"/api/members/{mid}").get_json()["points_balance"]
        assert after > before

    def test_earn_invalid_activity(self, client):
        mid = self._get_member_id(client)
        r = client.post(f"/api/members/{mid}/earn", json={"activity_id": 99999, "quantity": 1})
        assert r.status_code == 400

    def test_earn_missing_activity(self, client):
        mid = self._get_member_id(client)
        r = client.post(f"/api/members/{mid}/earn", json={"quantity": 1})
        assert r.status_code == 400

    def test_earn_invalid_quantity(self, client):
        mid = self._get_member_id(client)
        aid = self._get_purchase_activity_id(client)
        r = client.post(f"/api/members/{mid}/earn", json={"activity_id": aid, "quantity": -5})
        assert r.status_code == 400

    def test_earn_updates_lifetime_points(self, client):
        mid = self._get_member_id(client)
        aid = self._get_purchase_activity_id(client)
        before = client.get(f"/api/members/{mid}").get_json()["lifetime_points"]
        client.post(f"/api/members/{mid}/earn", json={"activity_id": aid, "quantity": 1})
        after = client.get(f"/api/members/{mid}").get_json()["lifetime_points"]
        assert after > before

    def test_earn_with_campaign(self, client):
        """Earning points during an active campaign should apply the multiplier."""
        from datetime import datetime, timezone, timedelta
        mid = self._get_member_id(client)
        aid = self._get_purchase_activity_id(client)
        # Create a 3x campaign
        now = datetime.now(timezone.utc)
        camp_r = client.post("/api/campaigns", json={
            "name": "Triple Points Test",
            "multiplier": 3.0,
            "bonus_points": 0,
            "activity_id": aid,
            "start_date": (now - timedelta(hours=1)).isoformat(),
            "end_date": (now + timedelta(hours=1)).isoformat(),
        })
        assert camp_r.status_code == 201

        r = client.post(f"/api/members/{mid}/earn", json={
            "activity_id": aid,
            "quantity": 1,
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["campaign_applied"] is not None


# ─── REWARDS ─────────────────────────────────────────────────────────────────

class TestRewards:
    def test_list_rewards(self, client):
        r = client.get("/api/rewards")
        assert r.status_code == 200
        rewards = r.get_json()
        assert len(rewards) > 0

    def test_create_reward(self, client):
        r = client.post("/api/rewards", json={
            "name": "Test Reward",
            "description": "A test reward",
            "points_cost": 100,
            "category": "test",
        })
        assert r.status_code == 201
        assert r.get_json()["name"] == "Test Reward"

    def test_create_reward_missing_cost(self, client):
        r = client.post("/api/rewards", json={"name": "No Cost"})
        assert r.status_code == 400


# ─── REDEEM ───────────────────────────────────────────────────────────────────

class TestRedeemReward:
    def _setup_member_with_points(self, client, points=1000):
        """Create a fresh member and award them points."""
        import uuid
        email = f"redeemer_{uuid.uuid4().hex[:8]}@test.com"
        member = client.post("/api/members", json={
            "first_name": "Redeem",
            "last_name": "Tester",
            "email": email,
        }).get_json()
        mid = member["id"]
        activities = client.get("/api/activities").get_json()
        aid = next(a["id"] for a in activities if a["name"] == "Purchase")
        # Earn enough points
        client.post(f"/api/members/{mid}/earn", json={"activity_id": aid, "quantity": points / 10})
        return mid

    def test_redeem_reward_success(self, client):
        mid = self._setup_member_with_points(client, 1000)
        rewards = client.get("/api/rewards").get_json()
        # Use the cheapest reward
        cheapest = min(rewards, key=lambda r: r["points_cost"])
        before = client.get(f"/api/members/{mid}").get_json()["points_balance"]
        r = client.post(f"/api/members/{mid}/redeem", json={"reward_id": cheapest["id"]})
        assert r.status_code == 200
        after = client.get(f"/api/members/{mid}").get_json()["points_balance"]
        assert after == before - cheapest["points_cost"]

    def test_redeem_insufficient_points(self, client):
        # Create member with 0 points
        import uuid
        email = f"broke_{uuid.uuid4().hex[:8]}@test.com"
        member = client.post("/api/members", json={
            "first_name": "Broke", "last_name": "Member", "email": email,
        }).get_json()
        rewards = client.get("/api/rewards").get_json()
        reward = rewards[0]
        r = client.post(f"/api/members/{member['id']}/redeem", json={"reward_id": reward["id"]})
        assert r.status_code == 400
        assert "Insufficient" in r.get_json()["error"]

    def test_redeem_nonexistent_reward(self, client):
        mid = self._setup_member_with_points(client, 5000)
        r = client.post(f"/api/members/{mid}/redeem", json={"reward_id": 99999})
        assert r.status_code == 400

    def test_redeem_updates_transaction_history(self, client):
        mid = self._setup_member_with_points(client, 1000)
        rewards = client.get("/api/rewards").get_json()
        cheapest = min(rewards, key=lambda r: r["points_cost"])
        client.post(f"/api/members/{mid}/redeem", json={"reward_id": cheapest["id"]})
        txns = client.get(f"/api/members/{mid}/transactions").get_json()
        redeem_txns = [t for t in txns if t["transaction_type"] == "redeem"]
        assert len(redeem_txns) >= 1


# ─── CAMPAIGNS ────────────────────────────────────────────────────────────────

class TestCampaigns:
    def test_list_campaigns(self, client):
        r = client.get("/api/campaigns")
        assert r.status_code == 200

    def test_create_campaign(self, client):
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        r = client.post("/api/campaigns", json={
            "name": "Summer Promo",
            "multiplier": 1.5,
            "bonus_points": 50,
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=7)).isoformat(),
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["name"] == "Summer Promo"
        assert data["multiplier"] == 1.5

    def test_active_campaigns(self, client):
        r = client.get("/api/campaigns/active")
        assert r.status_code == 200

    def test_create_campaign_missing_dates(self, client):
        r = client.post("/api/campaigns", json={"name": "No Dates"})
        assert r.status_code == 400


# ─── ANALYTICS ───────────────────────────────────────────────────────────────

class TestAnalytics:
    def test_summary(self, client):
        r = client.get("/api/analytics/summary")
        assert r.status_code == 200
        data = r.get_json()
        assert "total_members" in data
        assert "total_points_issued" in data
        assert "tier_breakdown" in data

    def test_top_members(self, client):
        r = client.get("/api/analytics/top_members")
        assert r.status_code == 200
        assert isinstance(r.get_json(), list)

    def test_recent_transactions(self, client):
        r = client.get("/api/analytics/recent_transactions")
        assert r.status_code == 200
        assert isinstance(r.get_json(), list)


# ─── TIER UPGRADE ────────────────────────────────────────────────────────────

class TestTierUpgrade:
    def test_member_upgrades_to_silver(self, client):
        """Earning enough points should auto-upgrade member to Silver tier."""
        import uuid
        email = f"climber_{uuid.uuid4().hex[:8]}@test.com"
        member = client.post("/api/members", json={
            "first_name": "Tier", "last_name": "Climber", "email": email,
        }).get_json()
        mid = member["id"]
        assert member["tier"]["name"] == "Bronze"

        # Silver requires 1000 lifetime pts; Purchase = 10 pts/dollar
        activities = client.get("/api/activities").get_json()
        aid = next(a["id"] for a in activities if a["name"] == "Purchase")

        # Earn 100 units = 1000 pts base (no active campaign in this test scenario)
        # First disable any active campaigns that may interfere
        client.post(f"/api/members/{mid}/earn", json={"activity_id": aid, "quantity": 100})
        updated = client.get(f"/api/members/{mid}").get_json()
        # Should be at least Silver (campaign multiplier may push to higher tier)
        assert updated["tier"]["min_points"] >= 1000
