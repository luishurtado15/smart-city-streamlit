from flask import Flask, request, jsonify
 
app = Flask(__name__)
 
@app.route('/sensor/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    print("📥 Datos recibidos:", data)
    # Aquí podrás procesar o guardar la información
    return jsonify({
        "status": "ok",
        "received": data
    }), 200
 
if __name__ == '__main__':
    # Escucha en todas las interfaces de red, puerto 5000
    app.run(host='0.0.0.0', port=5002)