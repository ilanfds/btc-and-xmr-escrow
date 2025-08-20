from dataclasses import dataclass
import enum
from typing import NewType, Optional

#Apenas para referenciar taxas e valores em XMR e BTC
Sats=NewType("Sats",int)
Atomic=NewType("Atomic",int)

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

class PayoutKind(str,enum.Enum):
    NORMAL = "NORMAL"
    DISPUTE="DISPUTE"

class PayoutStatus(str,enum.Enum):
    BROADCAST="BROADCAST"
    CONFIRMED="CONFIRMED"
    FAILED="FAILED"

class Role(str,enum.Enum):
    SELLER="SELLER"
    BUYER="BUYER"
    PLATFORM="PLATFORM"

class SpeedProfile(str, enum.Enum):
    fast = "fast"
    normal = "normal"
    slow = "slow"

class DisputeStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class DepositStatus(str, enum.Enum):
    PENDING="PENDING"
    CONFIRMED = "CONFIRMED"


CONFIRMATIONS_MIN = { 
    Asset.BTC:10,
    Asset.XMR: 3
}

BTC_DUST_SATS:Sats = Sats(1000)

@dataclass(frozen=True)#Dataclass inicia os construtores, enquanto frozen simula imutabilidade em python
class EscrowAmounts:
    price:int #Preco P em base unites Sats ou Atmomic
    platform_fee:int # 3% de P
    fn_est:int #Taxa da transacao, para transferir
    buffer:int #gordurinha para garantir execucao
    deposit_total:int # D = P + 0,03P + fn_est + buffer

def confirmations_min(asset:Asset)->int:
    return CONFIRMATIONS_MIN[asset]

#Valida velocidade, pois XMR nao usa velocidade
def is_valid_speed(asset:Asset, speed:Optional[SpeedProfile])->bool:
    if asset == Asset.BTC:
        return speed in {SpeedProfile.fast,SpeedProfile.normal,SpeedProfile.slow}
    return speed is None

def require_positive_int(name:str, value:int)->None:
    if not isinstance(value,int) or value <= 0:
        raise ValueError(f"{name} dever ser inteiro > 0")