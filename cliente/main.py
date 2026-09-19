import threading
from cliente.rede import conectar_servidor
from utils.protocolo import *

# funcao isolada para recepcao de dados
def escutar_servidor(client_socket):
    try:
        while True:
            # trava a execução aguardando pacotes do servidor
            dados = client_socket.recv(1024)
            
            # se dados vier vazio, o servidor encerrou a conexao
            if not dados:
                print("\n[CLIENTE] Conexão com o servidor encerrada.")
                break
                
            # decodifica e separa o comando do payload
            texto_decodificado = dados.decode('utf-8')
            comando, payload = interpretar_mensagem(texto_decodificado)
            
            print(f"\n[MENSAGEM RECEBIDA]: {comando} {payload}")
            
    except ConnectionResetError:
        print("\n[ERRO] O servidor foi desconectado abruptamente.")
    except Exception as e:
        print(f"\n[ERRO] Falha na recepção: {e}")

def main():
    client_socket = conectar_servidor()
    
    try:
        nickname = input("Digite seu nickname: ")
        nickname_formatado = formatar_mensagem("AUTH_CONN", nickname)
        client_socket.sendall(nickname_formatado)
        
        thread_escuta = threading.Thread(target=escutar_servidor, args=(client_socket,))
        thread_escuta.daemon = True
        thread_escuta.start()
        
    except KeyboardInterrupt:
        print("\n[CLIENTE] Encerramento forçado pelo utilizador.")    
    finally:
        client_socket.close()
        print("[CLIENTE] Conexão encerrada.")

if __name__ == "__main__":
    main()