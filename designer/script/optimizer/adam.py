import sys
sys.path.append('./designer/script/')


from tmm.get_jacobi_n_adjoint import get_jacobi_free_form
from tmm.get_jacobi import get_jacobi_simple
from tmm.get_spectrum import get_spectrum_free, get_spectrum_simple

from optimizer.grad_helper import stack_f, stack_J, stack_init_params
from utils.loss import calculate_RMS_f_spec, rms
from spectrum import BaseSpectrum
from film import FreeFormFilm, TwoMaterialFilm
import numpy as np
from typing import Sequence
import copy
from optimizer.optimizer import GradientOptimizer
from abc import abstractmethod

"""adam.py - Adam optimizer for thin film properties.

This module contains the AdamOptimizer class, which implements the Adam optimization
algorithm for optimizing thin film properties. This class inherits from the Optimizer
class defined in optimizer.py.

(generated by chatGPT)
"""


class AdamOptimizer(GradientOptimizer):
    """
    Implements the Adam optimization algorithm for thin film properties.

    ...

    Attributes
    ----------
    film : object
        A film object representing the thin film structure.
    target_spec_ls : Sequence[BaseSpectrum]
        A sequence of target spectra for optimization.
    max_steps : int
        The maximum number of optimization steps.
    alpha : float, optional, default=0.001
        The learning rate.
    beta1 : float, optional, default=0.9
        The exponential decay rate for the first moment estimates.
    beta2 : float, optional, default=0.999
        The exponential decay rate for the second-moment estimates.
    epsilon : float, optional, default=1e-8
        A small constant to prevent division by zero in the Adam optimizer.
    is_recorded : bool, optional, default=False
        Whether to record the optimization process.
    is_shown : bool, optional, default=False
        Whether to display the optimization process.
    records : list
        A list to store the recorded information during optimization.
    batch_size_spec: int
        Batch size of to pick out spectra from all spectra
        (spectra means different inc ang, polarization, etc.)
    batch_size_wl: int
        Batch size to pick out wavelengths from all wls
    Methods
    -------
    optimize():
        Executes the Adam optimization process.
    _loss():
        Calculates the root mean square (RMS) of the residual vector.
    _sgd():
        Makes mini-batches for stochastic gradient descent.
    _optimize_step():
        Executes a single optimization step.
    _update_best_and_patience():
        Updates the best solution found and adjusts the patience counter.
    _record():
        Records the current state of the optimization process.
    _show():
        Displays the current state of the optimization process.
    (generated by chatGPT)
    """

    def __init__(
        self,
        film,
        target_spec_ls: Sequence[BaseSpectrum],
        max_steps,
        **kwargs
    ):
        super().__init__(film, target_spec_ls, max_steps, **kwargs)

        # adam hyperparameters
        self.alpha = 0.001 if 'alpha' not in kwargs else kwargs['alpha']
        self.beta1 = 0.9 if 'beta1' not in kwargs else kwargs['beta1']
        self.beta2 = 0.999 if 'beta2' not in kwargs else kwargs['beta2']
        self.epsilon = 1e-8 if 'epsilon' not in kwargs else kwargs['epsilon']

        # initialize optimizer
        self.max_steps = max_steps
        self.max_patience = self.max_steps if 'patience' not in kwargs else kwargs[
            'patience']
        self.current_patience = self.max_patience
        self.best_loss = 0.
        self.m = 0
        self.v = 0  # adam hyperparameters
        self.n_arrs_ls = stack_init_params(self.film, self.target_spec_ls)

        self._get_param()  # init variable x

        # allocate space for f and J
        self.J = np.empty((self.total_wl_num, self.x.shape[0]))
        self.f = np.empty(self.total_wl_num)

    def optimize(self):
        # in case not do_record, return [initial film], [initial loss]
        self._record()

        for self.i in range(self.max_steps):
            self._optimize_step()
            self._set_param()
            if self.is_recorded:
                self._record()
            if self.is_shown:
                self._show()
            if not self._update_best_and_patience():
                break
        self.x = self.best_x
        self._set_param()  # restore to best x
        return self._rearrange_record()

    def _validate_loss(self):
        # return rms(self.f) THIS IS WRONG! should calculate on val set
        return calculate_RMS_f_spec(self.film, self.target_spec_ls)

    def _optimize_step(self):
        self._mini_batching()  # make mini batching params
        stack_f(
            self.f,
            self.n_arrs_ls,
            self.film.get_d(),
            self.target_spec_ls,
            spec_batch_idx=self.spec_batch_idx,
            wl_batch_idx=self.wl_batch_idx,
            get_f=self.get_f
        )
        stack_J(
            self.J,
            self.n_arrs_ls,
            self.film.get_d(),
            self.target_spec_ls,
            MAX_LAYER_NUMBER=250,  # TODO: refactor. This is not used
            spec_batch_idx=self.spec_batch_idx,
            wl_batch_idx=self.wl_batch_idx,
            get_J=self.get_J
        )

        self.g = self.J.T @ self.f
        self.m = self.beta1 * self.m + (1 - self.beta1) * self.g
        self.v = self.beta2 * self.v + (1 - self.beta2) * self.g ** 2
        self.m_hat = self.m / (1 - self.beta1 ** (self.i + 1))
        self.v_hat = self.v / (1 - self.beta2 ** (self.i + 1))
        self.x -= self.alpha * self.m_hat / \
            (np.sqrt(self.v_hat) + self.epsilon)


class AdamThicknessOptimizer(AdamOptimizer):

    def __init__(
            self,
            film,
            target_spec_ls: Sequence[BaseSpectrum],
            max_steps,
            alpha=1,
            **kwargs
    ):
        """
        Initializes the AdamThicknessOptimizer class, a subclass of AdamOptimizer.

        Args:
            film: The film object to be optimized.
            target_spec_ls (Sequence[BaseSpectrum]): A sequence of target spectra.
            max_steps (int): The maximum number of optimization steps.
            alpha (float): The learning rate (default: 1).
            **kwargs: Additional keyword arguments for hyperparameters, recording, and other user functionalities (inherited from AdamOptimizer):
                - beta1 (float): The exponential decay rate for the first moment estimates (default: 0.9).
                - beta2 (float): The exponential decay rate for the second moment estimates (default: 0.999).
                - epsilon (float): A small constant for numerical stability (default: 1e-8).
                - record (bool): Whether to record optimization steps (default: False).
                - show (bool): Whether to display optimization information (default: False).
                - optimize (callable): Custom optimization function (optional).
                - patience (int): Maximum number of steps without improvement before stopping (default: max_steps).
                - batch_size_spec (int): Number of spectra in each batch (default: len(target_spec_ls)).
                - batch_size_wl (int): Number of wavelengths in each batch (default: minimum wavelengths in target_spec_ls).
        """
        super().__init__(
            film,
            target_spec_ls,
            max_steps,
            alpha=alpha,
            ** kwargs
        )

        self.get_f = get_spectrum_simple
        self.get_J = get_jacobi_simple

    def _set_param(self):
        # Project back to feasible domain
        self.x[self.x < 0] = 0.
        self.film.update_d(self.x)

    def _get_param(self):
        self.x = self.film.get_d()


class AdamFreeFormOptimizer(AdamOptimizer):

    def __init__(
            self,
            film: FreeFormFilm,
            target_spec_ls: Sequence[BaseSpectrum],
            max_steps,
            alpha=0.1,
            **kwargs
    ):
        """
        Initializes the AdamFreeFormOptimizer class, inheriting from AdamOptimizer.

        Args:
            film (FreeFormFilm): The film object to be optimized.
            target_spec_ls (Sequence[BaseSpectrum]): A sequence of target spectra.
            max_steps (int): The maximum number of optimization steps.
            alpha (float): The learning rate (default: 0.1).
            **kwargs: Additional keyword arguments for hyperparameters, recording, and other user functionalities (inherited from AdamOptimizer):
                - beta1 (float): The exponential decay rate for the first moment estimates (default: 0.9).
                - beta2 (float): The exponential decay rate for the second moment estimates (default: 0.999).
                - epsilon (float): A small constant for numerical stability (default: 1e-8).
                - record (bool): Whether to record optimization steps (default: False).
                - show (bool): Whether to display optimization information (default: False).
                - optimize (callable): Custom optimization function (optional).
                - patience (int): Maximum number of steps without improvement before stopping (default: max_steps).
                - batch_size_spec (int): Number of spectra in each batch (default: len(target_spec_ls)).
                - batch_size_wl (int): Number of wavelengths in each batch (default: minimum wavelengths in target_spec_ls).
                - n_min (float): minimum refractive index allowed (default: smallest value for the EM wave to enter the first layer).
                - n_max (float): maximum refractive index allowed (default: inf). If exceed max/min during optimization, will be projected back along the dimension in \vec{n}.
        """
        super().__init__(
            film,
            target_spec_ls,
            max_steps,
            alpha=alpha,
            **kwargs
        )
        # avoid grad explode by asserting no total reflection
        if 'n_min' not in kwargs:
            self.n_min = film.calculate_n_inc(target_spec_ls[0].WLS)[0] * \
                np.sin(target_spec_ls[0].INC_ANG)
        else:
            self.n_min = kwargs['n_min']
        if 'n_max' not in kwargs:
            self.n_max = float('inf')
        else:
            self.n_max = kwargs['n_max']

        self.get_f = get_spectrum_free
        self.get_J = get_jacobi_free_form

    def _set_param(self):
        # project back to feasible region
        self.x[self.x < self.n_min] = self.n_min
        self.x[self.x > self.n_max] = self.n_max
        self.film.update_n(self.x)
        for l, s in zip(self.n_arrs_ls, self.target_spec_ls):
            l[0] = self.film.calculate_n_array(s.WLS)

    def _get_param(self):
        self.x = self.film.get_n()
