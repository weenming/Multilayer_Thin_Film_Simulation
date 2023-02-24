# Needle Optimization Using TFNN
## Overview
TFNN is an efficient algorithm in computing transmission matrices when simulating optical response of multi-layer structures.
We implement TFNN in needle optimization, which is a classical algorithm in designing layers with little known information of the target.

The aim of this project is 
- increase the efficiency of traditional algorithms
- search for the underlining rules determining the design results.
- find ways to realize better designs of multi-layer films.
  - lower total optical thickness
  - lower layer numbers
  - fewer "super thin" layers which is impractical in realistic manufacture.


## Dependents
Run on a machine supporting CUDA
- numpy
- numba
- cudatoolkit
- matplotlib



## File structure

- `script`
  - `TFNN` implements training of TFNN  
    - `get_insert_jacobi.py` Calculate insertion Jacobi matrix for gradient in needle method using TFNN
    - `get_jacobi.py` Calculate Jacobi matrix in gradient descent using TFNN
    - `get_n.py` Calculate and set refractive indices in Film instances
    - `get_spectrum.py` Calculate spectrum from a film instance
  - `design.py`
  - `film.py`
  - `LM_gradient_descent.py`
  - `needle_insert.py`

`main` files implements
- LM descent
- needle insertion iterations
- multi-thread acceleration.

`gets` module contains functions returning
- reflectance/transmittance spectrums
- gradient (Jacobi matrices) for optimizing layer thickness
- gradient for insertions in needle method.

## To-do

- film class
  - instance has: refractive index of each layer at specified wl
- conceal LM and insertions into modules, making main functions more concise and reduce duplicate code.
- unit tests

