import os
import shutil
from uuid import uuid4
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from core.database import get_session
from models.receita import Receita

router = APIRouter(prefix="/receitas", tags=["Receitas"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_receita(
    nome: str = Form(...),
    rendimento_padrao: int = Form(1),
    file: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session)
):
    """
    Cria uma nova receita no sistema.

    Recebe o nome da receita, seu rendimento padrão e um arquivo de imagem opcional.
    A imagem é processada e salva no servidor com um identificador único.
    """
    nome_arquivo = None
    if file:
        extensao = file.filename.split(".")[-1]
        nome_arquivo = f"{uuid4()}.{extensao}"
        caminho = os.path.join(UPLOAD_DIR, nome_arquivo)
        
        with open(caminho, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    nova_receita = Receita(
        nome=nome, 
        rendimento_padrao=rendimento_padrao,
        imagem=nome_arquivo
    )
    
    session.add(nova_receita)
    session.commit()
    session.refresh(nova_receita)
    return nova_receita

@router.get("/")
def listar_receita(session: Session = Depends(get_session)):
    """
    Lista todas as receitas cadastradas no sistema.
    """
    return session.exec(select(Receita)).all()

@router.patch("/{receita_id}")
async def editar_receita(
    receita_id: int,
    nome: Optional[str] = Form(None),
    rendimento_padrao: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session)
):
    """
    Atualiza os dados de uma receita existente.

    Permite a atualização parcial do nome, rendimento ou a substituição da imagem.
    Se uma nova imagem for enviada, a anterior é removida do servidor.
    """
    receita_db = session.get(Receita, receita_id)
    if not receita_db:
        raise HTTPException(status_code=404, detail="Receita não encontrada")

    if nome:
        receita_db.nome = nome
    if rendimento_padrao is not None:
        receita_db.rendimento_padrao = rendimento_padrao
    
    if file:
        if receita_db.imagem:
            caminho_antigo = os.path.join(UPLOAD_DIR, receita_db.imagem)
            if os.path.exists(caminho_antigo):
                os.remove(caminho_antigo)

        extensao = file.filename.split(".")[-1]
        nome_arquivo = f"{uuid4()}.{extensao}"
        caminho = os.path.join(UPLOAD_DIR, nome_arquivo)
        
        with open(caminho, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        receita_db.imagem = nome_arquivo

    session.add(receita_db)
    session.commit()
    session.refresh(receita_db)
    return receita_db

@router.delete("/{receita_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_receita(receita_id: int, session: Session = Depends(get_session)):
    """
    Remove uma receita do sistema pelo ID.

    Impede a exclusão caso a receita esteja vinculada a uma Ficha Técnica ativa,
    exigindo que o vínculo seja removido previamente para garantir a integridade.
    """
    receita = session.get(Receita, receita_id)
    
    if not receita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Receita não encontrada."
        )
    
    try:
        if receita.imagem:
            caminho_foto = os.path.join(UPLOAD_DIR, receita.imagem)
            if os.path.exists(caminho_foto): 
                os.remove(caminho_foto)

        session.delete(receita)
        session.commit()
        return None
        
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível excluir esta receita porque ela está vinculada a uma Ficha Técnica ativa. Limpe a Ficha Técnica primeiro."
        )