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
import queue
import threading
import time
from cliente.rede import conectar_servidor
from utils.protocolo import *
from utils.seguranca import criptografar, descriptografar
from config import BUFFER_SIZE, ENCODING

fila_mensagens = queue.Queue()

# funcao isolada para recepcao de dados
def escutar_servidor(client_socket):
    buffer = "" # O acumulador de mensagens TCP
    try:
        while True:
            dados = client_socket.recv(BUFFER_SIZE)
            if not dados:
                print("\n[CLIENTE] Conexão com o servidor encerrada.")
                break
                
            # Acumula os bytes recebidos convertendo para string
            buffer += dados.decode(ENCODING)
            
            # Enquanto houver quebras de linha completas no buffer, processa uma a uma!
            while '\n' in buffer:
                # Corta a primeira linha e guarda o resto colado de volta no buffer
                texto_linha, buffer = buffer.split('\n', 1)
                
                if not texto_linha.strip():
                    continue
                    
                # Interpreta apenas a linha cortada perfeitamente
                comando, payload = interpretar_mensagem(texto_linha)

                if comando == "SEND_CHAT":
                    if ": " in payload:
                        remetente, texto_cifrado = payload.split(": ", 1)
                        texto_limpo = descriptografar(texto_cifrado)
                        fila_mensagens.put(("SEND_CHAT", f"{remetente}: {texto_limpo}"))
                    else:
                        fila_mensagens.put(("SEND_CHAT", payload))
                        
                elif comando == "SYNC_STATUS":
                    fila_mensagens.put(("SYNC_STATUS", payload))
                elif comando in ["CHALLENGE_INVITE","MATCH_REJECT", "MATCH_INFO"]:
                    fila_mensagens.put((comando, payload))            
                else:
                    fila_mensagens.put((comando, payload))
                    
    except ConnectionResetError:
        print("\n[ERRO] O servidor foi desconectado abruptamente.", flush=True)
    except Exception as e:
        print(f"\n[ERRO] Falha na recepção: {e}", flush=True)
    finally:
        client_socket.close()

# funcao para enviar o pulso (keep-alive)
def enviar_heartbeat(client_socket):
    try:
        while True:
            time.sleep(5) # pausa de 5 segundos
            mensagem = formatar_mensagem("DEAD_TRIG", "")
            client_socket.sendall(mensagem)
    except Exception:
        # se a conexao cair, a thread morre silenciosamente
        pass

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
        
        thread_heartbeat = threading.Thread(target=enviar_heartbeat, args=(client_socket,))
        thread_heartbeat.daemon = True
        thread_heartbeat.start()
        
        while True:
            # a boca do cliente
            texto_digitado = input()

            if texto_digitado.startswith("/cor "):

                # Extrai apenas a cor (o payload) ignorando o "/cor" e formata com o comando "SYNC_STATUS"
                cor_escolhida = texto_digitado.split(" ", 1)[1]
                mensagem_formatada = formatar_mensagem("SYNC_STATUS", cor_escolhida)
                client_socket.sendall(mensagem_formatada)
            else:
                # Criptografa o texto antes de enviar
                texto_cifrado = criptografar(texto_digitado)
                mensagem_formatada = formatar_mensagem("SEND_CHAT", texto_cifrado)
                client_socket.sendall(mensagem_formatada)
           
        
    except KeyboardInterrupt:
        print("\n[CLIENTE] Encerramento forçado pelo utilizador.")    
    finally:
        client_socket.close()
        print("[CLIENTE] Conexão encerrada.")

if __name__ == "__main__":
    main()