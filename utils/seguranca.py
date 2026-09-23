def criptografar(texto_limpo: str, chave_deslocamento: int = 3) -> str:
    # Percorre cada caractere, converte para valor númerico, soma o deslocamento e volta para caractere, criando uma cifra básica
    texto_cifrado = ""
    for char in texto_limpo:
        texto_cifrado += chr(ord(char) + chave_deslocamento)
    return texto_cifrado

def descriptografar(texto_cifrado: str, chave_deslocamento: int = 3) -> str:
    # Processo inverso da criptografia
    texto_limpo = ""
    for char in texto_cifrado:
        texto_limpo += chr(ord(char) - chave_deslocamento)
    return texto_limpo