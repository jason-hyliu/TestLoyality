from flask import Blueprint, request, jsonify
from loyalty_platform.extensions import db
from loyalty_platform.models import Member, Tier
from loyalty_platform.services import PointsService
from datetime import date

members_bp = Blueprint("members", __name__, url_prefix="/api/members")


@members_bp.route("", methods=["GET"])
def list_members():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "")
    tier_id = request.args.get("tier_id", type=int)

    q = Member.query
    if search:
        q = q.filter(
            db.or_(
                Member.first_name.ilike(f"%{search}%"),
                Member.last_name.ilike(f"%{search}%"),
                Member.email.ilike(f"%{search}%"),
            )
        )
    if tier_id:
        q = q.filter(Member.tier_id == tier_id)

    pagination = q.order_by(Member.joined_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify(
        {
            "members": [m.to_dict() for m in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "page": page,
        }
    )


@members_bp.route("/<int:member_id>", methods=["GET"])
def get_member(member_id):
    member = db.get_or_404(Member, member_id)
    return jsonify(member.to_dict())


@members_bp.route("", methods=["POST"])
def create_member():
    data = request.get_json(force=True)
    required = ["first_name", "last_name", "email"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    if Member.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"error": "Email already registered"}), 409

    dob = None
    if data.get("date_of_birth"):
        dob = date.fromisoformat(data["date_of_birth"])

    # Assign lowest tier by default
    default_tier = Tier.query.order_by(Tier.min_points.asc()).first()

    member = Member(
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        email=data["email"].strip().lower(),
        phone=data.get("phone", "").strip() or None,
        date_of_birth=dob,
        tier_id=default_tier.id if default_tier else None,
    )
    db.session.add(member)
    db.session.commit()
    return jsonify(member.to_dict()), 201


@members_bp.route("/<int:member_id>", methods=["PUT"])
def update_member(member_id):
    member = db.get_or_404(Member, member_id)
    data = request.get_json(force=True)

    if "first_name" in data:
        member.first_name = data["first_name"].strip()
    if "last_name" in data:
        member.last_name = data["last_name"].strip()
    if "email" in data:
        new_email = data["email"].strip().lower()
        existing = Member.query.filter_by(email=new_email).first()
        if existing and existing.id != member_id:
            return jsonify({"error": "Email already registered"}), 409
        member.email = new_email
    if "phone" in data:
        member.phone = data["phone"].strip() or None
    if "is_active" in data:
        member.is_active = bool(data["is_active"])
    if "date_of_birth" in data:
        member.date_of_birth = date.fromisoformat(data["date_of_birth"]) if data["date_of_birth"] else None

    db.session.commit()
    return jsonify(member.to_dict())


@members_bp.route("/<int:member_id>", methods=["DELETE"])
def delete_member(member_id):
    member = db.get_or_404(Member, member_id)
    db.session.delete(member)
    db.session.commit()
    return jsonify({"message": "Member deleted"}), 200


@members_bp.route("/<int:member_id>/transactions", methods=["GET"])
def member_transactions(member_id):
    member = db.get_or_404(Member, member_id)
    txns = sorted(member.transactions, key=lambda t: t.created_at, reverse=True)
    return jsonify([t.to_dict() for t in txns])


@members_bp.route("/<int:member_id>/redemptions", methods=["GET"])
def member_redemptions(member_id):
    member = db.get_or_404(Member, member_id)
    reds = sorted(member.redemptions, key=lambda r: r.redeemed_at, reverse=True)
    return jsonify([r.to_dict() for r in reds])


@members_bp.route("/<int:member_id>/earn", methods=["POST"])
def earn_points(member_id):
    member = db.get_or_404(Member, member_id)
    data = request.get_json(force=True)
    activity_id = data.get("activity_id")
    quantity = data.get("quantity", 1)
    reference_id = data.get("reference_id")

    if not activity_id:
        return jsonify({"error": "'activity_id' is required"}), 400

    try:
        quantity = float(quantity)
        if quantity <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "'quantity' must be a positive number"}), 400

    result = PointsService.earn_points(member, activity_id, quantity, reference_id)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 200


@members_bp.route("/<int:member_id>/redeem", methods=["POST"])
def redeem_reward(member_id):
    member = db.get_or_404(Member, member_id)
    data = request.get_json(force=True)
    reward_id = data.get("reward_id")

    if not reward_id:
        return jsonify({"error": "'reward_id' is required"}), 400

    result = PointsService.redeem_reward(member, reward_id)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 200
