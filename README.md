# EVE Route Finder

## Description

Tool to optimize routes calculation between a staging point and a list of upwell structures (metenox drills).

## Getting Started

### Dependencies

* python3

### Installing

* Clone de repository
* * `git clone https://github.com/WilliamWeist/EVE-Route-Finder.git`
* Install the submodules
* * `git submodule init`
* * `git submodule update`
* Install the database
* * See [EVE-SDE-DB-Builder](https://github.com/WilliamWeist/EVE-SDE-DB-Builder) to generate the db file
* * Copy / Symlink the `EVE.db` file at the root of the project
* Install python dependencies
* * [Optional] Use a virtual environment
* * * Installation `python -m venv .venv`
* * * Activation `source .venv/bin/activate`
* * Run the installation script `./install.sh`

### Executing program

* Paste your list of structures into the `metenox_drill_list` file
* Launch the python script
```
python eve_route_finder.py
```

## Authors

William Weist 

![Static Badge](https://img.shields.io/badge/william__weist-Discord-5865F2?style=flat)


## License

This project is licensed under the GNU GPLv3 License - see the [LICENSE](LICENSE.md) file for details