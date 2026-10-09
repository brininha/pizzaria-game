'''
COMENTARIOS ELUCIDATIVOS

este arquivo gerencia a comunicacao do cliente com o servidor.
ele usa threads para permitir que o envio e o recebimento de mensagens 
acontecam ao mesmo tempo e de forma independente.

enquanto a execucao principal fica aguardando as entradas do usuario,
uma thread em segundo plano fica escutando a rede continuamente.
os dados recebidos sao guardados em uma fila para que o sistema principal 
(como a interface grafica) possa le-los e atualiza-los na tela.
'''

import os
import queue
import threading
import time
from cliente.rede import conectar_servidor
from utils.protocolo import *
from utils.seguranca import criptografar, descriptografar
from config import BUFFER_SIZE, ENCODING
from utils.logger import obter_logger

logger = obter_logger("cliente_rede")

# a fila de mensagens funciona como uma ponte de dados.
# a thread que escuta a rede coloca as mensagens aqui dentro, 
# para que a interface grafica possa ler e exibir sem travar o sistema.
fila_mensagens = queue.Queue()

def escutar_servidor(client_socket):
    '''
    funcao executada em segundo plano para receber os dados enviados pelo servidor.
    ela usa um buffer para garantir que mensagens enviadas muito juntas
    ou quebradas pela rede sejam remontadas e lidas corretamente.
    '''
    buffer = "" # acumulador de mensagens tcp
    try:
        while True:
            # aguarda e recebe o bloco de dados do socket
            dados = client_socket.recv(BUFFER_SIZE)
            if not dados:
                logger.warning("conexao com o servidor encerrada.")
                break
                
            # acumula os bytes recebidos convertendo para formato de texto
            buffer += dados.decode(ENCODING)
            
            # enquanto houver quebras de linha completas no buffer, processa uma a uma
            while '\n' in buffer:
                # corta a primeira linha inteira e guarda o resto de volta no buffer
                texto_linha, buffer = buffer.split('\n', 1)
                
                # ignora linhas em branco
                if not texto_linha.strip():
                    continue
                    
                # interpreta o texto para separar o tipo de comando e o conteudo (payload)
                comando, payload = interpretar_mensagem(texto_linha)

                # se for uma mensagem do chat, reverte a criptografia antes de exibir
                if comando == "SEND_CHAT":
                    if ": " in payload:
                        # separa o nome de quem enviou do texto baguncado
                        remetente, texto_cifrado = payload.split(": ", 1)
                        # descriptografa a mensagem de volta para o texto original
                        texto_limpo = descriptografar(texto_cifrado)
                        # guarda o nome e a mensagem limpa na fila para a interface mostrar
                        fila_mensagens.put(("SEND_CHAT", f"{remetente}: {texto_limpo}"))
                    else:
                        fila_mensagens.put(("SEND_CHAT", payload))
                        
                # se for mudanca de status (cor)
                elif comando == "SYNC_STATUS":
                    fila_mensagens.put(("SYNC_STATUS", payload))
                    
                # se for controle de partidas do minijogo
                elif comando in ["CHALLENGE_INVITE","MATCH_REJECT", "MATCH_INFO"]:
                    fila_mensagens.put((comando, payload))            
                
                # repassa qualquer outro comando nao mapeado diretamente para a fila
                else:
                    fila_mensagens.put((comando, payload))
                    
    except ConnectionResetError:
        logger.error("o servidor foi desconectado abruptamente.")
    except Exception as e:
        logger.error(f"falha na recepcao: {e}")
    finally:
        client_socket.close()


def enviar_heartbeat(client_socket):
    '''
    funcao que envia um sinal vazio para o servidor a cada 5 segundos.
    isso serve apenas para manter a conexao tcp ativa, impedindo que o 
    servidor desconecte o cliente por inatividade (timeout).
    '''
    try:
        while True:
            time.sleep(5) 
            mensagem = formatar_mensagem("DEAD_TRIG", "")
            client_socket.sendall(mensagem)
    except Exception:
        # se a conexao cair, a thread encerra sem apresentar erros na tela
        pass

def main():
    '''
    funcao principal que conecta o cliente ao servidor e inicializa as threads.
    no loop final, le o teclado do usuario e envia os comandos formatados para a rede.
    '''
    client_socket = conectar_servidor()
    
    try:
        # solicita a identificacao do usuario e envia o pacote de autenticacao
        nickname = input("Digite seu nickname: ")
        nickname_formatado = formatar_mensagem("AUTH_CONN", nickname)
        client_socket.sendall(nickname_formatado)
        
        # cria e inicia a thread paralela dedicada a escutar o servidor
        thread_escuta = threading.Thread(target=escutar_servidor, args=(client_socket,))
        # o comando daemon permite que a thread feche automaticamente se o programa principal fechar
        thread_escuta.daemon = True
        thread_escuta.start()
        
        # cria e inicia a thread paralela dedicada a manter a conexao viva
        thread_heartbeat = threading.Thread(target=enviar_heartbeat, args=(client_socket,))
        thread_heartbeat.daemon = True
        thread_heartbeat.start()
        
        # loop principal para captura de interacoes do usuario
        while True:
            # aguarda o usuario digitar algo no terminal
            texto_digitado = input()

            # verifica se o usuario digitou o comando de trocar a cor
            if texto_digitado.startswith("/cor "):
                # extrai apenas a cor ignorando a palavra '/cor '
                cor_escolhida = texto_digitado.split(" ", 1)[1]
                # formata o pacote de atualizacao de status e envia
                mensagem_formatada = formatar_mensagem("SYNC_STATUS", cor_escolhida)
                client_socket.sendall(mensagem_formatada)
                
            # se nao tiver comando no inicio, considera como uma mensagem de chat normal
            else:
                # aplica a criptografia no texto antes de enviar para a rede
                texto_cifrado = criptografar(texto_digitado)
                # formata o pacote de chat e envia
                mensagem_formatada = formatar_mensagem("SEND_CHAT", texto_cifrado)
                client_socket.sendall(mensagem_formatada)
           
    except KeyboardInterrupt:
        # encerra de forma limpa caso o usuario pressione ctrl+c
        logger.info("encerramento forcado pelo utilizador.")    
    finally:
        client_socket.close()
        logger.info("conexao encerrada.")

if __name__ == "__main__":
    main()