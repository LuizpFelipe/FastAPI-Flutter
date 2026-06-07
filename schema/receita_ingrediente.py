from pydantic import BaseModel
from typing import List

class IngredienteLote(BaseModel):
    ingrediente_id: int
    quantidade: float
    unidade: str

class ReceitaIngredienteLote(BaseModel):
    receita_id: int
    itens: List[IngredienteLote]