import unittest

if __name__ == "__main__":
    test_loader = unittest.TestLoader()
    test_runner = unittest.TextTestRunner()
    test_suite = test_loader.discover('test', pattern='test_*.py')
    test_runner.run(test_suite)
