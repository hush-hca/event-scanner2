from event_scanner.cat_rank import Candle
from event_scanner.volume_fire import filter_volume_fire

def candles(last): return [Candle(1,1,1,1,100)]*19+[Candle(1,1,1,1,last)]
def test_includes_two_x_boundary(): assert filter_volume_fire('X',candles(200)).multiple == 2
def test_excludes_below_two_x(): assert filter_volume_fire('X',candles(199)) is None
