# Testes

Sistema de testes para a API de Transações Financeiras com arquitetura hexagonal.

## Estrutura

```
tests/
├── conftest.py           # Fixtures compartilhadas
├── unit/                 # Testes unitários isolados
│   ├── test_money.py
│   ├── test_account.py
│   ├── test_transaction.py
│   ├── test_balance_calculator.py
│   ├── test_create_transaction_use_case.py
│   └── test_get_balance_use_case.py
└── integration/         # Testes com dependências reais
    ├── test_account_repository.py
    └── test_api_endpoints.py
```

## Executar Testes

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

## Cobertura

- **Meta**: >90% de cobertura
- **Relatório HTML**: `htmlcov/index.html`
- **Foco**: Lógica de negócio (domain e application)

## Fixtures Principais

- `db_session`: Sessão isolada de banco (SQLite in-memory)
- `test_account`: Conta ativa para testes
- `sample_transactions`: Transações de exemplo
- `mock_cache_service`: Cache simulado

## Estratégia

- **Unit**: Mocks para dependências externas
- **Integration**: SQLite in-memory + TestClient
- **Isolamento**: Rollback automático entre testes 