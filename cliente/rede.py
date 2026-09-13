import socket
from config import HOST, PORT

def conectar_servidor (host: str = HOST, port: int = PORT) -> socket.socket:
    # Cria um socket TCP/IP
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sucesso = False
    
    # Conecta ao servidor
    try:
        cliente_socket.connect((host, port))
        sucesso = True

    except ConnectionRefusedError:
        print("[CLIENTE] Não foi possível conectar ao servidor. Verifique se o servidor está em execução.")
        raise
    finally:
        if not sucesso:
            cliente_socket.close()
            
    return cliente_socket