from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models import db, Usuario, Empresa, usuario_empresa
from werkzeug.security import generate_password_hash

admin = Blueprint("admin", __name__)

@admin.route("/manage_companies")
@login_required
def manage_companies():
    if not current_user.es_admin:
        return redirect(url_for("index"))
    empresas = Empresa.query.all()
    return render_template("manage_companies.html", empresas=empresas)

@admin.route("/companies", methods=["GET"])
@login_required
def get_companies():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    empresas = Empresa.query.all()
    return jsonify([empresa.to_dict() for empresa in empresas])

@admin.route("/companies", methods=["POST"])
@login_required
def create_company():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json or request.form
    nueva_empresa = Empresa(nombre=data["nombre"], estado=data.get("estado", "activo"))
    db.session.add(nueva_empresa)
    db.session.commit()
    return jsonify({"message": "Empresa creada exitosamente", "empresa": nueva_empresa.to_dict()}), 201

@admin.route("/delete_company/<int:empresa_id>", methods=["POST"])
@login_required
def delete_company(empresa_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    empresa = Empresa.query.get_or_404(empresa_id)
    db.session.delete(empresa)
    db.session.commit()
    return jsonify({"message": "Empresa eliminada exitosamente"}), 200

@admin.route("/toggle_company_status/<int:empresa_id>", methods=["POST"])
@login_required
def toggle_company_status(empresa_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    empresa = Empresa.query.get_or_404(empresa_id)
    empresa.estado = "inactivo" if empresa.estado == "activo" else "activo"
    db.session.commit()
    return jsonify({"message": "Estado de la empresa actualizado", "estado": empresa.estado}), 200

@admin.route("/manage_users")
@login_required
def manage_users():
    if not current_user.es_admin:
        return redirect(url_for("index"))
    usuarios = Usuario.query.all()
    empresas = Empresa.query.all()
    return render_template("manage_users.html", usuarios=usuarios, empresas=empresas)

@admin.route("/users", methods=["GET"])
@login_required
def get_users():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    usuarios = Usuario.query.all()
    return jsonify([usuario.to_dict() for usuario in usuarios])

@admin.route("/users", methods=["POST"])
@login_required
def create_user():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json or request.form
    nuevo_usuario = Usuario(
        nombre_usuario=data["nombre_usuario"],
        email=data["email"],
        rol=data.get("rol", "usuario"),
        estado=data.get("estado", "activo"),
    )
    nuevo_usuario.set_password(data["password"])
    db.session.add(nuevo_usuario)
    db.session.commit()
    return jsonify({"message": "Usuario creado exitosamente", "usuario": nuevo_usuario.to_dict()}), 201

@admin.route("/users/<int:usuario_id>", methods=["PUT"])
@login_required
def update_user(usuario_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    usuario = Usuario.query.get_or_404(usuario_id)
    data = request.json
    usuario.nombre_usuario = data.get("nombre_usuario", usuario.nombre_usuario)
    usuario.email = data.get("email", usuario.email)
    usuario.estado = data.get("estado", usuario.estado)
    usuario.rol = data.get("rol", usuario.rol)
    if "password" in data:
        usuario.set_password(data["password"])
    db.session.commit()
    return jsonify({"message": "Usuario actualizado exitosamente", "usuario": usuario.to_dict()})

@admin.route("/users/<int:usuario_id>", methods=["DELETE"])
@login_required
def delete_user(usuario_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    usuario = Usuario.query.get_or_404(usuario_id)
    db.session.delete(usuario)
    db.session.commit()
    return jsonify({"message": "Usuario eliminado exitosamente"}), 200

@admin.route("/toggle_user_status/<int:usuario_id>", methods=["POST"])
@login_required
def toggle_user_status(usuario_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    usuario = Usuario.query.get_or_404(usuario_id)
    usuario.estado = "inactivo" if usuario.estado == "activo" else "activo"
    db.session.commit()
    return jsonify({"message": "Estado del usuario actualizado", "estado": usuario.estado}), 200

@admin.route("/assign_user_to_company", methods=["POST"])
@login_required
def assign_user_to_company():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json or request.form
    usuario_id = data.get("usuario_id")
    empresa_id = data.get("empresa_id")
    rol_en_empresa = data.get("rol_en_empresa", "empleado")

    usuario = Usuario.query.get_or_404(usuario_id)
    empresa = Empresa.query.get_or_404(empresa_id)

    # Verificar si la asignación ya existe
    existing_assignment = db.session.query(usuario_empresa).filter_by(usuario_id=usuario_id, empresa_id=empresa_id).first()

    if existing_assignment:
        # Actualizar el rol si ya existe la asignación
        existing_assignment.rol_en_empresa = rol_en_empresa
    else:
        # Crear nueva asignación
        new_assignment = usuario_empresa.insert().values(
            usuario_id=usuario_id, empresa_id=empresa_id, rol_en_empresa=rol_en_empresa
        )
        db.session.execute(new_assignment)

    db.session.commit()
    return jsonify({"message": "Usuario asignado a la empresa exitosamente"}), 200

@admin.route("/remove_user_from_company", methods=["POST"])
@login_required
def remove_user_from_company():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json or request.form
    usuario_id = data.get("usuario_id")
    empresa_id = data.get("empresa_id")

    # Eliminar la asignación
    db.session.query(usuario_empresa).filter_by(usuario_id=usuario_id, empresa_id=empresa_id).delete()

    db.session.commit()
    return jsonify({"message": "Usuario removido de la empresa exitosamente"}), 200