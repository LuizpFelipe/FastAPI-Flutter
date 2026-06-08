# Sistema de Gestão de Produção - Backend (FastAPI)

Este repositório contém a API RESTful desenvolvida em FastAPI que serve como motor de dados para o Sistema de Gestão de Produção. O backend é responsável pela persistência de dados, regras de negócio para cálculo de insumos, validação de integridade e integração com serviços de Inteligência Artificial para padronização de dados.

## Visão Geral

A aplicação foi construída utilizando Python com o framework FastAPI, priorizando alta performance, validação de tipos e documentação automática. O sistema utiliza um modelo relacional robusto para gerenciar a complexidade das fichas técnicas e escalas de produção.

## Arquitetura e Tecnologias

* Framework: FastAPI (performance assíncrona e documentação OpenAPI).
* ORM/Modelagem: SQLModel (integração entre SQLAlchemy e Pydantic).
* Banco de Dados: PostgreSQL.
* Inteligência Artificial: Integração com Groq API (LLM Llama-3) para normalização semântica de dados.
* Validação: Pydantic para schemas de entrada e saída.

## Estrutura do Projeto

* /core: Configurações de banco de dados e dependências compartilhadas.
* /models: Definições das entidades do banco de dados (SQLModel).
* /routers: Endpoints da API divididos por domínio (Receitas, Ingredientes, Ficha Técnica, Produção).
* /schema: Definição dos contratos de dados (Schemas Pydantic) para serialização.
* /uploads: Diretório local para armazenamento de arquivos e imagens.

## Funcionalidades Principais

* Gestão de Recursos: CRUD completo para Receitas e Ingredientes.
* Lógica Relacional: Gestão de fichas técnicas (vínculo entre receita e ingrediente) com atomicidade e tratamento de integridade.
* Inteligência Artificial: Endpoint dedicado para normalização de nomes, eliminando duplicidades e corrigindo erros de digitação.
* Cálculo de Produção: Motor matemático que calcula escalas de produção baseadas no rendimento padrão, realizando conversões automáticas de unidades (g para kg, ml para L).

## Configuração e Instalação

1. Clone o repositório:
git clone [https://github.com/LuizpFelipe/FastAPI-Flutter.git]
2. Crie e ative um ambiente virtual:
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
3. Instale as dependências:
pip install -r requirements.txt
4. Configure o arquivo `.env` com suas variáveis:
DATABASE_URL=postgresql://usuario:senha@localhost:5432/db_producao
GROQ_API_KEY=sua_chave_aqui
5. Execute a aplicação:
uvicorn main:app --reload

## Documentação da API

O sistema gera automaticamente a documentação via Swagger UI. Após rodar a aplicação, acesse:

http://localhost:8000/docs

## Padrões de Desenvolvimento

* Clean Architecture: Separação clara entre modelos de dados, roteadores e serviços de negócio.
* Tratamento de Erros: Implementação de exceções personalizadas para garantir que o cliente (Flutter) receba feedbacks claros e consistentes.
* Integridade Referencial: Bloqueio de exclusões em dados vinculados para garantir a consistência das fichas de produção.

---

Este documento serve como referência técnica para o desenvolvimento, manutenção e integração da API do Sistema de Gestão de Produção.