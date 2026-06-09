import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import Session, select
from typing import List, Optional

from core.database import get_session
from models.ingrediente import Ingrediente

router = APIRouter(prefix="/ingredientes", tags=["Ingredientes"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

@router.get("/", response_model=List[Ingrediente])
def listar_ingredientes(session: Session = Depends(get_session)):
    """
    Lista todos os ingredientes cadastrados no sistema.
    
    Retorna:
        List[Ingrediente]: Uma lista de objetos do tipo Ingrediente, 
        contendo o ID, nome e o nome do arquivo de imagem (se houver).
    """
    statement = select(Ingrediente)
    ingredientes = session.exec(statement).all()
    return ingredientes

@router.post("/", response_model=Ingrediente, status_code=status.HTTP_201_CREATED)
def criar_ingrediente(
    nome: str = Form(...),
    file: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session)
):
    """
    Cria um novo ingrediente, com suporte a upload opcional de imagem.
    
    Este endpoint recebe dados via 'FormData' (em vez de JSON puro) para 
    suportar o envio de arquivos. 
    
    Regras para a Imagem:
    - Se um arquivo for enviado, ele recebe um nome único (UUID) para evitar
      sobrescrita de arquivos com o mesmo nome original.
    - O arquivo físico é salvo no diretório configurado em UPLOAD_DIR.
    - Apenas o nome final gerado é armazenado no banco de dados.
    """
    imagem_nome = None
    if file:
        extensao = file.filename.split(".")[-1]
        imagem_nome = f"{uuid.uuid4()}.{extensao}"
        caminho_arquivo = os.path.join(UPLOAD_DIR, imagem_nome)
        
        with open(caminho_arquivo, "wb") as buffer:
            buffer.write(file.file.read())
            
    novo_ingrediente = Ingrediente(nome=nome, imagem=imagem_nome)
    session.add(novo_ingrediente)
    session.commit()
    session.refresh(novo_ingrediente)
    return novo_ingrediente

@router.patch("/{ingrediente_id}", response_model=Ingrediente)
def atualizar_ingrediente(
    ingrediente_id: int, 
    nome: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session)
):
    """
    Atualiza parcialmente um ingrediente existente.
    
    Este endpoint permite alterar apenas o nome, apenas a imagem, ou ambos.
    Por usar o método PATCH e aceitar arquivos, os dados devem ser enviados
    via 'FormData'.
    
    Se um novo arquivo de imagem for enviado, um novo nome (UUID) será gerado
    e substituirá o registro da imagem anterior no banco de dados.
    """
    ingrediente_db = session.get(Ingrediente, ingrediente_id)
    if not ingrediente_db:
        raise HTTPException(status_code=404, detail="Ingrediente não encontrado")
    
    if nome is not None:
        ingrediente_db.nome = nome
        
    if file:
        extensao = file.filename.split(".")[-1]
        imagem_nome = f"{uuid.uuid4()}.{extensao}"
        caminho_arquivo = os.path.join(UPLOAD_DIR, imagem_nome)
        with open(caminho_arquivo, "wb") as buffer:
            buffer.write(file.file.read())
        ingrediente_db.imagem = imagem_nome
        
    session.add(ingrediente_db)
    session.commit()
    session.refresh(ingrediente_db)
    return ingrediente_db

@router.delete("/{ingrediente_id}")
def apagar_ingrediente(ingrediente_id: int, session: Session = Depends(get_session)):
    """
    Remove definitivamente um ingrediente do sistema.
    
    Verifica se o ID existe antes de efetuar a exclusão. 
    Nota: Se o ingrediente estiver vinculado a alguma ficha técnica (ReceitaIngrediente),
    a exclusão poderá falhar caso existam restrições de chave estrangeira (Foreign Key constraints) 
    configuradas no banco de dados.
    """
    ingrediente = session.get(Ingrediente, ingrediente_id)
    if not ingrediente:
        raise HTTPException(status_code=404, detail="Ingrediente não encontrado")
    
    session.delete(ingrediente)
    session.commit()
    return {"mensagem": "Ingrediente removido com sucesso"}