import mysql.connector

# =============================================
# CAMBIA ESTOS DATOS CON LOS TUYOS
# =============================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1234",  # <-- Pon tu contraseña aquí
    "database": "sistema_expedientes"
}

def get_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn

def inicializar_db():
    # Primero crear la base de datos si no existe
    conn = mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS sistema_expedientes")
    conn.commit()
    conn.close()

    # Ahora crear las tablas
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personal (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            apellidos VARCHAR(100) NOT NULL,
            puesto VARCHAR(100) NOT NULL,
            fecha_contratacion DATE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documentos_catalogo (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(150) NOT NULL,
            tipo ENUM('unico', 'mensual') NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expediente_detalle (
            id INT AUTO_INCREMENT PRIMARY KEY,
            personal_id INT NOT NULL,
            documento_id INT NOT NULL,
            mes VARCHAR(20) DEFAULT NULL,
            estado ENUM('entregado', 'pendiente', 'sin_firma') NOT NULL DEFAULT 'pendiente',
            FOREIGN KEY (personal_id) REFERENCES personal(id),
            FOREIGN KEY (documento_id) REFERENCES documentos_catalogo(id)
        )
    """)

    # Insertar documentos base si no existen
    cursor.execute("SELECT COUNT(*) FROM documentos_catalogo")
    if cursor.fetchone()[0] == 0:
        documentos = [
            ("Cédula profesional", "unico"),
            ("Currículum vitae", "unico"),
            ("INE", "unico"),
            ("Formato de banco", "unico"),
            ("Estado de cuenta", "unico"),
            ("Nombramiento 2do trimestre", "unico"),
            ("Nombramiento 3er trimestre", "unico"),
            ("Contrato mensual", "mensual"),
            ("Bitacora de actividades", "mensual"),
        ]
        cursor.executemany(
            "INSERT INTO documentos_catalogo (nombre, tipo) VALUES (%s, %s)",
            documentos
        )

    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente.")
