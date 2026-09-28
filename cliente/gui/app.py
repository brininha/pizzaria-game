import customtkinter as ctk
from PIL import Image
import threading
from cliente.main_gui import conectar_servidor, escutar_servidor, fila_mensagens
from utils.protocolo import formatar_mensagem
from cliente.gui.imagem import recolorir_coruja
from utils.seguranca import criptografar

# Configurações globais do CustomTkinter
ctk.set_appearance_mode("light") 

class PizzariaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cojura's Pizzeria")
        self.geometry("800x600")
        self.configure(fg_color="#F6F4E8")
        
        # Conexão de rede (inicia vazia)
        self.client_socket = None
        self.jogadores_online = {}
        
        # Carrega a fonte customizada (se baixada), ou usa Courier provisoriamente
        self.fonte_pixel = ("Courier", 24, "bold") 
        
        # Inicializa a tela de login
        self.construir_tela_login()
        
        # Inicia o motor de verificação da fila
        self.verificar_fila()

    def verificar_fila(self):
        while not fila_mensagens.empty():
            comando, payload = fila_mensagens.get()
            
            if comando == "AUTH_REPLY" and payload == "OK":
                print("[GUI] Login autorizado! Abrindo o lobby...")
                self.frame_login.destroy()
                self.construir_tela_lobby()
                
            elif comando == "SEND_CHAT":
                # Mostra a mensagem na tela de chat
                self.caixa_chat.configure(state="normal")
                self.caixa_chat.insert("end", f"{payload}\n")
                self.caixa_chat.see("end")
                self.caixa_chat.configure(state="disabled")
                
            elif comando == "SYNC_STATUS":
                self.processar_sync_status(payload)
                
        self.after(100, self.verificar_fila)
    
    def construir_tela_login(self):
        # Frame centralizador
        self.frame_login = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_login.place(relx=0.5, rely=0.5, anchor="center")

        # Frame invisível para agrupar o título e a imagem horizontalmente
        self.frame_titulo = ctk.CTkFrame(self.frame_login, fg_color="transparent")
        self.frame_titulo.pack(pady=(0, 40))

        self.lbl_texto_titulo = ctk.CTkLabel(
            self.frame_titulo, 
            text="Cojura's Pizzeria", 
            font=("Courier", 40, "bold"),
            text_color="black"
        )
        self.lbl_texto_titulo.pack(side="left")

        # Imagem da pizza
        img_pizza = Image.open("cliente/gui/assets/pizza.png")
        ctk_img_pizza = ctk.CTkImage(light_image=img_pizza, size=(40, 40))
        
        self.lbl_img_pizza = ctk.CTkLabel(self.frame_titulo, image=ctk_img_pizza, text="")
        # side="left" alinha a imagem exatamente à direita do texto
        self.lbl_img_pizza.pack(side="left", padx=(10, 0), pady=(0, 10))

        # Gera a imagem da coruja recolorida dinamicamente
        imagem_pil = recolorir_coruja(
            "cliente/gui/assets/coruja_base.png", 
            cor_corpo="#D19C74",
            cor_avental="#464646",
            cor_bolso="#303030",
            cor_olhos="#79431A"
        )
        
        # Converte a imagem Pillow para o formato nativo do CustomTkinter
        owl_image = ctk.CTkImage(light_image=imagem_pil, size=(72, 100))
        
        self.lbl_coruja = ctk.CTkLabel(self.frame_login, image=owl_image, text="")
        
        self.lbl_coruja.pack(pady=(0, 0)) 

        # Caixa de texto do nickname
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
        # O pady=(0, 20) afasta o conjunto do fundo da tela, mantendo a colisão em cima
        self.entry_nickname.pack(pady=(0, 20))
        self.entry_nickname.bind("<Return>", self.enviar_login)

    def enviar_login(self, event=None):
        nickname = self.entry_nickname.get().strip()
        if not nickname:
            return

        # Conexão de rede (disparando o AUTH_CONN)
        try:
            # Conecta ao servidor 
            self.client_socket = conectar_servidor()
            
            # Envia a autenticação
            mensagem = formatar_mensagem("AUTH_CONN", nickname)
            self.client_socket.sendall(mensagem)
            
            # Inicia a thread de escuta em background
            thread_escuta = threading.Thread(target=escutar_servidor, args=(self.client_socket,))
            thread_escuta.daemon = True
            thread_escuta.start()
            
            # Desativa o input para evitar múltiplos envios
            self.entry_nickname.configure(state="disabled")
            
        except Exception as e:
            print(f"Falha ao conectar: {e}")
            
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
        self.caixa_chat.configure(state="disabled") # Bloqueia digitação direta no histórico

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
        self.frame_direito.pack_propagate(False) # forçando a largura fixa de 250px

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

        cores = ["#464646", "#1D3557", "#2A9D8F", "#E76F51"] 
        for cor in cores:
            btn_cor = ctk.CTkButton(
                self.frame_cores,
                text="",
                width=30, height=30,
                corner_radius=15,
                fg_color=cor,
                hover_color=cor,
                # o lambda captura a cor clicada e dispara a mudança pro servidor
                command=lambda c=cor: self.mudar_cor_avental(c) 
            )
            btn_cor.pack(side="left", padx=5)
            
    def enviar_chat(self, event=None):
        texto = self.entry_chat.get().strip()
        if not texto:
            return
            
        # limpa a caixa de digitação
        self.entry_chat.delete(0, "end")
        
        # atualiza a própria tela
        self.caixa_chat.configure(state="normal")
        self.caixa_chat.insert("end", f"Você: {texto}\n")
        self.caixa_chat.see("end") # rola para o fim
        self.caixa_chat.configure(state="disabled")

        # criptografa e envia pela rede
        texto_cifrado = criptografar(texto)
        mensagem_formatada = formatar_mensagem("SEND_CHAT", texto_cifrado) # Troque para texto_cifrado depois!
        self.client_socket.sendall(mensagem_formatada)

    def mudar_cor_avental(self, cor_hex):
        print(f"[GUI] Mudando cor do avental para: {cor_hex}")
        # Envia o SYNC_STATUS para o servidor avisando que a coruja mudou
        mensagem = formatar_mensagem("SYNC_STATUS", cor_hex)
        self.client_socket.sendall(mensagem)
        
    def processar_sync_status(self, payload):
        # Mostra o aviso do sistema no chat
        if hasattr(self, 'caixa_chat'):
            self.caixa_chat.configure(state="normal")
            self.caixa_chat.insert("end", f"[SISTEMA] {payload}\n")
            self.caixa_chat.see("end")
            self.caixa_chat.configure(state="disabled")
            
        # Atualiza o dicionário de jogadores
        if " entrou" in payload:
            nome = payload.replace(" entrou", "").strip()
            self.jogadores_online[nome] = "#464646" # Cor padrão (cinza)
        
        elif "_saiu" in payload:
            nome = payload.replace("_saiu", "").strip()
            if nome in self.jogadores_online:
                del self.jogadores_online[nome]
                
        elif " mudou para " in payload:
            partes = payload.split(" mudou para ")
            nome = partes[0].strip()
            cor_hex = partes[1].strip()
            if nome in self.jogadores_online:
                self.jogadores_online[nome] = cor_hex

        # Redesenha a lista lateral apenas se o lobby já estiver aberto
        if hasattr(self, 'lista_jogadores'):
            self.desenhar_lista_jogadores()

    def desenhar_lista_jogadores(self):
        # Limpa todos os itens atuais da tela
        for widget in self.lista_jogadores.winfo_children():
            widget.destroy()
            
        # Recria os itens atualizados
        for nome, cor in self.jogadores_online.items():
            frame_item = ctk.CTkFrame(self.lista_jogadores, fg_color="transparent")
            frame_item.pack(fill="x", pady=5)
            
            # Por enquanto, usamos um círculo colorido para representar o avatar
            avatar = ctk.CTkFrame(frame_item, width=20, height=20, corner_radius=10, fg_color=cor)
            avatar.pack(side="left", padx=(5, 10))
            
            lbl_nome = ctk.CTkLabel(frame_item, text=nome, font=("Courier", 14, "bold"), text_color="black")
            lbl_nome.pack(side="left")

# executa a aplicacao
if __name__ == "__main__":
    app = PizzariaApp()
    app.mainloop()