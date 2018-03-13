from abcpy.continuousmodels import *
import unittest

"""Tests whether the methods defined for continuous probabilistic models are working as intended."""

class CheckParametersAtInitializationTests(unittest.TestCase):
    """Tests that no probabilistic model with invalid parameters can be initialized."""

    # TODO: Test for all distributions the behaviour if input parameters are real distributions and not only
    # hyperparameters


    def test_Normal(self):
        with self.assertRaises(ValueError):
            Normal([1, -0.1])

    def test_MultivariateNormal(self):
        with self.assertRaises(ValueError):
            MultivariateNormal([[1]])

        with self.assertRaises(ValueError):
            MultivariateNormal([[1, 0, 0], [[1, 0], [0, 1]]])

        with self.assertRaises(ValueError):
            MultivariateNormal([[1, 0], [[1, 1], [0, 1]]])

        with self.assertRaises(ValueError):
            MultivariateNormal([[1, 0], [[-1, 0], [0, -1]]])

    def test_MultiStudentT(self):
        with self.assertRaises(ValueError):
            MultiStudentT([[1, 0], [[1, 1], [0, 1]], 1])

        with self.assertRaises(ValueError):
            MultiStudentT([[1, 0], [[-1, 0], [0, -1]], 1])

        with self.assertRaises(ValueError):
            MultiStudentT([[1, 0], [[1, 0], [0, 1]], -1])

    def test_Uniform(self):
        with self.assertRaises(ValueError):
            Uniform([[1, 2, 3], [4, 5]])


class DimensionTests(unittest.TestCase):
    """Tests whether the dimensions of all continuous models are defined in the correct way."""
    def test_Normal(self):
        N = Normal([1, 0.1])
        self.assertTrue(N.get_output_dimension()==1)

    def test_MultivariateNormal(self):
        M = MultivariateNormal([[1, 0], [[1, 0], [0, 1]]])
        self.assertTrue(M.get_output_dimension()==2)

    def test_MixtureNormal(self):
        M = MixtureNormal([1, 0])
        self.assertTrue(M.get_output_dimension()==2)

    def test_StudentT(self):
        S = StudentT([3, 1])
        self.assertTrue(S.get_output_dimension()==1)

    def test_MultiStudentT(self):
        M = MultiStudentT([[1, 0], [[0.1, 0], [0, 0.1]], 1])
        self.assertTrue(M.get_output_dimension()==2)

    def test_Uniform(self):
        U = Uniform([[0, 1], [1, 2]])
        self.assertTrue(U.get_output_dimension()==2)


class SampleFromDistributionTests(unittest.TestCase):
    """Tests the return value of forward_simulate for all continuous distributions."""
    def test_Normal(self):
        N = Normal([1, 0.1])
        samples = N.forward_simulate(3)
        self.assertTrue(isinstance(samples, list))
        self.assertTrue(len(samples)==3)

    def test_MultivariateNormal(self):
        M = MultivariateNormal([[1, 0], [[0.1, 0], [0, 0.1]]])
        samples = M.forward_simulate(3)
        self.assertTrue(isinstance(samples, list))
        self.assertTrue(len(samples) == 3)

    def test_MixtureNormal(self):
        M = MixtureNormal([1, 0])
        samples = M.forward_simulate(3)
        self.assertTrue(isinstance(samples, list))
        self.assertTrue(len(samples) == 3)

    def test_StudentT(self):
        S = StudentT([3, 1])
        samples = S.forward_simulate(3)
        self.assertTrue(isinstance(samples, list))
        self.assertTrue(len(samples) == 3)

    def test_MultiStudentT(self):
        S = MultiStudentT([[1, 0], [[0.1, 0], [0, 0.1]], 1])
        samples = S.forward_simulate(3)
        self.assertTrue(isinstance(samples, list))
        self.assertTrue(len(samples) == 3)

    def test_Uniform(self):
        U = Uniform([[0, 1], [1, 2]])
        samples = U.forward_simulate(3)
        self.assertTrue(isinstance(samples, list))
        self.assertTrue(len(samples) == 3)


class CheckParametersBeforeSamplingTests(unittest.TestCase):
    """Tests whether False will be returned if the input parameters of _check_parameters_before_sampling are not accepted."""
    def test_Normal(self):
        N = Normal([1, 0.1])
        self.assertFalse(N._check_parameters(InputConnector.from_list([1, -0.1])))

    def test_MultivariateNormal(self):
        M = MultivariateNormal([[1, 0], [[0.1, 0], [0, 0.1]]])
        self.assertFalse(M._check_parameters(InputConnector.from_list([[1, 0], [[1, 1], [0, 1]]])))
        self.assertFalse((M._check_parameters(InputConnector.from_list([[1, 0], [[-1, 0], [0, -1]]]))))

    def test_StudentT(self):
        S = StudentT([3, 1])
        self.assertFalse(S._check_parameters_before_sampling(InputConnector.from_list([3, -1])))

    def test_MultiStudentT(self):
        M = MultiStudentT([[1, 0], [[1, 0], [0, 1]], 1])
        self.assertFalse(M._check_parameters(InputConnector.from_list([[1, 0], [[1, 1], [1, 0]], 1])))
        self.assertFalse(M._check_parameters(InputConnector.from_list([[1, 0], [[-1, 0], [0, -1]], 1])))
        self.assertFalse(M._check_parameters(InputConnector.from_list([[1, 0], [[1, 0], [0, 1]], -1])))

    def test_Uniform(self):
        U = Uniform([[0, 1], [1, 2]])
        self.assertFalse(U._check_parameters(InputConnector.from_list([1, 1, 0, 2])))
        self.assertFalse(U._check_parameters(InputConnector.from_list([1, 1, 2, 0])))




if __name__ == '__main__':
    unittest.main()