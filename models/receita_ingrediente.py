from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .ingrediente import Ingrediente
    from .receita import Receita

class ReceitaIngrediente(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    receita_id: int = Field(foreign_key="receita.id")
    ingrediente_id: int = Field(foreign_key="ingrediente.id")
    quantidade: float
    unidade: str
    
    ingrediente: Optional["Ingrediente"] = Relationship(back_populates="receitas")
    receita: Optional["Receita"] = Relationship(back_populates="ingredientes")