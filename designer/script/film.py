import numpy as np
import gets.get_n as get_n
import spectrum


class Film:
    def __init__(self):
        self.d = np.array([])
        self.n = np.array([], dtype='complex')


class FilmSimple(Film):
    """
    Film that consist of 2 materials. Only d is modifiable. Materials are
    non - absorbing。

    Structure of the film: ABAB...substrate.
    0 - th layer is incident material.
    1 - st layer (self.d[0]) is A
    2 - nd layer (self.d[1]) is B
    ...
    last layer is substrate

    Arguments:
        A, B, substrate(str):
            material name of A, B, substrate

        d_init(numpy array): initial d.
        incidence(str): material of incidence

    Attributes:
        d(numpy array):
            thicknesses of each layer. d[0] is the first A.
            d.shape[0] is the layer number
        get_n_A, get_n_B, get_n_sub, get_n_inc (function: wl -> n):
            refractive indices of materials A, B, substrate and
            incident material
        spectrum(list of SpectrumSimple instances):

        n_arr (numpy array):
            array of refractive indices of layers at different wls


    """

    def __init__(self, A, B, substrate, d_init: np.array, incidence='Air'):
        try:
            exec(f"self.get_n_A = get_n.get_{A}")
            exec(f"self.get_n_B = get_n.get_{B}")
            exec(f"self.get_n_sub = get_n.get_{substrate}")
            exec(f"self.get_n_inc = get_n.get_{incidence}")
        except:
            raise ValueError(
                "Bad material. Dispersion must be specified in gets.get_n")
        self.d = d_init
        self.spectrum = []

    # Getter and Setter, etc of attribute spectrum
    def add_spec_param(self, inc_ang, wls):
        """
        Setter of the spectrum params: wls and inc

        """
        for s in self.spectrum:
            if s.WLS == wls and s.INC_ANG == inc_ang:
                return
        spec = spectrum.SpectrumSimple(inc_ang, wls, self)
        self.spectrum.append(spec)

    def remove_spec_param(self, inc_ang=None, wls=None):
        assert wls != None or inc_ang != None, "Must specify which spec to del"
        count = 0
        for s in self.spectrum:
            if (wls != None and s.WLS == wls) or \
                    (inc_ang != None and s.INC_ANG == inc_ang):
                self.spectrum.remove(s)
                count += 1
        return count

    def get_spec(self, inc_ang=None, wls=None):
        """ return spectrum with specified wls and inc_ang
        """
        if len(self.spectrum) == 1:
            # when only one spectrum, return the only one spectrum
            return s
        elif len(self.spectrum) == 0:
            raise ValueError("Uninitialized spectrum!")
        else:
            if inc_ang == None or wls == None:
                raise ValueError(
                    "In the case of multiple spectrums, must specify inc_ang\
                    and wls")
            for s in self.spectrum:
                if s.WLS == wls and s.INC_ANG == inc_ang:
                    return s
        # Not found, add to get_spec

    def get_all_spec_list(self):
        return self.spectrum

    def calculate_spectrum(self):
        for s in self.spectrum:
            s.calculate()

    # all layers should have non-zero thickness, except right after insertion
    # so check by explicitly calling these methods
    def check_thickness(self):
        assert np.min(self.d) > 0, "layers of zero thickness!"

    def remove_negative_thickness_layer(self):
        indices = [self.get_d()[i] for i in range(self.get_layer_number()) \
                    if self.get_d()[i] == 0]
        np.delete(self.d, indices)

    # Helper functions of insertion
    def insert_layer(self, layer_index, position, thickness):
        """
        insert a layer at the specified position
        """

    def get_insert_layer_n(self, index):
        """
        Insert layer should have a different material.
        e.g. ABABA, the material to insert at the 3-rd layer is: A
        """
        assert index < self.d.shape[0]
        if index % 2 == 0:
            return self.A
        else:
            return self.B


    # Functions to calculate n at given wls
    def calculate_n_array(self, wls: np.array):
        """
        calculate n at different wl for each layer.

        Returns:
            2d np.array, size is wls number * layer number. Refractive indices
        """
        n_arr = np.zeros(wls.shape[0], self.get_layer_number())
        for i in range(wls.shape[0]):
            wl = wls[i]
            n_A = self.get_n_A(wl)
            n_B = self.get_n_B(wl)
            l_B = self.get_layer_number() // 2
            l_A = self.get_layer_number() - l_B
            n_arr[i, :] = np.array([n_A, n_B] * l_B +
                                        [n_A] * (l_A - l_B))
        return n_arr

    def calculate_n_sub(self, wls):
        """
        calculate n at different wl for substrate

        Returns:
            1d np.array, size is wls.shape[0]. Refractive indices
        """
        n_arr = np.zeros(wls.shape[0])
        for i in range(wls.shape[0]):
            n_arr[i] = self.get_n_sub(wls[i])
        return n_arr

    def calculate_n_inc(self, wls):
        """
        calculate n at different wl for incident material

        Returns:
            1d np.array, size is wls.shape[0]. Refractive indices

        """
        n_arr = np.zeros(wls.shape[0])
        for i in range(wls.shape[0]):
            n_arr[i] = self.get_n_inc(wls[i])
        return n_arr


    # Accessor functions
    def get_d(self):
        return self.d

    def update_d(self, d):
        self.d = d
        for spec in self.get_all_spec_list():
            spec.outdate()
        return self.check_thickness()

    def get_layer_number(self):
        return self.d.shape[0]


    # Other utility functions
    def get_optical_thickness(self, wl):
        """
        Calculate the optical thickness of this film

        Arguments:
            wl (float):
                wavelength at which refractive index is evaluated
        """
        n_A = self.n_A(wl)
        n_B = self.n_B(wl)
        d_even = np.array([self.get_d()[i]
                           for i in range(0, self.get_layer_number(), 2)])
        d_odd = np.array([self.get_d()[i]
                          for i in range(1, self.get_layer_number(), 2)])
        return np.sum(n_A * d_even) + np.sum(n_B * d_odd)



def calculate_merit(film1, film2):
    spec_1_arr = np.array([])
    spec_2_arr = np.array([])
    
    for spec in film1.get_all_spec_list():
        # only R spec is counted
        spec_1_arr = np.append(spec_1_arr, spec.get_R())
        # target spectrum params
        inc_ang, wls = spec.INC_ANG, spec.WLS
        this_spec_2 = film2.get_spec(inc_ang, wls)
        # if spec updated, no need to calculate again
        if not this_spec_2.is_updated():
            this_spec_2.calculate()
        # only R spec is counted
        this_spec_2_arr = this_spec_2.get_R()
        spec_2_arr = np.append(spec_2_arr, this_spec_2_arr)
    # merit: RMS
    merit = np.sqrt(np.square(spec_1_arr - spec_2_arr)
                / spec_1_arr.shape[0])
    return merit