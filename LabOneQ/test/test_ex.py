import lib
import pytest

def inc(x):
    '''Increment x'''
    return x+1

def test_inc():
    assert inc(5) == 6

def test_inc_new():
    with pytest.raises(ZeroDivisionError) as error:
        1 / 0
    assert error.type==ZeroDivisionError
    