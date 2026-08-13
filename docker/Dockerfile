ARG ODOO_VER=18.0
ARG ODOO_REVISION=""

FROM odoo:${ODOO_VER}${ODOO_REVISION}

USER root

ENV ODOO_VENV_DIR=/opt/odoo-venv
ENV PATH=${ODOO_VENV_DIR}/bin:${PATH}

SHELL ["/bin/bash", "-xo", "pipefail", "-c"]

# Install git and venv tooling required for isolated Python environment.
RUN apt-get update && apt-get install -y --no-install-recommends git python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create a dedicated virtual environment for Odoo runtime dependencies.
# Keep access to base-image site-packages where Odoo preinstalls core Python libs.
RUN python3 -m venv --system-site-packages ${ODOO_VENV_DIR}

# Copy requirements.txt to the image or .docker_placeholder if addons direcotiry with requirements.txt is not present.
COPY .docker_placeholde[r] [a]ddons/requirements.tx[t] /mnt/extra-addons/

# install python packages
RUN if test -f '/mnt/extra-addons/requirements.txt'; then \
    ${ODOO_VENV_DIR}/bin/pip install -r /mnt/extra-addons/requirements.txt; \
    fi;
# install debugpy package for debugging
RUN ${ODOO_VENV_DIR}/bin/pip install debugpy

# install often required paskages
RUN ${ODOO_VENV_DIR}/bin/pip install html2text suds

USER odoo