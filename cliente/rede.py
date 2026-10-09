'''
COMENTARIOS ELUCIDATIVOS

este arquivo e responsavel apenas por estabelecer a conexao inicial do cliente com o servidor.
ele e importado e utilizado no inicio da execucao principal da interface grafica.
sua unica funcao e configurar a rede e devolver a porta de comunicacao pronta para uso.
'''

import socket
from config import HOST, PORT

def conectar_servidor(host: str = HOST, port: int = PORT) -> socket.socket:
    '''
    cria o canal de rede do cliente e tenta se conectar ao ip e porta do servidor.
    '''
    # af_inet significa que usaremos enderecos padrao de internet (ipv4)
    # sock_stream indica que usaremos o protocolo tcp (focado na entrega garantida de dados)
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sucesso = False
    
    try:
        # tenta abrir o canal de comunicacao com o servidor
        cliente_socket.connect((host, port)) 
        sucesso = True

    except ConnectionRefusedError:
        # avisa na tela caso o servidor esteja desligado ou indisponivel
        print("[CLIENTE] Não foi possível conectar ao servidor. Verifique se o servidor está em execução.")
        raise
        
    finally:
        # se a tentativa falhar por qualquer motivo, garante que a porta seja fechada 
        # para nao travar recursos no sistema operacional
        if not sucesso:
            cliente_socket.close()
            
    return cliente_socket