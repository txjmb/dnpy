import pytest

from cppyy_opendnp3 import opendnp3


def test_cppyy_opendnp3_widget():
    w = opendnp3.Opendnp3Widget(-3)
    assert w.get() == -3


@pytest.mark.parametrize("member_t, member_val", [(int, 1), (float, 3.1), (bool, False)])
def test_cppyy_opendnp3_gadget(member_t, member_val):
    g = opendnp3.Opendnp3Gadget[member_t](member_val)
    assert g.get() == pytest.approx(member_val)
