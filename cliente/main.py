from rede import conectar_servidor

def main():
    client_socket = conectar_servidor()

    try:
        pass  # próximas issues: enviar AUTH_CONN, escutar servidor, etc.
    finally:
        client_socket.close()
        print("[CLIENTE] Conexão encerrada.")

if __name__ == "__main__":
    main()