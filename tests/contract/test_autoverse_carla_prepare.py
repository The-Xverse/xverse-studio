"""Bootstrap protocol failures, distinct from actual native CARLA verification."""
import pytest
from xverse_studio.providers.autoverse.carla_prepare import prepare


class World:
    def __init__(self, frame=1):self.frame=frame;self.applied=None;self.ticks=[]
    def get_settings(self):raise AssertionError('Initial cached settings are not readiness')
    def wait_for_tick(self,*args):raise AssertionError('No asynchronous tick dependency')
    def apply_settings(self,value):self.applied=value
    def tick(self,deadline):self.ticks.append(deadline);return self.frame


class Client:
    def __init__(self,world):self.world=world
    def get_world(self):return self.world


def test_bootstrap_owns_tick_before_reading_initial_snapshot():
    world=World(8)
    observed=prepare(Client(world),lambda **values:values)
    assert world.applied=={'synchronous_mode':True,'fixed_delta_seconds':0.05,'no_rendering_mode':False}
    assert world.ticks==[10.0] and observed['observedFrame']==8


@pytest.mark.parametrize('frame',[0,-1,True,None])
def test_missing_authoritative_tick_is_not_reported_ready(frame):
    with pytest.raises(RuntimeError,match='CARLA_CLOCK_NOT_ADVANCING'):
        prepare(Client(World(frame)),lambda **values:values)
