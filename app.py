import os
from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_connection, inicializar_db

app = Flask(__name__)
app.secret_key = "sistema_expedientes_2026"
app.config['TEMPLATES_AUTO_RELOAD'] = True

inicializar_db()

@app.route("/")
def index():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total FROM personal")
    total = cursor.fetchone()["total"]
    conn.close()
    return render_template("index.html", total=total)

@app.route("/personal")
def listar_personal():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM personal ORDER BY apellidos ASC")
    trabajadores = cursor.fetchall()
    conn.close()
    return render_template("personal.html", trabajadores=trabajadores)

@app.route("/personal/nuevo", methods=["GET", "POST"])
def nuevo_personal():
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellidos = request.form["apellidos"]
        puesto = request.form["puesto"]
        fecha = request.form["fecha_contratacion"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO personal (nombre, apellidos, puesto, fecha_contratacion) VALUES (%s, %s, %s, %s)",
            (nombre, apellidos, puesto, fecha)
        )
        personal_id = cursor.lastrowid

        cursor.execute("SELECT id FROM documentos_catalogo WHERE tipo = 'unico'")
        docs = cursor.fetchall()
        for doc in docs:
            cursor.execute(
                "INSERT INTO expediente_detalle (personal_id, documento_id, estado) VALUES (%s, %s, 'pendiente')",
                (personal_id, doc[0])
            )

        conn.commit()
        conn.close()
        flash("Trabajador registrado correctamente.", "success")
        return redirect(url_for("listar_personal"))

    return render_template("nuevo_personal.html")

@app.route("/personal/eliminar/<int:personal_id>", methods=["POST"])
def eliminar_personal(personal_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expediente_detalle WHERE personal_id = %s", (personal_id,))
    cursor.execute("DELETE FROM personal WHERE id = %s", (personal_id,))
    conn.commit()
    conn.close()
    flash("Trabajador eliminado correctamente.", "success")
    return redirect(url_for("listar_personal"))

@app.route("/expediente/<int:personal_id>", methods=["GET", "POST"])
def ver_expediente(personal_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM personal WHERE id = %s", (personal_id,))
    trabajador = cursor.fetchone()

    if request.method == "POST":
        cursor2 = conn.cursor()
        cursor.execute("""
            SELECT ed.id, dc.nombre FROM expediente_detalle ed
            JOIN documentos_catalogo dc ON ed.documento_id = dc.id
            WHERE ed.personal_id = %s AND dc.tipo = 'unico'
        """, (personal_id,))
        docs = cursor.fetchall()
        for doc in docs:
            nuevo_estado = request.form.get(f"estado_{doc['id']}", "pendiente")
            cursor2.execute(
                "UPDATE expediente_detalle SET estado = %s WHERE id = %s",
                (nuevo_estado, doc["id"])
            )

        mes = request.form.get("mes")
        if mes:
            cursor.execute("SELECT id FROM documentos_catalogo WHERE tipo = 'mensual'")
            docs_mensuales = cursor.fetchall()
            for doc in docs_mensuales:
                cursor.execute("""
                    SELECT id FROM expediente_detalle
                    WHERE personal_id = %s AND documento_id = %s AND mes = %s
                """, (personal_id, doc["id"], mes))
                existe = cursor.fetchone()
                if not existe:
                    estado_mensual = request.form.get(f"mensual_{doc['id']}", "pendiente")
                    cursor2.execute("""
                        INSERT INTO expediente_detalle (personal_id, documento_id, mes, estado)
                        VALUES (%s, %s, %s, %s)
                    """, (personal_id, doc["id"], mes, estado_mensual))

        conn.commit()
        flash("Expediente actualizado.", "success")

    cursor.execute("""
        SELECT ed.id, dc.nombre, ed.estado FROM expediente_detalle ed
        JOIN documentos_catalogo dc ON ed.documento_id = dc.id
        WHERE ed.personal_id = %s AND dc.tipo = 'unico'
    """, (personal_id,))
    docs_unicos = cursor.fetchall()

    cursor.execute("""
        SELECT ed.id, dc.nombre, ed.mes, ed.estado FROM expediente_detalle ed
        JOIN documentos_catalogo dc ON ed.documento_id = dc.id
        WHERE ed.personal_id = %s AND dc.tipo = 'mensual'
        ORDER BY ed.mes ASC
    """, (personal_id,))
    docs_mensuales = cursor.fetchall()

    cursor.execute("SELECT * FROM documentos_catalogo WHERE tipo = 'mensual'")
    catalogo_mensual = cursor.fetchall()

    conn.close()

    pendientes = [d for d in docs_unicos if d["estado"] != "entregado"]

    return render_template("expediente.html",
        trabajador=trabajador,
        docs_unicos=docs_unicos,
        docs_mensuales=docs_mensuales,
        catalogo_mensual=catalogo_mensual,
        pendientes=pendientes
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
