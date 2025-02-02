import os
import pickle
import unittest
import numpy as np
import sys
sys.path.append("./designer/script")
sys.path.append("./")  # wtf?

import copy
from film import BaseFilm, FreeFormFilm, TwoMaterialFilm
import utils.get_n as get_n
from tmm.get_jacobi_n_adjoint import get_jacobi_free_form
from tmm.tmm_cpu.get_jacobi_n_adjoint_cpu import get_jacobi_free_form_cpu
from tmm.get_jacobi_adjoint import get_jacobi_simple
from tmm.get_spectrum import get_spectrum_free

import matplotlib.pyplot as plt


cells = 5
np.random.seed(1)
f1 = FreeFormFilm(np.array(
    [1., 2.] * cells, dtype='complex128') + np.random.random(cells * 2), 1000., 'SiO2')  # should not be less than 1?
inc_ang = 60.  # incident angle in degree
wls = np.linspace(500, 1000, 500)
f1.add_spec_param(inc_ang, wls)
fname = "./designer/tests/test_files/expected_jacobi_wrt_n_simple_R_500to1000_10layer_1-2-times-5-SiO2_60inc.csv"


class TestJacobi(unittest.TestCase):
    def test_film_jacobi(self):
        # must set spec before calculating spec
        jacobi = np.empty((wls.shape[0] * 2, cells * 2), dtype='float')
        get_jacobi_free_form(jacobi, wls, f1.get_d(),
                             f1.spectra[0].n, f1.spectra[0].n_sub, f1.spectra[0].n_inc, inc_ang)

        # read expected spec from file
        # count relative path from VS Code project root.....
        expected_jacobi = np.loadtxt(
            fname, dtype="float")
        np.testing.assert_almost_equal(
            jacobi[:wls.shape[0], :], -jacobi[wls.shape[0]:, :])
        np.testing.assert_almost_equal(
            jacobi[:wls.shape[0], :], expected_jacobi[:wls.shape[0], :] / 2)
        np.testing.assert_almost_equal(
            jacobi[wls.shape[0]:, :], expected_jacobi[wls.shape[0]:, :] / 2)

    def test_many_layer_film_jacobi(self):
        np.random.seed(1)
        cells = 1000
        f = FreeFormFilm(np.array([1, 2] * cells), 1000., 'SiO2')
        # must set spec before calculating spec
        inc_ang = 60.  # incident angle in degree
        wls = np.linspace(500, 1000, 5000)
        f.add_spec_param(inc_ang, wls)

        jacobi = np.empty((wls.shape[0] * 2, cells * 2))
        get_jacobi_free_form(jacobi, wls, f.get_d(),
                             f.spectra[0].n, f.spectra[0].n_sub, f.spectra[0].n_inc, inc_ang, jacobi.shape[1])


def test_film_jacobi_debug():
    np.random.seed(1)
    layer = 10
    d_expected = np.random.random(layer) * 1000

    substrate = A = "SiO2"
    B = "TiO2"
    f = TwoMaterialFilm(A, B, substrate, d_expected)
    # must set spec before calculating spec
    inc_ang = 60.  # incident angle in degree
    wls = np.linspace(500, 1000, 1)
    f.add_spec_param(inc_ang, wls)

    jacobi = np.empty((wls.shape[0] * 2, layer))
    get_jacobi_free_form(jacobi, wls, f.get_d(),
                         f.spectrums[0].n, f.spectrums[0].n_sub, f.spectrums[0].n_inc, inc_ang, s_ratio=0, p_ratio=1)

    print(jacobi)


def make_expected_file():
    jacobi = np.zeros((wls.shape[0] * 2, cells * 2), dtype='double')
    spec = np.zeros(wls.shape[0] * 2, dtype='double')
    h = 3e-9  # here, wither large or small h will introduce large error...
    # at least this is an edge of the analytical method...
    for i in range(f1.get_layer_number()):
        f_tmp = copy.deepcopy(f1)
        n = copy.deepcopy(f_tmp.get_n())
        n[i] += h
        f_tmp.update_n(n)

        get_spectrum_free(
            spec,
            wls,
            f1.get_d(),
            f1.calculate_n_array(wls),
            f1.calculate_n_sub(wls),
            f1.calculate_n_inc(wls),
            inc_ang
        )
        jacobi[:, i] -= spec

        get_spectrum_free(
            spec,
            wls,
            f_tmp.get_d(),
            f_tmp.calculate_n_array(wls),
            f_tmp.calculate_n_sub(wls),
            f_tmp.calculate_n_inc(wls),
            inc_ang
        )

        jacobi[:, i] += spec
        jacobi[:, i] /= h
    np.savetxt(fname, jacobi)


def plot_diff_h():
    jacobi_standard = np.empty((wls.shape[0] * 2, cells * 2), dtype='float')
    get_jacobi_free_form(jacobi_standard, wls, f1.get_d(),
                         f1.calculate_n_array(wls), f1.spectra[0].n_sub, f1.spectra[0].n_inc, inc_ang)

    spec_standard = np.empty(wls.shape[0] * 2, dtype='double')

    get_spectrum_free(
        spec_standard,
        wls,
        f1.get_d(),
        f1.calculate_n_array(wls),
        f1.calculate_n_sub(wls),
        f1.calculate_n_inc(wls),
        inc_ang
    )

    hs = [10 ** n for n in range(-30, -10, 3)] + [1e-9, 5e-9,
                                                  1e-8] + [10 ** n for n in range(-7, 20, 3)]
    errors = []
    for h in hs:
        jacobi = np.zeros((wls.shape[0] * 2, cells * 2), dtype='double')
        # h = 3e-9  # here, wither large or small h will introduce large error...
        # at least this is an edge of the analytical method...
        for i in range(f1.get_layer_number()):
            spec = np.zeros(wls.shape[0] * 2, dtype='double')

            jacobi[:, i] -= spec_standard

            f_tmp = copy.deepcopy(f1)
            n = copy.deepcopy(f_tmp.get_n())
            n[i] += h
            f_tmp.update_n(n)

            get_spectrum_free(
                spec,
                wls,
                f_tmp.get_d(),
                f_tmp.calculate_n_array(wls),
                f_tmp.calculate_n_sub(wls),
                f_tmp.calculate_n_inc(wls),
                inc_ang
            )

            jacobi[:, i] += spec
            jacobi[:, i] /= h
        errors.append(np.sqrt(np.sum(np.square(jacobi / 2 - jacobi_standard))))

    with open(os.path.dirname(__file__) + '/../../../../working/review/computation/result_dif_h', 'wb') as f:
        pickle.dump({
            'hs': hs, 
            'errors': errors
        }, f)

    # fig, ax = plt.subplots(1, 1)
    # ax.plot(hs, errors, marker='.')
    # ax.set_ylabel('RMS of brute force and analytical derivative')
    # ax.set_xlabel('h')
    # ax.set_xscale('log')
    # ax.set_yscale('log')
    # plt.show()


if __name__ == "__main__":
    # make_expected_file()
    # unittest.main()
    plot_diff_h()
