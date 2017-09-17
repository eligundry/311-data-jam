FROM jupyter/datascience-notebook:ae885c0a6226

ADD requirements.txt /requirements.txt
RUN conda install -c conda-forge --file /requirements.txt
RUN jupyter nbextension enable --py --sys-prefix widgetsnbextension \
    && jupyter nbextension enable --py --sys-prefix gmaps
