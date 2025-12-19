Installation
============

Requirements
------------

* Python 3.8 or higher
* pip or conda package manager

Install from PyPI
-----------------

.. code-block:: bash

    pip install mobility-datasets

Install from Source
-------------------

.. code-block:: bash

    git clone https://github.com/mhabedank/mobility-datasets.git
    cd mobility-datasets
    pip install -e .

Development Installation
------------------------

For development, install with dev dependencies:

.. code-block:: bash

    pip install -e ".[dev,docs]"

Install pre-commit hooks:

.. code-block:: bash

    pre-commit install

Dependencies
------------

Core dependencies:

* numpy >= 1.20.0
* scipy >= 1.7.0
* pandas >= 1.3.0
* click >= 8.0.0
* requests >= 2.26.0
* tqdm >= 4.62.0
