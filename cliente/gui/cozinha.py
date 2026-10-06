import pygame
import os
import threading
import random
import socket

def iniciar_partida(meu_nickname, oponente_nickname, ip_oponente, porta_oponente, meu_socket_udp):
    pygame.init()

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
        caminho = os.path.join(diretorio_assets, nome_arquivo)
        imagem = pygame.image.load(caminho).convert_alpha()
        return pygame.transform.scale(imagem, (300, 300))
    
    def carregar_icone(nome_arquivo):
        caminho = os.path.join(diretorio_assets, nome_arquivo)
        try:
            imagem = pygame.image.load(caminho).convert_alpha()
            return pygame.transform.scale(imagem, (60, 60)) # ajuste o tamanho dos tubos aqui
        except FileNotFoundError:
            # placeholder temporario caso a imagem não exista na pasta ainda
            surf = pygame.Surface((60, 60))
            surf.fill((180, 180, 180))
            return surf

    img_massa = carregar_dimensionar("massa.png")

    # mapeia a tecla para o nome descritivo e a imagem já carregada
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
    

    # usando uma seed fixa, os dois computadores geram a exata mesma fila
    random.seed(42) 
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

    # sincronizacao em tempo real
    rodando = True
    def escutar_udp():
        nonlocal pontuacao_oponente, rodando, fim_de_jogo, vencedor
        meu_socket_udp.settimeout(0.5)
        while rodando:
            try:
                dados, _ = meu_socket_udp.recvfrom(1024)
                msg = dados.decode('utf-8')
                if msg.startswith("SCORE:"):
                    pontuacao_oponente = int(msg.split(":")[1])
                    if pontuacao_oponente >= 100:
                        vencedor = oponente_nickname
                        fim_de_jogo = True
            except socket.timeout:
                continue
            except Exception as e:
                pass

    thread_udp = threading.Thread(target=escutar_udp)
    thread_udp.daemon = True
    thread_udp.start()

    relogio = pygame.time.Clock()

    # loop principal
    while rodando:
        tela.fill(branco)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

            elif evento.type == pygame.KEYDOWN and not fim_de_jogo:
                if evento.key in catalogo["molho"]:
                    pizza_atual["molho"] = evento.key
                elif evento.key in catalogo["queijo"]:
                    pizza_atual["queijo"] = evento.key
                elif evento.key in catalogo["extra"]:
                    pizza_atual["extra"] = evento.key
                
                # verificacao do pedido montado
                elif evento.key == pygame.K_SPACE:
                    pedido = fila_pedidos[indice_pedido]
                    
                    if (pizza_atual["molho"] == pedido["molho"] and 
                        pizza_atual["queijo"] == pedido["queijo"] and 
                        pizza_atual["extra"] == pedido["extra"]):
                        
                        pontuacao_jogador += 10
                        indice_pedido += 1
                        
                        # dispara o ponto via UDP para o oponente
                        meu_socket_udp.sendto(f"SCORE:{pontuacao_jogador}".encode('utf-8'), (ip_oponente, porta_oponente))
                        
                        # verifica se ganhou
                        if pontuacao_jogador >= 100:
                            vencedor = meu_nickname
                            fim_de_jogo = True
                    
                    # independentemente de acertar ou errar, a bandeja limpa para a próxima tentativa
                    pizza_atual = {"molho": None, "queijo": None, "extra": None}

        # renderização do HUD
        texto_jogador = fonte_pixel.render(f"{meu_nickname}: R${pontuacao_jogador}", True, verde if pontuacao_jogador > pontuacao_oponente else preto)
        texto_oponente = fonte_pixel.render(f"{oponente_nickname}: R${pontuacao_oponente}", True, vermelho if pontuacao_oponente > pontuacao_jogador else preto)

        tela.blit(texto_jogador, (30, 30))
        tela.blit(texto_oponente, (largura - texto_oponente.get_width() - 30, 30))

        # calcula o centro da pizza
        centro_x = (largura // 2) - 150 
        centro_y = 160 

        # desenha a esteira passando um pouco da altura da pizza (recuo de 20px)
        cor_esteira = (130, 130, 130)
        cor_borda_esteira = (80, 80, 80)
        cor_listra = (110, 110, 110) # cor das listras internas
        
        y_esteira = centro_y - 20
        altura_esteira = 340 
        
        # fundo da esteira
        pygame.draw.rect(tela, cor_esteira, (0, y_esteira, largura, altura_esteira))
        
        # desenha as listras verticais ao longo de toda a esteira (a cada 40 pixels)
        for x_listra in range(0, largura, 40):
            pygame.draw.line(tela, cor_listra, (x_listra, y_esteira), (x_listra, y_esteira + altura_esteira), 4)
        
        # linhas horizontais grossas nas bordas da esteira
        pygame.draw.line(tela, cor_borda_esteira, (0, y_esteira), (largura, y_esteira), 6)
        pygame.draw.line(tela, cor_borda_esteira, (0, y_esteira + altura_esteira - 4), (largura, y_esteira + altura_esteira - 4), 6)

        # desenha a massa por cima da esteira texturizada
        tela.blit(img_massa, (centro_x, centro_y))

        if pizza_atual["molho"]: tela.blit(catalogo["molho"][pizza_atual["molho"]]["img"], (centro_x, centro_y))
        if pizza_atual["queijo"]: tela.blit(catalogo["queijo"][pizza_atual["queijo"]]["img"], (centro_x, centro_y))
        if pizza_atual["extra"]: tela.blit(catalogo["extra"][pizza_atual["extra"]]["img"], (centro_x, centro_y))

        # desenha o papelzinho do pedido atual
        if not fim_de_jogo and indice_pedido < len(fila_pedidos):
            pedido = fila_pedidos[indice_pedido]
            
            nome_molho = catalogo["molho"][pedido["molho"]]["nome"]
            nome_queijo = catalogo["queijo"][pedido["queijo"]]["nome"]
            nome_extra = catalogo["extra"][pedido["extra"]]["nome"]
            
            tecla_m = pygame.key.name(pedido['molho']).upper()
            tecla_q = pygame.key.name(pedido['queijo']).upper()
            tecla_e = pygame.key.name(pedido['extra']).upper()
            
            # desenha a caixa branca do pedido centralizada e um pouco menor
            largura_caixa = 280
            altura_caixa = 120
            x_caixa = (largura // 2) - (largura_caixa // 2)
            y_caixa = 45
            
            pygame.draw.rect(tela, (255, 255, 255), (x_caixa, y_caixa, largura_caixa, altura_caixa), border_radius=10)
            pygame.draw.rect(tela, preto, (x_caixa, y_caixa, largura_caixa, altura_caixa), width=3, border_radius=10)
            
            texto_pedido = fonte_pixel.render(f"=== PEDIDO {indice_pedido + 1} ===", True, preto)
            
            linha_molho = fonte_pixel.render(f"{tecla_m}. {nome_molho}", True, vermelho)
            linha_queijo = fonte_pixel.render(f"{tecla_q}. {nome_queijo}", True, vermelho)
            linha_extra = fonte_pixel.render(f"{tecla_e}. {nome_extra}", True, vermelho)
            
            # ajusta as posicoes y para caber na caixa menor
            tela.blit(texto_pedido, (largura // 2 - texto_pedido.get_width() // 2, 50))
            tela.blit(linha_molho, (largura // 2 - linha_molho.get_width() // 2, 80))
            tela.blit(linha_queijo, (largura // 2 - linha_queijo.get_width() // 2, 105))
            tela.blit(linha_extra, (largura // 2 - linha_extra.get_width() // 2, 130))

        # renderizacao da bancada de ingredientes no rodape
        if not fim_de_jogo:
            y_bancada = altura - 110
            x_atual = 25 
            
            fonte_pequena = pygame.font.SysFont("Courier", 16, bold=True)
            
            for categoria, itens in catalogo.items():
                texto_cat = fonte_pequena.render(categoria.upper(), True, preto)
                
                # calcula o tamanho da caixa principal da categoria
                qtd_itens = len(itens)
                largura_caixa_cat = (qtd_itens * 70) + 10
                
                # desenha uma etiqueta (fundo branco, borda preta) para o titulo da categoria
                largura_titulo = texto_cat.get_width() + 16
                pygame.draw.rect(tela, (255, 255, 255), (x_atual + 10, y_bancada - 28, largura_titulo, 24), border_radius=5)
                pygame.draw.rect(tela, preto, (x_atual + 10, y_bancada - 28, largura_titulo, 24), width=2, border_radius=5)
                tela.blit(texto_cat, (x_atual + 18, y_bancada - 24))
                
                # desenha a caixa de fundo cinza da categoria
                cor_fundo_cat = (210, 210, 210)
                pygame.draw.rect(tela, cor_fundo_cat, (x_atual, y_bancada, largura_caixa_cat, 90), border_radius=8)
                pygame.draw.rect(tela, preto, (x_atual, y_bancada, largura_caixa_cat, 90), width=2, border_radius=8)
                
                x_item = x_atual + 10
                
                for indice, (tecla, dados) in enumerate(itens.items()):
                    icone = dados["icone"]
                    
                    # desenha linha divisoria preta entre os ingredientes
                    if indice > 0:
                        pygame.draw.line(tela, preto, (x_item - 5, y_bancada + 10), (x_item - 5, y_bancada + 80), 2)
                    
                    # centraliza o icone verticalmente na caixa (ja que tiramos o texto debaixo)
                    tela.blit(icone, (x_item, y_bancada + 15))
                    
                    x_item += 70 
                
                # espaco para a proxima caixa de categoria
                x_atual += largura_caixa_cat + 20
        
        if fim_de_jogo:
            # cria uma pelicula escura translucida sobre o jogo
            pelicula = pygame.Surface((largura, altura))
            pelicula.set_alpha(200)
            pelicula.fill(preto)
            tela.blit(pelicula, (0, 0))

            # define a mensagem e a cor com base em quem venceu
            if vencedor == meu_nickname:
                msg = "VOCÊ VENCEU!"
                cor_fim = verde
            else:
                msg = "VOCÊ PERDEU!"
                cor_fim = vermelho

            texto_fim = fonte_anuncio.render(msg, True, cor_fim)
            tela.blit(texto_fim, (largura // 2 - texto_fim.get_width() // 2, altura // 2 - 50))

            aviso_saida = fonte_pixel.render("Pressione [ENTER] para voltar", True, branco)
            tela.blit(aviso_saida, (largura // 2 - aviso_saida.get_width() // 2, altura // 2 + 50))

            # se apertar enter, quebra o loop e fecha o Pygame
            teclas_pressionadas = pygame.key.get_pressed()
            if teclas_pressionadas[pygame.K_RETURN]:
                rodando = False

        pygame.display.flip()
        relogio.tick(60)

    # ao fechar a janela do Pygame, volta ao estado limpo
    pygame.quit()