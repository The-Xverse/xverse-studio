"""Bounded, read-only public CARLA connectivity and vehicle diagnostics."""
import argparse
import json


def main():
    import carla
    parser = argparse.ArgumentParser()
    parser.add_argument('--vehicle-status', action='store_true')
    args = parser.parse_args()
    client = carla.Client('127.0.0.1', 2000)
    client.set_timeout(3.0)
    world = client.get_world()
    result = {'clientVersion':client.get_client_version(),'serverVersion':client.get_server_version(),
              'map':world.get_map().name,'frame':world.get_snapshot().frame,'synchronous':world.get_settings().synchronous_mode}
    if args.vehicle_status:
        sample=world.wait_for_tick(5.0)
        result.update(frame=sample.frame,elapsedSeconds=sample.timestamp.elapsed_seconds)
        vehicles=[]
        for actor in world.get_actors().filter('vehicle.*'):
            if actor.attributes.get('role_name') != 'ego_vehicle':
                continue
            if len(vehicles)>=4:break
            control=actor.get_control();velocity=actor.get_velocity();location=actor.get_location()
            physics=actor.get_physics_control()
            vehicles.append({'id':actor.id,'type':actor.type_id,'alive':actor.is_alive,'dormant':actor.is_dormant,
              'velocity':{'x':velocity.x,'y':velocity.y,'z':velocity.z},
              'location':{'x':location.x,'y':location.y,'z':location.z},
              'control':{'throttle':control.throttle,'brake':control.brake,'steer':control.steer,'gear':control.gear,'reverse':control.reverse,'handBrake':control.hand_brake,'manualGearShift':control.manual_gear_shift},
              'mass':physics.mass,'maxRpm':physics.max_rpm})
        result['vehicles']=vehicles
    print(json.dumps(result))


if __name__ == '__main__':
    main()
