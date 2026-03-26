"""Core business logic for the loyalty platform."""
from datetime import datetime, timezone
from loyalty_platform.extensions import db
from loyalty_platform.models import (
    Member,
    Tier,
    Activity,
    Campaign,
    PointTransaction,
    Reward,
    Redemption,
)


class PointsService:
    @staticmethod
    def _get_applicable_campaign(activity_id):
        """Return the best active campaign for a given activity (highest multiplier)."""
        now = datetime.now(timezone.utc)
        campaigns = Campaign.query.filter(
            Campaign.is_active == True,  # noqa: E712
            Campaign.start_date <= now,
            Campaign.end_date >= now,
            db.or_(
                Campaign.activity_id == activity_id,
                Campaign.activity_id.is_(None),
            ),
        ).all()
        if not campaigns:
            return None
        return max(campaigns, key=lambda c: c.multiplier)

    @staticmethod
    def _update_tier(member):
        """Recalculate and update member tier based on lifetime points."""
        best_tier = (
            Tier.query.filter(Tier.min_points <= member.lifetime_points)
            .order_by(Tier.min_points.desc())
            .first()
        )
        if best_tier:
            member.tier_id = best_tier.id

    @staticmethod
    def earn_points(member, activity_id, quantity=1.0, reference_id=None):
        """Award points to a member for performing an activity.

        Returns a dict with transaction details or an error.
        """
        activity = db.session.get(Activity, activity_id)
        if not activity:
            return {"error": "Activity not found"}
        if not activity.is_active:
            return {"error": "Activity is not active"}

        base_points = int(activity.points_per_unit * quantity)

        # Apply tier multiplier
        tier_multiplier = member.tier.multiplier if member.tier else 1.0

        # Apply campaign multiplier (if any)
        campaign = PointsService._get_applicable_campaign(activity_id)
        campaign_multiplier = campaign.multiplier if campaign else 1.0
        campaign_bonus = campaign.bonus_points if campaign else 0

        total_points = int(base_points * tier_multiplier * campaign_multiplier) + campaign_bonus

        member.points_balance += total_points
        member.lifetime_points += total_points

        # Re-evaluate tier after earning
        PointsService._update_tier(member)

        txn = PointTransaction(
            member_id=member.id,
            activity_id=activity.id,
            campaign_id=campaign.id if campaign else None,
            points=total_points,
            transaction_type="earn",
            description=(
                f"Earned {total_points} pts for '{activity.name}'"
                + (f" (campaign: {campaign.name})" if campaign else "")
            ),
            reference_id=reference_id,
        )
        db.session.add(txn)
        db.session.commit()

        return {
            "transaction": txn.to_dict(),
            "member": member.to_dict(),
            "points_earned": total_points,
            "campaign_applied": campaign.to_dict() if campaign else None,
        }

    @staticmethod
    def redeem_reward(member, reward_id):
        """Redeem a reward for a member.

        Returns a dict with redemption details or an error.
        """
        reward = db.session.get(Reward, reward_id)
        if not reward:
            return {"error": "Reward not found"}
        if not reward.is_active:
            return {"error": "Reward is not available"}
        if reward.stock is not None and reward.stock <= 0:
            return {"error": "Reward is out of stock"}
        if reward.min_tier_id:
            required_tier = Tier.query.get(reward.min_tier_id)
            member_tier = member.tier
            if not member_tier or member_tier.min_points < required_tier.min_points:
                return {
                    "error": f"This reward requires '{required_tier.name}' tier or above"
                }
        if member.points_balance < reward.points_cost:
            return {
                "error": f"Insufficient points. Required: {reward.points_cost}, Available: {member.points_balance}"
            }

        member.points_balance -= reward.points_cost
        if reward.stock is not None:
            reward.stock -= 1

        redemption = Redemption(
            member_id=member.id,
            reward_id=reward.id,
            points_spent=reward.points_cost,
            status="pending",
        )
        db.session.add(redemption)

        txn = PointTransaction(
            member_id=member.id,
            points=-reward.points_cost,
            transaction_type="redeem",
            description=f"Redeemed '{reward.name}' for {reward.points_cost} pts",
        )
        db.session.add(txn)
        db.session.commit()

        return {
            "redemption": redemption.to_dict(),
            "member": member.to_dict(),
            "points_spent": reward.points_cost,
        }

    @staticmethod
    def adjust_points(member, points, description="Manual adjustment"):
        """Manually adjust a member's points balance (admin use)."""
        member.points_balance += points
        if points > 0:
            member.lifetime_points += points
            PointsService._update_tier(member)

        txn = PointTransaction(
            member_id=member.id,
            points=points,
            transaction_type="adjust",
            description=description,
        )
        db.session.add(txn)
        db.session.commit()

        return {
            "transaction": txn.to_dict(),
            "member": member.to_dict(),
        }
