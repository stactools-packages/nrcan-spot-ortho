FROM continuumio/miniconda3

RUN apt-get update \
    && apt-get install build-essential -y \
    && rm -rf /var/lib/apt/lists/*
RUN conda update conda && conda install pip

COPY environment.yml /tmp/environment.yml
RUN conda env update -f /tmp/environment.yml -n base && rm /tmp/environment.yml

COPY . /tmp/stactools-spot
RUN cd /tmp/stactools-spot && pip install . && rm -rf /tmp/stactools-spot

ENTRYPOINT [ "python", "-m", "stactools.cli" ]
