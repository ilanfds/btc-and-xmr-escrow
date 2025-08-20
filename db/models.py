from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import JSON, BigInteger, Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, Text, UniqueConstraint, String
from domain.types import *

from sqlalchemy.sql import expression

class Base(DeclarativeBase):
    pass

#Tabelas
class Escrow(Base):
    __tablename__ = "escrows"

    id:Mapped[int]=mapped_column(primary_key= True, autoincrement= True)
    asset: Mapped[Asset]=mapped_column(Enum(Asset,name="asset"),nullable=False)
    price:Mapped[int]=mapped_column(BigInteger,nullable=False) #P
    platform_fee:Mapped[int] = mapped_column(BigInteger,nullable=False)
    fn_est:Mapped[int] = mapped_column(BigInteger,nullable=False)
    buffer:Mapped[int] = mapped_column(BigInteger,nullable=False)
    deposit_total:Mapped[int] = mapped_column(BigInteger,nullable=False) # D = P + fee + fn_est + buffer
    seller_payout_address:Mapped[str]=mapped_column(Text,nullable=False)
    buyer_payout_address:Mapped[str|None]=mapped_column(Text)
    payout_speed_profile:Mapped[SpeedProfile|None] = mapped_column(Enum(SpeedProfile,name="speed_profile"))
    state:Mapped[EscrowState] = mapped_column(Enum(EscrowState, name="escrow_state"), nullable=False, default=EscrowState.CREATED)
    delivered_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    dispute_deadline:Mapped[datetime | None] = mapped_column(DateTime(timezone=True)) # delivered_at + 72h
    auto_release_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # delivered_at + 7d
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    destinations = relationship("EscrowDestination", back_populates="escrow")
    deposits = relationship("Deposit", back_populates="escrow")
    payouts = relationship("Payout", back_populates="escrow")
    disputes = relationship("Dispute", back_populates="escrow")

    __table_args__ = (
        Index("ix_escrows_state", "state"),
        Index("ix_escrows_asset_state", "asset", "state"),
        Index("ix_escrows_auto_release_at", "auto_release_at"),

        # Checks de sanidade (núcleo mínimo)
        CheckConstraint("price >= 0", name="ck_escrows_price_nonneg"),
        CheckConstraint("platform_fee >= 0", name="ck_escrows_platform_fee_nonneg"),
        CheckConstraint("fn_est >= 0", name="ck_escrows_fn_est_nonneg"),
        CheckConstraint("buffer >= 0", name="ck_escrows_buffer_nonneg"),
        CheckConstraint("deposit_total >= 0", name="ck_escrows_deposit_total_nonneg"),

        # Se você não usa coluna computada, garanta a fórmula:
        CheckConstraint(
            "deposit_total >= price + platform_fee + fn_est + buffer",
            name="ck_escrows_deposit_total_formula"
        ),
    )
    
class EscrowDestination(Base):
    __tablename__="escrow_destinations"

    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    escrow_id:Mapped[int]=mapped_column(ForeignKey("escrows.id",ondelete="CASCADE"),nullable=False)
    asset: Mapped[Asset]=mapped_column(Enum(Asset,name="asset"),nullable=False)
    destination:Mapped[str]=mapped_column(Text,nullable=False)#aonde o comprador tem q pagar
    meta: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict) #meta	jsonb	BTC: derivation path; XMR: account_index/subaddr_index
    active:Mapped[bool]=mapped_column(default=True,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    escrow = relationship("Escrow", back_populates="destinations")

    #Como eh gerada uma carteira pra cada pagamento, nao permite dois enderecos iguais
    __table_args__=(
        UniqueConstraint("destination", name="uq_escrow_destinations_destination"),
        Index("ix_escrow_destinations_destination", "destination"),
        Index(  # 1 ativo por escrow (opcional, recomendado)
            "uq_escrow_destination_active",
            "escrow_id",
            unique=True,
            postgresql_where=expression.text("active IS TRUE")
        ),
        )


class Deposit(Base):
    __tablename__ = "deposits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    escrow_id: Mapped[int] = mapped_column(ForeignKey("escrows.id", ondelete="CASCADE"), nullable=False)
    asset: Mapped[Asset] = mapped_column(Enum(Asset,name="asset"),nullable=False)
    txid: Mapped[str] = mapped_column(Text,nullable=False) #nao tenho crtz se esse nullable eh false
    vout:Mapped[int|None]=mapped_column(Integer) #btc usa, xmr pode usar
    destination: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False) #valor depositado
    confirmations_current: Mapped[int] = mapped_column(Integer,default=0,nullable=False)
    confirmed_height: Mapped[int|None] = mapped_column(Integer)
    status: Mapped[DepositStatus] = mapped_column(Enum(DepositStatus, name="deposit_status"), default=DepositStatus.PENDING, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    escrow = relationship("Escrow", back_populates="deposits")

    __table_args__ = (
        UniqueConstraint("txid", "vout", name="uq_deposits_txid_vout"),
        Index("ix_deposits_escrow_id", "escrow_id"),
        Index("ix_deposits_destination", "destination"),
        Index("ix_deposits_status", "status"),
        CheckConstraint("amount >= 0", name="ck_deposits_amount_nonneg"),
        CheckConstraint("confirmations_current >= 0", name="ck_deposits_confs_nonneg"),
        )

class Payout(Base):
    __tablename__= "payouts"

    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
    escrow_id:Mapped[int]=mapped_column(ForeignKey("escrows.id",ondelete="CASCADE"),nullable=False)
    asset:Mapped[Asset]=mapped_column(Enum(Asset,name="asset"),nullable=False)
    kind:Mapped[PayoutKind]=mapped_column(Enum(PayoutKind,name="payout_kind"),nullable=False)
    txid:Mapped[str|None]=mapped_column(Text)
    status: Mapped[PayoutStatus] = mapped_column(Enum(PayoutStatus, name="payout_status"), default=PayoutStatus.BROADCAST,nullable=False)
    feerate_profile: Mapped[SpeedProfile | None] = mapped_column(Enum(SpeedProfile, name="feerate_profile"))
    vbytes_est: Mapped[int | None]
    fn_est_at_send: Mapped[int | None]
    fn_real: Mapped[int | None]
    broadcast_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


    escrow = relationship("Escrow", back_populates="payouts")
    outputs = relationship("PayoutOutput", back_populates="payout")

    __table_args__ = (
        Index("ix_payouts_escrow_id", "escrow_id"),
        Index("ix_payouts_status", "status"),
        Index("ix_payouts_txid", "txid"),
              # Postgres: apenas 1 payout BROADCAST “vivo” por escrow
        Index(
            "uq_one_broadcast_payout_per_escrow",
            "escrow_id",
            unique=True,
            postgresql_where=(expression.text("status = 'BROADCAST'"))
        ),
        UniqueConstraint("txid", name="uq_payouts_txid"),
        # Checks básicos de não-negatividade quando presentes
        CheckConstraint("(fn_est_at_send IS NULL) OR (fn_est_at_send >= 0)", name="ck_payouts_fn_est_nonneg"),
        CheckConstraint("(fn_real IS NULL) OR (fn_real >= 0)", name="ck_payouts_fn_real_nonneg"),
        CheckConstraint("(vbytes_est IS NULL) OR (vbytes_est >= 0)", name="ck_payouts_vbytes_nonneg"),
    )


class PayoutOutput(Base):
    __tablename__ = "payout_outputs"

    id: Mapped[int] = mapped_column(primary_key=True)
    payout_id: Mapped[int] = mapped_column(ForeignKey("payouts.id"),nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role, name="role"), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)

    payout = relationship("Payout", back_populates="outputs")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payout_outputs_amount_nonneg"),
    )


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[int] = mapped_column(primary_key=True)
    escrow_id: Mapped[int] = mapped_column(ForeignKey("escrows.id"))
    opened_by: Mapped[Role] = mapped_column(Enum(Role, name="opened_by"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[DisputeStatus] = mapped_column(Enum(DisputeStatus, name="dispute_status"), default=DisputeStatus.OPEN)
    to_seller: Mapped[int | None]
    to_buyer: Mapped[int | None]
    resolved_by: Mapped[str | None]
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime | None]
    price_at_open: Mapped[int] = mapped_column(BigInteger, nullable=False)  # <- NOVO
    escrow = relationship("Escrow", back_populates="disputes")

    __table_args__ = (
        # Somente 1 disputa OPEN por escrow (índice parcial)
        Index(
            "uq_one_open_dispute_per_escrow",
            "escrow_id",
            unique=True,
            postgresql_where=(expression.text("status = 'OPEN'"))
        ),
        # Checks de não-negatividade
        CheckConstraint("(to_seller IS NULL) OR (to_seller >= 0)", name="ck_disputes_to_seller_nonneg"),
        CheckConstraint("(to_buyer IS NULL) OR (to_buyer >= 0)", name="ck_disputes_to_buyer_nonneg"),
        CheckConstraint("price_at_open >= 0", name="ck_disputes_price_at_open_nonneg"),
    )


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(Text, nullable=False)
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    request_hash: Mapped[str] = mapped_column(Text, nullable=False)
    response_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),nullable=False)
    expires_at: Mapped[datetime | None]

    __table_args__ = (
        UniqueConstraint("key", "endpoint", name="uq_idempotency"),
    )


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(Text, nullable=False)  # BTC ou XMR
    kind: Mapped[str] = mapped_column(Text, nullable=False)      # DEPOSIT
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False,nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("idempotency_key", "kind", name="uq_webhook"),
    )

class LedgerAccount(Base):
    __tablename__ = "ledger_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset: Mapped[Asset] = mapped_column(Enum(Asset, name="asset"), nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)  # ESCROW, SELLER, BUYER, PLATFORM
    ref_id: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),nullable=False)

    __table_args__ = (
        UniqueConstraint("asset", "kind", "ref_id", name="uq_ledger_accounts"),
    )


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    journal_id: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), nullable=False)
    asset: Mapped[Asset] = mapped_column(Enum(Asset, name="asset"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("ledger_accounts.id"),nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # positivo=crédito, negativo=débito
    memo: Mapped[str | None] = mapped_column(Text)
    ref_type: Mapped[str] = mapped_column(Text)
    ref_id: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),nullable=False)

    __table_args__ = (
        Index("ix_ledger_entries_account_id", "account_id"),
        Index("ix_ledger_entries_journal_id", "journal_id"),
        Index("ix_ledger_entries_asset", "asset"),
        CheckConstraint("amount <> 0", name="ck_ledger_entries_amount_nonzero"),
    )
    