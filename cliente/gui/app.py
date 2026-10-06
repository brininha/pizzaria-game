import customtkinter as ctk
from PIL import Image
import threading
from cliente.main_gui import conectar_servidor, escutar_servidor, fila_mensagens, enviar_heartbeat
from utils.protocolo import formatar_mensagem
from cliente.gui.imagem import recolorir_coruja
from utils.seguranca import criptografar
from utils.logger import obter_logger

logger = obter_logger("interface_cliente")

# configuracoes globais do customtkinter
ctk.set_appearance_mode("light") 

class PizzariaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cojura's Pizzeria")
        self.geometry("800x600")
        self.configure(fg_color="#F6F4E8")
        
        # conexao de rede (inicia vazia)
        self.client_socket = None
        self.jogadores_online = {}
        
        # carrega a fonte customizada (se baixada), ou usa courier provisoriamente
        self.fonte_pixel = ("Courier", 24, "bold") 
        
        # inicializa a tela de login
        self.construir_tela_login()
        
        # inicia o motor de verificacao da fila
        self.verificar_fila()

    def verificar_fila(self):
        while not fila_mensagens.empty():
            comando, payload = fila_mensagens.get()
            
            if comando == "AUTH_REPLY" and payload == "OK":
                logger.info(f"[{self.meu_nickname}] login autorizado! abrindo o lobby...")
                
                self.frame_login.destroy()
                self.construir_tela_lobby()
                
                self.jogadores_online[self.meu_nickname] = {"cor": "#464646", "ocupado": False}
                self.desenhar_lista_jogadores()
                
            elif comando == "SEND_CHAT":
                # mostra a mensagem na tela de chat
                self.caixa_chat.configure(state="normal")
                self.caixa_chat.insert("end", f"{payload}\n")
                self.caixa_chat.see("end")
                self.caixa_chat.configure(state="disabled")
                
            elif comando == "SYNC_STATUS":
                self.processar_sync_status(payload)

            elif comando == "CHALLENGE_INVITE":
                self.mostrar_convite(payload)

            elif comando == "MATCH_REJECT":
                self.processar_sync_status(f"Desafio falhou: {payload}")

            elif comando == "MATCH_INFO":
                logger.info(f"recebido match_info! iniciando p2p com: {payload}")
                self.abrir_cozinha_pygame(payload)

        self.after(100, self.verificar_fila)
    
    def construir_tela_login(self):
        # frame centralizador
        self.frame_login = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_login.place(relx=0.5, rely=0.5, anchor="center")

        # frame invisivel para agrupar o titulo e a imagem horizontalmente
        self.frame_titulo = ctk.CTkFrame(self.frame_login, fg_color="transparent")
        self.frame_titulo.pack(pady=(0, 40))

        self.lbl_texto_titulo = ctk.CTkLabel(
            self.frame_titulo, 
            text="Cojura's Pizzeria", 
            font=("Courier", 40, "bold"),
            text_color="black"
        )
        self.lbl_texto_titulo.pack(side="left")

        # imagem da pizza
        img_pizza = Image.open("cliente/gui/assets/pizza.png")
        ctk_img_pizza = ctk.CTkImage(light_image=img_pizza, size=(40, 40))
        
        self.lbl_img_pizza = ctk.CTkLabel(self.frame_titulo, image=ctk_img_pizza, text="")
        # side="left" alinha a imagem exatamente a direita do texto
        self.lbl_img_pizza.pack(side="left", padx=(10, 0), pady=(0, 10))

        # gera a imagem da coruja recolorida dinamicamente
        imagem_pil = recolorir_coruja(
            "cliente/gui/assets/coruja_vestida.png", 
            cor_corpo="#D19C74",
            cor_chapeu="#FFFFFF",
            cor_avental="#FFFFFF",
            cor_bolso="#CFCFCF",
            cor_olhos="#D7C9B2"
        )
        
        # converte a imagem pillow para o formato nativo do customtkinter
        owl_image = ctk.CTkImage(light_image=imagem_pil, size=(97, 163))
        
        self.lbl_coruja = ctk.CTkLabel(self.frame_login, image=owl_image, text="")
        
        self.lbl_coruja.pack(pady=(0, 0)) 

        # caixa de texto do nickname
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
        # o pady=(0, 20) afasta o conjunto do fundo da tela, mantendo a colisao em cima
        self.entry_nickname.pack(pady=(0, 20))
        self.entry_nickname.bind("<Return>", self.enviar_login)

    def enviar_login(self, event=None):
        nickname = self.entry_nickname.get().strip()
        if not nickname:
            return
        
        self.meu_nickname = nickname

        # conexao de rede (disparando o auth_conn)
        try:
            import socket
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.bind(("", 0))
            self.minha_porta_udp = self.udp_socket.getsockname()[1]

            self.client_socket = conectar_servidor()
            
            # agora envia o formato que o servidor espera: "nome:porta"
            mensagem = formatar_mensagem("AUTH_CONN", f"{nickname}:{self.minha_porta_udp}")
            self.client_socket.sendall(mensagem)
            
            thread_escuta = threading.Thread(target=escutar_servidor, args=(self.client_socket,))
            thread_escuta.daemon = True
            thread_escuta.start()
            
            thread_heartbeat = threading.Thread(target=enviar_heartbeat, args=(self.client_socket,))
            thread_heartbeat.daemon = True
            thread_heartbeat.start()
            
            self.entry_nickname.configure(state="disabled")
            
        except Exception as e:
            logger.error(f"falha ao conectar: {e}")
            
    def construir_tela_lobby(self):
        # frame principal que ocupa a tela toda
        self.frame_lobby = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_lobby.pack(fill="both", expand=True, padx=20, pady=20)

        # painel esquerdo
        self.frame_esquerdos = ctk.CTkFrame(self.frame_lobby, fg_color="transparent")
        self.frame_esquerdos.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # titulo do chat
        ctk.CTkLabel(self.frame_esquerdos, text="💬 Praça de alimentação", font=("Courier", 24, "bold"), text_color="black").pack(anchor="w", pady=(0, 10))

        # historico do chat
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
        self.caixa_chat.configure(state="disabled") # bloqueia digitacao direta no historico

        # rodape do chat
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

        # painel direito
        self.frame_direito = ctk.CTkFrame(self.frame_lobby, fg_color="transparent", width=250)
        self.frame_direito.pack(side="right", fill="y")
        self.frame_direito.pack_propagate(False) # forcando a largura fixa de 250px

        # titulo lista online
        ctk.CTkLabel(self.frame_direito, text="👥 Online", font=("Courier", 20, "bold"), text_color="black").pack(anchor="w", pady=(0, 10))

        # lista de jogadores
        self.lista_jogadores = ctk.CTkScrollableFrame(
            self.frame_direito,
            fg_color="white",
            border_color="#A31D1D",
            border_width=2,
            corner_radius=15
        )
        self.lista_jogadores.pack(fill="both", expand=True, pady=(0, 20))
        
        # titulo vestiario
        ctk.CTkLabel(self.frame_direito, text="👕 Vestiário", font=("Courier", 20, "bold"), text_color="black").pack(anchor="center", pady=(0, 10))

        # botoes de cores
        self.frame_cores = ctk.CTkFrame(self.frame_direito, fg_color="transparent")
        self.frame_cores.pack(pady=(0, 10))

        cores = ["#B1FFB7", "#FFFEC0", "#FFBDF2", "#A7B8FF"] 
        for cor in cores:
            btn_cor = ctk.CTkButton(
                self.frame_cores,
                text="",
                width=30, height=30,
                corner_radius=15,
                fg_color=cor,
                hover_color=cor,
                # o lambda captura a cor clicada e dispara a mudanca pro servidor
                command=lambda c=cor: self.mudar_cor_avental(c) 
            )
            btn_cor.pack(side="left", padx=5)
            
    def enviar_chat(self, event=None):
        texto = self.entry_chat.get().strip()
        if not texto:
            return
            
        # limpa a caixa de digitacao
        self.entry_chat.delete(0, "end")
        
        # atualiza a propria tela
        self.caixa_chat.configure(state="normal")
        self.caixa_chat.insert("end", f"Você: {texto}\n")
        self.caixa_chat.see("end") # rola para o fim
        self.caixa_chat.configure(state="disabled")

        # criptografa e envia pela rede
        texto_cifrado = criptografar(texto)
        mensagem_formatada = formatar_mensagem("SEND_CHAT", texto_cifrado) 
        self.client_socket.sendall(mensagem_formatada)

    def mudar_cor_avental(self, cor_hex):
        logger.info(f"[{self.meu_nickname}] mudando cor do avental para: {cor_hex}")
        
        self.jogadores_online[self.meu_nickname]["cor"] = cor_hex
        self.desenhar_lista_jogadores()
        # envia o sync_status para o servidor avisando que a coruja mudou
        mensagem = formatar_mensagem("SYNC_STATUS", cor_hex)
        self.client_socket.sendall(mensagem)
        
    def processar_sync_status(self, payload):
        # mostra o aviso do sistema no chat
        if hasattr(self, 'caixa_chat'):
            self.caixa_chat.configure(state="normal")
            self.caixa_chat.insert("end", f"[SISTEMA] {payload}\n")
            self.caixa_chat.see("end")
            self.caixa_chat.configure(state="disabled")
            
        # atualiza o dicionario de jogadores
        # verifica primeiro se e um aviso de partida
        if " entrou em partida" in payload:
            nome = payload.replace(" entrou em partida", "").strip()
            if nome in self.jogadores_online:
                self.jogadores_online[nome]["ocupado"] = True
                
        # depois verifica se e um aviso de login normal
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

        if hasattr(self, 'lista_jogadores'):
            self.desenhar_lista_jogadores()


    def desenhar_lista_jogadores(self):
        for widget in self.lista_jogadores.winfo_children():
            widget.destroy()
            
        for nome, info in self.jogadores_online.items():
            # extrai os novos dados do dicionario
            cor = info["cor"]
            ocupado = info.get("ocupado", False)
            
            frame_item = ctk.CTkFrame(self.lista_jogadores, fg_color="transparent")
            frame_item.pack(fill="x", pady=5)
            
            imagem_pil = recolorir_coruja("cliente/gui/assets/coruja_vestida.png", cor_corpo="#D19C74", cor_chapeu="#FFFFFF", cor_avental=cor, cor_bolso=cor, cor_olhos="#79431A")
            ctk_img = ctk.CTkImage(light_image=imagem_pil, size=(30, 42))
            
            avatar = ctk.CTkLabel(frame_item, image=ctk_img, text="")
            avatar.pack(side="left", padx=(5, 10))
            
            # define o texto base (apenas o nome e a indicacao de quem e voce)
            texto_exibicao = f"{nome} (Você)" if nome == self.meu_nickname else nome
                
            # o nome fica cinza se estiver ocupado
            lbl_nome = ctk.CTkLabel(frame_item, text=texto_exibicao, font=("Courier", 14, "bold"), text_color="gray" if ocupado else "black")
            lbl_nome.pack(side="left")

            # renderiza o botao de desafio
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
        logger.info(f"[{self.meu_nickname}] enviando convite para {oponente}...")
        self.oponente_atual = oponente
        mensagem = formatar_mensagem("REQ_MATCH", oponente)
        self.client_socket.sendall(mensagem)

    # funcao para mostrar o convite de partida        
    def mostrar_convite(self, desafiante):
        janela_convite = ctk.CTkToplevel(self)
        janela_convite.title("Novo Desafio!")
        
        # centralizar a janela de convite em relacao a janela principal do lobby
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
        
        # aplica a mesma cor de fundo bege do lobby
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
        
        # botoes com cores mais suaves e elegantes
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
        self.withdraw()
        
        # o info_oponente chega do servidor como "192.168.0.5:5050:8472"
        ip_oponente, porta_oponente_str, semente_str = info_oponente.split(":")
        porta_oponente = int(porta_oponente_str)
        semente_partida = int(semente_str)
        
        logger.info(f"[{self.meu_nickname}] bem-vindo a cozinha (pygame)")
        logger.info(f"[{self.meu_nickname}] adversario: {self.oponente_atual} ({ip_oponente}:{porta_oponente})")
        
        import cliente.gui.cozinha as cozinha
        
        cozinha.iniciar_partida(
            self.meu_nickname, 
            self.oponente_atual, 
            ip_oponente, 
            porta_oponente, 
            self.udp_socket,
            semente_partida
        )
        
        self.deiconify()
        self.client_socket.sendall(formatar_mensagem("BACK_LOBBY", "OK"))

# executa a aplicacao
if __name__ == "__main__":
    app = PizzariaApp()
    app.mainloop()