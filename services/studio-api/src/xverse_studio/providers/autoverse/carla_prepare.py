"""Configure only the newly owned simulator through the public CARLA API.

The admitted demo uses asynchronous simulation; no project supplies settings or
an endpoint. This helper must only be launched after exclusive simulator ownership.
"""
import json


def main():
    import carla
    client = carla.Client('127.0.0.1', 2000)
    client.set_timeout(5.0)
    world = client.get_world()
    settings = world.get_settings()
    before = settings.synchronous_mode
    settings.synchronous_mode = False
    settings.fixed_delta_seconds = None
    settings.no_rendering_mode = False
    world.apply_settings(settings)
    snapshot = world.wait_for_tick(10.0)
    print(json.dumps({'requestedSynchronousMode':False,'previousSynchronousMode':before,
                      'observedSynchronousMode':world.get_settings().synchronous_mode,
                      'observedFrame':snapshot.frame,'observedElapsedSeconds':snapshot.timestamp.elapsed_seconds}))
    if world.get_settings().synchronous_mode or snapshot.frame == 0:
        raise RuntimeError('CARLA_CLOCK_NOT_ADVANCING')


if __name__ == '__main__':
    main()
