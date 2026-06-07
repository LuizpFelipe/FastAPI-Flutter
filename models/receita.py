from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .receita_ingrediente import ReceitaIngrediente

class Receita(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    imagem: Optional[str] = None
    rendimento_padrao: int = Field(default=1)
     
    ingredientes: List["ReceitaIngrediente"] = Relationship(back_populates="receita")