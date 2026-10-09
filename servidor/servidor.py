'''
COMENTARIOS ELUCIDATIVOS

este arquivo e o servidor central do lobby.
ele recebe as conexoes dos clientes usando o protocolo tcp e gerencia quem esta online.

o servidor faz tres coisas principais simultaneamente:
- fica aguardando novas conexoes (main).
- cria uma thread exclusiva para escutar e responder cada cliente conectado (lidar_com_cliente).
- roda uma funcao em paralelo para desconectar quem travou ou ficou inativo (monitorar_inativos).

quando duas pessoas vao jogar, o servidor apenas envia o ip e a porta udp
de um para o outro. a partida acontece via udp diretamente entre os computadores,
sem passar por este servidor.
'''

import socket
import threading
import random
import time
from config import HOST, PORT
from utils.protocolo import *
from utils.logger import obter_logger

logger = obter_logger("servidor")

# variavel global que guarda os dados de quem esta conectado.
# a chave e o socket da conexao e o valor e um dicionario com nome, status, porta udp e ultimo sinal.
clientes_online = {}

def fazer_broadcast(mensagem: bytes, remetente_ignorado=None):
    '''
    funcao para enviar uma mensagem para todos os clientes conectados.
    se quisermos que o autor da mensagem nao receba o proprio aviso, 
    passamos a conexao dele na variavel remetente_ignorado.
    '''
    for cliente_socket in list(clientes_online.keys()): 
        if cliente_socket != remetente_ignorado:
            try:
                cliente_socket.sendall(mensagem)
            except Exception:
                pass

def iniciar_servidor():
    '''
    configura o socket do servidor e a porta de rede para aceitar conexoes tcp.
    '''
    # instancia o socket utilizando ipv4 e tcp
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # quando o servidor e desligado, a porta e liberada imediatamente
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # associa o socket ao ip e porta e o coloca em modo de escuta
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    
    logger.info(f"aguardando conexoes na porta {PORT}...")
    
    return server_socket

def lidar_com_cliente(conexao, endereco):
    '''
    funcao executada em uma thread separada para cada cliente.
    ela recebe os dados de autenticacao, salva o cliente na lista e 
    entra em um loop infinito aguardando comandos.
    o bloco finally garante que o cliente seja removido caso a conexao caia.
    '''
    ip_cliente, porta_cliente = endereco
    logger.info(f"cliente conectado: {ip_cliente}:{porta_cliente}")

    nickname = None
    
    try:
        # recebe a primeira mensagem para identificar o cliente e a porta udp
        dados_auth = conexao.recv(1024)
        if not dados_auth:
            logger.warning(f"conexao encerrada abruptamente por {ip_cliente}:{porta_cliente}")
            return

        texto_decodificado = dados_auth.decode('utf-8')
        comando, payload = interpretar_mensagem(texto_decodificado)

        if comando == "AUTH_CONN":
            # separa o nickname e a porta udp enviados pelo cliente
            partes = payload.split(":")
            nickname = partes[0]
            porta_udp_local = None

            if len(partes) > 1:
                try:
                    porta_udp_local = int(partes[1])
                except ValueError:
                    logger.error(f"porta udp invalida recebida de {ip_cliente}:{porta_cliente}")

            # salva o cliente na variavel global com status disponivel
            clientes_online[conexao] = {
                "nome": nickname, 
                "ultimo_sinal": time.time(),
                "porta_udp": porta_udp_local,
                "status": "disponivel" 
            }
            
            logger.info(f"usuario '{nickname}' entrou no lobby (udp: {porta_udp_local})")
            
            # confirma para o cliente que ele entrou
            conexao.sendall(formatar_mensagem("AUTH_REPLY", "OK"))
            
            # envia para o novo cliente os nomes de quem ja estava conectado
            for socket_antigo, dados in clientes_online.items():
                if socket_antigo != conexao:
                    nome_antigo = dados["nome"]
                    conexao.sendall(formatar_mensagem("SYNC_STATUS", f"{nome_antigo} entrou"))
            
            # avisa os outros clientes que um novo jogador entrou
            fazer_broadcast(formatar_mensagem("SYNC_STATUS", f"{nickname} entrou"), remetente_ignorado=conexao)

        # loop principal de recebimento de mensagens deste cliente
        while True:
            # tenta ler os dados, trata erros de fechamento forcado
            try:
                dados = conexao.recv(1024)
            except ConnectionResetError:
                break 
            
            # se o cliente fechar a conexao normalmente, recv retorna vazio
            if not dados:
                break
            
            texto_decodificado = dados.decode('utf-8')
            comando, payload = interpretar_mensagem(texto_decodificado)
            
            # atualiza o tempo do ultimo sinal de vida do cliente
            if conexao in clientes_online:
                clientes_online[conexao]["ultimo_sinal"] = time.time()
                
            # comando enviado apenas para manter a conexao ativa
            if comando == 'DEAD_TRIG':
                continue

            # comando de envio de mensagem no chat
            if comando == 'SEND_CHAT':
                # junta o nome do remetente com o texto da mensagem
                mensagem_chat = f"{nickname}: {payload}"
                resposta_bytes = formatar_mensagem("SEND_CHAT", mensagem_chat)

                # envia para todos os outros clientes, menos para quem enviou
                fazer_broadcast(resposta_bytes, remetente_ignorado=conexao)
                
                quem_enviou = clientes_online[conexao]["nome"]
                logger.info(f"[{quem_enviou} diz no chat]: {payload}")

            # comando que avisa mudanca na cor do avatar
            elif comando == 'SYNC_STATUS':
                mensagem_status = f"{nickname} mudou para {payload}"
                resposta_bytes = formatar_mensagem("SYNC_STATUS", mensagem_status)
                fazer_broadcast(resposta_bytes, remetente_ignorado=conexao)

            # comando de teste para verificar resposta da rede
            elif comando == 'ECHO':
                resposta_bytes = formatar_mensagem("ECHO_REPLY", payload)
                conexao.sendall(resposta_bytes)

            # comando de convite para partida
            elif comando == 'REQ_MATCH':
                nickname_oponente = payload
                oponente_encontrado = False

                # procura o cliente solicitado na lista de conectados
                for socket_cliente, dados_cliente in clientes_online.items():
                    if dados_cliente["nome"] == nickname_oponente:
                        oponente_encontrado = True
                        
                        # verifica se o jogador ja esta em outra partida
                        if dados_cliente.get("status") != "disponivel":
                            resposta_bytes = formatar_mensagem("MATCH_REJECT", "Ocupado")
                            conexao.sendall(resposta_bytes)
                        else:
                            # envia o convite para o oponente
                            socket_cliente.sendall(formatar_mensagem("CHALLENGE_INVITE", nickname))
                        break 

                # se nao achar o nome na lista, avisa quem enviou o convite
                if not oponente_encontrado:
                    resposta_bytes = formatar_mensagem("MATCH_REJECT", "Oponente offline")
                    conexao.sendall(resposta_bytes)  

            # comando de aceite do convite
            elif comando == 'ACCEPT_MATCH':
                nickname_oponente = payload
                socket_oponente = None

                # encontra a conexao de quem fez o convite originalmente
                for socket_cliente, dados_cliente in clientes_online.items():
                    if dados_cliente["nome"] == nickname_oponente:
                        socket_oponente = socket_cliente
                        break

                if socket_oponente:
                    status_remetente = clientes_online[conexao].get("status")
                    status_oponente = clientes_online[socket_oponente].get("status")
                    
                    # verifica se ambos ainda estao com status disponivel
                    if status_remetente == "disponivel" and status_oponente == "disponivel": 
                    
                        # altera o status dos dois para jogando
                        clientes_online[conexao]["status"] = "jogando"
                        clientes_online[socket_oponente]["status"] = "jogando"

                        # avisa o lobby que eles entraram em partida
                        fazer_broadcast(formatar_mensagem("SYNC_STATUS", f"{nickname} entrou em partida"))
                        fazer_broadcast(formatar_mensagem("SYNC_STATUS", f"{nickname_oponente} entrou em partida"))
                        
                        # obtem ips e portas udp de ambos
                        ip_recebedor = conexao.getpeername()[0]
                        porta_recebedor = clientes_online[conexao]["porta_udp"]
                        ip_oponente = socket_oponente.getpeername()[0]
                        porta_oponente = clientes_online[socket_oponente]["porta_udp"]

                        # gera um numero para os clientes sincronizarem a ordem dos eventos da partida
                        semente_partida = random.randint(1000, 9999)

                        # envia as informacoes de conexao cruzadas para os dois clientes
                        socket_oponente.sendall(formatar_mensagem("MATCH_INFO", f"{ip_recebedor}:{porta_recebedor}:{semente_partida}"))
                        conexao.sendall(formatar_mensagem("MATCH_INFO", f"{ip_oponente}:{porta_oponente}:{semente_partida}"))
                        
                    else:
                        # rejeita caso um deles ja tenha entrado em partida nesse intervalo
                        conexao.sendall(formatar_mensagem("MATCH_REJECT", "Conflito de estado: jogador ocupado"))
            
            # comando de recusa do convite
            elif comando == 'REJECT_MATCH':
                nickname_oponente = payload
                for socket_cliente, dados_cliente in clientes_online.items():
                    if dados_cliente["nome"] == nickname_oponente:
                        socket_cliente.sendall(formatar_mensagem("MATCH_REJECT", "Convite recusado"))
                        break      
                    
            # comando informando que a partida acabou e o jogador retornou
            elif comando == 'BACK_LOBBY':
                if conexao in clientes_online:
                    clientes_online[conexao]["status"] = "disponivel"
                    fazer_broadcast(formatar_mensagem("SYNC_STATUS", f"{nickname} voltou"))

    finally:   
        # limpa os dados do cliente se ele desconectar ou der erro
        if conexao in clientes_online:
            nickname = clientes_online[conexao]["nome"] 
            del clientes_online[conexao]
            logger.info(f"{nickname} saiu do lobby")

            # avisa os demais clientes da saida
            msg_broadcast = formatar_mensagem("SYNC_STATUS", f"{nickname} saiu")
            fazer_broadcast(msg_broadcast)
        
        # fecha a conexao tcp e libera os recursos
        conexao.close()
        logger.info(f"conexao encerrada com {ip_cliente}:{porta_cliente}")

def monitorar_inativos():
    '''
    funcao que roda em background para desconectar clientes que pararam de responder.
    '''
    while True:
        time.sleep(10) # executa a checagem a cada 10 segundos
        
        tempo_atual = time.time()
        
        # cria uma lista com as chaves para nao alterar o dicionario enquanto ele e lido
        for cliente_socket in list(clientes_online.keys()):
            ultimo_sinal = clientes_online[cliente_socket]["ultimo_sinal"]
            status_atual = clientes_online[cliente_socket].get("status")
            
            # ignora clientes que estao jogando, pois a conexao tcp fica ociosa durante a partida udp
            if status_atual == "jogando":
                continue
            
            # verifica se o tempo sem resposta ultrapassou 15 segundos
            if tempo_atual - ultimo_sinal > 15:
                logger.warning("removendo cliente inativo por timeout")
                
                # guarda o nome para enviar o aviso aos demais
                nickname = clientes_online[cliente_socket]["nome"]
                
                # remove do dicionario global imediatamente
                del clientes_online[cliente_socket]
                
                try:
                    # forca a interrupcao da leitura e escrita no socket a nivel de sistema operacional
                    cliente_socket.shutdown(socket.SHUT_RDWR)
                    cliente_socket.close() 
                except Exception:
                    pass
                
                logger.info(f"{nickname} removido do lobby por inatividade.")
                fazer_broadcast(formatar_mensagem("SYNC_STATUS", f"{nickname} caiu"))

if __name__ == "__main__":
    server_socket = iniciar_servidor()

    try:
        # inicia a thread de verificacao de inativos
        thread_ceifador = threading.Thread(target=monitorar_inativos)
        # permite que a thread seja encerrada automaticamente quando o programa principal parar
        thread_ceifador.daemon = True 
        thread_ceifador.start()
        
        # loop infinito para aceitar novas conexoes de clientes
        while True:
            # bloqueia a execucao aqui ate que um novo cliente tente se conectar
            conexao, endereco = server_socket.accept() 
            
            # cria uma nova thread dedicada apenas para este cliente
            thread = threading.Thread(target=lidar_com_cliente, args=(conexao, endereco))
            thread.start()

    finally:
        server_socket.close()