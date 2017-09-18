FROM jupyter/datascience-notebook

ADD requirements.txt /requirements.txt
RUN conda install -c conda-forge --file /requirements.txt
RUN pip install peewee_migrate
RUN jupyter nbextension enable --py --sys-prefix widgetsnbextension \
    && jupyter nbextension enable --py --sys-prefix gmaps
