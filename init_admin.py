from app import create_app
from models import db, User
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def init_admin():
    logger.debug("Iniciando la función init_admin")
    app = create_app()
    logger.debug("Aplicación creada")
    with app.app_context():
        logger.debug("Dentro del contexto de la aplicación")
        admin_user = User.query.filter_by(email="el_renyk_rmg@hotmail.com").first()
        logger.debug(f"Usuario encontrado: {admin_user}")
        if admin_user:
            admin_user.role = "admin"
        else:
            admin_user = User(
                name="Renyk", email="el_renyk_rmg@hotmail.com", role="admin"
            )
            admin_user.set_password(
                "tu_contraseña_segura"
            )  # Reemplaza con una contraseña segura
        db.session.add(admin_user)
        db.session.commit()
        logger.info("Administrador inicializado con éxito.")


if __name__ == "__main__":
    init_admin()
