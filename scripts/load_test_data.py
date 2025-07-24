#!/usr/bin/env python3
"""
Script simples para carregar transaçoes de teste
Insere transaçoes em uma conta específica
"""

import httpx
import random
from datetime import date, timedelta
import time

# Configuraçoes da API
API_BASE_URL = "http://localhost:8000/api/v1"
TOTAL_TRANSACTIONS = 1000

# Tipos de transaçoes
TRANSACTION_TYPES = ["credit", "debit"]

CREDIT_DESCRIPTIONS = [
    "Depósito salario",
    "Transferência recebida",
    "Rendimento investimento",
    "Pagamento freelance",
    "Reembolso recebido",
]

DEBIT_DESCRIPTIONS = [
    "Saque ATM",
    "Compra online",
    "Supermercado",
    "Posto de gasolina",
    "Pagamento conta",
    "Aluguel",
]


def generate_random_date():
    """Gera data aleatória no último ano"""
    start_date = date.today() - timedelta(days=365)
    end_date = date.today()
    days_diff = (end_date - start_date).days
    random_days = random.randint(0, days_diff)
    return start_date + timedelta(days=random_days)


def generate_transaction(account_id):
    """Gera dados de uma transaçao aleatória"""
    transaction_type = random.choice(TRANSACTION_TYPES)

    if transaction_type == "credit":
        amount = round(random.uniform(100.00, 3000.00), 2)
        description = random.choice(CREDIT_DESCRIPTIONS)
    else:
        amount = round(random.uniform(20.00, 1500.00), 2)
        description = random.choice(DEBIT_DESCRIPTIONS)

    return {
        "account_id": account_id,
        "amount": str(amount),
        "transaction_type": transaction_type,
        "description": description,
        "transaction_date": generate_random_date().isoformat(),
        "reference_id": f"REF-{random.randint(100000, 999999)}",
    }


def create_transaction(client, transaction_data):
    """Cria uma transaçao via API"""
    try:
        response = client.post(f"{API_BASE_URL}/transactions/", json=transaction_data)
        return response.status_code == 201
    except Exception:
        return False


def load_transactions(account_id, total):
    """Carrega todas as transaçoes"""
    print(f"\n=== CARREGANDO {total} TRANSAÇOES NA CONTA {account_id} ===")

    success_count = 0
    error_count = 0
    start_time = time.time()

    with httpx.Client(timeout=30.0) as client:
        for i in range(total):
            transaction_data = generate_transaction(account_id)

            if create_transaction(client, transaction_data):
                success_count += 1
            else:
                error_count += 1

            # Mostrar progresso a cada 100 transaçoes
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = success_count / elapsed if elapsed > 0 else 0
                print(
                    f"Progresso: {i + 1}/{total} | Sucesso: {success_count} | Taxa: {rate:.0f} trans/seg"
                )

    total_time = time.time() - start_time

    print(f"\n=== RESULTADO ===")
    print(f"Tempo total: {total_time:.1f} segundos")
    print(f"Transaçoes criadas: {success_count}")
    print(f"Erros: {error_count}")
    if total_time > 0:
        print(f"Taxa média: {success_count / total_time:.0f} transaçoes/segundo")


def main():
    """Funçao principal"""
    print("=== CARREGADOR SIMPLES DE TRANSAÇOES ===")

    # Verificar se API esta acessível
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE_URL}/accounts/")
            if response.status_code != 200:
                print(
                    "API nao esta acessível. Verifique se esta rodando em http://localhost:8000"
                )
                return
    except Exception:
        print("Erro conectando com a API. Verifique se esta rodando.")
        return

    print("API esta acessivel")

    # Pedir ID da conta
    try:
        account_id = int(input("\nDigite o ID da conta: "))
    except ValueError:
        print("ID invalido!")
        return

    # Pedir quantidade de transaçoes
    try:
        total = int(
            input(f"Quantas transaçoes inserir? (padrao: {TOTAL_TRANSACTIONS}): ")
            or TOTAL_TRANSACTIONS
        )
    except ValueError:
        total = TOTAL_TRANSACTIONS

    # Confirmar execuçao
    print(f"\nVai inserir {total} transaçoes na conta ID {account_id}")
    confirm = input("Continuar? (s/N): ").lower()

    if confirm in ["s", "sim", "y", "yes"]:
        load_transactions(account_id, total)
    else:
        print("Operaçao cancelada.")


if __name__ == "__main__":
    main()
