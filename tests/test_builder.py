import pytest

from smartagg_builder import __version__ as VERSION
from smartagg_builder.builder import Builder

from carto.exceptions import CartoException
from carto.visualizations import Visualization

import warnings
warnings.filterwarnings('ignore')

@pytest.fixture
def builder():
    return Builder('./config.yaml')


def test_version():
    assert VERSION != None

def test_constructor():
    # Constructor should work with your current yaml config
    builder = Builder('./config.yaml')
    assert builder != None

    # Constructor should fail with a non existing file
    with pytest.raises(FileNotFoundError):
        Builder('./config.yaml.whatever')

def test_get_carto_username(builder):
    # Base test
    assert builder.get_carto_username() == 'jsanzcdb'

    # Fail test using the example config
    with pytest.raises(CartoException):
        fail_builder = Builder('./config.yaml.example')
        fail_builder.get_carto_username()


def test_get_maps(builder):
    # Base test
    all_maps = builder.get_maps()
    assert type(all_maps) == list
    assert len(all_maps) > 0
    assert all(map(lambda m: type(m) == Visualization,all_maps))

    # False test
    no_maps = builder.get_maps(name_filter='something impossible')
    assert type(no_maps) == list
    assert len(no_maps) == 0

def test_get_sb_maps(builder):
    # Base test
    sb_maps = builder.get_sb_maps()
    assert type(sb_maps) == list
    assert len(sb_maps) > 0
    assert all(map(lambda m: type(m) == Visualization,sb_maps))

