import socket
from config import HOST, PORT

def iniciar_servidor():
    #Instancia o socket utilizando IPv4 e TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    #Associa o socket ao IP e porta e o coloca em modo de escuta
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    
    print(f"[SERVIDOR] Aguardando conexões na porta {PORT}...")
    
    return server_socket

if __name__ == "__main__":
    server_socket = iniciar_servidor()

    try:
         # Issue 3: aceita UMA conexão por enquanto (bloqueante)
        # A partir da Issue 7 isso vira um loop com threading
        conexao, endereco = server_socket.accept()
        ip_cliente, porta_cliente = endereco
        print(f"[SERVIDOR] Cliente conectado: {ip_cliente}:{porta_cliente}")
    finally:
        server_socket.close()