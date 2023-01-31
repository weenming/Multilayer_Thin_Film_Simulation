import unittest
import numpy as np
import script.film as film
import script.gets.get_n as get_n
import script.gets.get_spectrum as get_spectrum


class TestFilm(unittest.TestCase):

    def test_film_init_1layer(self):
        d_expected = np.array([100.])
        substrate = A = "SiO2"
        B = "TiO2"
        f = film.FilmSimple(A, B, substrate, d_expected)
        self.assertAlmostEqual(f.get_d(), d_expected)

    def test_film_init_100layers(self):
        d_expected = np.array([100.] * 100)
        substrate = A = "SiO2"
        B = "TiO2"
        f = film.FilmSimple(A, B, substrate, d_expected)
        self.assertAlmostEqual(f.get_d(), d_expected)

    def test_film_change_d(self):
        layer_number = 100
        d_expected = np.array([i + 0.1 for i in range(layer_number)])
        wls = np.linspace(500., 1000., 500)
        inc_ang = 30.
        
        substrate = A = "SiO2"
        B = "TiO2"
        
        n_expected = np.array([[get_n.get_n_SiO2(wl), get_n.get_n_TiO2(wl)] * \
            layer_number for wl in wls])
        f = film.FilmSimple(A, B, substrate, d_expected)
        f.add_spec_param(inc_ang, wls)

        self.assertAlmostEqual(f.get_d(), d_expected)
        self.assertAlmostEqual(f.calculate_n_array(wls), n_expected)

    def test_film_spectrum(self):
        d_expected = np.array([i + 0.1 for i in range(100)])
        n_expected = np.array()
        substrate = A = "SiO2"
        B = "TiO2"
        f = film.FilmSimple(A, B, substrate, d_expected)
        # must set spec before calculating spec
        f.add_spec_param(inc_ang, wls)
        f.calculate_spectrum()
        self.assertAlmostEqual(get_spectrum(), expected_spec)
    