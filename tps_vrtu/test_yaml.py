import confuse
import IPython as ip
import pdb

# ip.embed()

config = confuse.Configuration("testyaml")
config.set_file("tps_vrtu.yaml")

template = {
    'message_sources': confuse.Sequence(
        {
            'message_source_id': int,
            'desc': str,
            'source_type': confuse.OneOf('rabbitmq', 'activemq'),
            'source_uri': str,
            'topics': confuse.Sequence(
                {
                    'topic_id': int,
                    'name': str,
                    'source_message_type': confuse.OneOf('xml', 'json')
                }
            ),
        }
    ),
    'outstations': confuse.Sequence(
        {
            'outstation_id': int,
            'master_id':int,
            'desc': str,
            'points': 
                {
                    'analogs': confuse.Sequence(
                        {
                            'point_id': int,
                            'desc': str,
                            'point_type': confuse.OneOf('analog','float'),
                            'scaling': int,
                            'message_source_id': int,
                            'message_topic_id': int,
                            'point_path': str
                        }),
                    'binaries': confuse.Sequence(
                        {
                            'point_id': int,
                            'desc': str,
                            'point_type': confuse.OneOf('binary'),
                            'message_source_id': int,
                            'message_topic_id': int,
                            'point_path': str
                        })
                }
        }
    )
}

valid = config.get(template)
breakpoint()

print(config["outstations"][0]["points"])

