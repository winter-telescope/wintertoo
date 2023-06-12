# wintertoo
[![PyPI version](https://badge.fury.io/py/wintertoo.svg)](https://badge.fury.io/py/wintertoo)
[![CI](https://github.com/winter-telescope/wintertoo/actions/workflows/continuous_integration.yml/badge.svg)](https://github.com/winter-telescope/wintertoo/actions/workflows/continuous_integration.yml) 
[![Coverage Status](https://coveralls.io/repos/github/winter-telescope/wintertoo/badge.svg?branch=main)](https://coveralls.io/github/winter-telescope/wintertoo?branch=main) 

General package for Target-of-Opportunity (ToO) observations with the [WINTER observatory](https://github.com/winter-telescope). 

Current functionality includes:
* Converting RA/DEC positions to fields
* Building ToO schedules
* Verifying ToO schedules

## Installation
### Install from pypi
```bash
pip install wintertoo
```

### Install from source
```bash
git clone git@github.com:winter-telescope/wintertoo.git
cd wintertoo
pip install --editable ".[dev]"
pre-commit install
```
