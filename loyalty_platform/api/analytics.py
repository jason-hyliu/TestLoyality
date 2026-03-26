from flask import Blueprint, jsonify
from loyalty_platform.extensions import db
from loyalty_platform.models import Member, Tier, PointTransaction, Redemption, Activity

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@analytics_bp.route("/summary", methods=["GET"])
def summary():
    total_members = Member.query.count()
    active_members = Member.query.filter_by(is_active=True).count()
    total_points_issued = (
        db.session.query(db.func.sum(PointTransaction.points))
        .filter(PointTransaction.transaction_type == "earn")
        .scalar() or 0
    )
    total_points_redeemed = (
        db.session.query(db.func.sum(PointTransaction.points))
        .filter(PointTransaction.transaction_type == "redeem")
        .scalar() or 0
    )
    total_redemptions = Redemption.query.count()

    tier_breakdown = []
    for tier in Tier.query.order_by(Tier.min_points.asc()).all():
        count = Member.query.filter_by(tier_id=tier.id).count()
        tier_breakdown.append({"tier": tier.to_dict(), "count": count})

    return jsonify(
        {
            "total_members": total_members,
            "active_members": active_members,
            "total_points_issued": total_points_issued,
            "total_points_redeemed": total_points_redeemed,
            "total_redemptions": total_redemptions,
            "tier_breakdown": tier_breakdown,
        }
    )


@analytics_bp.route("/top_members", methods=["GET"])
def top_members():
    members = (
        Member.query.order_by(Member.lifetime_points.desc()).limit(10).all()
    )
    return jsonify([m.to_dict() for m in members])


@analytics_bp.route("/recent_transactions", methods=["GET"])
def recent_transactions():
    txns = (
        PointTransaction.query.order_by(PointTransaction.created_at.desc())
        .limit(20)
        .all()
    )
    return jsonify([t.to_dict() for t in txns])
