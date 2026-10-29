"""Input ownership and keyboard-only policy; no native window claim."""
from types import SimpleNamespace
import pytest
from xverse_studio.blueprints.autoverse import documents
from xverse_studio.providers.autoverse.adapter import AutoverseProvider, configuration
from xverse_studio.providers.autoverse.pygame_manual import configure_keyboard_only
from xverse_studio.storage.core import Problem
from xverse_studio.runs.service import Runs
from xverse_studio.xdl import XDLAdapter


def test_keyboard_mode_never_initializes_original_joystick_or_global_hardware():
    calls = []
    def forbidden():
        raise AssertionError('Unapproved global hardware initialization')
    pygame = SimpleNamespace(init=forbidden, joystick=SimpleNamespace(init=forbidden),
        display=SimpleNamespace(init=lambda: calls.append('display')),
        font=SimpleNamespace(init=lambda: calls.append('font')))
    configure_keyboard_only(pygame)
    assert pygame.init() == (2, 0)
    pygame.joystick.init()
    assert pygame.joystick.get_count() == 0
    assert pygame.joystick.get_init() is False
    with pytest.raises(RuntimeError):
        pygame.joystick.Joystick(0)
    assert calls == ['display', 'font']


@pytest.mark.parametrize('mode,kind', [('native-pygame','native-window'), ('studio-browser','normalized-driver')])
def test_canonical_source_selects_exactly_one_input_surface(mode, kind):
    source = documents(mode)
    config = configuration(source, XDLAdapter().compile(source))
    assert config['inputSurface'] == mode
    provider = AutoverseProvider({'identityDigest':'fixture'})
    assert provider.run_metadata(config)['inputSurface']['kind'] == kind


def test_native_window_rejects_browser_input_even_when_provider_has_input_api(client):
    runs = client.app.state.studio.runs
    runs.installed_providers['autoverse.demo'] = SimpleNamespace(input_request=lambda *_: pytest.fail('Browser publisher reached'))
    runs.read = lambda _: {'providerId':'autoverse.demo','state':'running','inputSurface':{'kind':'native-window'}}
    with pytest.raises(Problem) as caught:
        Runs.input_request(runs, 'fixture', 'acquire', {}, 'fixture')
    assert caught.value.code == 'CAPABILITY_UNSUPPORTED'


def test_sensor_startup_publishes_owned_frame_before_public_subscription():
    from xverse_studio.providers.autoverse.public_entry import prepare_sensor_subscriptions
    calls=[]
    class Sensor:
        def get_world(self):return SimpleNamespace(tick=lambda timeout:calls.append(('tick',timeout)) or 7)
        def listen(self,callback):calls.append(('listen',callback))
    carla=SimpleNamespace(Sensor=Sensor)
    prepare_sensor_subscriptions(carla)
    callback=object()
    Sensor().listen(callback)
    assert calls==[('tick',10.0),('listen',callback)]


def test_sensor_preparation_is_limited_to_startup_and_rejects_missing_frame():
    from xverse_studio.providers.autoverse.public_entry import prepare_sensor_subscriptions
    calls=[]
    class Sensor:
        def get_world(self):return SimpleNamespace(tick=lambda timeout:calls.append('tick') or 9)
        def listen(self,callback):calls.append('listen')
    carla=SimpleNamespace(Sensor=Sensor)
    prepare_sensor_subscriptions(carla)
    for _ in range(6):Sensor().listen(None)
    assert calls==['tick','listen']*5+['listen']
    class MissingFrame:
        def get_world(self):return SimpleNamespace(tick=lambda timeout:0)
        def listen(self,callback):pytest.fail('Unconfirmed sensor must not subscribe')
    carla=SimpleNamespace(Sensor=MissingFrame)
    prepare_sensor_subscriptions(carla)
    with pytest.raises(RuntimeError,match='CARLA_SENSOR_FRAME_UNCONFIRMED'):
        MissingFrame().listen(None)
