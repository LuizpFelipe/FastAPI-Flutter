from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, exists
from sqlalchemy.orm import joinedload

from core.database import get_session
from models.receita_ingrediente import ReceitaIngrediente
from models.receita import Receita
from models.ingrediente import Ingrediente
from schema.receita_ingrediente import ReceitaIngredienteLote
from schema.producao_schema import PayloadListaCompras

router = APIRouter(prefix="/receita-ingrediente", tags=["Receita Ingrediente"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def criar_relacao(relacao: ReceitaIngrediente, session: Session = Depends(get_session)):
    """
    Cria um vínculo único entre uma receita e um ingrediente.
    
    Valida a existência da receita e do ingrediente antes de persistir a relação.
    """
    receita = session.get(Receita, relacao.receita_id)
    if not receita:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    
    ingrediente = session.get(Ingrediente, relacao.ingrediente_id)
    if not ingrediente:
        raise HTTPException(status_code=404, detail="Ingrediente não encontrado")
    
    session.add(relacao)
    session.commit()
    session.refresh(relacao)
    return relacao

@router.post("/lote", status_code=status.HTTP_201_CREATED)
def criar_relacoes_lote(lote: ReceitaIngredienteLote, session: Session = Depends(get_session)):
    """
    Cria múltiplos vínculos de ingredientes para uma receita em uma única operação.
    
    Processa uma lista de itens e valida cada ingrediente individualmente, 
    garantindo atomicidade (rollback total em caso de erro).
    """
    receita = session.get(Receita, lote.receita_id)
    if not receita:
        raise HTTPException(status_code=404, detail="Receita não encontrada")

    novas_relacoes = []
    try:
        for item in lote.itens:
            ingrediente = session.get(Ingrediente, item.ingrediente_id)
            if not ingrediente:
                session.rollback()
                raise HTTPException(
                    status_code=404, 
                    detail=f"Ingrediente ID {item.ingrediente_id} não encontrado"
                )
            
            nova_relacao = ReceitaIngrediente(
                receita_id=lote.receita_id,
                ingrediente_id=item.ingrediente_id,
                quantidade=item.quantidade,
                unidade=item.unidade
            )
            session.add(nova_relacao)
            novas_relacoes.append(nova_relacao)

        session.commit()
        return {"message": f"{len(novas_relacoes)} itens adicionados com sucesso"}

    except Exception as e:
        session.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Erro ao processar lote: {str(e)}")

@router.delete("/limpar-ficha/{receita_id}")
def excluir_ficha_completa(receita_id: int, session: Session = Depends(get_session)):
    """
    Remove todos os ingredientes associados a uma receita específica.
    """
    statement = select(ReceitaIngrediente).where(ReceitaIngrediente.receita_id == receita_id)
    resultados = session.exec(statement).all()
    
    if not resultados:
        raise HTTPException(status_code=404, detail="Ficha já está vazia ou não existe.")

    for item in resultados:
        session.delete(item)
    
    session.commit()
    return {"message": f"Ficha da receita {receita_id} removida com sucesso"}

@router.get("/receita/{receita_id}")
def listar_ingredientes_da_receita(receita_id: int, session: Session = Depends(get_session)):
    """
    Retorna a lista de ingredientes completa de uma receita, incluindo dados 
    básicos do ingrediente (nome e imagem) através de carregamento otimizado.
    """
    statement = (
        select(ReceitaIngrediente)
        .where(ReceitaIngrediente.receita_id == receita_id)
        .options(joinedload(ReceitaIngrediente.ingrediente))
    )
    resultados = session.exec(statement).all()

    lista_final = []
    for r in resultados:
        item_dict = {
            "id": r.id,
            "receita_id": r.receita_id,
            "ingrediente_id": r.ingrediente_id,
            "quantidade": r.quantidade,
            "unidade": r.unidade,
            "ingrediente": None
        }
        if r.ingrediente:
            item_dict["ingrediente"] = {
                "id": r.ingrediente.id,
                "nome": r.ingrediente.nome,
                "imagem": getattr(r.ingrediente, 'imagem', None)
            }
        lista_final.append(item_dict)

    return lista_final

@router.get("/com-ficha")
def listar_receitas_com_ficha(session: Session = Depends(get_session)):
    """
    Retorna uma lista de todas as receitas que possuem pelo menos um 
    ingrediente cadastrado na ficha técnica.
    """
    statement = select(Receita).where(
        exists().where(ReceitaIngrediente.receita_id == Receita.id)
    )
    return session.exec(statement).all()

@router.patch("/{id}")
def editar_vinculo(id: int, quantidade: float, unidade: str, session: Session = Depends(get_session)):
    """
    Atualiza a quantidade e a unidade de um vínculo existente.
    """
    db_item = session.get(ReceitaIngrediente, id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Vínculo não encontrado")
    
    db_item.quantidade = quantidade
    db_item.unidade = unidade
    
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

@router.delete("/{id}", status_code=status.HTTP_200_OK)
def excluir_item_individual(id: int, session: Session = Depends(get_session)):
    """
    Remove um ingrediente específico da ficha técnica de uma receita.
    """
    db_item = session.get(ReceitaIngrediente, id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item não encontrado na ficha")
    
    session.delete(db_item)
    session.commit()
    return {"message": "Item removido com sucesso"}

def converter_para_base(valor: float, unidade_receita: str):
    u = unidade_receita.strip().lower()
    if u in ["kg", "quilograma"]: return valor * 1000, "g"
    if u in ["l", "litro"]: return valor * 1000, "ml"
    return valor, u

def converter_para_exibicao(valor_base: float, unidade_base: str):
    u = unidade_base.strip().lower()
    if valor_base >= 1000:
        if u == "g": return valor_base / 1000, "kg"
        if u == "ml": return valor_base / 1000, "L"
    return valor_base, u

@router.post("/lista-compras")
def gerar_lista_compras(payload: PayloadListaCompras, session: Session = Depends(get_session)):
    """
    Calcula a lista consolidada de ingredientes para um lote de produção.
    
    1. Identifica todas as receitas e quantidades desejadas pelo usuário.
    2. Calcula a escala necessária com base no rendimento de cada receita.
    3. Agrupa ingredientes idênticos por unidade de medida.
    4. Converte unidades para o formato de exibição otimizado (ex: g para kg).
    """
    ids_receitas = [item.receita_id for item in payload.itens]
    quantidades_desejadas = {item.receita_id: item.quantidade_produzir for item in payload.itens}

    statement = (
        select(ReceitaIngrediente)
        .where(ReceitaIngrediente.receita_id.in_(ids_receitas))
        .options(
            joinedload(ReceitaIngrediente.ingrediente),
            joinedload(ReceitaIngrediente.receita)
        )
    )
    resultados = session.exec(statement).all()
    
    lista_agrupada = {}
    
    for r in resultados:
        if not r.ingrediente: continue
            
        ing_id = r.ingrediente_id
        qtd_desejada = quantidades_desejadas.get(r.receita_id, 1.0)
        
        rendimento = getattr(r.receita, 'rendimento_padrao', 1)
        if rendimento <= 0: rendimento = 1
        
        fator_escala = qtd_desejada / rendimento
        qtd_necessaria = r.quantidade * fator_escala
        
        qtd_base, unidade_base = converter_para_base(qtd_necessaria, r.unidade)
        chave = (ing_id, unidade_base)
        
        if chave not in lista_agrupada:
            lista_agrupada[chave] = {
                "nome": r.ingrediente.nome,
                "quantidade_base": qtd_base,
                "unidade_base": unidade_base
            }
        else:
            lista_agrupada[chave]["quantidade_base"] += qtd_base

    lista_final = []
    for dados in lista_agrupada.values():
        qtd_exibicao, unidade_exibicao = converter_para_exibicao(
            dados["quantidade_base"], dados["unidade_base"]
        )

        qtd_formatada = round(qtd_exibicao, 2)
        if qtd_formatada.is_integer():
            qtd_formatada = int(qtd_formatada)

        lista_final.append({
            "nome": dados["nome"],
            "quantidade": qtd_formatada,
            "unidade": unidade_exibicao
        })
        
    return lista_final