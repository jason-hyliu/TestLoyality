from flask import Blueprint, request, jsonify
from loyalty_platform.extensions import db
from loyalty_platform.models import Activity

activities_bp = Blueprint("activities", __name__, url_prefix="/api/activities")


@activities_bp.route("", methods=["GET"])
def list_activities():
    activities = Activity.query.order_by(Activity.name.asc()).all()
    return jsonify([a.to_dict() for a in activities])


@activities_bp.route("/<int:activity_id>", methods=["GET"])
def get_activity(activity_id):
    activity = db.get_or_404(Activity, activity_id)
    return jsonify(activity.to_dict())


@activities_bp.route("", methods=["POST"])
def create_activity():
    data = request.get_json(force=True)
    if not data.get("name"):
        return jsonify({"error": "'name' is required"}), 400
    if Activity.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "Activity name already exists"}), 409
    activity = Activity(
        name=data["name"].strip(),
        description=data.get("description", ""),
        points_per_unit=int(data.get("points_per_unit", 1)),
        unit_label=data.get("unit_label", "action"),
        is_active=data.get("is_active", True),
    )
    db.session.add(activity)
    db.session.commit()
    return jsonify(activity.to_dict()), 201


@activities_bp.route("/<int:activity_id>", methods=["PUT"])
def update_activity(activity_id):
    activity = db.get_or_404(Activity, activity_id)
    data = request.get_json(force=True)
    if "name" in data:
        activity.name = data["name"].strip()
    if "description" in data:
        activity.description = data["description"]
    if "points_per_unit" in data:
        activity.points_per_unit = int(data["points_per_unit"])
    if "unit_label" in data:
        activity.unit_label = data["unit_label"]
    if "is_active" in data:
        activity.is_active = bool(data["is_active"])
    db.session.commit()
    return jsonify(activity.to_dict())


@activities_bp.route("/<int:activity_id>", methods=["DELETE"])
def delete_activity(activity_id):
    activity = db.get_or_404(Activity, activity_id)
    db.session.delete(activity)
    db.session.commit()
    return jsonify({"message": "Activity deleted"})
