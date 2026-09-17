from cliente.rede import conectar_servidor
from utils.protocolo import *

def main():
    client_socket = conectar_servidor()
    
    try:
        nickname = input("Digite seu nickname: ")
        nickname_formatado = formatar_mensagem("AUTH_CONN", nickname)
        client_socket.sendall(nickname_formatado)
    
        
        dados_recebidos = client_socket.recv(1024)
        texto_decodificado = dados_recebidos.decode('utf-8')
        comando, payload = interpretar_mensagem(texto_decodificado)
        print(f"[RESPOSTA RECEBIDA]: {comando} - {payload}")
    finally:
        client_socket.close()
        print("[CLIENTE] Conexão encerrada.")

if __name__ == "__main__":
    main()