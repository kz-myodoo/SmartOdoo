ARG ODOO_VER=18.0

FROM odoo:${ODOO_VER}

USER root

SHELL ["/bin/bash", "-xo", "pipefail", "-c"]

# Install git for cloning repositories in case of requirements.txt contains git+https links
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt to the image
COPY addons/requirements.tx[t] /mnt/extra-addons/

# install python packages
RUN if test -f '/mnt/extra-addons/requirements.txt'; then \
        pip3 install -r /mnt/extra-addons/requirements.txt || pip3 install --break-system-packages -r /mnt/extra-addons/requirements.txt; \
    fi;
# install debugpy package for debugging
RUN pip3 install --break-system-packages debugpy || pip3 install debugpy

# install often required paskages
RUN pip3 install --break-system-packages html2text suds || pip3 install html2text suds

USER odoo