"""Seed data for the loyalty platform."""
from datetime import datetime, timezone, timedelta
from loyalty_platform.extensions import db
from loyalty_platform.models import Tier, Activity, Campaign, Reward


def seed_tiers():
    tiers = [
        Tier(
            name="Bronze",
            min_points=0,
            multiplier=1.0,
            color="#cd7f32",
            description="Entry level membership",
        ),
        Tier(
            name="Silver",
            min_points=1000,
            multiplier=1.25,
            color="#c0c0c0",
            description="Earn 25% more points on every action",
        ),
        Tier(
            name="Gold",
            min_points=5000,
            multiplier=1.5,
            color="#ffd700",
            description="Earn 50% more points on every action",
        ),
        Tier(
            name="Platinum",
            min_points=10000,
            multiplier=2.0,
            color="#e5e4e2",
            description="Double points on every action",
        ),
    ]
    for tier in tiers:
        if not Tier.query.filter_by(name=tier.name).first():
            db.session.add(tier)
    db.session.commit()


def seed_activities():
    activities = [
        Activity(
            name="Purchase",
            description="Earn points for every dollar spent",
            points_per_unit=10,
            unit_label="dollar",
        ),
        Activity(
            name="Sign Up",
            description="Welcome bonus points for new members",
            points_per_unit=200,
            unit_label="action",
        ),
        Activity(
            name="Referral",
            description="Earn points for each successful referral",
            points_per_unit=500,
            unit_label="referral",
        ),
        Activity(
            name="Birthday Bonus",
            description="Bonus points on your birthday",
            points_per_unit=300,
            unit_label="action",
        ),
        Activity(
            name="Product Review",
            description="Earn points for leaving a product review",
            points_per_unit=50,
            unit_label="review",
        ),
        Activity(
            name="Social Share",
            description="Earn points for sharing on social media",
            points_per_unit=25,
            unit_label="share",
        ),
    ]
    for activity in activities:
        if not Activity.query.filter_by(name=activity.name).first():
            db.session.add(activity)
    db.session.commit()


def seed_campaigns():
    now = datetime.now(timezone.utc)
    purchase_activity = Activity.query.filter_by(name="Purchase").first()
    campaigns = [
        Campaign(
            name="Double Points Weekend",
            description="Earn double points on all purchases this weekend!",
            multiplier=2.0,
            bonus_points=0,
            activity_id=purchase_activity.id if purchase_activity else None,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=2),
            is_active=True,
        ),
        Campaign(
            name="New Member Bonus",
            description="Extra 100 bonus points for new member sign-ups",
            multiplier=1.0,
            bonus_points=100,
            activity_id=None,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=335),
            is_active=True,
        ),
    ]
    for campaign in campaigns:
        if not Campaign.query.filter_by(name=campaign.name).first():
            db.session.add(campaign)
    db.session.commit()


def seed_rewards():
    gold_tier = Tier.query.filter_by(name="Gold").first()
    platinum_tier = Tier.query.filter_by(name="Platinum").first()
    rewards = [
        Reward(
            name="$5 Store Credit",
            description="Redeem for $5 off your next purchase",
            points_cost=500,
            category="discount",
        ),
        Reward(
            name="$10 Store Credit",
            description="Redeem for $10 off your next purchase",
            points_cost=1000,
            category="discount",
        ),
        Reward(
            name="$25 Store Credit",
            description="Redeem for $25 off your next purchase",
            points_cost=2500,
            category="discount",
        ),
        Reward(
            name="Free Shipping",
            description="Get free shipping on your next order",
            points_cost=200,
            category="shipping",
        ),
        Reward(
            name="Exclusive Member Gift",
            description="A special gift reserved for Gold members and above",
            points_cost=3000,
            category="gift",
            min_tier_id=gold_tier.id if gold_tier else None,
        ),
        Reward(
            name="VIP Experience",
            description="Exclusive VIP event access for Platinum members",
            points_cost=8000,
            category="experience",
            stock=10,
            min_tier_id=platinum_tier.id if platinum_tier else None,
        ),
        Reward(
            name="Brand Merchandise",
            description="Branded tote bag and accessories",
            points_cost=1500,
            category="merchandise",
        ),
    ]
    for reward in rewards:
        if not Reward.query.filter_by(name=reward.name).first():
            db.session.add(reward)
    db.session.commit()


def seed_all():
    seed_tiers()
    seed_activities()
    seed_campaigns()
    seed_rewards()
