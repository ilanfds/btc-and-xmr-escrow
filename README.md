# CriptoEscrow

Plataforma de **escrow off-chain** para **Bitcoin (BTC)** e **Monero (XMR)**.  
O objetivo é permitir transações seguras entre comprador e vendedor, com fundos retidos até a confirmação de entrega ou resolução de disputa.

## Visão Geral

- **Ativos suportados**: Bitcoin (signet/testnet) e Monero (stagenet).
- **Taxa da plataforma**: 3% sobre o preço (`P`).
- **Modelo de taxas**: o **comprador paga todas as taxas de rede** (depósito e payout).
- **Fluxo sem reembolso**: qualquer diferença entre taxa estimada e real é absorvida no miner fee.
- **Segurança**: apenas o **worker** mantém chaves privadas e assina transações.
- **Estados do Escrow**:  
  `CREATED → FUNDED → RELEASED | DISPUTED → RESOLVED → CLOSED`

## Tecnologias

- **Backend**: FastAPI (Python)  
- **Banco de Dados**: PostgreSQL (via SQLAlchemy + Alembic)  
- **Fila/Cache**: Redis  
- **Infraestrutura**: Docker Compose (containers para API, worker, BTC node, XMR daemon/wallet)  

## Componentes Principais

- **API**: criação e gerenciamento de escrows, endpoints REST (idempotentes).  
- **Worker**: assina e transmite transações (BTC/XMR).  
- **Adapters**: integração com `bitcoin-core` e `monero-wallet-rpc`.  
- **Watchers**: monitoram depósitos e confirmam estados via webhooks.  
- **Ledger interno**: modelo de contabilidade de dupla entrada para rastrear todos os movimentos.  

## Funcionalidades Planejadas (MVP)

- Criar escrow com preço definido e endereço/subaddress exclusivo para depósito.  
- Observar depósitos até atingir confirmações mínimas (BTC=3, XMR=10).  
- Marcar entrega (vendedor) e liberar fundos (comprador).  
- Abrir e resolver disputas com divisão arbitrada.  
- Auto-liberação após prazo (se não houver disputa).  
- Logs e auditoria completos, com idempotência em todas as operações críticas.  

## Status
## Como rodar (dev)
🚧 **Em desenvolvimento**  


