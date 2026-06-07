from pydantic import BaseModel
from typing import List

class ItemProducao(BaseModel):
    receita_id: int
    quantidade_produzir: float

class PayloadListaCompras(BaseModel):
    itens: List[ItemProducao]