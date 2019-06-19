from environs import Env
import ast


env = Env()


with env.prefixed("SMARTAGG_"):
    config_path = env("CONFIG_FILE_PATH", default=None)
    config = {
        "file_path": config_path,
    }

    config['prometheus_enabled'] = env.bool("PROMETHEUS_ENABLED", False)
    if config['prometheus_enabled']:
        with env.prefixed("PROMETHEUS_"):
            config.update(
                {
                    "prometheus_server": env("SERVER"),
                    "prometheus_job": env("JOB_NAME"),
                    "prometheus_grouping_keys": ast.literal_eval(env("GROUPING_KEYS", "{}")),
                }
            )
