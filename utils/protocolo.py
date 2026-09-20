'''
COMENTÁRIOS ELUCIDATIVOS

Esse arquivo contempla duas funções utilitárias usadas para codificar e decodificar mensagens.

Entendendo os parâmetros:
Comando: instrução de entrega, usada para identificar a ação esperada pela tentativa de comunicação.
Payload: é o conteúdo da mensagem, a informação que acompanha o comando.
Exemplo: comando "SEND_CHAT" com payload "Oie, tudo bem?", a informação (payload) foi rotulada (comando).

Podemos pensar que estamos enviando cartas com rótulos e o texto em questão.

Breve explicação das funções:
formatar_mensagem(...) é usada para envio de mensagens, elas tem que ir em linguagem que a máquina 
entende, por isso é codificada em bytes.
interpretar_mensagem(...) é usada para mensagens que chegam, decodificamos o que está escrito para
conseguirmos interpretar a mensagem na linguagem humana.
'''

from config import ENCODING

def formatar_mensagem(comando: str, payload: str = "") -> bytes:
    
    # Monta a mensagem e codifica em bytes, pronta para ser enviada com sendall().

    mensagem = f"{comando} {payload}\n"
    return mensagem.encode(ENCODING) # em bytes a mensagem consegue trafegar no socket


def interpretar_mensagem(dados_brutos: str) -> tuple[str, str]:

    # Recebe a string já decodificada e separa no primeiro espaço, retornando (COMANDO, PAYLOAD).
    
    dados_brutos = dados_brutos.strip()  # remove o \n do fim

    if " " in dados_brutos:
        comando, payload = dados_brutos.split(" ", 1)
    else:
        comando, payload = dados_brutos, ""

    return comando, payload