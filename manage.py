"""Helper CLI commands for this project."""

import click

import data_jam.models as models


@click.group()
def cli():
    pass


@cli.command()
def create_tables():
    models.ServiceRequest.create_table()
    models.Storm.create_table()


@cli.command()
@click.argument('path', type=click.File('r', encoding='utf-8'))
def import_service_request_data(path):
    models.ServiceRequest.import_from_csv(path)


@cli.command()
@click.argument('path', type=click.File('r', encoding='utf-8'))
def import_storm_data(path):
    models.Storm.import_from_csv(path)


if __name__ == '__main__':
    cli()
