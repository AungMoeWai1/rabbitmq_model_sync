import configparser

def load_rabbitmq_config(file_path):
    config = {}
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip()

    return {
        'host': config.get('rabbitmq_host'),
        'port': int(config.get('rabbitmq_port', 5672)),
        'user': config.get('rabbitmq_user'),
        'password': config.get('rabbitmq_password'),
        'queue': config.get('rabbitmq_queue'),
    }

