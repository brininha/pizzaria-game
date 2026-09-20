import socket
from config import HOST, PORT

def conectar_servidor(host: str = HOST, port: int = PORT) -> socket.socket:
    # Cria um socket TCP/IP
    # AF_INET: address family - internet, isso indica que o socket vai usar endereços do tipo IPv4
    # SOCK_STREAM: indica que o socket é TCP
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sucesso = False
    
    # Conecta ao servidor
    try:
        cliente_socket.connect((host, port)) # abertura de um canal de comunicação entre cliente e servidor
        sucesso = True

    # Tratamento de exceções
    except ConnectionRefusedError:
        print("[CLIENTE] Não foi possível conectar ao servidor. Verifique se o servidor está em execução.")
        raise
    finally:
        if not sucesso:
            cliente_socket.close()
            
    return cliente_socket