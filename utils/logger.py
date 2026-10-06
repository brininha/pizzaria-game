import logging
import os
import sys
import datetime

# cria a pasta logs na raiz do projeto se ela nao existir
os.makedirs("logs", exist_ok=True)

# gera um nome de arquivo unico baseado na data e hora exatas da execucao
agora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
nome_arquivo_log = f"logs/historico_{agora}.log"

# configuracao padrao do logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        # salva no arquivo txt unico para esta execucao
        logging.FileHandler(nome_arquivo_log, encoding="utf-8"),
        # exibe no terminal simultaneamente
        logging.StreamHandler(sys.stdout)
    ]
)

def obter_logger(nome_modulo):
    # cria um canal de log com o nome do arquivo atual
    return logging.getLogger(nome_modulo)