'''
COMENTARIOS ELUCIDATIVOS

este arquivo contem duas funcoes auxiliares usadas para preparar e ler as mensagens da rede.

entendendo os parametros:
comando: eh a instrucao principal, usada para identificar que tipo de acao o sistema deve tomar.
payload: eh o conteudo da mensagem, a informacao extra que acompanha o comando.
exemplo: comando "send_chat" com payload "oie, tudo bem?", a acao eh enviar um chat e a informacao eh o texto.

formatar_mensagem eh usada antes do envio, ela junta o comando e o payload em uma linha e converte
tudo para bytes, que e o formato exigido para trafegar pela rede.

interpretar_mensagem eh usada quando os dados chegam, ela recebe o texto, separa o comando do conteudo
e devolve os dois para que o sistema saiba o que fazer.
'''

from config import ENCODING

def formatar_mensagem(comando: str, payload: str = "") -> bytes:
    '''
    junta o comando e a informacao, adiciona uma quebra de linha no final para marcar 
    o fim do pacote e transforma tudo em bytes para poder ser enviado no socket.
    '''
    mensagem = f"{comando} {payload}\n"
    return mensagem.encode(ENCODING) 

def interpretar_mensagem(dados_brutos: str) -> tuple[str, str]:
    '''
    pega a mensagem que chegou da rede, tira a quebra de linha do final e 
    corta o texto no primeiro espaco em branco para separar o comando da informacao.
    '''
    dados_brutos = dados_brutos.strip() 

    # verifica se tem espaco no texto para poder separar em duas variaveis
    if " " in dados_brutos:
        comando, payload = dados_brutos.split(" ", 1)
    else:
        # se nao tiver espaco, significa que e um comando vazio, sem payload
        comando, payload = dados_brutos, ""

    return comando, payload