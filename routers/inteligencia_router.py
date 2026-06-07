from fastapi import APIRouter
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    client = None
else:
    client = Groq(api_key=api_key)

@router.get("/normalizar-nome")
def normalizar_nome(termo: str):
    """
    Normaliza nomes de ingredientes ou receitas através de IA generativa.
    
    Este endpoint atua como uma camada de sanitização de dados:
    1. Recebe um termo bruto (ex: 'farina de trgo').
    2. Aplica uma limpeza básica (trim/capitalize).
    3. Aciona o modelo Llama-3.1 via Groq com um system prompt especializado 
       em terminologia culinária e correção ortográfica.
    4. Garante uma resposta determinística (temperature=0.1) e minimalista.
    
    Args:
        termo (str): O nome do ingrediente ou receita a ser normalizado.
        
    Returns:
        dict: Um dicionário contendo a 'sugestao' de nome corrigido. 
        Em caso de erro na API ou configuração, retorna o próprio termo original.
    """
    if not client:
        return {"erro": "Cliente Groq não configurado"}
        
    termo_limpo = termo.strip().capitalize()
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "Você é um corretor ortográfico especialista em culinária. "
                        "Sua única função é corrigir erros de digitação e padronizar nomes de ingredientes e receitas. "
                        "Exemplos de correção:\n"
                        "- 'noz mocada' -> 'Noz moscada'\n"
                        "- 'maca' -> 'Maçã'\n"
                        "- 'farinha de trgo' -> 'Farinha de trigo'\n"
                        "REGRA ABSOLUTA: Retorne APENAS o nome corrigido. Não escreva frases, não justifique, "
                        "não use pontuação final e não seja educado. Apenas devolva a palavra. "
                        "Se a palavra já estiver correta, devolva exatamente a mesma palavra."
                    )
                },
                {"role": "user", "content": termo_limpo}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=15,
        )
        
        sugestao = chat_completion.choices[0].message.content.strip()
        
        return {"sugestao": sugestao}
    
    except Exception as e:
        return {"sugestao": termo_limpo}