import pygame
import os 

def iniciar_partida(nickname_jogador, nickename_oponente):

    pygame.init()


    largura, altura = 800, 600
    tela = pygame.display.set_mode((largura, altura))
    pygame.display.set_caption("Cojura' s Pizzaria - Cozinha")

    branco = (246, 244, 232)
    preto = (0, 0, 0)
    vermelho = (163, 29, 29) 
    fonte_pixel = pygame.font.SysFont("Courier", 24, bold=True)
    fonte_relogio = pygame.font.SysFont("Courier", 64, bold=True)

    # Caminho dos assets (ajuste conforme a estrutura do repositório)
    diretorio_assests = os.path.join("cliente", "gui", "assets")

    def carregar_dimensionar(nome_arquivo):
        caminho = os.path.join(diretorio_assests, nome_arquivo)
        imagem = pygame.image.load(caminho).convert_alpha()
        return pygame.transform.scale(imagem, (350, 350))


    img_massa = carregar_dimensionar("massa.png")

    molhos = {
        pygame.K_1: carregar_dimensionar("molho-de-tomate.png"),
        pygame.K_2: carregar_dimensionar("molho-pesto.png"),
        pygame.K_3: carregar_dimensionar("molho-branco.png")
    }

    queijos = {
        pygame.K_4: carregar_dimensionar("mussarela.png"),
        pygame.K_5: carregar_dimensionar("cheddar.png"),
    }

    extras = {
        pygame.K_6: carregar_dimensionar("pepperoni.png"),
        pygame.K_7: carregar_dimensionar("cogumelo.png"),
        pygame.K_8: carregar_dimensionar("cebola-roxa.png"),
        pygame.K_9: carregar_dimensionar("manjericao.png"),
    }

    pizza_atual = {"molho": None, "queijo": None, "extra": None}

    pontuacao_oponente = 0
    pontuacao_jogador = 0
    tempo_restante = 60  

    evento_tempo = pygame.USEREVENT + 1
    pygame.time.set_timer(evento_tempo, 1000)  

    rodando = True
    relogio = pygame.time.Clock()

    while rodando: 
        tela.fill(branco)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

            elif evento.type == evento_tempo:
                if tempo_restante > 0:
                    tempo_restante -= 1
                else:
                    # Issue 33.4: Travar comandos quando o tempo acabar
                    pass

            elif evento.type == pygame.KEYDOWN and tempo_restante > 0:
                if evento.key in molhos:
                    pizza_atual["molho"] = molhos[evento.key]
                elif evento.key in queijos:
                    pizza_atual["queijo"] = queijos[evento.key]
                elif evento.key in extras:
                    pizza_atual["extra"] = extras[evento.key]
                
                elif evento.key == pygame.K_SPACE:
                    pizza_atual = {"molho": None, "queijo": None, "extra": None}
                    pontuacao_jogador += 10

#----Renderização da interface----

    texto_jogador = fonte_pixel.render(f"{nickname_jogador}: R${pontuacao_jogador}", True, preto)
    texto_oponente = fonte_pixel.render(f"{nickename_oponente}: R${pontuacao_oponente}", True, preto)

    tela.blit(texto_jogador, (30, 30))
    tela.blit(texto_oponente, (largura - texto_oponente.get_width() - 30, 30))

    texto_tempo = fonte_relogio.render(f"{tempo_restante}s", True, vermelho)
    tela.blit(texto_tempo, (largura//2 - texto_tempo.get_width()// 2, 20))

    centro_x = largura // 2 - 175
    centro_y = altura // 2 - 100

    tela.blit(img_massa, (centro_x, centro_y))

    if pizza_atual["molho"]:
        tela.blit(pizza_atual["molho"], (centro_x, centro_y))

    if pizza_atual["queijo"]:
        tela.blit(pizza_atual["queijo"], (centro_x, centro_y))

    if pizza_atual["extra"]:
        tela.blit(pizza_atual["extra"], (centro_x, centro_y))

    pygame.display.flip()
    relogio.tick(60)

pygame.quit()
