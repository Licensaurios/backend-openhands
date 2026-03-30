from server import init_webapp, socketio

# Ajusta la ruta a tu config de desarrollo en Kali
app = init_webapp("./config/dev.config")

if __name__ == '__main__':
    # Usamos socketio.run para habilitar el servidor de eventos
    print("🚀 OpenHands Backend corriendo en http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)