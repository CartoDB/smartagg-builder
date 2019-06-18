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
        builder = Builder('./config.yaml')
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
        return result
    except Exception:
        import sys
        sys.exit(1)


if __name__ == "__main__":
    import sys

    try:
        result = cli()
        sys.exit(0)
    except Exception:
        sys.exit(1)
