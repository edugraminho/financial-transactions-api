# Financial Transactions API

API para controle de lançamentos financeiros em contas correntes, desenvolvida com **FastAPI** e **PostgreSQL**, implementando **Arquitetura Hexagonal** e estratégias de **cache** para alta performance.

## 🎯 Sobre o Projeto

Sistema para gerenciamento de transações financeiras que permite:

- **Registrar transações** de entrada (crédito) e saída (débito)
- **Consultar saldo** da conta em data específica com cache inteligente
- **Listar transações** com paginação e filtros por data
- **Performance ultra-otimizada** para milhões de transações através de cache multi-layer, snapshots automáticos e agregações SQL

## 🏗️ Arquitetura

### Arquitetura Hexagonal (Clean Architecture)

```
📁 app/
├── 🟢 domain/          # Regras de Negócio
│   ├── entities/       # Account, Transaction, BalanceSnapshot
│   ├── value_objects/  # Money (Decimal precision)
│   ├── repositories/   # Interfaces (abstrações)
│   └── services/       # BalanceCalculator
├── 🟡 application/     # Casos de Uso
│   ├── use_cases/      # CreateTransaction, GetBalance, ListTransactions
│   └── services/       # CacheService, SnapshotService
├── 🔵 infrastructure/ # Implementações
│   ├── repositories/   # SQLAlchemy (PostgreSQL)
│   └── services/       # Redis cache
├── 🔗 api/            # Interface Externa
│   ├── routes/         # FastAPI endpoints
│   └── schemas/        # Pydantic DTOs
└── ⚙️ core/           # Configurações e dependências
```

### Stack Tecnológica

- **FastAPI** - Framework web moderno e rápido
- **PostgreSQL** - Banco de dados robusto para dados financeiros  
- **Redis** - Cache inteligente com TTL automático
- **SQLAlchemy** - ORM com queries otimizadas e connection pooling
- **Pydantic** - Validação de dados com type hints
- **Docker** - Containerização para facilitar deployment

## 🚀 Como Executar

### Pré-requisitos

- **Docker** e **Docker Compose** instalados

### 1. Clone o Repositório

```bash
git clone <repository-url>
cd financial-transactions-api
```

### 2. Configure as Variáveis de Ambiente

Crie um arquivo `.env` com as seguintes variáveis:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/financial_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=financial_db

# Cache
REDIS_URL=redis://redis:6379/0

# Application
ENVIRONMENT=development
```

### 3. Execute com Docker Compose

```bash
# Iniciar todos os serviços
docker compose up --build

# Ou em background
docker compose up --build -d
```

### 4. Verifique se está funcionando

```bash
# Health check
curl http://localhost:8000/health

# Documentação interativa (Swagger)
# Abra no navegador: http://localhost:8000/docs
```

## 📊 Carregar Dados de Teste

Para testar a performance do sistema com grandes volumes de transações, use o script `load_test_data.py`:

### Como usar

```bash
# 1. Execute o script dentro do container da API
docker exec -it financial-transactions-api-api-1 python scripts/load_test_data.py

# 2. Siga as instruções do script:
# - Digite o ID da conta (ex: 1)
# - Digite a quantidade de transações (ex: 1000)
# - Confirme a operação
```

### Para que serve

O script gera transações aleatórias com:
- **Tipos**: Crédito (depósitos, transferências) e Débito (saques, compras)
- **Valores**: Aleatórios entre R$ 20,00 e R$ 3.000,00
- **Datas**: Distribuídas ao longo do último ano
- **Descrições**: Realistas (supermercado, salário, etc.)

**Ideal para**:
- Testar performance com muitas transações (100, 1K, 10K+)
- Demonstrar funcionamento dos snapshots automáticos
- Verificar otimizações de cache e índices


## 🧪 Executar Testes

### Via Docker (Recomendado)
```bash
# Todos os testes
./scripts/run_tests_docker.sh all

# Apenas unitários
./scripts/run_tests_docker.sh unit

# Apenas integração
./scripts/run_tests_docker.sh integration

# Com cobertura
./scripts/run_tests_docker.sh coverage
```

### Via Python Local
```bash
# Instalar dependências
pip install pytest pytest-cov

# Executar testes
python scripts/run_tests.py --coverage
python scripts/run_tests.py --unit
python scripts/run_tests.py --integration
```


## ⚡ Estratégias de Performance

### Sistema de Performance Multi-Layer

O sistema implementa **3 camadas de otimização** para consultas ultra-rápidas:

#### **1. Cache Hierárquico**

```
🚀 Layer 1: Redis Cache (~2ms)
├── TTL: 1h (data atual) | 24h (histórico)
└── Invalidação automática

🔄 Layer 2: Balance Snapshots (~5-15ms)
├── Automático para contas com 100+ transações
└── Cálculo incremental

⚡ Layer 3: SQL Otimizado (~10-50ms)
├── Agregações nativas PostgreSQL
└── Índices compostos
```

#### **2. Índices de Performance**

```sql
-- Transações
CREATE INDEX idx_account_date ON transactions(account_id, transaction_date);
CREATE INDEX idx_date ON transactions(transaction_date);

-- Balance Snapshots
CREATE INDEX idx_snapshot_account_date ON balance_snapshots(account_id, snapshot_date);
```

#### **3. Balance Snapshots Automáticos**

- Sistema detecta contas com muitas transações (>100)
- Cria snapshots automáticos em pontos estratégicos
- Consultas futuras calculam apenas o delta
- **Performance**: até 150x mais rápido para histórico

### Benchmarks de Performance

- **Consulta de saldo**: < 50ms (com cache)
- **Criação de transação**: < 100ms
- **Listagem paginada**: < 150ms
- **Throughput**: 1000+ req/s

### Performance Response Indicators

O sistema indica a fonte dos dados para monitoramento:

```json
{
  "balance": {"amount": "5000.00", "currency": "BRL"},
  "source": "cache",           // Redis (ultra-rápido)
  "source": "snapshot",        // Snapshot + delta (rápido)  
  "source": "calculated+snapshot_created", // Criou snapshot
  "source": "calculated"       // Cálculo completo
}
```

## 🚀 Exemplos de Uso

### Criar Conta

```bash
curl -X POST "http://localhost:8000/api/v1/accounts" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "ACC-001",
    "account_name": "Conta Principal"
  }'
```

### Registrar Transação

```bash
curl -X POST "http://localhost:8000/api/v1/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "amount": "250.00",
    "transaction_type": "debit", 
    "description": "Pagamento de fornecedor",
    "transaction_date": "2024-01-16",
    "reference_id": "PAG-001"
  }'
```

### Consultar Saldo

```bash
# Saldo atual
curl "http://localhost:8000/api/v1/accounts/1/balance"

# Saldo em data específica
curl "http://localhost:8000/api/v1/accounts/1/balance?target_date=2024-01-15"
```

### Listar Transações

```bash
# Todas as transações da conta
curl "http://localhost:8000/api/v1/transactions?account_id=1"

# Com paginação e filtros
curl "http://localhost:8000/api/v1/transactions?account_id=1&page=1&limit=10&start_date=2024-01-01"
```

## 🔒 Características de Segurança

- **Precisão monetária**: Uso de `Decimal` para valores exatos
- **Validações rigorosas**: Pydantic + regras de domínio
- **Transações imutáveis**: Apenas inserção, sem edição/exclusão
- **Error handling**: Fallbacks graceful em todas as camadas

## 🛠️ Desenvolvimento

### Qualidade de Código

- **Ruff**: Linting e formatação
- **Type hints**: Tipagem completa
- **Arquitetura Hexagonal**: Separação clara de responsabilidades
- **Dependency Injection**: Facilita testes e manutenção

### Estrutura de Testes

```
tests/
├── conftest.py           # Fixtures compartilhadas
├── unit/                 # Testes unitários isolados
│   ├── test_money.py
│   ├── test_account.py
│   ├── test_transaction.py
│   ├── test_balance_calculator.py
│   └── test_*_use_case.py
└── integration/         # Testes com dependências reais
    ├── test_account_repository.py
    └── test_api_endpoints.py
```

**Cobertura**: >85% focada em lógica de negócio  
**Fixtures**: Banco SQLite in-memory + mocks para serviços  
**Estratégia**: Unit (mocks) + Integration (TestClient)

---

**Desenvolvido com foco em performance, escalabilidade e manutenibilidade**

**Autor:** Eduardo F Graminho  
[@https://www.linkedin.com/in/edugraminho/](https://www.linkedin.com/in/edugraminho/)




