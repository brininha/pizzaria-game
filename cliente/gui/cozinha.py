'''
COMENTARIOS ELUCIDATIVOS

este arquivo e responsavel pela interface e pela logica do minijogo de montar pizzas.
ele utiliza a biblioteca pygame para desenhar os graficos e capturar as teclas digitadas.

nesta etapa ocorre a comunicacao p2p (ponto a ponto). o servidor tcp central 
nao e utilizado durante a partida. os pontos sao enviados diretamente do seu 
computador para o ip e a porta do adversario utilizando o protocolo udp.

para garantir que os dois jogadores recebam os mesmos pedidos na mesma ordem
sem precisarem trafegar essas informacoes pela rede, utilizamos uma semente 
aleatoria (seed) igual para ambos, que foi gerada pelo servidor na hora do convite.

tambem usamos ia para gerar boa parte desse codigo, mas revisamos e criticamos tudo.
'''

import pygame
import os
import threading
import random
import socket
from utils.logger import obter_logger

def iniciar_partida(meu_nickname, oponente_nickname, ip_oponente, porta_oponente, meu_socket_udp, semente_partida):
    '''
    funcao principal que configura a tela do jogo, carrega as imagens,
    inicia a escuta da rede udp e gerencia o loop de atualizacao dos graficos.
    '''
    pygame.init()
    
    # inicia o logger para registrar os eventos p2p
    logger = obter_logger("cozinha_pygame")
    logger.info(f"[{meu_nickname}] partida p2p iniciada contra {oponente_nickname} (semente: {semente_partida})")

    largura, altura = 800, 600
    tela = pygame.display.set_mode((largura, altura))
    pygame.display.set_caption("Cojura's Pizzeria - Cozinha")

    branco = (246, 244, 232)
    preto = (0, 0, 0)
    vermelho = (163, 29, 29)
    verde = (42, 157, 143)
    
    fonte_pixel = pygame.font.SysFont("Courier", 24, bold=True)
    fonte_anuncio = pygame.font.SysFont("Courier", 48, bold=True)

    diretorio_assets = os.path.join("cliente", "gui", "assets")

    def carregar_dimensionar(nome_arquivo):
        # carrega a imagem do disco e redimensiona para o tamanho grande (pizza na esteira)
        caminho = os.path.join(diretorio_assets, nome_arquivo)
        imagem = pygame.image.load(caminho).convert_alpha()
        return pygame.transform.scale(imagem, (300, 300))
    
    def carregar_icone(nome_arquivo):
        # carrega a imagem do disco e redimensiona para o tamanho pequeno (botoes do menu)
        caminho = os.path.join(diretorio_assets, nome_arquivo)
        try:
            imagem = pygame.image.load(caminho).convert_alpha()
            return pygame.transform.scale(imagem, (60, 60)) 
        except FileNotFoundError:
            # cria um quadrado cinza temporario caso a imagem ainda nao exista na pasta
            surf = pygame.Surface((60, 60))
            surf.fill((180, 180, 180))
            return surf

    img_massa = carregar_dimensionar("massa.png")

    # dicionario que mapeia a tecla do teclado para as informacoes do ingrediente correspondente
    catalogo = {
        "molho": {
            pygame.K_1: {"nome": "Tomate", "img": carregar_dimensionar("molho-de-tomate.png"), "icone": carregar_icone("tubo-tomate.png")},
            pygame.K_2: {"nome": "Pesto", "img": carregar_dimensionar("molho-pesto.png"), "icone": carregar_icone("tubo-pesto.png")},
            pygame.K_3: {"nome": "Branco", "img": carregar_dimensionar("molho-branco.png"), "icone": carregar_icone("tubo-branco.png")}
        },
        "queijo": {
            pygame.K_4: {"nome": "Mussarela", "img": carregar_dimensionar("mussarela.png"), "icone": carregar_icone("pote-mussarela.png")},
            pygame.K_5: {"nome": "Cheddar", "img": carregar_dimensionar("cheddar.png"), "icone": carregar_icone("pote-cheddar.png")},
        },
        "extra": {
            pygame.K_6: {"nome": "Pepperoni", "img": carregar_dimensionar("pepperoni.png"), "icone": carregar_icone("tigela-pepperoni.png")},
            pygame.K_7: {"nome": "Cogumelo", "img": carregar_dimensionar("cogumelo.png"), "icone": carregar_icone("tigela-cogumelo.png")},
            pygame.K_8: {"nome": "Cebola", "img": carregar_dimensionar("cebola-roxa.png"), "icone": carregar_icone("tigela-cebola.png")},
            pygame.K_9: {"nome": "Manjericão", "img": carregar_dimensionar("manjericao.png"), "icone": carregar_icone("tigela-manjericao.png")},
        }
    }
    
    # aplica a semente fornecida pelo servidor tcp.
    # isso garante que a funcao random gere exatamente a mesma sequencia de pedidos
    # para ambos os jogadores, mantendo os computadores sincronizados sem uso de rede.
    random.seed(semente_partida) 
    fila_pedidos = []
    for _ in range(10): 
        fila_pedidos.append({
            "molho": random.choice(list(catalogo["molho"].keys())),
            "queijo": random.choice(list(catalogo["queijo"].keys())),
            "extra": random.choice(list(catalogo["extra"].keys()))
        })

    indice_pedido = 0
    pizza_atual = {"molho": None, "queijo": None, "extra": None}

    pontuacao_oponente = 0
    pontuacao_jogador = 0
    
    fim_de_jogo = False
    vencedor = ""

    rodando = True
    
    def escutar_udp():
        '''
        funcao executada em uma thread separada para ler pacotes udp.
        ela escuta a porta local atualizando a pontuacao do oponente sempre
        que um pacote chega, parando o jogo se ele atingir 100 pontos.
        '''
        nonlocal pontuacao_oponente, rodando, fim_de_jogo, vencedor
        
        # o timeout evita que a thread trave infinitamente na leitura
        meu_socket_udp.settimeout(0.5)
        while rodando:
            try:
                dados, _ = meu_socket_udp.recvfrom(1024)
                msg = dados.decode('utf-8')
                
                # extrai a pontuacao da mensagem udp recebida
                if msg.startswith("SCORE:"):
                    pontuacao_oponente = int(msg.split(":")[1])
                    
                    # verifica se o oponente venceu a partida
                    if pontuacao_oponente >= 100 and not fim_de_jogo:
                        vencedor = oponente_nickname
                        fim_de_jogo = True
                        logger.info(f"[{meu_nickname}] {oponente_nickname} atingiu 100 pontos e venceu a partida")
            except socket.timeout:
                continue
            except Exception as e:
                pass

    # inicia a escuta udp em paralelo para nao travar os graficos
    thread_udp = threading.Thread(target=escutar_udp)
    thread_udp.daemon = True
    thread_udp.start()

    relogio = pygame.time.Clock()

    # loop principal que atualiza a tela a cada quadro
    while rodando:
        tela.fill(branco)

        # processamento de teclas e eventos do sistema
        for evento in pygame.event.get():
            # se o usuario fechar a janela no x
            if evento.type == pygame.QUIT:
                rodando = False

            # se o usuario apertar uma tecla durante a partida ativa
            elif evento.type == pygame.KEYDOWN and not fim_de_jogo:
                # registra a tecla como um ingrediente na pizza atual
                if evento.key in catalogo["molho"]:
                    pizza_atual["molho"] = evento.key
                elif evento.key in catalogo["queijo"]:
                    pizza_atual["queijo"] = evento.key
                elif evento.key in catalogo["extra"]:
                    pizza_atual["extra"] = evento.key
                
                # se o jogador apertar espaco, valida se a pizza montada esta igual ao pedido
                elif evento.key == pygame.K_SPACE:
                    pedido = fila_pedidos[indice_pedido]
                    
                    if (pizza_atual["molho"] == pedido["molho"] and 
                        pizza_atual["queijo"] == pedido["queijo"] and 
                        pizza_atual["extra"] == pedido["extra"]):
                        
                        # adiciona a pontuacao e avanca para o proximo pedido da fila
                        pontuacao_jogador += 10
                        indice_pedido += 1
                        
                        logger.info(f"[{meu_nickname}] pizza {indice_pedido} montada com sucesso! enviando pontuacao {pontuacao_jogador} via udp")
                        
                        # envia o pacote udp contendo a nova pontuacao diretamente para o ip do oponente
                        meu_socket_udp.sendto(f"SCORE:{pontuacao_jogador}".encode('utf-8'), (ip_oponente, porta_oponente))
                        
                        # verifica se este ponto foi o suficiente para vencer a partida
                        if pontuacao_jogador >= 100:
                            vencedor = meu_nickname
                            fim_de_jogo = True
                            logger.info(f"[{meu_nickname}] alcancou 100 pontos e venceu a partida")
                    
                    # reseta a bandeja de ingredientes independentemente de acertar ou errar
                    pizza_atual = {"molho": None, "queijo": None, "extra": None}

        # renderizacao do placar no topo da tela
        texto_jogador = fonte_pixel.render(f"{meu_nickname}: R${pontuacao_jogador}", True, verde if pontuacao_jogador > pontuacao_oponente else preto)
        texto_oponente = fonte_pixel.render(f"{oponente_nickname}: R${pontuacao_oponente}", True, vermelho if pontuacao_oponente > pontuacao_jogador else preto)

        tela.blit(texto_jogador, (30, 30))
        tela.blit(texto_oponente, (largura - texto_oponente.get_width() - 30, 30))

        # calculo das posicoes centrais para a area da pizza
        centro_x = (largura // 2) - 150 
        centro_y = 160 

        # renderizacao da esteira mecanica de fundo
        cor_esteira = (130, 130, 130)
        cor_borda_esteira = (80, 80, 80)
        cor_listra = (110, 110, 110) 
        
        y_esteira = centro_y - 20
        altura_esteira = 340 
        
        pygame.draw.rect(tela, cor_esteira, (0, y_esteira, largura, altura_esteira))
        
        for x_listra in range(0, largura, 40):
            pygame.draw.line(tela, cor_listra, (x_listra, y_esteira), (x_listra, y_esteira + altura_esteira), 4)
        
        pygame.draw.line(tela, cor_borda_esteira, (0, y_esteira), (largura, y_esteira), 6)
        pygame.draw.line(tela, cor_borda_esteira, (0, y_esteira + altura_esteira - 4), (largura, y_esteira + altura_esteira - 4), 6)

        # desenha a massa basica da pizza
        tela.blit(img_massa, (centro_x, centro_y))

        # sobrepoe os ingredientes escolhidos pelo jogador acima da massa
        if pizza_atual["molho"]: tela.blit(catalogo["molho"][pizza_atual["molho"]]["img"], (centro_x, centro_y))
        if pizza_atual["queijo"]: tela.blit(catalogo["queijo"][pizza_atual["queijo"]]["img"], (centro_x, centro_y))
        if pizza_atual["extra"]: tela.blit(catalogo["extra"][pizza_atual["extra"]]["img"], (centro_x, centro_y))

        # renderizacao da nota fiscal de pedido no topo central
        if not fim_de_jogo and indice_pedido < len(fila_pedidos):
            pedido = fila_pedidos[indice_pedido]
            
            nome_molho = catalogo["molho"][pedido["molho"]]["nome"]
            nome_queijo = catalogo["queijo"][pedido["queijo"]]["nome"]
            nome_extra = catalogo["extra"][pedido["extra"]]["nome"]
            
            largura_caixa = 260
            altura_caixa = 135
            x_caixa = (largura // 2) - (largura_caixa // 2)
            y_caixa = 40
            
            pygame.draw.rect(tela, (200, 200, 200), (x_caixa + 6, y_caixa + 6, largura_caixa, altura_caixa))
            
            cor_papel = (253, 250, 235)
            pygame.draw.rect(tela, cor_papel, (x_caixa, y_caixa, largura_caixa, altura_caixa))
            
            pygame.draw.rect(tela, (90, 90, 90), (x_caixa, y_caixa, largura_caixa, 12))
            
            pygame.draw.rect(tela, preto, (x_caixa, y_caixa, largura_caixa, altura_caixa), width=2)
            
            y_linha = y_caixa + 45
            for x_tracejado in range(x_caixa + 15, x_caixa + largura_caixa - 15, 12):
                pygame.draw.line(tela, preto, (x_tracejado, y_linha), (x_tracejado + 6, y_linha), 1)
            
            fonte_comanda_titulo = pygame.font.SysFont("Courier", 20, bold=True)
            fonte_comanda_item = pygame.font.SysFont("Courier", 16, bold=True)
            
            texto_pedido = fonte_comanda_titulo.render(f"PEDIDO {indice_pedido + 1}", True, preto)
            linha_molho = fonte_comanda_item.render(f"- {nome_molho}", True, preto)
            linha_queijo = fonte_comanda_item.render(f"- {nome_queijo}", True, preto)
            linha_extra = fonte_comanda_item.render(f"- {nome_extra}", True, preto)
            
            tela.blit(texto_pedido, (largura // 2 - texto_pedido.get_width() // 2, y_caixa + 20))
            tela.blit(linha_molho, (largura // 2 - linha_molho.get_width() // 2, y_caixa + 55))
            tela.blit(linha_queijo, (largura // 2 - linha_queijo.get_width() // 2, y_caixa + 75))
            tela.blit(linha_extra, (largura // 2 - linha_extra.get_width() // 2, y_caixa + 95))

        # renderizacao do menu de ingredientes na parte inferior da tela
        if not fim_de_jogo:
            y_bancada = altura - 110
            x_atual = 25 
            
            fonte_pequena = pygame.font.SysFont("Courier", 16, bold=True)
            fonte_micro = pygame.font.SysFont("Courier", 11, bold=True)
            
            for categoria, itens in catalogo.items():
                texto_cat = fonte_pequena.render(categoria.upper(), True, preto)
                
                qtd_itens = len(itens)
                largura_caixa_cat = (qtd_itens * 70) + 10
                
                largura_titulo = texto_cat.get_width() + 16
                pygame.draw.rect(tela, (255, 255, 255), (x_atual + 10, y_bancada - 28, largura_titulo, 24), border_radius=5)
                pygame.draw.rect(tela, preto, (x_atual + 10, y_bancada - 28, largura_titulo, 24), width=2, border_radius=5)
                tela.blit(texto_cat, (x_atual + 18, y_bancada - 24))
                
                cor_fundo_cat = (210, 210, 210)
                pygame.draw.rect(tela, cor_fundo_cat, (x_atual, y_bancada, largura_caixa_cat, 90), border_radius=8)
                pygame.draw.rect(tela, preto, (x_atual, y_bancada, largura_caixa_cat, 90), width=2, border_radius=8)
                
                x_item = x_atual + 10
                
                for indice, (tecla, dados) in enumerate(itens.items()):
                    icone = dados["icone"]
                    nome_tecla = pygame.key.name(tecla).upper()
                    nome_ingrediente = dados["nome"]
                    
                    if indice > 0:
                        pygame.draw.line(tela, preto, (x_item - 5, y_bancada + 10), (x_item - 5, y_bancada + 80), 2)
                    
                    tela.blit(icone, (x_item, y_bancada - 5))
                    
                    texto_nome = fonte_micro.render(nome_ingrediente, True, preto)
                    offset_nome = (60 - texto_nome.get_width()) // 2
                    tela.blit(texto_nome, (x_item + offset_nome, y_bancada + 54))
                    
                    texto_tecla = fonte_pequena.render(f"{nome_tecla}", True, preto)
                    offset_tecla = (60 - texto_tecla.get_width()) // 2
                    tela.blit(texto_tecla, (x_item + offset_tecla, y_bancada + 68))
                    
                    x_item += 70 
                
                x_atual += largura_caixa_cat + 20
        
        # renderizacao da tela final sobreposta ao jogo
        if fim_de_jogo:
            pelicula = pygame.Surface((largura, altura))
            pelicula.set_alpha(150)
            pelicula.fill(preto)
            tela.blit(pelicula, (0, 0))

            largura_fim = 600
            altura_fim = 220
            x_fim = (largura // 2) - (largura_fim // 2)
            y_fim = (altura // 2) - (altura_fim // 2)
            
            pygame.draw.rect(tela, (50, 50, 50), (x_fim + 8, y_fim + 8, largura_fim, altura_fim), border_radius=15)
            
            cor_fundo_placa = (253, 250, 235)
            pygame.draw.rect(tela, cor_fundo_placa, (x_fim, y_fim, largura_fim, altura_fim), border_radius=15)
            pygame.draw.rect(tela, preto, (x_fim, y_fim, largura_fim, altura_fim), width=4, border_radius=15)
            
            if vencedor == meu_nickname:
                titulo_fim = "Excelente trabalho!"
                subtitulo_fim = "Venceu a corrida das pizzas."
                cor_destaque = (42, 157, 143) 
            else:
                titulo_fim = "Fim de expediente!"
                subtitulo_fim = "Perdeu a corrida para o oponente."
                cor_destaque = (224, 122, 95) 
                
            texto_titulo = fonte_anuncio.render(titulo_fim, True, cor_destaque)
            texto_subtitulo = fonte_pixel.render(subtitulo_fim, True, preto)
            
            fonte_saida = pygame.font.SysFont("Courier", 16, bold=True)
            aviso_saida = fonte_saida.render("Pressione [ENTER] para voltar ao lobby", True, (100, 100, 100))
            
            tela.blit(texto_titulo, (largura // 2 - texto_titulo.get_width() // 2, y_fim + 40))
            tela.blit(texto_subtitulo, (largura // 2 - texto_subtitulo.get_width() // 2, y_fim + 100))
            tela.blit(aviso_saida, (largura // 2 - aviso_saida.get_width() // 2, y_fim + 170))

            teclas_pressionadas = pygame.key.get_pressed()
            # aguarda o comando do usuario para fechar a tela
            if teclas_pressionadas[pygame.K_RETURN]:
                rodando = False

        pygame.display.flip()
        
        # fixa o limite maximo de quadros por segundo da tela
        relogio.tick(60)

    # encerra as funcionalidades graficas ao sair do loop principal
    logger.info(f"[{meu_nickname}] fechou a janela da cozinha e retornou ao lobby")
    pygame.quit()