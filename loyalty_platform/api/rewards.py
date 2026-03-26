from flask import Blueprint, request, jsonify
from loyalty_platform.extensions import db
from loyalty_platform.models import Reward

rewards_bp = Blueprint("rewards", __name__, url_prefix="/api/rewards")


@rewards_bp.route("", methods=["GET"])
def list_rewards():
    category = request.args.get("category")
    q = Reward.query
    if category:
        q = q.filter(Reward.category == category)
    rewards = q.order_by(Reward.points_cost.asc()).all()
    return jsonify([r.to_dict() for r in rewards])


@rewards_bp.route("/<int:reward_id>", methods=["GET"])
def get_reward(reward_id):
    reward = db.get_or_404(Reward, reward_id)
    return jsonify(reward.to_dict())


@rewards_bp.route("", methods=["POST"])
def create_reward():
    data = request.get_json(force=True)
    required = ["name", "points_cost"]
    for field in required:
        if data.get(field) is None:
            return jsonify({"error": f"'{field}' is required"}), 400
    reward = Reward(
        name=data["name"].strip(),
        description=data.get("description", ""),
        points_cost=int(data["points_cost"]),
        category=data.get("category", "general"),
        image_url=data.get("image_url"),
        stock=data.get("stock"),
        is_active=data.get("is_active", True),
        min_tier_id=data.get("min_tier_id"),
    )
    db.session.add(reward)
    db.session.commit()
    return jsonify(reward.to_dict()), 201


@rewards_bp.route("/<int:reward_id>", methods=["PUT"])
def update_reward(reward_id):
    reward = db.get_or_404(Reward, reward_id)
    data = request.get_json(force=True)
    if "name" in data:
        reward.name = data["name"].strip()
    if "description" in data:
        reward.description = data["description"]
    if "points_cost" in data:
        reward.points_cost = int(data["points_cost"])
    if "category" in data:
        reward.category = data["category"]
    if "image_url" in data:
        reward.image_url = data["image_url"]
    if "stock" in data:
        reward.stock = data["stock"]
    if "is_active" in data:
        reward.is_active = bool(data["is_active"])
    if "min_tier_id" in data:
        reward.min_tier_id = data["min_tier_id"]
    db.session.commit()
    return jsonify(reward.to_dict())


@rewards_bp.route("/<int:reward_id>", methods=["DELETE"])
def delete_reward(reward_id):
    reward = db.get_or_404(Reward, reward_id)
    db.session.delete(reward)
    db.session.commit()
    return jsonify({"message": "Reward deleted"})
