"""
Assistente Pokémon — Workshop Strands Agents (passos 1 a 5).

Passo 2: agente + modelo local (Ollama) + prompt de sistema + loop de conversa
Passo 3: callback handler para acompanhar o agentic loop
Passo 4: ferramentas com acesso à PokeAPI (tools_pokeapi.py)
Passo 5: memória de conversa com FileSessionManager
"""

from strands import Agent
from strands.models.ollama import OllamaModel
from strands.session.file_session_manager import FileSessionManager

# --- Passo 4: as ferramentas da PokeAPI substituem a base estática do passo 3 ---
# import json
# from pathlib import Path
# POKEDEX_DATA = json.loads(Path("data/pokemons.json").read_text())["pokedex"]
# As funções buscar_pokemon() e listar_pokemons() do passo 3 foram substituídas
# pelas ferramentas importadas abaixo.
from tools_pokeapi import (
    buscar_pokemon,
    buscar_fraquezas_tipo,
    buscar_movimento,
    buscar_habilidade,
    buscar_cadeia_evolucao,
    buscar_natureza,
)

# Passo 2: modelo local servido pelo Ollama
modelo = OllamaModel(
    host="http://localhost:11434",
    model_id="llama3.1",
)

# Passo 4: prompt de sistema com guardrails e a lista de ferramentas disponíveis
SYSTEM_PROMPT = """
Você é um agente que ajuda treinadores de Pokémon a criar estratégias.

REGRAS OBRIGATÓRIAS:
- Você NÃO possui conhecimento próprio sobre Pokémon. Toda informação DEVE vir das ferramentas.
- SEMPRE use as ferramentas ANTES de responder qualquer pergunta sobre Pokémon.
- Passe o nome EXATAMENTE como o usuário digitou para a ferramenta. NÃO traduza, corrija ou modifique nomes.
- Se a ferramenta retornar que o Pokémon não existe, diga: "O Pokémon [nome exato] não existe." e ofereça listar alternativas.
- NUNCA invente nomes, dados, stats, tipos ou habilidades. Se não veio da ferramenta, não existe.

FERRAMENTAS DISPONÍVEIS:
- buscar_pokemon: dados completos (tipos, stats, habilidades, movimentos)
- buscar_fraquezas_tipo: relações de dano entre tipos (forte contra, fraco contra)
- buscar_movimento: detalhes de um ataque (poder, precisão, efeito)
- buscar_habilidade: efeito de uma ability e quais Pokémon a possuem
- buscar_cadeia_evolucao: cadeia evolutiva completa
- buscar_natureza: efeitos de uma nature nos stats

FLUXO CORRETO:
1. Usuário menciona um Pokémon → chamar buscar_pokemon com o nome EXATO
2. Ferramenta retorna dados → usar APENAS esses dados
3. Ferramenta retorna erro/não encontrado → informar que não existe, sem inventar

Seus objetivos:
1. Identificar fortalezas e fraquezas dos Pokémon usando as ferramentas.
2. Ajudar a traçar estratégias de batalha.
3. Responder sempre em Português Brasileiro.
4. Manter as respostas concisas, no máximo 2-3 parágrafos.
"""

# Passo 3: callback handler para acompanhar o agentic loop (raciocínio → ação → observação)
_after_tool = False


def callback_handler(**kwargs):
    global _after_tool
    if "reasoningText" in kwargs:
        print(f"💭 {kwargs['reasoningText']}", end="", flush=True)
    if "data" in kwargs:
        if _after_tool:
            print("\n")
            _after_tool = False
        print(kwargs["data"], end="", flush=True)
    if "current_tool_use" in kwargs:
        _after_tool = True
        t = kwargs["current_tool_use"]
        if t.get("name"):
            print(f"\n\n🔧 Ferramenta: {t['name']}")
        if t.get("input"):
            print(f"   Parâmetros: {t['input']}")


# Passo 5: memória da conversa persistida em arquivos
session_manager = FileSessionManager(
    session_id="chat",
    storage_dir="./sessions",
)

agente = Agent(
    model=modelo,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        buscar_pokemon,
        buscar_fraquezas_tipo,
        buscar_movimento,
        buscar_habilidade,
        buscar_cadeia_evolucao,
        buscar_natureza,
    ],
    session_manager=session_manager,
    callback_handler=callback_handler,
)

# Passo 2: loop de conversação
print("🎮 Assistente Pokémon pronto! Digite 'sair' para encerrar.\n")

while True:
    try:
        pergunta = input("👩‍💻 Você: ")
    except (EOFError, KeyboardInterrupt):
        print("\nAté a próxima, treinador!")
        break

    if pergunta.strip().lower() in ("sair", "exit", "quit"):
        print("Até a próxima, treinador!")
        break

    print("🤖 Agente: ", end="", flush=True)
    agente(pergunta)
    print()  # linha em branco entre turnos
