'''
COMENTARIOS ELUCIDATIVOS

este arquivo e responsavel por manipular a imagem do avatar (a coruja).
ele recebe a imagem base desenhada em tons de cinza e substitui 
cores especificas por novas cores escolhidas pelo jogador ou pelo sistema.
isso permite gerar corujas customizadas dinamicamente, sem a necessidade
de armazenar dezenas de arquivos de imagem diferentes no disco.
'''

from PIL import Image

def hex_para_rgb(hex_str):
    '''
    converte uma cor em formato hexadecimal (ex: #ffffff) para o 
    formato rgb (ex: 255, 255, 255), que e o padrao compreendido 
    pela biblioteca de manipulacao de imagens.
    '''
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def recolorir_coruja(caminho_base, cor_corpo="#b4b4b4", cor_chapeu="#292929", cor_avental="#464646", cor_bolso="#303030", cor_olhos="#8f8f8f"):
    '''
    abre o arquivo original e varre a imagem pixel por pixel.
    cada parte da coruja foi desenhada com um tom de cinza especifico 
    para servir como um marcador de substituicao.
    '''
    
    # dicionario que mapeia a cor cinza original para a nova cor solicitada
    mapa_cores = {
        hex_para_rgb("b4b4b4"): hex_para_rgb(cor_corpo),
        hex_para_rgb("292929"): hex_para_rgb(cor_chapeu),
        hex_para_rgb("464646"): hex_para_rgb(cor_avental),
        hex_para_rgb("303030"): hex_para_rgb(cor_bolso),
        hex_para_rgb("8f8f8f"): hex_para_rgb(cor_olhos)
    }

    # abre a imagem e converte para rgba para garantir a leitura da transparencia
    img = Image.open(caminho_base).convert("RGBA")
    dados = img.getdata()
    
    novos_pixels = []
    
    # percorre todos os pixels da imagem sequencialmente
    for pixel in dados:
        # ignora processamento se o pixel for totalmente transparente (fundo)
        if pixel[3] == 0:  
            novos_pixels.append(pixel)
            continue
            
        # extrai apenas as informacoes de vermelho, verde e azul (ignora o alfa)
        rgb = pixel[:3]
        
        # se a cor do pixel atual estiver listada no nosso mapa de substituicao, troca a cor
        if rgb in mapa_cores:
            nova_cor = mapa_cores[rgb]
            # anexa a nova cor, mantendo o nivel de transparencia (pixel[3]) da imagem original
            novos_pixels.append(nova_cor + (pixel[3],)) 
            
        # se nao estiver no mapa (como as linhas pretas de contorno), mantem a cor original
        else:
            novos_pixels.append(pixel)
            
    # aplica a lista de pixels modificados de volta no objeto da imagem e devolve
    img.putdata(novos_pixels)
    return img