'''
COMENTARIOS ELUCIDATIVOS

Vou pensar no socket como se fosse uma tomada, conecta um software a uma rede de internet.

Na main desse codigo, o servidor fica na escuta, quando um cliente tenta se comunicar,
abre uma thread na funcao paralela lidar_com_cliente, essa funcao vai tentar autenticar
o cliente e ficar escutando as mensagens que ele envia, e um canal dedicado a ele.
na main, o servidor nao fica travado, continua escutando enquanto outros fluxos podem acontecer 
paralelamente.
'''

import socket
import threading
import random
import time
from config import HOST, PORT
from utils.protocolo import *
from utils.logger import obter_logger

logger = obter_logger("servidor")

clientes_online = {}

def fazer_broadcast(mensagem: bytes, remetente_ignorado=None):
    # envia mensagem para clientes conectados e pula o envio para 'remetente_ignorado' se fornecido
    for cliente_socket in list(clientes_online.keys()): 
        if cliente_socket != remetente_ignorado:
            try:
                cliente_socket.sendall(mensagem)
            except Exception:
                pass

def iniciar_servidor():
    # instancia o socket utilizando ipv4 e tcp
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # quando o servidor e desligado, a porta e liberada na mesma hora
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # associa o socket ao ip e porta e o coloca em modo de escuta
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    
    logger.info(f"aguardando conexoes na porta {PORT}...")
    
    return server_socket

# funcao que roda em paralelo para cada usuario conectado
def lidar_com_cliente(conexao, endereco):
    # movemos toda a logica de recepcao/envio para dentro da funcao
    ip_cliente, porta_cliente = endereco
    logger.info(f"cliente conectado: {ip_cliente}:{porta_cliente}")

    nickname = None
    
    try:
        dados_auth = conexao.recv(1024)
        if not dados_auth:
            logger.warning(f"conexao encerrada abruptamente por {ip_cliente}:{porta_cliente}")
            return

        texto_decodificado = dados_auth.decode('utf-8')
        comando, payload = interpretar_mensagem(texto_decodificado)

        if comando == "AUTH_CONN":
            # separa o nickname da porta udp
            partes = payload.split(":")
            nickname = partes[0]
            porta_udp_local = None

            if len(partes) > 1:
                try:
                    porta_udp_local = int(partes[1])
                except ValueError:
                    logger.error(f"porta udp invalida recebida de {ip_cliente}:{porta_cliente}")

            # salva no dicionario uma unica vez com todas as infos
            clientes_online[conexao] = {
                "nome": nickname, 
                "ultimo_sinal": time.time(),
                "porta_udp": porta_udp_local,
                "status": "disponivel" 
            }
            
            logger.info(f"usuario '{nickname}' entrou no lobby (udp: {porta_udp_local})")
            
            # autoriza a entrada
            conexao.sendall(formatar_mensagem("AUTH_REPLY", "OK"))
            
            # sincroniza a lista de contatos
            for socket_antigo, dados in clientes_online.items():
                if socket_antigo != conexao:
                    nome_antigo = dados["nome"]
                    conexao.sendall(formatar_mensagem("SYNC_STATUS", f"{nome_antigo} entrou"))
            
            fazer_broadcast(formatar_mensagem("SYNC_STATUS", f"{nickname} entrou"), remetente_ignorado=conexao)

        while True:
            # tenta receber os dados, lidando com interrupcoes abruptas
            try:
                dados = conexao.recv(1024)
            except ConnectionResetError:
                break # sai do loop se a conexao for forcadamente resetada
            
            # se recv() retornar zero bytes, o cliente encerrou a conexao de forma limpa
            if not dados:
                break
            
            texto_decodificado = dados.decode('utf-8')
            comando, payload = interpretar_mensagem(texto_decodificado)
            
            if conexao in clientes_online:
                clientes_online[conexao]["ultimo_sinal"] = time.time()
                
            if comando == 'DEAD_TRIG':
                continue

            # implementacao do roteamento do chat global
            if comando == 'SEND_CHAT':

                # anexa o nome do remetente a mensagem original
                mensagem_chat = f"{nickname}: {payload}"

                # empacota novamente como send_chat
                resposta_bytes = formatar_mensagem("SEND_CHAT", mensagem_chat)

                # distribui para todos, exceto o autor da mensagem
                fazer_broadcast(resposta_bytes, remetente_ignorado=conexao)
                
                quem_enviou = clientes_online[conexao]["nome"]
                logger.info(f"[{quem_enviou} diz no chat]: {payload}")

            elif comando == 'SYNC_STATUS':
                # formata a mensagem para incluir quem mudou de cor 
                mensagem_status = f"{nickname} mudou para {payload}"

                # empacota novamente como sync_status
                resposta_bytes = formatar_mensagem("SYNC_STATUS", mensagem_status)

                # distribui para todos, exceto o autor da mensagem
                fazer_broadcast(resposta_bytes, remetente_ignorado=conexao)

            elif comando == 'ECHO':
                resposta_bytes = formatar_mensagem("ECHO_REPLY", payload)
                conexao.sendall(resposta_bytes)

            elif comando == 'REQ_MATCH':
                nickname_oponente = payload
                oponente_encontrado = False

                # procurar o oponente pelo nickname no dicionario de clientes online
                for socket_cliente, dados_cliente in clientes_online.items():
                    if dados_cliente["nome"] == nickname_oponente:
                        oponente_encontrado = True
                        if dados_cliente.get("status") != "disponivel":
                            resposta_bytes = formatar_mensagem("MATCH_REJECT", "Ocupado")
                            conexao.sendall(resposta_bytes)
                        else:
                            socket_cliente.sendall(formatar_mensagem("CHALLENGE_INVITE", nickname))
                        break 

                if not oponente_encontrado:
                    resposta_bytes = formatar_mensagem("MATCH_REJECT", "Oponente offline")
                    conexao.sendall(resposta_bytes)  

            elif comando == 'ACCEPT_MATCH':
                nickname_oponente = payload
                socket_oponente = None

                for socket_cliente, dados_cliente in clientes_online.items():
                    if dados_cliente["nome"] == nickname_oponente:
                        socket_oponente = socket_cliente
                        break

                if socket_oponente:
                   
                    status_remetente = clientes_online[conexao].get("status")
                    status_oponente = clientes_online[socket_oponente].get("status")
                    
                    if status_remetente == "disponivel" and status_oponente == "disponivel": 
                    
                        clientes_online[conexao]["status"] = "jogando"
                        clientes_online[socket_oponente]["status"] = "jogando"

                        fazer_broadcast(formatar_mensagem("SYNC_STATUS", f"{nickname} entrou em partida"))
                        fazer_broadcast(formatar_mensagem("SYNC_STATUS", f"{nickname_oponente} entrou em partida"))
                        
                        ip_recebedor = conexao.getpeername()[0]
                        porta_recebedor = clientes_online[conexao]["porta_udp"]
                        ip_oponente = socket_oponente.getpeername()[0]
                        porta_oponente = clientes_online[socket_oponente]["porta_udp"]

                        # sorteia um numero aleatorio para guiar a fila de pedidos desta partida especifica
                        semente_partida = random.randint(1000, 9999)

                        # entrega o ip, porta e semente cruzados
                        socket_oponente.sendall(formatar_mensagem("MATCH_INFO", f"{ip_recebedor}:{porta_recebedor}:{semente_partida}"))
                        conexao.sendall(formatar_mensagem("MATCH_INFO", f"{ip_oponente}:{porta_oponente}:{semente_partida}"))
                        
                    else:
                        conexao.sendall(formatar_mensagem("MATCH_REJECT", "Conflito de estado: jogador ocupado"))
            
            elif comando == 'REJECT_MATCH':
                nickname_oponente = payload
                for socket_cliente, dados_cliente in clientes_online.items():
                    if dados_cliente["nome"] == nickname_oponente:
                        socket_cliente.sendall(formatar_mensagem("MATCH_REJECT", "Convite recusado"))
                        break      
                    
            elif comando == 'BACK_LOBBY':
                if conexao in clientes_online:
                    clientes_online[conexao]["status"] = "disponivel"
                    fazer_broadcast(formatar_mensagem("SYNC_STATUS", f"{nickname} voltou"))

    finally:   
        if conexao in clientes_online:
            nickname = clientes_online[conexao]["nome"] 
            del clientes_online[conexao]
            logger.info(f"{nickname} saiu do lobby")

            # broadcast de saida (avisa os restantes)
            msg_broadcast = formatar_mensagem("SYNC_STATUS", f"{nickname} saiu")
            fazer_broadcast(msg_broadcast)
        
        # garante que o socket especifico deste cliente seja fechado sem quebrar o servidor
        conexao.close()
        logger.info(f"conexao encerrada com {ip_cliente}:{porta_cliente}")

def monitorar_inativos():
    while True:
        time.sleep(10) # faz a varredura a cada 10 segundos
        
        tempo_atual = time.time()
        
        # list() cria uma copia das chaves para nao quebrar o loop durante a iteracao
        for cliente_socket in list(clientes_online.keys()):
            ultimo_sinal = clientes_online[cliente_socket]["ultimo_sinal"]
            
            status_atual = clientes_online[cliente_socket].get("status")
            
            # se estiver jogando, ignora o timeout e vai para o próximo!
            if status_atual == "jogando":
                continue
            
            if tempo_atual - ultimo_sinal > 15: # passou do limite de tolerancia de 15s?
                logger.warning("removendo cliente inativo por timeout")
                
                # salva o nome para poder avisar o lobby
                nickname = clientes_online[cliente_socket]["nome"]
                
                # remove da memoria imediatamente
                del clientes_online[cliente_socket]
                
                try:
                    # shutdown() é o comando que força o recv() a destravar no Python
                    cliente_socket.shutdown(socket.SHUT_RDWR)
                    cliente_socket.close() 
                except Exception:
                    pass
                
                # avisa os outros jogadores que a pessoa caiu
                logger.info(f"{nickname} removido do lobby por inatividade.")
                fazer_broadcast(formatar_mensagem("SYNC_STATUS", f"{nickname} caiu"))

if __name__ == "__main__":
    server_socket = iniciar_servidor()

    try:
        # loop continuo para aceitar multiplos clientes simultaneamente
        thread_ceifador = threading.Thread(target=monitorar_inativos)
        thread_ceifador.daemon = True
        thread_ceifador.start()
        while True:
            # esse accept() trava o servidor e fica aguardando alguem chamar
            conexao, endereco = server_socket.accept() # canal exclusivo para o usuario que chamou
            
            # instancia e inicia uma nova thread para o cliente
            thread = threading.Thread(target=lidar_com_cliente, args=(conexao, endereco))
            thread.start()

    finally:
        server_socket.close()