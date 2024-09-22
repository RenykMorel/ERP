from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models import db, Usuario, Empresa, usuario_empresa, Rol, Permiso
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

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
    page = request.args.get('page', 1, type=int)
    per_page = 10
    empresas = Empresa.query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'companies': [empresa.to_dict() for empresa in empresas.items],
        'total_pages': empresas.pages,
        'current_page': page
    })

@admin.route("/companies", methods=["POST"])
@login_required
def create_company():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json or request.form
    try:
        nueva_empresa = Empresa(
            nombre=data["nombre"],
            rnc=data["rnc"],
            direccion=data["direccion"],
            tipo=data["tipo"],
            representante=data["representante"],
            estado=data.get("estado", "activo")
        )
        db.session.add(nueva_empresa)
        db.session.commit()
        return jsonify({"message": "Empresa creada exitosamente", "empresa": nueva_empresa.to_dict()}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe una empresa con ese nombre o RNC"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/companies/<int:empresa_id>", methods=["DELETE"])
@login_required
def delete_company(empresa_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    empresa = Empresa.query.get_or_404(empresa_id)
    try:
        db.session.delete(empresa)
        db.session.commit()
        return jsonify({"message": "Empresa eliminada exitosamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/toggle_company_status/<int:empresa_id>", methods=["POST"])
@login_required
def toggle_company_status(empresa_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    empresa = Empresa.query.get_or_404(empresa_id)
    try:
        empresa.estado = "inactivo" if empresa.estado == "activo" else "activo"
        db.session.commit()
        return jsonify({"message": "Estado de la empresa actualizado", "estado": empresa.estado}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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
    page = request.args.get('page', 1, type=int)
    per_page = 10
    usuarios = Usuario.query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'users': [usuario.to_dict() for usuario in usuarios.items],
        'total_pages': usuarios.pages,
        'current_page': page
    })

@admin.route("/users", methods=["POST"])
@login_required
def create_user():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json or request.form
    try:
        nuevo_usuario = Usuario(
            nombre_usuario=data["nombre"],
            email=data["email"],
            rol=data.get("rol", "usuario"),
            estado="activo",
        )
        nuevo_usuario.set_password(data.get("password", "defaultpassword"))
        db.session.add(nuevo_usuario)
        db.session.commit()
        return jsonify({"message": "Usuario creado exitosamente", "usuario": nuevo_usuario.to_dict()}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe un usuario con ese nombre o email"}), 400
    except KeyError as e:
        return jsonify({"error": f"Falta el campo requerido: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/users/<int:usuario_id>", methods=["PUT"])
@login_required
def update_user(usuario_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    usuario = Usuario.query.get_or_404(usuario_id)
    data = request.json
    try:
        usuario.nombre_usuario = data.get("nombre_usuario", usuario.nombre_usuario)
        usuario.email = data.get("email", usuario.email)
        usuario.estado = data.get("estado", usuario.estado)
        usuario.rol = data.get("rol", usuario.rol)
        if "password" in data:
            usuario.set_password(data["password"])
        db.session.commit()
        return jsonify({"message": "Usuario actualizado exitosamente", "usuario": usuario.to_dict()})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe un usuario con ese nombre o email"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/users/<int:usuario_id>", methods=["DELETE"])
@login_required
def delete_user(usuario_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    usuario = Usuario.query.get_or_404(usuario_id)
    try:
        db.session.delete(usuario)
        db.session.commit()
        return jsonify({"message": "Usuario eliminado exitosamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/toggle_user_status/<int:usuario_id>", methods=["POST"])
@login_required
def toggle_user_status(usuario_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    usuario = Usuario.query.get_or_404(usuario_id)
    try:
        usuario.estado = "inactivo" if usuario.estado == "activo" else "activo"
        db.session.commit()
        return jsonify({"message": "Estado del usuario actualizado", "estado": usuario.estado}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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

    try:
        existing_assignment = db.session.query(usuario_empresa).filter_by(usuario_id=usuario_id, empresa_id=empresa_id).first()

        if existing_assignment:
            existing_assignment.rol_en_empresa = rol_en_empresa
        else:
            new_assignment = usuario_empresa.insert().values(
                usuario_id=usuario_id, empresa_id=empresa_id, rol_en_empresa=rol_en_empresa
            )
            db.session.execute(new_assignment)

        db.session.commit()
        return jsonify({"message": "Usuario asignado a la empresa exitosamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/remove_user_from_company", methods=["POST"])
@login_required
def remove_user_from_company():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json or request.form
    usuario_id = data.get("usuario_id")
    empresa_id = data.get("empresa_id")

    try:
        result = db.session.query(usuario_empresa).filter_by(usuario_id=usuario_id, empresa_id=empresa_id).delete()
        if result == 0:
            return jsonify({"error": "No se encontró la asignación del usuario a la empresa"}), 404
        db.session.commit()
        return jsonify({"message": "Usuario removido de la empresa exitosamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/companies/<int:empresa_id>", methods=["GET"])
@login_required
def get_company(empresa_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    empresa = Empresa.query.get_or_404(empresa_id)
    return jsonify(empresa.to_dict())

@admin.route("/companies/<int:empresa_id>", methods=["PUT"])
@login_required
def update_company(empresa_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    empresa = Empresa.query.get_or_404(empresa_id)
    data = request.json
    try:
        empresa.nombre = data.get("nombre", empresa.nombre)
        empresa.rnc = data.get("rnc", empresa.rnc)
        empresa.direccion = data.get("direccion", empresa.direccion)
        empresa.tipo = data.get("tipo", empresa.tipo)
        empresa.representante = data.get("representante", empresa.representante)
        empresa.estado = data.get("estado", empresa.estado)
        db.session.commit()
        return jsonify({"message": "Empresa actualizada exitosamente", "empresa": empresa.to_dict()})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe una empresa con ese nombre o RNC"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/users/<int:usuario_id>", methods=["GET"])
@login_required
def get_user(usuario_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    usuario = Usuario.query.get_or_404(usuario_id)
    return jsonify(usuario.to_dict())

@admin.route("/users/<int:usuario_id>/companies", methods=["GET"])
@login_required
def get_user_companies(usuario_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    usuario = Usuario.query.get_or_404(usuario_id)
    empresas = [{"empresa": empresa.to_dict(), "rol": asignacion.rol_en_empresa} 
                for empresa, asignacion in db.session.query(Empresa, usuario_empresa)
                .join(usuario_empresa)
                .filter(usuario_empresa.c.usuario_id == usuario_id)
                .all()]
    return jsonify(empresas)

@admin.route("/roles", methods=["GET"])
@login_required
def get_roles():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    roles = Rol.query.all()
    return jsonify([rol.to_dict() for rol in roles])

@admin.route("/roles", methods=["POST"])
@login_required
def create_role():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json
    try:
        nuevo_rol = Rol(nombre=data["nombre"], descripcion=data.get("descripcion", ""))
        db.session.add(nuevo_rol)
        db.session.commit()
        return jsonify({"message": "Rol creado exitosamente", "rol": nuevo_rol.to_dict()}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe un rol con ese nombre"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/roles/<int:rol_id>", methods=["PUT"])
@login_required
def update_role(rol_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    rol = Rol.query.get_or_404(rol_id)
    data = request.json
    try:
        rol.nombre = data.get("nombre", rol.nombre)
        rol.descripcion = data.get("descripcion", rol.descripcion)
        db.session.commit()
        return jsonify({"message": "Rol actualizado exitosamente", "rol": rol.to_dict()})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe un rol con ese nombre"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/roles/<int:rol_id>", methods=["DELETE"])
@login_required
def delete_role(rol_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    rol = Rol.query.get_or_404(rol_id)
    try:
        db.session.delete(rol)
        db.session.commit()
        return jsonify({"message": "Rol eliminado exitosamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/permisos", methods=["GET"])
@login_required
def get_permisos():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    permisos = Permiso.query.all()
    return jsonify([permiso.to_dict() for permiso in permisos])

@admin.route("/permisos", methods=["POST"])
@login_required
def create_permiso():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json
    try:
        nuevo_permiso = Permiso(nombre=data["nombre"], descripcion=data.get("descripcion", ""))
        db.session.add(nuevo_permiso)
        db.session.commit()
        return jsonify({"message": "Permiso creado exitosamente", "permiso": nuevo_permiso.to_dict()}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe un permiso con ese nombre"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/permisos/<int:permiso_id>", methods=["PUT"])
@login_required
def update_permiso(permiso_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    permiso = Permiso.query.get_or_404(permiso_id)
    data = request.json
    try:
        permiso.nombre = data.get("nombre", permiso.nombre)
        permiso.descripcion = data.get("descripcion", permiso.descripcion)
        db.session.commit()
        return jsonify({"message": "Permiso actualizado exitosamente", "permiso": permiso.to_dict()})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe un permiso con ese nombre"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/permisos/<int:permiso_id>", methods=["DELETE"])
@login_required
def delete_permiso(permiso_id):
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    permiso = Permiso.query.get_or_404(permiso_id)
    try:
        db.session.delete(permiso)
        db.session.commit()
        return jsonify({"message": "Permiso eliminado exitosamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/assign_permiso_to_rol", methods=["POST"])
@login_required
def assign_permiso_to_rol():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json
    rol_id = data.get("rol_id")
    permiso_id = data.get("permiso_id")

    rol = Rol.query.get_or_404(rol_id)
    permiso = Permiso.query.get_or_404(permiso_id)

    try:
        if permiso not in rol.permisos:
            rol.permisos.append(permiso)
            db.session.commit()
            return jsonify({"message": "Permiso asignado al rol exitosamente"}), 200
        else:
            return jsonify({"message": "El permiso ya está asignado a este rol"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin.route("/remove_permiso_from_rol", methods=["POST"])
@login_required
def remove_permiso_from_rol():
    if not current_user.es_admin:
        return jsonify({"error": "Acceso no autorizado"}), 403
    data = request.json
    rol_id = data.get("rol_id")
    permiso_id = data.get("permiso_id")

    rol = Rol.query.get_or_404(rol_id)
    permiso = Permiso.query.get_or_404(permiso_id)

    try:
        if permiso in rol.permisos:
            rol.permisos.remove(permiso)
            db.session.commit()
            return jsonify({"message": "Permiso removido del rol exitosamente"}), 200
        else:
            return jsonify({"message": "El permiso no estaba asignado a este rol"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500