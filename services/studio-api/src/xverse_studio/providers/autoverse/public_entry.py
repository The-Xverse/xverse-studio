"""Owned wrapper around the existing public vehicle CLI.

In synchronous startup, publish each spawned sensor into a world frame before its
public subscription call. The vehicle process owns these preparation ticks and
subsequent advancement. Companion source and production algorithms stay intact.
"""
import faulthandler
from pathlib import Path
import runpy
import sys


def prepare_sensor_subscriptions(carla):
    original = carla.Sensor.listen
    remaining = 5  # Collision, lane, GNSS, camera and radar in the admitted CLI.
    def listen(sensor, callback):
        nonlocal remaining
        # The owned vehicle process remains the sole synchronous tick owner.
        # Publish the newly spawned sensor into a frame before subscribing.
        frame = sensor.get_world().tick(10.0)
        if type(frame) is not int or frame <= 0:
            raise RuntimeError("CARLA_SENSOR_FRAME_UNCONFIRMED")
        remaining -= 1
        if remaining == 0:
            # Later camera/view changes must not acquire extra simulation ticks.
            carla.Sensor.listen = original
        return original(sensor, callback)
    carla.Sensor.listen = listen


def main():
    import carla
    if "--sync" in sys.argv[2:]:
        prepare_sensor_subscriptions(carla)
    faulthandler.enable()
    faulthandler.dump_traceback_later(30, repeat=True)
    entry = Path(sys.argv[1]).resolve(strict=True)
    sys.argv = sys.argv[1:]
    sys.path.insert(0, str(entry.parent))
    runpy.run_path(str(entry), run_name="__main__")


if __name__ == "__main__":
    main()
