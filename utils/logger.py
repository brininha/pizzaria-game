'''
COMENTARIOS ELUCIDATIVOS

este arquivo e responsavel por registrar e salvar o historico de tudo o que 
acontece no sistema durante a execucao. 

ele cria um arquivo de texto novo toda vez que o programa e iniciado, 
guardando eventos, avisos e erros com data e hora exatas,
isso e fundamental para rastrear bugs e analisar 
falhas de rede apos elas ocorrerem.
'''

import logging
import os
import sys
import datetime

# cria a pasta de logs na raiz do projeto, caso ela ainda nao exista no computador
os.makedirs("logs", exist_ok=True)

# captura o momento exato em que o programa iniciou para criar um arquivo unico.
# isso garante que logs de sessoes anteriores nao sejam apagados ou sobrescritos.
agora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
nome_arquivo_log = f"logs/historico_{agora}.log"

# configuracao global que dita como as mensagens serao formatadas e armazenadas
logging.basicConfig(
    level=logging.INFO,
    # define a estrutura da linha de log: data, hora, nome do arquivo fonte, gravidade e texto
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        # grava as informacoes no arquivo de texto no disco rigido
        logging.FileHandler(nome_arquivo_log, encoding="utf-8"),
        # imprime as mesmas informacoes na tela do terminal em tempo real
        logging.StreamHandler(sys.stdout)
    ]
)

def obter_logger(nome_modulo):
    '''
    esta funcao e importada pelos outros arquivos do projeto, ela devolve um 
    canal de registro carimbado com o nome do arquivo que a chamou, 
    isso facilita identificar exatamente em qual modulo ocorreu uma falha ou acao.
    '''
    return logging.getLogger(nome_modulo)