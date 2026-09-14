from rede import conectar_servidor
from protocolo import *

def main():
    client_socket = conectar_servidor()
    
    try:
        mensagem_bytes = formatar_mensagem("ECHO", "Teste de conexao")
        client_socket.sendall(mensagem_bytes)
        
        dados_recebidos = client_socket.recv(1024)
        texto_decodificado = dados_recebidos.decode('utf-8')
        comando, payload = interpretar_mensagem(texto_decodificado)
        print(f"[RESPOSTA RECEBIDA]: {comando} - {payload}")
    finally:
        client_socket.close()
        print("[CLIENTE] Conexão encerrada.")

if __name__ == "__main__":
    main()