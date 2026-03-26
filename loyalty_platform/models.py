from datetime import datetime, timezone
from loyalty_platform.extensions import db


class Tier(db.Model):
    __tablename__ = "tiers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    min_points = db.Column(db.Integer, nullable=False, default=0)
    multiplier = db.Column(db.Float, nullable=False, default=1.0)
    color = db.Column(db.String(20), nullable=False, default="#6c757d")
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    members = db.relationship("Member", backref="tier", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "min_points": self.min_points,
            "multiplier": self.multiplier,
            "color": self.color,
            "description": self.description,
        }


class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30))
    points_balance = db.Column(db.Integer, nullable=False, default=0)
    lifetime_points = db.Column(db.Integer, nullable=False, default=0)
    tier_id = db.Column(db.Integer, db.ForeignKey("tiers.id"), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    date_of_birth = db.Column(db.Date)
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    transactions = db.relationship(
        "PointTransaction", backref="member", lazy=True, cascade="all, delete-orphan"
    )
    redemptions = db.relationship(
        "Redemption", backref="member", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "points_balance": self.points_balance,
            "lifetime_points": self.lifetime_points,
            "tier": self.tier.to_dict() if self.tier else None,
            "is_active": self.is_active,
            "date_of_birth": (
                self.date_of_birth.isoformat() if self.date_of_birth else None
            ),
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }


class Activity(db.Model):
    """Defines actions that can earn points (purchase, referral, birthday, etc.)"""

    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    points_per_unit = db.Column(db.Integer, nullable=False, default=1)
    unit_label = db.Column(db.String(50), default="action")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    transactions = db.relationship("PointTransaction", backref="activity", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "points_per_unit": self.points_per_unit,
            "unit_label": self.unit_label,
            "is_active": self.is_active,
        }


class Campaign(db.Model):
    """Time-limited bonus point campaigns / multipliers"""

    __tablename__ = "campaigns"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    multiplier = db.Column(db.Float, nullable=False, default=2.0)
    bonus_points = db.Column(db.Integer, nullable=False, default=0)
    activity_id = db.Column(db.Integer, db.ForeignKey("activities.id"), nullable=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    activity = db.relationship("Activity", backref="campaigns")

    def is_running(self):
        now = datetime.now(timezone.utc)
        start = self.start_date.replace(tzinfo=timezone.utc) if self.start_date.tzinfo is None else self.start_date
        end = self.end_date.replace(tzinfo=timezone.utc) if self.end_date.tzinfo is None else self.end_date
        return self.is_active and start <= now <= end

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "multiplier": self.multiplier,
            "bonus_points": self.bonus_points,
            "activity_id": self.activity_id,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_active": self.is_active,
            "is_running": self.is_running(),
        }


class PointTransaction(db.Model):
    __tablename__ = "point_transactions"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activities.id"), nullable=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=True)
    points = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # earn / redeem / adjust
    description = db.Column(db.String(255))
    reference_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    campaign = db.relationship("Campaign", backref="transactions")

    def to_dict(self):
        return {
            "id": self.id,
            "member_id": self.member_id,
            "activity": self.activity.to_dict() if self.activity else None,
            "campaign": self.campaign.to_dict() if self.campaign else None,
            "points": self.points,
            "transaction_type": self.transaction_type,
            "description": self.description,
            "reference_id": self.reference_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Reward(db.Model):
    __tablename__ = "rewards"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    points_cost = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), default="general")
    image_url = db.Column(db.String(255))
    stock = db.Column(db.Integer, nullable=True)  # None = unlimited
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    min_tier_id = db.Column(db.Integer, db.ForeignKey("tiers.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    min_tier = db.relationship("Tier", backref="exclusive_rewards")
    redemptions = db.relationship(
        "Redemption", backref="reward", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "points_cost": self.points_cost,
            "category": self.category,
            "image_url": self.image_url,
            "stock": self.stock,
            "is_active": self.is_active,
            "min_tier": self.min_tier.to_dict() if self.min_tier else None,
        }


class Redemption(db.Model):
    __tablename__ = "redemptions"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    reward_id = db.Column(db.Integer, db.ForeignKey("rewards.id"), nullable=False)
    points_spent = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending/fulfilled/cancelled
    redeemed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "member_id": self.member_id,
            "reward": self.reward.to_dict() if self.reward else None,
            "points_spent": self.points_spent,
            "status": self.status,
            "redeemed_at": self.redeemed_at.isoformat() if self.redeemed_at else None,
        }
