from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models import db, User, Company, user_company
from werkzeug.security import generate_password_hash

admin = Blueprint("admin", __name__)


@admin.route("/manage_companies")
@login_required
def manage_companies():
    if current_user.role != "admin":
        return redirect(url_for("index"))
    companies = Company.query.all()
    return render_template("manage_companies.html", companies=companies)


@admin.route("/companies", methods=["GET"])
@login_required
def get_companies():
    if current_user.role != "admin":
        return jsonify({"error": "Acceso no autorizado"}), 403
    companies = Company.query.all()
    return jsonify([company.to_dict() for company in companies])


@admin.route("/companies", methods=["POST"])
@login_required
def create_company():
    if current_user.role != "admin":
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json or request.form
    new_company = Company(name=data["name"], status=data.get("status", "active"))
    db.session.add(new_company)
    db.session.commit()
    return (
        jsonify(
            {"message": "Empresa creada exitosamente", "company": new_company.to_dict()}
        ),
        201,
    )


@admin.route("/delete_company/<int:company_id>", methods=["POST"])
@login_required
def delete_company(company_id):
    if current_user.role != "admin":
        return jsonify({"error": "Acceso no autorizado"}), 403
    company = Company.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    return jsonify({"message": "Empresa eliminada exitosamente"}), 200


@admin.route("/toggle_company_status/<int:company_id>", methods=["POST"])
@login_required
def toggle_company_status(company_id):
    if current_user.role != "admin":
        return jsonify({"error": "Acceso no autorizado"}), 403
    company = Company.query.get_or_404(company_id)
    company.status = "inactive" if company.status == "active" else "active"
    db.session.commit()
    return (
        jsonify(
            {"message": "Estado de la empresa actualizado", "status": company.status}
        ),
        200,
    )


@admin.route("/manage_users")
@login_required
def manage_users():
    if current_user.role != "admin":
        return redirect(url_for("index"))
    users = User.query.all()
    companies = Company.query.all()
    return render_template("manage_users.html", users=users, companies=companies)


@admin.route("/users", methods=["GET"])
@login_required
def get_users():
    if current_user.role != "admin":
        return jsonify({"error": "Acceso no autorizado"}), 403
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])


@admin.route("/users", methods=["POST"])
@login_required
def create_user():
    if current_user.role != "admin":
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json or request.form
    new_user = User(
        username=data["username"],
        email=data["email"],
        role=data.get("role", "user"),
        status=data.get("status", "active"),
    )
    new_user.set_password(data["password"])
    db.session.add(new_user)
    db.session.commit()
    return (
        jsonify({"message": "Usuario creado exitosamente", "user": new_user.to_dict()}),
        201,
    )


@admin.route("/users/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    if current_user.role != "admin":
        return jsonify({"error": "Acceso no autorizado"}), 403
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get("username", user.username)
    user.email = data.get("email", user.email)
    user.status = data.get("status", user.status)
    user.role = data.get("role", user.role)
    if "password" in data:
        user.set_password(data["password"])
    db.session.commit()
    return jsonify(
        {"message": "Usuario actualizado exitosamente", "user": user.to_dict()}
    )


@admin.route("/users/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id):
    if current_user.role != "admin":
        return jsonify({"error": "Acceso no autorizado"}), 403
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Usuario eliminado exitosamente"}), 200


@admin.route("/toggle_user_status/<int:user_id>", methods=["POST"])
@login_required
def toggle_user_status(user_id):
    if current_user.role != "admin":
        return jsonify({"error": "Acceso no autorizado"}), 403
    user = User.query.get_or_404(user_id)
    user.status = "inactive" if user.status == "active" else "active"
    db.session.commit()
    return (
        jsonify({"message": "Estado del usuario actualizado", "status": user.status}),
        200,
    )


@admin.route("/assign_user_to_company", methods=["POST"])
@login_required
def assign_user_to_company():
    if current_user.role != "admin":
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json or request.form
    user_id = data.get("user_id")
    company_id = data.get("company_id")
    role_in_company = data.get("role_in_company", "employee")

    user = User.query.get_or_404(user_id)
    company = Company.query.get_or_404(company_id)

    # Verificar si la asignación ya existe
    existing_assignment = (
        db.session.query(user_company)
        .filter_by(user_id=user_id, company_id=company_id)
        .first()
    )

    if existing_assignment:
        # Actualizar el rol si ya existe la asignación
        existing_assignment.role_in_company = role_in_company
    else:
        # Crear nueva asignación
        new_assignment = user_company.insert().values(
            user_id=user_id, company_id=company_id, role_in_company=role_in_company
        )
        db.session.execute(new_assignment)

    db.session.commit()
    return jsonify({"message": "Usuario asignado a la empresa exitosamente"}), 200


@admin.route("/remove_user_from_company", methods=["POST"])
@login_required
def remove_user_from_company():
    if current_user.role != "admin":
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json or request.form
    user_id = data.get("user_id")
    company_id = data.get("company_id")

    # Eliminar la asignación
    db.session.query(user_company).filter_by(
        user_id=user_id, company_id=company_id
    ).delete()

    db.session.commit()
    return jsonify({"message": "Usuario removido de la empresa exitosamente"}), 200
