import numpy as np
from film import FilmSimple


def calculate_RMS(film1: FilmSimple, film2: FilmSimple):
    ''' calculates the RMS loss of the spectrum generated by two given films 
    '''
    R_1 = np.array([])
    R_2 = np.array([])
    T_1 = np.array([])
    T_2 = np.array([])
    
    for this_spec_film1 in film1.get_all_spec_list():
        # target spectrum params
        inc_ang, wls = this_spec_film1.INC_ANG, this_spec_film1.WLS
        this_spec_film2 = film2.get_spec(inc_ang, wls)
        # if spec updated, no need to calculate again
        if not this_spec_film1.is_updated():
            this_spec_film1.calculate()
        if not this_spec_film2.is_updated():
            this_spec_film2.calculate()
        # R and T spec are counted
        R_1 = np.append(R_1, this_spec_film1.get_R())
        R_2 = np.append(R_2, this_spec_film2.get_R())
        
        T_1 = np.append(T_1, this_spec_film1.get_T())
        T_2 = np.append(T_2, this_spec_film2.get_T())
    # merit: RMS
    RMS = np.sqrt((np.square(R_1 - R_2).sum() + np.square(T_1 - T_2).sum()) \
                / (R_1.shape[0] + T_1.shape[0]))
    return RMS