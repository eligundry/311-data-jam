"""Helper CLI commands for this project."""

import click

import data_jam.models as models


@click.group()
def cli():
    pass


@cli.command()
def migrate():
    models.MIGRATION_ROUTER.run()


@cli.command()
@click.argument('name')
def rollback(name):
    models.MIGRATION_ROUTER.rollback(name)


@cli.command()
@click.argument('name')
def create_migration(name):
    models.MIGRATION_ROUTER.create(name)


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


@cli.command()
@click.argument('path', type=click.File('r', encoding='utf-8'))
def import_permitted_events_data(path):
    models.PermittedEvent.import_from_csv(path)
    print("Successfully import the Permitted Events data!")


@cli.command()
@click.option('--page', default=1, type=click.INT)
def import_nyc_events(page):
    models.Event.import_from_site(page)
    print("Successfully imported the Events data!")


@cli.command()
@click.argument('path', type=click.File('r', encoding='utf-8'))
def import_weather(path):
    models.Weather.import_from_csv(path)
    print("Successfully imported Weather data!")


if __name__ == '__main__':
    cli()
