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
import socket
import threading
import time
from cliente.rede import conectar_servidor
from config import HOST 
from utils.protocolo import *
from utils.seguranca import criptografar, descriptografar

# funcao isolada para recepcao de dados
def escutar_servidor(cliente_socket):
    try:
        # laço infinito pra ficar escutando
        while True:
            # trava a execucao aguardando pacotes do servidor
            dados = cliente_socket.recv(1024)
            
            # se dados vier vazio, o servidor encerrou a conexao
            if not dados:
                print("\n[CLIENTE] Conexão com o servidor encerrada.")
                break
                
            # decodifica e separa o comando do payload
            texto_decodificado = dados.decode('utf-8')
            comando, payload = interpretar_mensagem(texto_decodificado)

            # Intérprete do cliente
            if comando == "SEND_CHAT":
                # O servidor envia no formato "Remetente: texto_cifrado"
                # Precisamos separar para não descriptografar o nome do remetente
                if ": " in payload:
                    remetente, texto_cifrado = payload.split(": ", 1)
                    texto_limpo = descriptografar(texto_cifrado)
                    print(f"\n[CHAT] {remetente}: {texto_limpo}")
                else:
                    texto_limpo = descriptografar(payload)
                    print(f"\n[CHAT] {texto_limpo}")

            elif comando == "SYNC_STATUS":
                print(f"\n[SISTEMA] {payload}")

            else:
                # Comandos de background, como a resposta do AUTH_CONN ou ECHO
                pass
            
    except ConnectionResetError:
        print("\n[ERRO] O servidor foi desconectado abruptamente.", flush=True)
    except Exception as e:
        print(f"\n[ERRO] Falha na recepção: {e}", flush=True)
    finally:
        cliente_socket.close()
        os._exit(0)  # Encerra o programa imediatamente, mesmo que outras threads estejam rodando

# funcao para enviar o pulso (keep-alive)
def enviar_heartbeat(cliente_socket):
    try:
        while True:
            time.sleep(5) # pausa de 5 segundos
            mensagem = formatar_mensagem("DEAD_TRIG", "")
            cliente_socket.sendall(mensagem)
    except Exception:
        # se a conexao cair, a thread morre silenciosamente
        pass

def main():
    cliente_socket = conectar_servidor()

    #Instancia o socket UDP e associa a uma porta livre (0)
    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_udp.bind((HOST, 0)) 
    porta_udp_local = socket_udp.getsockname()[1]

    try:
        nickname = input("Digite seu nickname: ")
        payload_auth = f"{nickname}:{porta_udp_local}"
        nickname_formatado = formatar_mensagem("AUTH_CONN", payload_auth)
        cliente_socket.sendall(nickname_formatado)
        
        # isso aqui podera rodar em paralelo ao codigo principal
        thread_escuta = threading.Thread(target=escutar_servidor, args=(cliente_socket,))
        # isso aqui permite que o programa principal encerre sem esperar por esses processos,
        # eles tambem serao encerrados
        thread_escuta.daemon = True
        thread_escuta.start()
        
        thread_heartbeat = threading.Thread(target=enviar_heartbeat, args=(cliente_socket,))
        thread_heartbeat.daemon = True
        thread_heartbeat.start()
        
        while True:
            # a boca do cliente
            texto_digitado = input()

            if texto_digitado.startswith("/cor "):

                # Extrai apenas a cor (o payload) ignorando o "/cor" e formata com o comando "SYNC_STATUS"
                cor_escolhida = texto_digitado.split(" ", 1)[1]
                mensagem_formatada = formatar_mensagem("SYNC_STATUS", cor_escolhida)
                cliente_socket.sendall(mensagem_formatada)

            elif texto_digitado.startswith("/jogar"):
                # Extrai o nickname do oponente (payload) ignorando o "/jogar"
                nickname_oponente = texto_digitado.split(" ", 1)[1]
                mensagem_formatada = formatar_mensagem("REQ_MATCH", nickname_oponente)
                cliente_socket.sendall(mensagem_formatada)
                print(f"[SISTEMA] Desafio enviado para {nickname_oponente}...")
            else:
                # Criptografa o texto antes de enviar
                texto_cifrado = criptografar(texto_digitado)
                mensagem_formatada = formatar_mensagem("SEND_CHAT", texto_cifrado)
                cliente_socket.sendall(mensagem_formatada)
           
        
    except KeyboardInterrupt:
        print("\n[CLIENTE] Encerramento forçado pelo utilizador.")    
    finally:
        cliente_socket.close()
        print("[CLIENTE] Conexão encerrada.")

if __name__ == "__main__":
    main()