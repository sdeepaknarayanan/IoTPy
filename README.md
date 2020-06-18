<div align="center">    
 
# IoTPy: Python + Streams

</div>

## Description

IoTPy is a Python package that helps you to build applications that operate on streams of data.

The two goals of IoTPy:

* Build non-terminating functions that operate on endless streams by reusing terminating functions, such as those in libraries like NumPy and SciPy.

* Build multithreaded, multicore, distributed applications by simply connecting streams.

Sensors, social media, news feeds, webcams and other sources generate streams of data. Many applications ingest and analyze data streams to control actuators, generate alerts, and feed continuous displays. IoTPy helps you to build such applications.

IoTPy is currently distributed under the 3-Clause BSD license.

## Installation

### Dependencies
* Python (>=2.7)
* NumPy (>=1.11.0)

For distributed applications, additional dependencies include the following 
* Pika (>=1.1.0)
Note that Pika may require other software to run.

### User Installation
The easiest way to install IoTPy is using ```pip``` as shows below.
```bash
pip install IoTPy
```
To install from source, please proceed as shown below:
```bash
git clone https://github.com/AssembleSoftware/IoTPy.git
cd IoTPy
python setup.py install
```
## Documentation

* Our project website is [AssembleSoftware](https://www.assemblesoftware.com/). We request anyone using IoTPy to visit the website to develop a better understading of IoTPy and its aims. 

* Documentation for the Code will be released soon. 

## Core Contributors

* Prof. [Kanianthra Mani Chandy](http://cms.caltech.edu/people/mani), California Institute of Technology
* S. Deepak Narayanan, IIT Gandhinagar

## Contributing

* We will soon create a branch ```dev``` where people can contribute. 




