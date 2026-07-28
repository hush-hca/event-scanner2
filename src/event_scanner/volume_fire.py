from dataclasses import dataclass
from statistics import mean

from .cat_rank import Candle

@dataclass(frozen=True)
class VolumeFireResult:
    symbol: str; current_volume: float; average_volume: float; multiple: float

def filter_volume_fire(symbol: str, candles: list[Candle]) -> VolumeFireResult | None:
    if len(candles) < 20: return None
    current = candles[-1].volume
    average = mean(c.volume for c in candles[-20:-1])
    if average <= 0 or current / average < 2: return None
    return VolumeFireResult(symbol, current, average, round(current / average, 2))
