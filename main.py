from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  

cred = credentials.Certificate("firebaseKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route("/")
def index():
    return "API funcionando"

@app.route("/amigosInfo/<uid>", methods=["GET"])
def get_amigos_info(uid):
    try:
        hoy = datetime.now().strftime("%Y-%m-%d")
        print(f"Consultando amigos de: {uid} para el día {hoy}")
        
        amigos_ref = db.collection("usuarios").document(uid).collection("amigos")
        amigos_docs = amigos_ref.stream()

        amigos_info = []

        for doc in amigos_docs:
            amigo = doc.to_dict()
            print("Amigo encontrado:", amigo)

            uid_amigo = amigo.get("uid")
            if not uid_amigo:
                print("UID del amigo no encontrado en el documento:", doc.id)
                continue

            # Emociones
            emociones_doc = db.collection("usuarios").document(uid_amigo).collection("emociones").document(hoy).get()
            emociones = emociones_doc.to_dict() if emociones_doc.exists else {}
            print(f"Emociones de {uid_amigo}:", emociones)

            # Sueño
            sueno_doc = db.collection("usuarios").document(uid_amigo).collection("sueno").document(hoy).get()
            sueno = sueno_doc.to_dict() if sueno_doc.exists else {
                "duracionHoras": 0,
                "duracionMinutos": 0,
                "horaDormir": None,
                "horaDespertar": None
            }
            print(f"Sueño de {uid_amigo}:", sueno)

            amigos_info.append({
                "uid": uid_amigo,
                "nombre": amigo.get("nombre"),
                "alias": amigo.get("alias"),
                "emociones": emociones,
                "sueno": sueno
            })

        return jsonify(amigos_info)

    except Exception as e:
        print("Error general:", e)
        return jsonify({"error": "Error al obtener la info de los amigos"}), 500

@app.route("/mensajes", methods=["GET"])
def get_mensajes():
    try:
        mensajes_ref = db.collection("mensajes")
        mensajes_docs = mensajes_ref.stream()

        mensajes = []
        for doc in mensajes_docs:
            data = doc.to_dict()
            mensaje = data.get("mensaje")
            if mensaje:
                mensajes.append(mensaje)

        return jsonify({"mensajes": mensajes})
    
    except Exception as e:
        print("Error al obtener mensajes:", e)
        return jsonify({"error": "Error al obtener mensajes"}), 500

@app.route("/enviarMensaje", methods=["POST"])
def set_mensaje():
    try:
        data = request.get_json()
        uid_usuario = data.get("uid_usuario")
        uid_amigo = data.get("uid_amigo")
        mensaje = data.get("mensaje")

        if not uid_usuario or not uid_amigo or not mensaje:
            return jsonify({"error": "Faltan parámetros"}), 400

        amigo_ref_receptor = db.collection("usuarios").document(uid_amigo).collection("amigos").document(uid_usuario)

        amigo_ref_receptor.set({
            "ultimoMensaje": mensaje,
            "fechaUltimoMensaje": datetime.now()
        }, merge=True)

        return jsonify({"message": "Mensaje enviado y actualizado correctamente"}), 200

    except Exception as e:
        print("Error al enviar el mensaje:", e)
        return jsonify({"error": "Error al enviar el mensaje"}), 500

@app.route("/leerUltimoMensaje", methods=["POST"])
def leer_ultimo_mensaje():
    try:
        data = request.get_json()
        uid_usuario = data.get("uid_usuario") 
        uid_amigo = data.get("uid_amigo")

        if not uid_usuario or not uid_amigo:
            return jsonify({"error": "Faltan parámetros"}), 400

        # usuarios/uid_usuario/amigos/uid_amigo
        amigo_ref = db.collection("usuarios").document(uid_usuario).collection("amigos").document(uid_amigo)
        amigo_doc = amigo_ref.get()

        if amigo_doc.exists:
            data = amigo_doc.to_dict()
            ultimo_mensaje = data.get("ultimoMensaje")

            if amigo_doc.exists:
                data = amigo_doc.to_dict()
                ultimo_mensaje = data.get("ultimoMensaje", "no-message")
                return jsonify({"ultimoMensaje": ultimo_mensaje}), 200
            else:
                return jsonify({"ultimoMensaje": "no-message"}), 200
            
        else:
            return jsonify({"ultimoMensaje": "no-message"}), 200

    except Exception as e:
        print("Error al leer el último mensaje:", e)
        return jsonify({"error": "Error al leer el último mensaje"}), 500
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)  