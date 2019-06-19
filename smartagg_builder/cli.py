"""
This script will take a configuration file that needs to exist
in the calling folder and named `config.yaml` and following
its settings will connect with a CARTO account and generate/overwrite
some filtered named map templates, enriched with the
data included in the layers CartoCSS definition as enclosed
comments.

Please read the `README.md` file to get the full description
and reasoning of this workflow
"""


from smartagg_builder import __version__ as VERSION
from smartagg_builder.builder import Builder
from smartagg_builder.config import config
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway


def cli():
    """
    Main method to execute when called as a script

    Returns:
        An array with the template identifiers modified

    Raises:
        ValueError: something wrong happened
    """
    try:
        # Generate  the BUILDER object
        builder = Builder(config["file_path"])
        logger = builder.get_logger()
        result = None
        # Check the account
        logger.debug('Checking account...')
        username = builder.get_carto_username()
        logger.debug('Working with {} user'.format(username))

        # Find the maps that have a certain tag
        all_maps = builder.get_sb_maps()

        # Run the builder.process method over all maps
        result = list(map(builder.process, all_maps))

        # Profit!
        logger.info('Done!')
        reportToPrometheus(success=True)
        return result
    except Exception as e:
        import sys
        print(e)
        reportToPrometheus(success=False)
        sys.exit(1)

def reportToPrometheus(success=False):
    if not config["prometheus_enabled"]:
        return
    print("Prometheus reporting enabled")

    registry = CollectorRegistry()

    last_execution = Gauge(
        'smartagg_builder_task_last_execution_seconds',
        'Last time smartagg_builder task executed',
        registry=registry
    )
    last_execution.set_to_current_time()

    status = Gauge(
        'smartagg_builder_task_status',
        'Status of smartagg_builder last execution',
        registry=registry
    )

    if success:
        last_sucess = Gauge(
            'smartagg_builder_task_last_success_seconds',
            'Last time smartagg_builder task successfully finished',
            registry=registry
        )
        last_sucess.set_to_current_time()
        status.set(1)

    push_to_gateway(
        config["prometheus_server"],
        job=config["prometheus_job"],
        grouping_key=config["prometheus_grouping_keys"],
        registry=registry
    )

if __name__ == "__main__":
    import sys

    try:
        result = cli()
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)
