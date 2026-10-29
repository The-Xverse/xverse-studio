"""Bootstrap the newly owned simulator in the admitted synchronous mode.

Only the provider's owned-start path invokes this helper. Construct known public
settings rather than adopting an initial, potentially empty client snapshot. The
existing vehicle CLI becomes the tick owner after this bounded preparation step.
"""
import json


def prepare(client, settings_factory):
    world = client.get_world()
    settings = settings_factory(synchronous_mode=True, fixed_delta_seconds=0.05,
                                no_rendering_mode=False)
    world.apply_settings(settings)
    # The public synchronous tick is an explicit request to the owned simulator;
    # waiting for an asynchronous frame here can never establish tick ownership.
    frame = world.tick(10.0)
    if type(frame) is not int or frame <= 0:
        raise RuntimeError('CARLA_CLOCK_NOT_ADVANCING')
    return {'requestedSynchronousMode': True, 'fixedDeltaSeconds': 0.05,
            'observedFrame': frame, 'sourceClockMapping': 'unavailable'}


def main():
    import carla
    client = carla.Client('127.0.0.1', 2000)
    client.set_timeout(10.0)
    print(json.dumps(prepare(client, carla.WorldSettings)))


if __name__ == '__main__':
    main()
