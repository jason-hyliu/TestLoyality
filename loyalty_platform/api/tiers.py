from flask import Blueprint, request, jsonify
from loyalty_platform.extensions import db
from loyalty_platform.models import Tier

tiers_bp = Blueprint("tiers", __name__, url_prefix="/api/tiers")


@tiers_bp.route("", methods=["GET"])
def list_tiers():
    tiers = Tier.query.order_by(Tier.min_points.asc()).all()
    return jsonify([t.to_dict() for t in tiers])


@tiers_bp.route("/<int:tier_id>", methods=["GET"])
def get_tier(tier_id):
    tier = db.get_or_404(Tier, tier_id)
    return jsonify(tier.to_dict())


@tiers_bp.route("", methods=["POST"])
def create_tier():
    data = request.get_json(force=True)
    if not data.get("name"):
        return jsonify({"error": "'name' is required"}), 400
    if Tier.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "Tier name already exists"}), 409
    tier = Tier(
        name=data["name"].strip(),
        min_points=data.get("min_points", 0),
        multiplier=data.get("multiplier", 1.0),
        color=data.get("color", "#6c757d"),
        description=data.get("description", ""),
    )
    db.session.add(tier)
    db.session.commit()
    return jsonify(tier.to_dict()), 201


@tiers_bp.route("/<int:tier_id>", methods=["PUT"])
def update_tier(tier_id):
    tier = db.get_or_404(Tier, tier_id)
    data = request.get_json(force=True)
    if "name" in data:
        tier.name = data["name"].strip()
    if "min_points" in data:
        tier.min_points = int(data["min_points"])
    if "multiplier" in data:
        tier.multiplier = float(data["multiplier"])
    if "color" in data:
        tier.color = data["color"]
    if "description" in data:
        tier.description = data["description"]
    db.session.commit()
    return jsonify(tier.to_dict())


@tiers_bp.route("/<int:tier_id>", methods=["DELETE"])
def delete_tier(tier_id):
    tier = db.get_or_404(Tier, tier_id)
    db.session.delete(tier)
    db.session.commit()
    return jsonify({"message": "Tier deleted"})
