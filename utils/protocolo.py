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