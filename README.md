# 🦉🍕 Cojura's Pizzeria

Este projeto é uma aplicação distribuída desenvolvida para a disciplina de Redes de Computadores. Ele consiste em um (*lobby*) com chat global e um minijogo competitivo de montar pizzas, operando em uma arquitetura híbrida que mescla a comunicação cliente-servidor e ponto a ponto (P2P).

## Arquitetura de rede

O sistema foi desenhado para explorar as diferenças e aplicações práticas dos principais protocolos da camada de transporte:

* **TCP:** Gerencia o saguão principal. É responsável por manter o controle de estado dos jogadores (online, ocupado), rotear mensagens do chat global, processar convites para partidas e gerir desconexões abruptas através de *heartbeats* e *timeouts*.
* **UDP:** Gerencia o minijogo. Quando dois jogadores aceitam uma partida, o servidor TCP realiza a troca de IPs e portas entre eles. A partir desse momento, a partida ocorre via UDP direto entre as máquinas (*peer-to-peer*), garantindo velocidade e menor latência na atualização das pontuações, sem sobrecarregar o servidor central.

## Funcionalidades

* **Saguão multiplayer:** Lista de jogadores online atualizada em tempo real.
* **Chat criptografado:** Mensagens globais protegidas por uma cifra de substituição na camada de aplicação.
* **Customização de avatar:** Mudança da cor do avental da coruja refletida instantaneamente para todos no saguão.
* **Sistema de matchmaking:** Envio, aceitação e recusa de convites com tratamento de concorrência (*race conditions*).
* **Minigame sincronizado:** Geração idêntica de pedidos nos dois clientes baseada em uma *seed* compartilhada. Vence quem fizer 100 pontos primeiro.
* **Logs de execução:** Histórico detalhado gerado automaticamente em arquivos `.log` para auditoria.

## Tecnologias utilizadas

* **Python 3** (linguagem principal)
* **Sockets nativos** (`socket`) e **threads** (`threading`) para a infraestrutura de rede.
* **CustomTkinter** para a interface gráfica moderna do lobby.
* **Pygame** para o motor gráfico e captura de eventos do minijogo.
* **Pillow (PIL)** para manipulação dinâmica de cores dos *sprites*.

## Como executar o projeto

### 1. Preparando o ambiente

Recomenda-se o uso de um ambiente virtual para isolar as dependências do projeto. No terminal, na raiz do projeto, execute:

**Criar o ambiente virtual:**

```bash
python -m venv venv

```

**Ativar o ambiente:**

* No Linux/macOS: `source venv/bin/activate`
* No Windows: `venv\Scripts\activate`

**Instalar as dependências:**

```bash
pip install -r requirements.txt

```

### 2. Rodando a aplicação

O sistema exige que o servidor esteja online antes dos clientes.

**Inicie o Servidor:**
Abra um terminal, ative o ambiente virtual e rode:

```bash
python servidor.py

```

**Inicie os Clientes:**
Abra novos terminais (quantos clientes desejar), ative o ambiente virtual em cada um deles e rode:

```bash
python app.py

```

*Nota: Por padrão, a aplicação roda em `localhost` (127.0.0.1). Para testar com computadores diferentes na mesma rede Wi-Fi, altere a variável `HOST` no arquivo `config.py` para o endereço IPv4 da máquina que está rodando o servidor.*