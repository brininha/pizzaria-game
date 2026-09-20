'''
COMENTÁRIOS ELUCIDATIVOS

Já tem vários comentários ao longo do código, só quero registrar a ideia do que se passa nessas linhas.

A linha de execução principal é responsável por ficar recebendo as entradas do cliente.
Usamos threads para permitir que fluxos executem em paralelo, nesse caso, é a escuta constante ao servidor.
Ou seja, o cliente pode ficar horas com a sua linha principal travada pensando no que vai digitar,
mas a recepção de mensagens continuará a acontecer em simultâneo através da thread em segundo plano.
Muito legal.
'''
import os
import threading
from cliente.rede import conectar_servidor
from utils.protocolo import *

# funcao isolada para recepcao de dados
def escutar_servidor(client_socket):
    try:
        # laço infinito pra ficar escutando
        while True:
            # trava a execucao aguardando pacotes do servidor
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
        print("\n[ERRO] O servidor foi desconectado abruptamente.", flush=True)
    except Exception as e:
        print(f"\n[ERRO] Falha na recepção: {e}", flush=True)
    finally:
        client_socket.close()
        os._exit(0)  # Encerra o programa imediatamente, mesmo que outras threads estejam rodando

def main():
    client_socket = conectar_servidor()
    
    try:
        nickname = input("Digite seu nickname: ")
        nickname_formatado = formatar_mensagem("AUTH_CONN", nickname)
        client_socket.sendall(nickname_formatado)
        
        # isso aqui podera rodar em paralelo ao codigo principal
        thread_escuta = threading.Thread(target=escutar_servidor, args=(client_socket,))
        # isso aqui permite que o programa principal encerre sem esperar por esses processos,
        # eles tambem serao encerrados
        thread_escuta.daemon = True
        thread_escuta.start()
        
        while True:
            # a boca do cliente
            texto_digitado = input()
            # empacotamento da mensagem e envio para o servidor
            mensagem_formatada = formatar_mensagem("SEND_CHAT", texto_digitado)
            client_socket.sendall(mensagem_formatada)
        
    except KeyboardInterrupt:
        print("\n[CLIENTE] Encerramento forçado pelo utilizador.")    
    finally:
        client_socket.close()
        print("[CLIENTE] Conexão encerrada.")

if __name__ == "__main__":
    main()