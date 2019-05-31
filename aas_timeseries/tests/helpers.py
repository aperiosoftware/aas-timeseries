import os
from traceback import print_exc

import pytest

from matplotlib.testing.compare import compare_images

DATA = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))


def compare_to_reference_json(tmpdir, test_name, image_tests=False):

    tmpdir = tmpdir.strpath

    expected_files = sorted(os.listdir(os.path.join(DATA, test_name)))
    actual_files = sorted(os.listdir(tmpdir))

    if not image_tests:
        expected_files = [x for x in expected_files if not x.endswith('.png')]

    assert expected_files == actual_files

    for filename in expected_files:

        expected_file = os.path.join(DATA, test_name, filename)
        actual_file = os.path.join(tmpdir, filename)

        if filename.endswith('.png'):

            try:
                msg = compare_images(expected_file, actual_file, tol=0)
            except Exception:
                msg = 'Image comparison failed:'
                print_exc()

            if msg is not None:
                pytest.fail(msg, pytrace=False)

        else:

            with open(expected_file) as f:
                expected = f.read().strip()
            with open(actual_file) as f:
                actual = f.read().strip()

            # Normalize line endings
            expected = expected.replace('\r\n', '\n').replace('\r', '\n')
            actual = actual.replace('\r\n', '\n').replace('\r', '\n')

            assert expected == actual
