
def bisectionMethod(x, y):
    """Applies the bisection method / binary search to a set of values

    Args:
        x: list of 3 floats; Initial range being searched
        y: list of 3 floats; Corresponding values to x

    Returns:
        x:  list of 3 floats; New, smaller range containing the root
    """
    if y[0] * y[1] < 0:
        return [x[0], (x[0] + x[1])/2, x[1]]
    elif y[1] * y[2] < 0:
        return [x[1], (x[1] + x[2])/2, x[2]]
    else:
        raise ValueError("No valid root detected by binary search in provided bounds")


def defaultIndefiniteIterationParameters():
    """Cleanly returns commonly desired parameters for approximating values

    Returns:
        tol:        The tolerated error in verifying a calculation as "correct"
        err:        An initial error to begin a loop
        counter:    A safety counter to identify how many iterations were required, and to set an upper limit
    """
    tol = 10 ** -8
    err = 1
    counter = 1
    return tol, err, counter


def addMidpoint(y):
    """Adds a midpoint value to a list

    Args:
        y:      An initial list of two floats

    Returns:
        y:      The final list of three floats, including a midpoint value
    """
    y.append(y[1])
    y[1] = (y[0] + y[2]) / 2
    return y
