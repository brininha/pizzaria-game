'''
COMENTÁRIOS ELUCIDATIVOS

Vou pensar no socket como se fosse uma tomada, conecta um software a uma rede de internet.

Na main desse código, o servidor fica na escuta, quando um cliente tenta se comunicar,
abre uma thread na função paralela lidar_com_cliente, essa função vai tentar autenticar
o cliente e ficar escutando as mensagens que ele envia, é um canal dedicado a ele.
Na main, o servidor não fica travado, continua escutando enquanto outros fluxos podem acontecer 
paralelamente.
'''

import socket
import threading
import time
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
    # Quando o servidor eh desligado, a porta eh liberada na mesma hora
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Associa o socket ao IP e porta e o coloca em modo de escuta
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    
    print(f"[SERVIDOR] Aguardando conexões na porta {PORT}...")
    
    return server_socket

# Função que roda em paralelo para cada usuário conectado
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
            # separa o nickname da porta UDP
            partes = payload.split(":")
            nickname = partes[0]
            porta_udp_local = None

            if len(partes) > 1:
                try:
                    porta_udp_local = int(partes[1])
                except ValueError:
                    print(f"[SERVIDOR] Porta UDP inválida recebida de {ip_cliente}:{porta_cliente}")

            # salva no dicionário uma unica vez com todas as infos
            clientes_online[conexao] = {
                "nome": nickname, 
                "ultimo_sinal": time.time(),
                "porta_udp": porta_udp_local,
                "status": "disponivel" 
            }
            
            print(f"[LOGIN] Usuário '{nickname}' entrou no lobby (UDP: {porta_udp_local}).")
            
            # autoriza a entrada
            conexao.sendall(formatar_mensagem("AUTH_REPLY", "OK"))
            
            # sincroniza a lista de contatos
            for socket_antigo, dados in clientes_online.items():
                if socket_antigo != conexao:
                    nome_antigo = dados["nome"]
                    conexao.sendall(formatar_mensagem("SYNC_STATUS", f"{nome_antigo} entrou"))
            
            fazer_broadcast(formatar_mensagem("SYNC_STATUS", f"{nickname} entrou"), remetente_ignorado=conexao)

        while True:
            # tenta receber os dados, lidando com interrupções abruptas
            try:
                dados = conexao.recv(1024)
            except ConnectionResetError:
                break # sai do loop se a conexão for forçadamente resetada
            
            # se recv() retornar zero bytes, o cliente encerrou a conexão de forma limpa
            if not dados:
                break
            
            texto_decodificado = dados.decode('utf-8')
            comando, payload = interpretar_mensagem(texto_decodificado)
            
            if conexao in clientes_online:
                clientes_online[conexao]["ultimo_sinal"] = time.time()
                
            if comando == 'DEAD_TRIG':
                continue

            # Implementação do roteamento do chat global
            if comando == 'SEND_CHAT':

                # Anexa o nome do remetente à mensagem original
                mensagem_chat = f"{nickname}: {payload}"

                # Empacota novamente como SEND_CHAT
                resposta_bytes = formatar_mensagem("SEND_CHAT", mensagem_chat)

                # Distribui para todos, exceto o autor da mensagem
                fazer_broadcast(resposta_bytes, remetente_ignorado=conexao)
                
                quem_enviou = clientes_online[conexao]["nome"]
                print(f"[{quem_enviou} diz]: {payload}")

            elif comando == 'SYNC_STATUS':
                # Formata a mensagem para incluir quem mudou de cor 
                mensagem_status = f"{nickname} mudou para {payload}"

                # Empacota novamente como SYNC_STATUS
                resposta_bytes = formatar_mensagem("SYNC_STATUS", mensagem_status)

                # Distribui para todos, exceto o autor da mensagem
                fazer_broadcast(resposta_bytes, remetente_ignorado=conexao)

            elif comando == 'ECHO':
                resposta_bytes = formatar_mensagem("ECHO_REPLY", payload)
                conexao.sendall(resposta_bytes)

            elif comando == 'REQ_MATCH':
                nickname_oponente = payload
                oponente_encontrado = False

                # Procurar o oponente pelo nickname no dicionário de clientes online
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
                   clientes_online[conexao]["status"] = "jogando"
                   clientes_online[socket_oponente]["status"] = "jogando"

                   fazer_broadcast(formatar_mensagem("SYNC_STATUS", f"{nickname} entrou em partida"))
                   fazer_broadcast(formatar_mensagem("SYNC_STATUS", f"{nickname_oponente} entrou em partida"))
                   
                   ip_recebedor = conexao.getpeername()[0]
                   porta_recebedor = clientes_online[conexao]["porta_udp"]
                   ip_oponente = socket_oponente.getpeername()[0]
                   porta_oponente = clientes_online[socket_oponente]["porta_udp"]

                   # Entrega o IP/Porta cruzados
                   socket_oponente.sendall(formatar_mensagem("MATCH_INFO", f"{ip_recebedor}:{porta_recebedor}"))
                   conexao.sendall(formatar_mensagem("MATCH_INFO", f"{ip_oponente}:{porta_oponente}"))
            
            elif comando == 'REJECT_MATCH':
                nickname_oponente = payload
                for socket_cliente, dados_cliente in clientes_online.items():
                    if dados_cliente["nome"] == nickname_oponente:
                        socket_cliente.sendall(formatar_mensagem("MATCH_REJECT", "Convite recusado"))
                        break      

    finally:   
        if conexao in clientes_online:
            nickname = clientes_online[conexao]["nome"] 
            del clientes_online[conexao]
            print(f"[SERVIDOR] {nickname} saiu do lobby.")

            # Broadcast de saída (avisa os restantes)
            msg_broadcast = formatar_mensagem("SYNC_STATUS", f"{nickname} saiu")
            fazer_broadcast(msg_broadcast)
        
        # Garante que o socket específico deste cliente seja fechado sem quebrar o servidor
        conexao.close()
        print(f"[SERVIDOR] Conexão encerrada com {ip_cliente}:{porta_cliente}")

def monitorar_inativos():
    while True:
        time.sleep(10) # faz a varredura a cada 10 segundos
        
        tempo_atual = time.time()
        
        # list() cria uma copia das chaves para nao quebrar o loop durante a iteraçao
        for cliente_socket in list(clientes_online.keys()):
            ultimo_sinal = clientes_online[cliente_socket]["ultimo_sinal"]
            
            if tempo_atual - ultimo_sinal > 15: # passou do limite de tolerancia de 15s?
                print("[SISTEMA] Removendo cliente inativo por timeout.")
                try:
                    cliente_socket.close() # corta a ligaçao forçadamente
                except Exception:
                    pass
                
                # Nota de arquitetura: Ao fechar o socket aqui, o recv() que estava travado 
                # lá na função lidar_com_cliente vai rebentar. Isso empurra o código daquela 
                # thread diretamente para o bloco 'finally', que por sua vez remove o cliente 
                # do dicionário e avisa o lobby inteiro da queda

if __name__ == "__main__":
    server_socket = iniciar_servidor()

    try:
        # Loop contínuo para aceitar múltiplos clientes simultaneamente
        thread_ceifador = threading.Thread(target=monitorar_inativos)
        thread_ceifador.daemon = True
        thread_ceifador.start()
        while True:
            # Esse accept() trava o servidor e fica aguardando alguém chamar
            conexao, endereco = server_socket.accept() # canal exclusivo para o usuário que chamou
            
            # Instancia e inicia uma nova thread para o cliente
            thread = threading.Thread(target=lidar_com_cliente, args=(conexao, endereco))
            thread.start()

    finally:
        server_socket.close()