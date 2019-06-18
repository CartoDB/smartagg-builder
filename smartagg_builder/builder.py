"""
Class containing BUILDER named map migration logic.

This class is meant to be executed in several steps
being the most important one the `process` method that
shoud produce a new named map template in the client
CARTO account, enriched with the data passed through the
different layers CartoCSS comments.
"""
from carto.auth import APIKeyAuthClient
from carto.sql import SQLClient
from carto.maps import NamedMapManager, NamedMap
from carto.visualizations import VisualizationManager

from pyrestcli.exceptions import NotFoundException

import logging

from yaml import load, FullLoader as Loader
from pathlib import Path

import json
from json.decoder import JSONDecodeError

import re
import warnings

warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.CRITICAL,
    format=' %(asctime)s [%(levelname)-5s] %(message)s',
    datefmt='%I:%M:%S %p')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class Builder(object):
    """
    Class that encapsulates the generation of the new named map templates

    Attributes:
        logger: produces logging output
        config: dictionary with configuration parameters
        auth_client: an API key CARTO authentication client
    """

    def __init__(self, config_path):
        """
        Initializes the instance

        Args:
            config_path: the path to the configuration file
        """

        self.logger = logging.getLogger('sb')
        """The instance logger"""
        self.config = self.load_config(config_path)
        """Configuration dict"""
        self.logger.setLevel(self.config['log_level'])
        self.logger.debug('Configuration processed')

        creds = self.config["carto_account"]
        self.logger.debug(creds)
        self.auth_client = APIKeyAuthClient(
            creds["api_url"], creds["api_key"], creds["organization"]
        )
        """API key CARTO authentication client"""

    def get_logger(self):
        """
        Get the logger
        """
        return self.logger

    def load_config(self, config):
        """
        Return the configuration from a path

        Args:
            config: the path to the configuration file

        Returns:
            A dict with the configuration

        Raises:
            FileNotFoundError: wrong configuration file path passed
            KeyError: the "sb" key not found in the configuration file
        """
        config_file = Path(config)
        if not config_file.exists():
            raise FileNotFoundError
        else:
            with config_file.open("r") as config_reader:
                content = load(config_reader.read(), Loader=Loader)
                if 'sb' in content:
                    return content['sb']
                else:
                    raise KeyError()
                return ["sb"]

    def get_carto_username(self):
        """
        Returns the user name for the client passed

        Returns:
            String with CARTO account name

        Raises:
            CartoException: an error thrown by the CARTO request
            Exception: some error in the client happened
        """
        self.logger.debug("Getting the CARTO user name...")
        sql = SQLClient(self.auth_client)
        query = "SELECT CDB_Username()"
        q = sql.send(query)
        self.logger.debug(q)
        if "rows" in q and len(q["rows"]) == 1:
            return q["rows"][0]["cdb_username"]
        else:
            raise Exception("Your client is not valid")

    def get_maps(self, name_filter=None):
        """
        Get the visualizations of the user account

        Returns:
            Array with the visualization objects

        Args:
            name_filter: a string to filter visualizations based in their title
        """

        all_vizs = VisualizationManager(self.auth_client).all()

        if name_filter == None:
            return all_vizs
        else:
            filtered = [map for map in all_vizs if map.name.find(
                name_filter) != -1]
            return filtered

    def get_sb_maps(self):
        """
        Get the visualizations to process

        Returns:
            A dict with the visualizations
        """

        return self.get_maps(name_filter=self.config["maps"]["name_filter"])

    def generate_named_map_template(self, nm):
        """
        Produces a new named map template

        Args:
            A CARTO Python SDK named map dictionary

        Returns:
            A new dict with the necessary properties
        """

        return {
            "version": nm.version,
            "name": nm.name,
            "auth": nm.auth,
            "placeholders": nm.placeholders,
            "layergroup": nm.layergroup,
            "view": nm.view,
        }

    def process_template(self, named_map, new_name):
        """
        Process the given named map template to produce a new valid one

        Args:
            named_map: dict with the initial template to process
            new_name: the name of the new tempplate to generate

        Returns:
            A new dict based on the given template with the enriched data

        Raises:
            ValueError
        """

        try:
            template = self.generate_named_map_template(named_map)

            layers = filter(lambda l: l["type"] != "http",
                            template["layergroup"]["layers"])
            for layer in layers:
                self.logger.debug('\t\tProcessing layer {}'.format(layer['id']))
                options = layer['options']
                cartocss = options["cartocss"].replace("\n", "")
                delimiter = "\@{}\@".format(self.config["maps"]["delimiter"])

                search = re.search(
                    "{}(.*){}".format(delimiter, delimiter), cartocss)

                if search:
                    definition = search.groups()[0]
                    self.logger.debug("\t\tCustom definition found")
                    self.logger.debug("\t\t" + definition)
                    def_obj = json.loads(definition)
                    for key, value in def_obj.items():
                        self.logger.debug('\t\t\tAdding property: {}'.format(key))
                        options[key] = value
        except JSONDecodeError as e:
            self.logger.error('Error generating the template {}'.format(new_name))
            raise ValueError('The provided template fragment for the new template {} is not correct'.format(new_name))

        template["name"] = new_name

        return template

    def process(self, map):
        """
        Main processing method for a given named map template

        Args:
            map: a dict with an existing named map template

        Returns:
            A str with the new named map temaplate identifier
        """
        nmm = NamedMapManager(self.auth_client)

        self.logger.info('Processing map: {}'.format(map.name))

        template_id = "tpl_" + map.get_id().replace("-", "_")
        current_nm_map = self.get_template(template_id)

        # Check if the derived map exists
        derived_nm_map_name = template_id + self.config["named_maps"]["suffix"]

        self.logger.debug('\tTemplate: {}'.format(derived_nm_map_name))
        derived_nm_map = self.get_template(derived_nm_map_name)

        if derived_nm_map != None:
            # Remove the existing named map
            self.logger.debug( "\tThe named map exists, removing it")
            derived_nm_map.client = self.auth_client
            derived_nm_map.delete()

            self.logger.debug("\t{} removed".format(derived_nm_map_name))

        # Create a new template using the old one
        self.logger.info(
            '\tCreating the new template {}'.format(derived_nm_map_name))
        new_nm_template = self.process_template(
            current_nm_map, derived_nm_map_name)
        new_nm = nmm.create(template=new_nm_template)

        return new_nm.get_id()

    def get_templates(self):
        """
        Return the CARTO account named map template ids

        Returns:
            An array of named map identifiers
        """

        named_map_manager = NamedMapManager(self.auth_client)
        all_maps = named_map_manager.all()
        ids = [map.template_id for map in all_maps]
        return ids

    def get_template(self, id):
        """
        Return a dict with a named map template

        Args:
            id: str with the desired template

        Returns:
            A dict with the named map template

        Raises:
            NotFoundException: when the template does not exist
        """

        named_map_manager = NamedMapManager(self.auth_client)
        try:
            nm_map = named_map_manager.get(id)
            return nm_map
        except NotFoundException:
            self.logger.debug("Template not found")
            return None
