from dataclasses import dataclass
from statistics import mean

@dataclass(frozen=True)
class Candle:
    open: float; high: float; low: float; close: float; volume: float

@dataclass(frozen=True)
class CatRankResult:
    symbol: str; score: int; volume_score: int; accumulation_score: int; support_score: int; breakout_score: int; flags: tuple[str, ...]

def score_contract(symbol: str, c4: list[Candle], cd: list[Candle], cw: list[Candle]) -> CatRankResult:
    if min(len(c4), len(cd), len(cw)) < 5: return CatRankResult(symbol,0,0,0,0,0,('insufficient_data',))
    last=c4[-1]; avg=mean(c.volume for c in c4[-20:-1] or c4[:-1]); volume=min(30, int(20*last.volume/max(avg,1)))
    accumulation=25 if c4[-1].low>=c4[-5].low and (max(c.high for c in c4[-10:])-min(c.low for c in c4[-10:]))/max(min(c.low for c in c4[-10:]),1)<.25 else 10
    support_ok=all(data[-1].close>=min(c.low for c in data[-5:]) for data in (c4,cd,cw)); support=25 if support_ok else 0
    high=max(c.high for c in c4[-20:]); breakout=20 if 0<=(high-last.close)/max(high,1)<=.08 else 8
    flags=tuple(x for x,yes in [('support_break',not support_ok),('hostile_movement',(last.high-last.low)/max(last.close,1)>.15)] if yes)
    return CatRankResult(symbol,min(100,volume+accumulation+support+breakout),volume,accumulation,support,breakout,flags)
