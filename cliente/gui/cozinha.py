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
        return pygame.transform.scale(imagem, (350, 350))

    img_massa = carregar_dimensionar("massa.png")

    # Estrutura unificada: mapeia a tecla para o nome descritivo e a imagem já carregada
    catalogo = {
        "molho": {
            pygame.K_1: {"nome": "Molho de Tomate", "img": carregar_dimensionar("molho-de-tomate.png")},
            pygame.K_2: {"nome": "Molho Pesto", "img": carregar_dimensionar("molho-pesto.png")},
            pygame.K_3: {"nome": "Molho Branco", "img": carregar_dimensionar("molho-branco.png")}
        },
        "queijo": {
            pygame.K_4: {"nome": "Mussarela", "img": carregar_dimensionar("mussarela.png")},
            pygame.K_5: {"nome": "Cheddar", "img": carregar_dimensionar("cheddar.png")},
        },
        "extra": {
            pygame.K_6: {"nome": "Pepperoni", "img": carregar_dimensionar("pepperoni.png")},
            pygame.K_7: {"nome": "Cogumelo", "img": carregar_dimensionar("cogumelo.png")},
            pygame.K_8: {"nome": "Cebola Roxa", "img": carregar_dimensionar("cebola-roxa.png")},
            pygame.K_9: {"nome": "Manjericão", "img": carregar_dimensionar("manjericao.png")},
        }
    }
    
    # ==========================================
    # REGRA 2: FILA DE PEDIDOS IDÊNTICA
    # Usando uma seed fixa, os dois computadores geram a exata mesma fila!
    # ==========================================
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

    # ==========================================
    # REGRA 3: ESCUTA UDP P2P (Sincronização em tempo real)
    # ==========================================
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

    # ==========================================
    # LOOP PRINCIPAL (Com indentação corrigida)
    # ==========================================
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
                
                # Verificação do pedido montado
                elif evento.key == pygame.K_SPACE:
                    pedido = fila_pedidos[indice_pedido]
                    
                    if (pizza_atual["molho"] == pedido["molho"] and 
                        pizza_atual["queijo"] == pedido["queijo"] and 
                        pizza_atual["extra"] == pedido["extra"]):
                        
                        pontuacao_jogador += 10
                        indice_pedido += 1
                        
                        # Dispara o ponto via UDP para o oponente
                        meu_socket_udp.sendto(f"SCORE:{pontuacao_jogador}".encode('utf-8'), (ip_oponente, porta_oponente))
                        
                        # Verifica se ganhou
                        if pontuacao_jogador >= 100:
                            vencedor = meu_nickname
                            fim_de_jogo = True
                    
                    # Independentemente de acertar ou errar, a bandeja limpa para a próxima tentativa
                    pizza_atual = {"molho": None, "queijo": None, "extra": None}

        # Renderização do HUD
        texto_jogador = fonte_pixel.render(f"{meu_nickname}: R${pontuacao_jogador}", True, verde if pontuacao_jogador > pontuacao_oponente else preto)
        texto_oponente = fonte_pixel.render(f"{oponente_nickname}: R${pontuacao_oponente}", True, vermelho if pontuacao_oponente > pontuacao_jogador else preto)

        tela.blit(texto_jogador, (30, 30))
        tela.blit(texto_oponente, (largura - texto_oponente.get_width() - 30, 30))

        # Desenha a pizza centralizada e sobrepõe os ingredientes escolhidos
        centro_x, centro_y = largura // 2 - 175, altura // 2 - 100
        tela.blit(img_massa, (centro_x, centro_y))

        if pizza_atual["molho"]: tela.blit(catalogo["molho"][pizza_atual["molho"]]["img"], (centro_x, centro_y))
        if pizza_atual["queijo"]: tela.blit(catalogo["queijo"][pizza_atual["queijo"]]["img"], (centro_x, centro_y))
        if pizza_atual["extra"]: tela.blit(catalogo["extra"][pizza_atual["extra"]]["img"], (centro_x, centro_y))

        # Desenha o papelzinho do pedido atual com nomes mais imersivos
        if not fim_de_jogo and indice_pedido < len(fila_pedidos):
            pedido = fila_pedidos[indice_pedido]
            
            # Busca os nomes reais no catálogo
            nome_molho = catalogo["molho"][pedido["molho"]]["nome"]
            nome_queijo = catalogo["queijo"][pedido["queijo"]]["nome"]
            nome_extra = catalogo["extra"][pedido["extra"]]["nome"]
            
            # Monta a string visual mostrando a tecla como dica (ex: "[1] Molho de Tomate")
            tecla_m = pygame.key.name(pedido['molho']).upper()
            tecla_q = pygame.key.name(pedido['queijo']).upper()
            tecla_e = pygame.key.name(pedido['extra']).upper()
            
            texto_pedido = fonte_pixel.render(f"=== PEDIDO {indice_pedido + 1} ===", True, preto)
            linha_molho = fonte_pixel.render(f"[{tecla_m}] {nome_molho}", True, vermelho)
            linha_queijo = fonte_pixel.render(f"[{tecla_q}] {nome_queijo}", True, vermelho)
            linha_extra = fonte_pixel.render(f"[{tecla_e}] {nome_extra}", True, vermelho)
            
            tela.blit(texto_pedido, (largura // 2 - texto_pedido.get_width() // 2, 70))
            tela.blit(linha_molho, (largura // 2 - linha_molho.get_width() // 2, 100))
            tela.blit(linha_queijo, (largura // 2 - linha_queijo.get_width() // 2, 130))
            tela.blit(linha_extra, (largura // 2 - linha_extra.get_width() // 2, 160))

        # Tela de Vitória/Derrota
        if fim_de_jogo:
            msg = f"{vencedor} GANHOU!"
            cor_fim = verde if vencedor == meu_nickname else vermelho
            texto_fim = fonte_anuncio.render(msg, True, cor_fim)
            tela.blit(texto_fim, (largura // 2 - texto_fim.get_width() // 2, altura // 2))

        pygame.display.flip()
        relogio.tick(60)

    # Ao fechar a janela do Pygame, volta ao estado limpo
    pygame.quit()