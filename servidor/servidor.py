import socket
import threading
from config import HOST, PORT
from utils.protocolo import *

clientes_online = {}

def fazer_broadcast(mensagem: bytes, remetente_ignorado=None):
    # Envia mensagem para clientes conectados e pula o envio para 'remetente_ignorado' se fornecido

    for cliente_socket in list(clientes_online.keys()): # list() para evitar erros caso alguém se desconecte durante iteração
        if cliente_socket != remetente_ignorado:
            try:
                cliente_socket.sendall(mensagem)
            except Exception:
                pass

def iniciar_servidor():
    # Instancia o socket utilizando IPv4 e TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Associa o socket ao IP e porta e o coloca em modo de escuta
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    
    print(f"[SERVIDOR] Aguardando conexões na porta {PORT}...")
    
    return server_socket

def lidar_com_cliente(conexao, endereco):
    # Movemos toda a lógica de recepção/envio para dentro da função
    ip_cliente, porta_cliente = endereco
    print(f"[SERVIDOR] Cliente conectado: {ip_cliente}:{porta_cliente}")

    nickname = None
    
    try:
        dados_auth = conexao.recv(1024)
        if not dados_auth:
            print(f"[SERVIDOR] Conexão encerrada abruptamente por {ip_cliente}:{porta_cliente}")
            return

        texto_decodificado = dados_auth.decode('utf-8')
        comando, payload = interpretar_mensagem(texto_decodificado)

        if comando == "AUTH_CONN":
            nickname = payload
            clientes_online[conexao] = nickname
            print(f"[LOGIN] Usuário '{nickname}' entrou no lobby.")
            conexao.sendall(formatar_mensagem("AUTH_REPLY", "OK"))

        while True:
            # Tenta receber os dados, lidando com interrupções abruptas
            try:
                dados = conexao.recv(1024)
            except ConnectionResetError:
                break # Sai do loop se a conexão for forçadamente resetada
            
            # Se recv() retornar zero bytes, o cliente encerrou a conexão de forma limpa
            if not dados:
                break
            
            texto_decodificado = dados.decode('utf-8')
            comando, payload = interpretar_mensagem(texto_decodificado)
            
            if comando == 'ECHO':
                resposta_bytes = formatar_mensagem("ECHO_REPLY", payload)
                conexao.sendall(resposta_bytes)

    finally:   
        if conexao in clientes_online:
            del clientes_online[conexao]
            print(f"[LOGOUT] Usuário '{nickname}' saiu do lobby.")

            # Broadcast de saída (avisa os restantes)
            msg_broadcast = formatar_mensagem("SYNC_STATUS", f"{nickname}_saiu")
            fazer_broadcast(msg_broadcast)
        
        # Garante que o socket específico deste cliente seja fechado sem quebrar o servidor
        conexao.close()
        print(f"[SERVIDOR] Conexão encerrada com {ip_cliente}:{porta_cliente}")

if __name__ == "__main__":
    server_socket = iniciar_servidor()

    try:
        # Loop contínuo para aceitar múltiplos clientes simultaneamente (Issue 7)
        while True:
            conexao, endereco = server_socket.accept()
            
            # Instancia e inicia uma nova thread para o cliente
            thread = threading.Thread(target=lidar_com_cliente, args=(conexao, endereco))
            thread.start()

    finally:
        server_socket.close()