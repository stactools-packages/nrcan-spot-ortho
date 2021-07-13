FROM continuumio/miniconda3

RUN apt-get update \
    && apt-get install build-essential -y \
    && rm -rf /var/lib/apt/lists/*
RUN conda update conda && conda install pip

COPY environment.yml /tmp/environment.yml
RUN conda env update -f /tmp/environment.yml -n base && rm /tmp/environment.yml

COPY . /tmp/stactools-nrcan_spot_ortho
RUN cd /tmp/stactools-nrcan_spot_ortho && pip install . && rm -rf /tmp/stactools-nrcan_spot_ortho

ENTRYPOINT [ "python", "-m", "stactools.cli" ]
