'''
COMENTARIOS ELUCIDATIVOS

a interface grafica foi a parte onde mais tivemos o apoio da inteligencia artificial.

o grupo criou toda a prototipagem visual e o design das telas utilizando o canva, 
mas pedimos para a ia gerar boa parte do codigo estrutural desta interface.
 
tomamos essa decisao porque o tempo de projeto estava curto e a nossa prioridade
era aprender e aplicar os recursos de redes.

este arquivo e o gerenciador visual do cliente. ele cria a janela principal, 
desenha a tela de login, o lobby, o chat e a lista de jogadores, 
ele trabalha em conjunto com as threads de rede, lendo a fila de mensagens e 
atualizando a tela assim que uma informacao nova chega do servidor.
'''

import customtkinter as ctk
from PIL import Image
import threading
from cliente.main_gui import conectar_servidor, escutar_servidor, fila_mensagens, enviar_heartbeat
from utils.protocolo import formatar_mensagem
from cliente.gui.imagem import recolorir_coruja
from utils.seguranca import criptografar
from utils.logger import obter_logger

logger = obter_logger("interface_cliente")

# configuracoes globais de cor e aparencia da janela
ctk.set_appearance_mode("light") 

class PizzariaApp(ctk.CTk):
    def __init__(self):
        '''
        funcao que roda assim que o aplicativo abre. 
        ela configura o tamanho da tela, a cor de fundo e inicia a tela de login.
        '''
        super().__init__()

        self.title("Cojura's Pizzeria")
        self.geometry("800x600")
        self.configure(fg_color="#F6F4E8")
        
        # variaveis para guardar a conexao e quem esta online no momento
        self.client_socket = None
        self.jogadores_online = {}
        
        # fonte principal usada nos textos da tela
        self.fonte_pixel = ("Courier", 24, "bold") 
        
        # desenha a tela inicial para o jogador digitar o nome
        self.construir_tela_login()
        
        # liga o motor que fica checando se chegou mensagem nova da rede
        self.verificar_fila()

    def verificar_fila(self):
        '''
        esta funcao eh muito importante para a interface, ela roda repetidamente (a cada 100ms).
        ela pega as mensagens que a thread de rede guardou na fila e altera a tela
        de acordo com o que chegou (exemplo: mostra mensagem no chat, atualiza cores).
        '''
        while not fila_mensagens.empty():
            comando, payload = fila_mensagens.get()
            
            # se o servidor aceitou o login, apaga a tela inicial e abre o lobby
            if comando == "AUTH_REPLY" and payload == "OK":
                logger.info(f"[{self.meu_nickname}] login autorizado! abrindo o lobby...")
                
                self.frame_login.destroy()
                self.construir_tela_lobby()
                
                # adiciona o proprio jogador na lista de online com a cor padrao
                self.jogadores_online[self.meu_nickname] = {"cor": "#464646", "ocupado": False}
                self.desenhar_lista_jogadores()
                
            # se for mensagem de chat, destranca a caixa, escreve e tranca de novo
            elif comando == "SEND_CHAT":
                self.caixa_chat.configure(state="normal")
                self.caixa_chat.insert("end", f"{payload}\n")
                self.caixa_chat.see("end")
                self.caixa_chat.configure(state="disabled")
                
            # se for aviso do sistema (alguem entrou, saiu ou mudou de cor)
            elif comando == "SYNC_STATUS":
                self.processar_sync_status(payload)

            # se for um convite de outro jogador, abre a janelinha para aceitar
            elif comando == "CHALLENGE_INVITE":
                self.mostrar_convite(payload)

            # se o jogador tentou convidar alguem ocupado ou offline
            elif comando == "MATCH_REJECT":
                self.processar_sync_status(f"Desafio falhou: {payload}")

            # se os dois aceitaram jogar, o servidor manda os ips para iniciar a partida udp
            elif comando == "MATCH_INFO":
                logger.info(f"recebido match_info! iniciando p2p com: {payload}")
                self.abrir_cozinha_pygame(payload)

        # chama a si mesma novamente apos 100 milissegundos
        self.after(100, self.verificar_fila)
    
    def construir_tela_login(self):
        '''
        monta a primeira tela que o usuario ve, com o titulo, a imagem da coruja
        e a caixa para digitar o nome.
        '''
        # caixa invisivel no centro da tela para segurar os outros elementos
        self.frame_login = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_login.place(relx=0.5, rely=0.5, anchor="center")

        # caixa invisivel para deixar o titulo e a imagem da pizza lado a lado
        self.frame_titulo = ctk.CTkFrame(self.frame_login, fg_color="transparent")
        self.frame_titulo.pack(pady=(0, 40))

        self.lbl_texto_titulo = ctk.CTkLabel(
            self.frame_titulo, 
            text="Cojura's Pizzeria", 
            font=("Courier", 40, "bold"),
            text_color="black"
        )
        self.lbl_texto_titulo.pack(side="left")

        # carrega e exibe a imagem da pizza
        img_pizza = Image.open("cliente/gui/assets/pizza.png")
        ctk_img_pizza = ctk.CTkImage(light_image=img_pizza, size=(40, 40))
        
        self.lbl_img_pizza = ctk.CTkLabel(self.frame_titulo, image=ctk_img_pizza, text="")
        self.lbl_img_pizza.pack(side="left", padx=(10, 0), pady=(0, 10))

        # gera a imagem da coruja com as cores padrao
        imagem_pil = recolorir_coruja(
            "cliente/gui/assets/coruja_vestida.png", 
            cor_corpo="#D19C74",
            cor_chapeu="#FFFFFF",
            cor_avental="#FFFFFF",
            cor_bolso="#CFCFCF",
            cor_olhos="#D7C9B2"
        )
        owl_image = ctk.CTkImage(light_image=imagem_pil, size=(97, 163))
        
        self.lbl_coruja = ctk.CTkLabel(self.frame_login, image=owl_image, text="")
        self.lbl_coruja.pack(pady=(0, 0)) 

        # caixa de texto para o jogador digitar o nome
        self.entry_nickname = ctk.CTkEntry(
            self.frame_login,
            placeholder_text="Insira seu nickname",
            font=self.fonte_pixel,
            width=400,
            height=55,
            corner_radius=25,
            border_color="#A31D1D", 
            border_width=2,
            fg_color="white",
            justify="center",
            text_color="black",
        )
        self.entry_nickname.pack(pady=(0, 20))
        # quando o jogador aperta enter, chama a funcao de enviar o login
        self.entry_nickname.bind("<Return>", self.enviar_login)

    def enviar_login(self, event=None):
        '''
        pega o nome digitado, prepara a porta udp do jogador e avisa o servidor tcp
        que este cliente quer entrar no lobby.
        '''
        nickname = self.entry_nickname.get().strip()
        if not nickname:
            return
        
        self.meu_nickname = nickname

        try:
            # antes de falar com o servidor, ja criamos a nossa porta udp local
            # usar a porta 0 faz o sistema operacional escolher uma porta livre automaticamente
            import socket
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.bind(("", 0))
            self.minha_porta_udp = self.udp_socket.getsockname()[1]

            # conecta ao servidor central
            self.client_socket = conectar_servidor()
            
            # envia o nome e a porta udp escolhida para o servidor salvar na agenda dele
            mensagem = formatar_mensagem("AUTH_CONN", f"{nickname}:{self.minha_porta_udp}")
            self.client_socket.sendall(mensagem)
            
            # liga as threads de escuta e de manter a conexao viva
            thread_escuta = threading.Thread(target=escutar_servidor, args=(self.client_socket,))
            thread_escuta.daemon = True
            thread_escuta.start()
            
            thread_heartbeat = threading.Thread(target=enviar_heartbeat, args=(self.client_socket,))
            thread_heartbeat.daemon = True
            thread_heartbeat.start()
            
            # desativa a caixa de texto para evitar duplo enter enquanto espera o servidor
            self.entry_nickname.configure(state="disabled")
            
        except Exception as e:
            logger.error(f"falha ao conectar: {e}")
            
    def construir_tela_lobby(self):
        '''
        monta a tela do lobby, dividida em duas partes: 
        lado esquerdo com o chat geral e lado direito com a lista de jogadores e cores.
        '''
        self.frame_lobby = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_lobby.pack(fill="both", expand=True, padx=20, pady=20)

        # painel esquerdo (onde fica o chat)
        self.frame_esquerdos = ctk.CTkFrame(self.frame_lobby, fg_color="transparent")
        self.frame_esquerdos.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(self.frame_esquerdos, text="💬 Praça de alimentação", font=("Courier", 24, "bold"), text_color="black").pack(anchor="w", pady=(0, 10))

        # caixa de texto grande onde aparecem as mensagens do historico
        self.caixa_chat = ctk.CTkTextbox(
            self.frame_esquerdos, 
            font=("Courier", 16),
            fg_color="white",
            text_color="black",
            border_color="#A31D1D",
            border_width=2,
            corner_radius=15
        )
        self.caixa_chat.pack(fill="both", expand=True, pady=(0, 10))
        self.caixa_chat.insert("end", "Bem-vindo à Cojura's Pizzeria!\n\n")
        self.caixa_chat.configure(state="disabled") 

        # caixa de texto menor onde o usuario digita a mensagem nova
        self.frame_input_chat = ctk.CTkFrame(self.frame_esquerdos, fg_color="transparent")
        self.frame_input_chat.pack(fill="x")

        self.entry_chat = ctk.CTkEntry(
            self.frame_input_chat,
            placeholder_text="Digite sua mensagem...",
            font=("Courier", 16),
            height=40,
            fg_color="white",
            text_color="black",
            border_color="#A31D1D",
            border_width=2,
            corner_radius=20
        )
        self.entry_chat.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_chat.bind("<Return>", self.enviar_chat)

        self.btn_enviar = ctk.CTkButton(
            self.frame_input_chat,
            text="Enviar",
            font=("Courier", 16, "bold"),
            fg_color="#A31D1D",
            hover_color="#801515",
            corner_radius=20,
            width=100,
            height=40,
            command=self.enviar_chat
        )
        self.btn_enviar.pack(side="right")

        # painel direito (onde fica a lista de quem ta online)
        self.frame_direito = ctk.CTkFrame(self.frame_lobby, fg_color="transparent", width=250)
        self.frame_direito.pack(side="right", fill="y")
        self.frame_direito.pack_propagate(False) 

        ctk.CTkLabel(self.frame_direito, text="👥 Online", font=("Courier", 20, "bold"), text_color="black").pack(anchor="w", pady=(0, 10))

        # lista rolável para mostrar todos os jogadores sem quebrar a tela
        self.lista_jogadores = ctk.CTkScrollableFrame(
            self.frame_direito,
            fg_color="white",
            border_color="#A31D1D",
            border_width=2,
            corner_radius=15
        )
        self.lista_jogadores.pack(fill="both", expand=True, pady=(0, 20))
        
        ctk.CTkLabel(self.frame_direito, text="👕 Vestiário", font=("Courier", 20, "bold"), text_color="black").pack(anchor="center", pady=(0, 10))

        self.frame_cores = ctk.CTkFrame(self.frame_direito, fg_color="transparent")
        self.frame_cores.pack(pady=(0, 10))

        # cria os botoezinhos redondos para trocar a cor do avental
        cores = ["#B1FFB7", "#FFFEC0", "#FFBDF2", "#A7B8FF"] 
        for cor in cores:
            btn_cor = ctk.CTkButton(
                self.frame_cores,
                text="",
                width=30, height=30,
                corner_radius=15,
                fg_color=cor,
                hover_color=cor,
                command=lambda c=cor: self.mudar_cor_avental(c) 
            )
            btn_cor.pack(side="left", padx=5)
            
    def enviar_chat(self, event=None):
        '''
        funcao chamada quando o jogador clica em enviar ou aperta enter no chat.
        ela escreve a mensagem na propria tela, criptografa o texto e manda pro servidor.
        '''
        texto = self.entry_chat.get().strip()
        if not texto:
            return
            
        self.entry_chat.delete(0, "end")
        
        self.caixa_chat.configure(state="normal")
        self.caixa_chat.insert("end", f"Você: {texto}\n")
        self.caixa_chat.see("end") 
        self.caixa_chat.configure(state="disabled")

        # protege a mensagem antes de jogar na rede
        texto_cifrado = criptografar(texto)
        mensagem_formatada = formatar_mensagem("SEND_CHAT", texto_cifrado) 
        self.client_socket.sendall(mensagem_formatada)

    def mudar_cor_avental(self, cor_hex):
        '''
        atualiza a cor da propria coruja e avisa o servidor para espalhar
        a mudanca para os outros jogadores.
        '''
        logger.info(f"[{self.meu_nickname}] mudando cor do avental para: {cor_hex}")
        
        self.jogadores_online[self.meu_nickname]["cor"] = cor_hex
        self.desenhar_lista_jogadores()
        
        mensagem = formatar_mensagem("SYNC_STATUS", cor_hex)
        self.client_socket.sendall(mensagem)
        
    def processar_sync_status(self, payload):
        '''
        le os avisos do sistema (entrou, saiu, cor) e atualiza a lista interna
        de quem esta online e o status de cada um.
        '''
        if hasattr(self, 'caixa_chat'):
            self.caixa_chat.configure(state="normal")
            self.caixa_chat.insert("end", f"[SISTEMA] {payload}\n")
            self.caixa_chat.see("end")
            self.caixa_chat.configure(state="disabled")
            
        if " entrou em partida" in payload:
            nome = payload.replace(" entrou em partida", "").strip()
            if nome in self.jogadores_online:
                self.jogadores_online[nome]["ocupado"] = True
                
        elif " entrou" in payload:
            nome = payload.replace(" entrou", "").strip()
            self.jogadores_online[nome] = {"cor": "#464646", "ocupado": False}
            
        elif " voltou" in payload:
            nome = payload.replace(" voltou", "").strip()
            if nome in self.jogadores_online:
                self.jogadores_online[nome]["ocupado"] = False
        
        elif " saiu" in payload:
            nome = payload.replace(" saiu", "").strip()
            if nome in self.jogadores_online:
                del self.jogadores_online[nome]
                
        elif " mudou para " in payload:
            partes = payload.split(" mudou para ")
            nome = partes[0].strip()
            cor_hex = partes[1].strip()
            if nome in self.jogadores_online:
                self.jogadores_online[nome]["cor"] = cor_hex

        # recria a barra lateral com os status novos
        if hasattr(self, 'lista_jogadores'):
            self.desenhar_lista_jogadores()

    def desenhar_lista_jogadores(self):
        '''
        apaga e desenha novamente todos os bonequinhos e botoes na barra lateral direita.
        '''
        for widget in self.lista_jogadores.winfo_children():
            widget.destroy()
            
        for nome, info in self.jogadores_online.items():
            cor = info["cor"]
            ocupado = info.get("ocupado", False)
            
            frame_item = ctk.CTkFrame(self.lista_jogadores, fg_color="transparent")
            frame_item.pack(fill="x", pady=5)
            
            imagem_pil = recolorir_coruja("cliente/gui/assets/coruja_vestida.png", cor_corpo="#D19C74", cor_chapeu="#FFFFFF", cor_avental=cor, cor_bolso=cor, cor_olhos="#79431A")
            ctk_img = ctk.CTkImage(light_image=imagem_pil, size=(30, 42))
            
            avatar = ctk.CTkLabel(frame_item, image=ctk_img, text="")
            avatar.pack(side="left", padx=(5, 10))
            
            texto_exibicao = f"{nome} (Você)" if nome == self.meu_nickname else nome
                
            # deixa o nome cinza se a pessoa estiver jogando com outro
            lbl_nome = ctk.CTkLabel(frame_item, text=texto_exibicao, font=("Courier", 14, "bold"), text_color="gray" if ocupado else "black")
            lbl_nome.pack(side="left")

            # so desenha o botao de desafiar se nao for voce mesmo
            if nome != self.meu_nickname:
                btn_desafiar = ctk.CTkButton(
                    frame_item,
                    text="Ocupado" if ocupado else "Desafiar",
                    font=("Courier", 12, "bold"),
                    width=70,
                    height=24,
                    corner_radius=8,
                    fg_color="#555555" if ocupado else "#A31D1D",
                    hover_color="#555555" if ocupado else "#801515",
                    state="disabled" if ocupado else "normal",
                    command=lambda n=nome: self.enviar_desafio(n)
                )
                btn_desafiar.pack(side="right", padx=(10, 10))

    def enviar_desafio(self, oponente):
        '''
        avisa o servidor central tcp que voce quer jogar contra essa pessoa.
        '''
        logger.info(f"[{self.meu_nickname}] enviando convite para {oponente}...")
        self.oponente_atual = oponente
        mensagem = formatar_mensagem("REQ_MATCH", oponente)
        self.client_socket.sendall(mensagem)
     
    def mostrar_convite(self, desafiante):
        '''
        cria uma janelinha flutuante no meio da tela quando alguem te convida.
        '''
        janela_convite = ctk.CTkToplevel(self)
        janela_convite.title("Novo Desafio!")
        
        # calculo para fazer a janelinha aparecer bem no centro da tela principal
        largura_popup = 340
        altura_popup = 160
        x_main = self.winfo_x()
        y_main = self.winfo_y()
        w_main = self.winfo_width()
        h_main = self.winfo_height()
        
        x_popup = x_main + (w_main // 2) - (largura_popup // 2)
        y_popup = y_main + (h_main // 2) - (altura_popup // 2)
        
        janela_convite.geometry(f"{largura_popup}x{altura_popup}+{x_popup}+{y_popup}")
        janela_convite.attributes("-topmost", True)
        janela_convite.configure(fg_color="#F6F4E8")
        
        lbl_texto = ctk.CTkLabel(
            janela_convite, 
            text=f"O(a) {desafiante} desafiou-o!\nAceitar a partida?", 
            font=("Courier", 16, "bold"), 
            text_color="black"
        )
        lbl_texto.pack(pady=25)
        
        frame_botoes = ctk.CTkFrame(janela_convite, fg_color="transparent")
        frame_botoes.pack()
        
        def aceitar():
            self.oponente_atual = desafiante
            mensagem = formatar_mensagem("ACCEPT_MATCH", desafiante)
            self.client_socket.sendall(mensagem)
            janela_convite.destroy()
            
        def recusar():
            mensagem = formatar_mensagem("REJECT_MATCH", desafiante)
            self.client_socket.sendall(mensagem)
            janela_convite.destroy()
            
        btn_sim = ctk.CTkButton(
            frame_botoes, text="Sim", command=aceitar, width=100, 
            fg_color="#81B29A", hover_color="#5F8D76", 
            text_color="white", font=("Courier", 14, "bold")
        )
        btn_sim.pack(side="left", padx=15)
        
        btn_nao = ctk.CTkButton(
            frame_botoes, text="Não", command=recusar, width=100, 
            fg_color="#E07A5F", hover_color="#B55A41", 
            text_color="white", font=("Courier", 14, "bold")
        )
        btn_nao.pack(side="right", padx=15)
        
    def abrir_cozinha_pygame(self, info_oponente):
        '''
        funcao responsavel pela transicao do tcp para o udp.
        ela esconde o lobby, separa o ip e a porta do adversario e 
        abre a tela do minijogo para a partida p2p começar.
        '''
        # esconde a interface grafica (lobby)
        self.withdraw()
        
        # desmonta a mensagem que o servidor mandou com os dados do oponente
        ip_oponente, porta_oponente_str, semente_str = info_oponente.split(":")
        porta_oponente = int(porta_oponente_str)
        semente_partida = int(semente_str)
        
        logger.info(f"[{self.meu_nickname}] bem-vindo a cozinha (pygame)")
        logger.info(f"[{self.meu_nickname}] adversario: {self.oponente_atual} ({ip_oponente}:{porta_oponente})")
        
        import cliente.gui.cozinha as cozinha
        
        # roda o jogo no pygame usando conexao direta (udp)
        cozinha.iniciar_partida(
            self.meu_nickname, 
            self.oponente_atual, 
            ip_oponente, 
            porta_oponente, 
            self.udp_socket,
            semente_partida
        )
        
        # quando a partida de pygame fechar, o codigo volta para ca.
        # faz o lobby aparecer de novo e avisa o servidor que voce voltou pro chat.
        self.deiconify()
        self.client_socket.sendall(formatar_mensagem("BACK_LOBBY", "OK"))

if __name__ == "__main__":
    app = PizzariaApp()
    app.mainloop()