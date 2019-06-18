# CARTO SmartAggregations for BUILDER maps

This is a script that help BUILDER users to publish maps using CARTO Smart Aggregation features from the Maps API.

[1]: https://carto.com/developers/maps-api/guides/tile-aggregation/


## Why?

The current version of BUILDER does not support Maps API [Smart Aggregation][1] features. With the Maps API overviews going to be deprecated that leaves BUILDER users without the ability to render big amounts of data. This is solved for CARTO ENGINE usage as the Smart Aggregations are used automatically by CARTO VL and on-deman by CARTO.js.

## How

The process on BUILDER is as follows:

* Open the BUILDER map that you want to use
* Add a custom prefix to its name (by default `[SB]`). This will mark it for processing.
* On the layer you want to enable smart aggregation edit the CartoCSS and ad a comment

```text
/*@sb@
{
  "minzoom":5,
  "maxzoom":10,
  "aggregation": {
    "placement": "point-sample",
    "resolution": 4,
    "threshold": 10
   }
}
@sb@

/* Your normal CartoCSS */
#layer {
    ...
```

* Everything between the `@sb@...@sb@` will be added to the options object of your layer definition. This can be used not only for the Smart Aggregation definition but also to add a `minzoom` and `maxzoom` parameters. This is helpful if you are retrieving `MVT` tiles, since vector tiles don't take into account CartoCSS filters.
* From that moment you will have on your account a new template to use on your CARTO.js or Mobile SDK applications that can retrieve raster and vector tiles leveraging the Smart Aggregations for the Maps API.

The script does the following:

* Checks if your credentials are OK
* Finds on your account maps with the prefix (`[SB]` by default)
* For each map:
  * Takes the BUILDER map underlying template for the Named Maps API
  * Duplicates the named map template with a given suffix (`_sb` by default)
  * Process each BUILDER layer CartoCSS
  * If a layer CartoCSS has content between the delimiter (`@sb@` by default) it takes that content and tries to add it to the new layer definition).

So if you have a BUILDER map at the url https://yourorg.carto.com/u/youruser/builder/{ID}, the map identifier is `{ID}`. The backing named map template is called `tpl_{ID2}`, where `ID2` is just replacing `-` by `_` in `{ID}`, and the new named map template is `tpl_{ID2}_sb`.

## Configuration

All configuration for the tool is set up using a config.yaml file that stores:

* CARTO account credentials
* Tag to search for the maps to transform
* Delimiter to search for the JSON configuration
* Suffix to add to the derived named map templates
* Logging level


## How to run

The script is set up to use [poetry][2] so you can simply download the code and execute `poetry run sb`.

You can also create a new environment with `Python 3` and add manually the two dependencies `pip install carto PyYAML` and then run `python3 -m smartagg_builder.cli`. This script should be easy to deploy as a stand alone function on AWS Lambda or GCP Cloud Functions.


[2]: https://poetry.eustace.io
