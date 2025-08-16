from datetime import datetime, timezone
from this import d
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import JSON, BigInteger, DateTime, Enum, ForeignKey, Integer, Text, UniqueConstraint, null
import enum

from sqlalchemy.sql import ddl
class Base(DeclarativeBase):
    pass

class Asset(str, enum.Enum): #Enum de strings
    BTC="BTC"
    XMR="XMR"

class EscrowState(str, enum.Enum):
    CREATED="CREATED"
    FUNDED="FUNDED"
    RELEASED="RELEASED"
    DISPUTED="DISPUTED"
    RESOLVED="RESOLVED"
    CLOSED="CLOSED"


class SpeedProfile(str, enum.Enum):
    fast = "fast"
    normal = "normal"
    slow = "slow"

class DepositStatus(str, enum.Enum):
    NORMAL="NORMAL"
    DISPUTE="DISPUTE"

#Tabelas
class Escrow(Base):
    __tablename__ = "escrow"

    id:Mapped[int]=mapped_column(primary_key= True, autoincrement= True)
    asset: Mapped[Asset]=mapped_column(Enum(Asset,name="asset"),nullable=False)
    price:Mapped[int]=mapped_column(BigInteger,nullable=False) #P
    platform_fee:Mapped[int] = mapped_column(BigInteger,nullable=False)
    fn_est:Mapped[int] = mapped_column(BigInteger,nullable=False)
    buffer:Mapped[int] = mapped_column(BigInteger,nullable=False)
    deposit_total:Mapped[int] = mapped_column(BigInteger,nullable=False) # D = P + fee + fn_est + buffer
    seller_payout_addres:Mapped[str]=mapped_column(Text,nullable=False)
    buyer_payout_address:Mapped[str|None]=mapped_column(Text)
    payout_speed_profile:Mapped[SpeedProfile] = mapped_column(Enum(SpeedProfile,name="speed_profile"))
    state:Mapped[EscrowState] = mapped_column(Enum(EscrowState, name="escrow_state"), nullable=False, default=EscrowState.CREATED)
    delivered_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    dispute_deadline:Mapped[datetime | None] = mapped_column(DateTime(timezone=True)) # delivered_at + 72h
    auto_release_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # delivered_at + 7d
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc),onupdate=datetime.now(timezone.utc), nullable=False)

    
class EscrowDestination(Base):
    __tablename__="escrow_destinations"

    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    escrow_id:Mapped[int]=mapped_column(ForeignKey("escrow.id",ondelete="CASCADE"),nullable=False)
    asset: Mapped[Asset]=mapped_column(Enum(Asset,name="asset"),nullable=False)
    destination:Mapped[str]=mapped_column(Text,nullable=False)#aonde o comprador tem q pagar
    meta:Mapped[dict|None] = mapped_column(JSON) #meta	jsonb	BTC: derivation path; XMR: account_index/subaddr_index
    active:Mapped[bool]=mapped_column(default=True,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)

    #Como eh gerada uma carteira pra cada pagamento, nao permite dois enderecos iguais
    __table_args__=(UniqueConstraint("destination", name="uq_escrow_destinations_destination"))


class Deposits(Base):
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
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (UniqueConstraint("txid", "vout", name="uq_deposits_txid_vout"))