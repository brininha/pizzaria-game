from PIL import Image

def hex_para_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def recolorir_coruja(caminho_base, cor_corpo="#b4b4b4", cor_avental="#464646", cor_bolso="#303030", cor_olhos="#8f8f8f"):
    # Mapeamento estrito da paleta de cinza que você definiu para novas cores
    mapa_cores = {
        hex_para_rgb("b4b4b4"): hex_para_rgb(cor_corpo),
        hex_para_rgb("464646"): hex_para_rgb(cor_avental),
        hex_para_rgb("303030"): hex_para_rgb(cor_bolso),
        hex_para_rgb("8f8f8f"): hex_para_rgb(cor_olhos)
    }

    img = Image.open(caminho_base).convert("RGBA")
    dados = img.getdata()
    
    novos_pixels = []
    for pixel in dados:
        if pixel[3] == 0:  # Ignora pixels 100% transparentes
            novos_pixels.append(pixel)
            continue
            
        rgb = pixel[:3]
        # Se a cor do pixel atual estiver no nosso mapa de cinzas, substitui
        if rgb in mapa_cores:
            nova_cor = mapa_cores[rgb]
            novos_pixels.append(nova_cor + (pixel[3],)) # Mantém a opacidade original
        else:
            novos_pixels.append(pixel)
            
    img.putdata(novos_pixels)
    return img