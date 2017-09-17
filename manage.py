"""Helper CLI commands for this project."""

import click

import data_jam.models as models


@click.group()
def cli():
    pass


@cli.command()
def create_tables():
    """Create the tables needed by this project."""
    models.ServiceRequest.create_table()
    models.Storm.create_table()


@cli.command()
@click.argument('path', type=click.File('r', encoding='utf-8'))
def import_service_request_data(path):
    """Import NYC 311 Service Requests CSV into the database.

    This data can be found at the following link. It is a huge dataset.

    https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9

    """
    models.ServiceRequest.import_from_csv(path)
    print("Successfully imported the 311 data!")


@cli.command()
@click.argument('path', type=click.File('r', encoding='utf-8'))
def import_storm_data(path):
    """Import the NOAA weather dataset.

    I had to manually pull this data from HTML, so I checked the dataset file
    into this repo as ``data/storms.csv``.

    """
    models.Storm.import_from_csv(path)
    print("Successfully imported the Storm data!")


if __name__ == '__main__':
    cli()
