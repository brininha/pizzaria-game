import customtkinter as ctk
from PIL import Image
import threading
from cliente.main_gui import conectar_servidor, escutar_servidor, fila_mensagens
from utils.protocolo import formatar_mensagem
from cliente.gui.imagem import recolorir_coruja

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
        
        # Carrega a fonte customizada (se baixada), ou usa Courier provisoriamente
        self.fonte_pixel = ("Courier", 24, "bold") 
        
        # Inicializa a tela de login
        self.construir_tela_login()
        
        # Inicia o motor de verificação da fila
        self.verificar_fila()

    def verificar_fila(self):
        while not fila_mensagens.empty():
            comando, payload = fila_mensagens.get()
            print(f"[GUI] Processando: {comando}")
            
            # Nas próximas Issues, faremos os if/elif aqui para atualizar a tela
            if comando == "AUTH_REPLY" and payload == "OK":
                print("Login autorizado! Indo para o lobby...")
                # self.construir_tela_lobby()
                
        self.after(100, self.verificar_fila)
    
    def construir_tela_login(self):
        # Frame centralizador
        self.frame_login = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_login.place(relx=0.5, rely=0.5, anchor="center")

        # Frame invisível para agrupar o título e a imagem horizontalmente
        self.frame_titulo = ctk.CTkFrame(self.frame_login, fg_color="transparent")
        self.frame_titulo.pack(pady=(0, 40))

        # Apenas o texto (sem o emoji)
        self.lbl_texto_titulo = ctk.CTkLabel(
            self.frame_titulo, 
            text="Cojura's Pizzeria", 
            font=("Courier", 40, "bold"),
            text_color="black"
        )
        self.lbl_texto_titulo.pack(side="left")

        # Imagem da pizza (recortada do seu protótipo)
        # Salve a fatia de pizza como 'pizza.png' com fundo transparente na pasta assets
        img_pizza = Image.open("cliente/gui/assets/pizza.png")
        ctk_img_pizza = ctk.CTkImage(light_image=img_pizza, size=(40, 40)) # Ajuste o tamanho proporcional ao texto
        
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
        # pady=(0, 0) é o segredo: empurra a coruja exatamente para a borda inferior
        self.lbl_coruja.pack(pady=(0, 0)) 

        # Caixa de texto do Nickname
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

        # ==========================================
        # CONEXÃO DE REDE (Disparando o AUTH_CONN)
        # ==========================================
        try:
            # 1. Conecta ao servidor 
            self.client_socket = conectar_servidor()
            
            # 2. Envia a autenticação
            mensagem = formatar_mensagem("AUTH_CONN", nickname)
            self.client_socket.sendall(mensagem)
            
            # 3. Inicia a thread de escuta em background
            thread_escuta = threading.Thread(target=escutar_servidor, args=(self.client_socket,))
            thread_escuta.daemon = True
            thread_escuta.start()
            
            # Desativa o input para evitar múltiplos envios
            self.entry_nickname.configure(state="disabled")
            
        except Exception as e:
            print(f"Falha ao conectar: {e}")

# Executa a aplicação
if __name__ == "__main__":
    app = PizzariaApp()
    app.mainloop()