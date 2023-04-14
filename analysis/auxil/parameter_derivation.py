import numpy as np


# { Main functions to be called from the Parameter Class

def find_parameters(dpar, **kwargs):
    """
    Searches for necessary parameters to calculate the derived parameter and
    add those parameters to the source parameters
    """

    fname = 'parameters_for_' + dpar.name

    if not fname in globals():
        return False

    names, components = globals()[fname](dpar, **kwargs)

    try:
        for n, c in zip(names, components):
            p = dpar.star.parameter_set.get(name__exact=n, component__exact=c,
                                            average__exact=True)
            dpar.source_parameters.add(p)
        return True
    except Exception as e:
        print(e)
        return False


def calculate(dpar, *args, **kwargs):
    """
    Calculates the parameter
    """

    fname = 'calculate_' + dpar.name

    if fname in globals():
        return globals()[fname](dpar, **kwargs)


# }

# { Decorator functions

def averageParameter(func):
    def func_wrapper(*args, **kwargs):

        new_args = []
        for arg in args:
            if hasattr(arg, 'value') and hasattr(arg, 'error'):
                new_args.append(np.random.normal(arg.value, arg.error, 512))
            elif type(arg) == tuple and len(arg) == 2:
                new_args.append(np.random.normal(arg[0], arg[1], 512))
            else:
                new_args.append(arg)
        new_args = tuple(new_args)

        value = func(*new_args, **kwargs)

        if hasattr(value, '__iter__') and len(value) > 1:
            return np.average(value), np.std(value)
        else:
            return value, 0.0

    return func_wrapper


# }

# MASS RATIO
# ===================================================

@averageParameter
def q(k1, k2):
    """
    Calculate the mass ratio
    """
    k1, k2 = np.abs(k1), np.abs(k2)
    return k1 / k2


def parameters_for_q(dpar, **kwargs):
    """
    Mass ratio is calculated from the two amplitudes K1 and K2
    """
    return ['K', 'K'], \
        [1, 2]


def calculate_q(dpar, *args, **kwargs):
    """
    Mass ratio is just K2 / K1
    """

    k1 = dpar.source_parameters.get(name__exact='K', component__exact=1, average__exact=True)
    k2 = dpar.source_parameters.get(name__exact='K', component__exact=2, average__exact=True)

    q_, eq_ = q(k1, k2)

    dpar.value = q_
    dpar.error = eq_


# REDUCED MASS
# ===================================================

@averageParameter
def msini(p, e, k1, k2):
    """
    Calculate reduced mass for the component belonging to k1,
    to calculate for the other component, reverce k1 and k2.
    """
    k1, k2 = np.abs(k1), np.abs(k2)
    msini = (1.0361e-7) * (1 - e ** 2) ** (3 / 2) * (k1 + k2) ** 2 * p * k1

    return msini


def parameters_for_msini(dpar, **kwargs):
    """
    Msini is calculated from the two amplitudes K1 and K2 and period
    """
    return ['K', 'K', 'p', 'e'], \
        [1, 2, 0, 0]


def calculate_msini(dpar, *args, **kwargs):
    """
    Msini = (1.0361e-7) * (1-e**2)**(3/2) * (k1+k2)**2 * k2 * P
    """

    k1 = dpar.source_parameters.get(name__exact='K', component__exact=1, average__exact=True)
    k2 = dpar.source_parameters.get(name__exact='K', component__exact=2, average__exact=True)
    p = dpar.source_parameters.get(name__exact='p', component__exact=0, average__exact=True)
    e = dpar.source_parameters.get(name__exact='e', component__exact=0, average__exact=True)

    val, err = msini(p, e, k1, k2) if dpar.component == 1 else msini(p, e, k2, k1)

    dpar.value = val
    dpar.error = err
    dpar.unit = 'Msol'


# REDUCED separation
# ===================================================

@averageParameter
def asini(p, e, k):
    """
    Calculate the reduced semi major axis for the component belonging to k
    """
    k = np.abs(k)
    asini = (1.9758e-2) * np.sqrt(1 - e ** 2) * k * p

    return asini


def parameters_for_asini(dpar, **kwargs):
    """
    Msini is calculated from the two amplitudes K1 and K2 and period
    """
    c = dpar.component
    return ['K', 'p', 'e'], \
        [c, 0, 0]


def calculate_asini(dpar, *args, **kwargs):
    """
    asini = (1.9758e-2) * np.sqrt(1-e**2) * K * P
    """
    c = dpar.component

    k = dpar.source_parameters.get(name__exact='K', component__exact=c, average__exact=True)
    p = dpar.source_parameters.get(name__exact='p', component__exact=0, average__exact=True)
    e = dpar.source_parameters.get(name__exact='e', component__exact=0, average__exact=True)

    val, err = asini(p, e, k)

    dpar.value = val
    dpar.error = err
    dpar.unit = 'Rsol'


# RADIUS
# ===================================================

def parameters_for_r(dpar, **kwargs):
    """
    Radius is derived from the mass and the surface gravity
    """
    c = dpar.component
    return ['m', 'logg'], \
        [c, c]


def calculate_r(dpar, *args, **kwargs):
    """
    radius is calculate as sqrt(G M / g)
    """

    M = self.source_parameters.get(name__exact='m', component__exact=dpar.component)
    g = self.source_parameters.get(name__exact='logg', component__exact=dpar.component)

    G = 6.673839999999998e-05
    M = np.random.normal(M.value, M.error, 512)
    g = np.random.normal(g.value, g.error, 512)
    r = np.sqrt(G * M * 1.988547e+30 / 10 ** g) / 69550800000.0

    self.value = np.average(r)
    self.error = np.std(r)
    self.unit = 'Rsol'
