'''
COMENTARIOS ELUCIDATIVOS

este arquivo e responsavel pela seguranca e privacidade das mensagens do chat.
ele implementa uma cifra de substituicao simples (cifra de cesar).
a ideia e trocar cada letra da mensagem por outra letra algumas posicoes a frente 
na tabela de caracteres do computador. 
isso mascara o conteudo para que ele nao trafegue legivel pelos cabos de rede.
'''

def criptografar(texto_limpo: str, chave_deslocamento: int = 3) -> str:
    '''
    recebe o texto original e aplica a mascara de protecao.
    para cada caractere, descobre o seu numero na tabela padrao do sistema (ord),
    soma o valor do deslocamento e transforma esse novo numero de volta em texto (chr).
    '''
    texto_cifrado = ""
    for char in texto_limpo:
        texto_cifrado += chr(ord(char) + chave_deslocamento)
    return texto_cifrado

def descriptografar(texto_cifrado: str, chave_deslocamento: int = 3) -> str:
    '''
    faz o caminho inverso para recuperar a mensagem original na tela do destinatario.
    pega cada caractere protegido, transforma em numero, subtrai o valor do deslocamento
    e converte novamente para a letra original, revelando o texto limpo.
    '''
    texto_limpo = ""
    for char in texto_cifrado:
        texto_limpo += chr(ord(char) - chave_deslocamento)
    return texto_limpo