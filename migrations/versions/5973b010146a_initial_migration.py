"""Initial migration

Revision ID: 5973b010146a
Revises: 
Create Date: 2024-09-27 23:09:49.867334

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5973b010146a'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # Primero, eliminar las tablas dependientes
    op.drop_table('usuario_modulos')
    op.drop_table('usuario_modulo')
    op.drop_table('rol_permisos')
    op.drop_table('usuario_roles')
    op.drop_table('usuario_empresa')
    op.drop_table('transacciones')
    op.drop_table('notificaciones')
    op.drop_table('cuentas')
    op.drop_table('admin_reportes')
    op.drop_table('admin_facturas')

    # Luego, eliminar las tablas principales
    op.drop_table('modulos')
    op.drop_table('permisos')
    op.drop_table('roles')
    op.drop_table('banco')
    op.drop_table('historial')
    op.drop_table('admin_planes_suscripcion')
    op.drop_table('admin_configuracion_seguridad')

    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.drop_index('ix_usuarios_email')
        batch_op.drop_index('ix_usuarios_nombre_usuario')
    op.drop_table('usuarios')

    # Modificar la tabla 'bancos'
    with op.batch_alter_table('bancos', schema=None) as batch_op:
        batch_op.alter_column('telefono',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
        batch_op.alter_column('estatus',
               existing_type=postgresql.ENUM('activo', 'inactivo', name='banco_estatus_enum'),
               type_=sa.String(length=20),
               existing_nullable=True)
        batch_op.alter_column('fecha_creacion',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
        batch_op.alter_column('fecha_actualizacion',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
        batch_op.create_unique_constraint(None, ['nombre'])
        batch_op.create_unique_constraint(None, ['telefono'])

    # ### end Alembic commands ###

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # Primero, revertir los cambios en la tabla 'bancos'
    with op.batch_alter_table('bancos', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_constraint(None, type_='unique')
        batch_op.alter_column('fecha_actualizacion',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True)
        batch_op.alter_column('fecha_creacion',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True)
        batch_op.alter_column('estatus',
               existing_type=sa.String(length=20),
               type_=postgresql.ENUM('activo', 'inactivo', name='banco_estatus_enum'),
               existing_nullable=True)
        batch_op.alter_column('telefono',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)

    # Luego, recrear las tablas principales
    op.create_table('usuarios',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('usuarios_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('nombre_usuario', sa.VARCHAR(length=64), autoincrement=False, nullable=False),
    sa.Column('email', sa.VARCHAR(length=120), autoincrement=False, nullable=False),
    sa.Column('password_hash', sa.VARCHAR(length=500), autoincrement=False, nullable=False),
    sa.Column('es_admin', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('es_super_admin', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('rol', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('estado', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('fecha_registro', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('nombre', sa.VARCHAR(length=64), autoincrement=False, nullable=False),
    sa.Column('apellido', sa.VARCHAR(length=64), autoincrement=False, nullable=False),
    sa.Column('telefono', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('empresa_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='usuarios_pkey'),
    postgresql_ignore_search_path=False
    )
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.create_index('ix_usuarios_nombre_usuario', ['nombre_usuario'], unique=True)
        batch_op.create_index('ix_usuarios_email', ['email'], unique=True)

    op.create_table('empresas',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('empresas_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('nombre', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('estado', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('rnc', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('direccion', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('fecha_creacion', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('tipo', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('representante', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('telefono', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='empresas_pkey'),
    sa.UniqueConstraint('nombre', name='empresas_nombre_key'),
    sa.UniqueConstraint('rnc', name='empresas_rnc_key'),
    postgresql_ignore_search_path=False
    )
    op.create_table('admin_configuracion_seguridad',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('clave', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('valor', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('descripcion', sa.TEXT(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='admin_configuracion_seguridad_pkey'),
    sa.UniqueConstraint('clave', name='admin_configuracion_seguridad_clave_key')
    )
    op.create_table('admin_planes_suscripcion',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('nombre', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('descripcion', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('precio', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('duracion_dias', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('caracteristicas', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('estado', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='admin_planes_suscripcion_pkey')
    )
    op.create_table('historial',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('accion', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('fecha', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='historial_pkey')
    )
    op.create_table('banco',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('nombre', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('telefono', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('contacto', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('telefono_contacto', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('estatus', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('fecha_creacion', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='banco_pkey'),
    sa.UniqueConstraint('nombre', name='banco_nombre_key'),
    sa.UniqueConstraint('telefono', name='banco_telefono_key')
    )
    op.create_table('roles',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('roles_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('nombre', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('permisos_json', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('descripcion', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='roles_pkey'),
    sa.UniqueConstraint('nombre', name='roles_nombre_key'),
    postgresql_ignore_search_path=False
    )
    op.create_table('permisos',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('permisos_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('nombre', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='permisos_pkey'),
    sa.UniqueConstraint('nombre', name='permisos_nombre_key'),
    postgresql_ignore_search_path=False
    )
    op.create_table('modulos',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('modulos_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('nombre', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('modulo_padre_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['modulo_padre_id'], ['modulos.id'], name='modulos_modulo_padre_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='modulos_pkey'),
    sa.UniqueConstraint('nombre', name='modulos_nombre_key'),
    postgresql_ignore_search_path=False
    )

    # Finalmente, recrear las tablas dependientes
    op.create_table('admin_facturas',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('numero_factura', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('empresa_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('monto', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('fecha_emision', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('fecha_vencimiento', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('estado', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name='admin_facturas_empresa_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='admin_facturas_pkey'),
    sa.UniqueConstraint('numero_factura', name='admin_facturas_numero_factura_key')
    )
    op.create_table('admin_reportes',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('nombre', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('descripcion', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('tipo', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('parametros', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('fecha_creacion', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('usuario_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='admin_reportes_usuario_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='admin_reportes_pkey')
    )
    op.create_table('cuentas',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('cuentas_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('numero', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('tipo', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('saldo', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('banco_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('usuario_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('fecha_creacion', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('fecha_actualizacion', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['banco_id'], ['bancos.id'], name='cuentas_banco_id_fkey'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='cuentas_usuario_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='cuentas_pkey'),
    sa.UniqueConstraint('numero', name='cuentas_numero_key'),
    postgresql_ignore_search_path=False
    )
    op.create_table('notificaciones',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('mensaje', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('fecha_creacion', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('leida', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('usuario_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='notificaciones_usuario_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='notificaciones_pkey')
    )
    op.create_table('transacciones',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('tipo', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('monto', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('descripcion', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('cuenta_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('fecha_creacion', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('fecha_actualizacion', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['cuenta_id'], ['cuentas.id'], name='transacciones_cuenta_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='transacciones_pkey')
    )
    op.create_table('usuario_empresa',
    sa.Column('usuario_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('empresa_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('rol_en_empresa', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name='usuario_empresa_empresa_id_fkey'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='usuario_empresa_usuario_id_fkey'),
    sa.PrimaryKeyConstraint('usuario_id', 'empresa_id', name='usuario_empresa_pkey')
    )
    op.create_table('usuario_roles',
    sa.Column('usuario_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('rol_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['rol_id'], ['roles.id'], name='usuario_roles_rol_id_fkey'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='usuario_roles_usuario_id_fkey')
    )
    op.create_table('rol_permisos',
    sa.Column('rol_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('permiso_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['permiso_id'], ['permisos.id'], name='rol_permisos_permiso_id_fkey'),
    sa.ForeignKeyConstraint(['rol_id'], ['roles.id'], name='rol_permisos_rol_id_fkey')
    )
    op.create_table('usuario_modulo',
    sa.Column('usuario_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('modulo_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('permisos', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('fecha_asignacion', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['modulo_id'], ['modulos.id'], name='usuario_modulo_modulo_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='usuario_modulo_usuario_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('usuario_id', 'modulo_id', name='usuario_modulo_pkey')
    )
    op.create_table('usuario_modulos',
    sa.Column('usuario_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('modulo_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['modulo_id'], ['modulos.id'], name='usuario_modulos_modulo_id_fkey'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='usuario_modulos_usuario_id_fkey')
    )

    # Agregar la clave foránea a la tabla 'usuarios' que no se pudo agregar antes
    op.create_foreign_key('usuarios_empresa_id_fkey', 'usuarios', 'empresas', ['empresa_id'], ['id'])

    # ### end Alembic commands ###