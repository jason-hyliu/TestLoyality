from flask import Blueprint, request, jsonify
from loyalty_platform.extensions import db
from loyalty_platform.models import Campaign
from datetime import datetime, timezone

campaigns_bp = Blueprint("campaigns", __name__, url_prefix="/api/campaigns")


def _parse_dt(value):
    """Parse ISO datetime string, supporting both Z and +00:00 suffixes."""
    if not value:
        return None
    value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)


@campaigns_bp.route("", methods=["GET"])
def list_campaigns():
    campaigns = Campaign.query.order_by(Campaign.start_date.desc()).all()
    return jsonify([c.to_dict() for c in campaigns])


@campaigns_bp.route("/active", methods=["GET"])
def active_campaigns():
    now = datetime.now(timezone.utc)
    campaigns = Campaign.query.filter(
        Campaign.is_active == True,  # noqa: E712
        Campaign.start_date <= now,
        Campaign.end_date >= now,
    ).all()
    return jsonify([c.to_dict() for c in campaigns])


@campaigns_bp.route("/<int:campaign_id>", methods=["GET"])
def get_campaign(campaign_id):
    campaign = db.get_or_404(Campaign, campaign_id)
    return jsonify(campaign.to_dict())


@campaigns_bp.route("", methods=["POST"])
def create_campaign():
    data = request.get_json(force=True)
    required = ["name", "start_date", "end_date"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    campaign = Campaign(
        name=data["name"].strip(),
        description=data.get("description", ""),
        multiplier=float(data.get("multiplier", 2.0)),
        bonus_points=int(data.get("bonus_points", 0)),
        activity_id=data.get("activity_id"),
        start_date=_parse_dt(data["start_date"]),
        end_date=_parse_dt(data["end_date"]),
        is_active=data.get("is_active", True),
    )
    db.session.add(campaign)
    db.session.commit()
    return jsonify(campaign.to_dict()), 201


@campaigns_bp.route("/<int:campaign_id>", methods=["PUT"])
def update_campaign(campaign_id):
    campaign = db.get_or_404(Campaign, campaign_id)
    data = request.get_json(force=True)
    if "name" in data:
        campaign.name = data["name"].strip()
    if "description" in data:
        campaign.description = data["description"]
    if "multiplier" in data:
        campaign.multiplier = float(data["multiplier"])
    if "bonus_points" in data:
        campaign.bonus_points = int(data["bonus_points"])
    if "activity_id" in data:
        campaign.activity_id = data["activity_id"]
    if "start_date" in data:
        campaign.start_date = _parse_dt(data["start_date"])
    if "end_date" in data:
        campaign.end_date = _parse_dt(data["end_date"])
    if "is_active" in data:
        campaign.is_active = bool(data["is_active"])
    db.session.commit()
    return jsonify(campaign.to_dict())


@campaigns_bp.route("/<int:campaign_id>", methods=["DELETE"])
def delete_campaign(campaign_id):
    campaign = db.get_or_404(Campaign, campaign_id)
    db.session.delete(campaign)
    db.session.commit()
    return jsonify({"message": "Campaign deleted"})
