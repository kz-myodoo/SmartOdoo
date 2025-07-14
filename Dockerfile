ARG ODOO_VER=18.0

FROM odoo:${ODOO_VER}

SHELL ["/bin/bash", "-xo", "pipefail", "-c"]

# Version with --break-system-packages is for odoo18 +
RUN pip3 install --break-system-packages pip --upgrade || pip3 install pip --upgrade 

# install python packages
RUN if [[ -f "/mnt/extra-addons/requirements.txt" ]]; then \
        pip3 install --break-system-packages -r /mnt/extra-addons/requirements.txt || pip3 install -r /mnt/extra-addons/requirements.txt; \
    fi;

# install debugpy package for debugging
RUN pip3 install --break-system-packages debugpy || pip3 install debugpy

# install often required paskages
RUN pip3 install --break-system-packages html2text suds || pip3 install html2text suds