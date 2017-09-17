FROM jupyter/datascience-notebook

RUN conda install -c \
        conda-forge \
        gmaps \
        peewee \
        click \
        psycopg2
