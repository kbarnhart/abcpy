import unittest
import numpy as np
import warnings

from abcpy.backends import BackendDummy
from abcpy.continuousmodels import Normal

from abcpy.distances import Euclidean

from abcpy.approx_lhd import SynLiklihood

from abcpy.continuousmodels import Uniform

from abcpy.statistics import Identity

from abcpy.inferences import RejectionABC, PMC, PMCABC, SABC, ABCsubsim, SMCABC, APMCABC, RSMCABC

class RejectionABCTest(unittest.TestCase):
    def test_sample(self):
        # setup backend
        dummy = BackendDummy()

        # define a uniform prior distribution
        mu = Uniform([[-5.0], [5.0]], name='mu')
        sigma = Uniform([[0.0], [10.0]], name='sigma')
        # define a Gaussian model
        self.model = Normal([mu,sigma])

        # define sufficient statistics for the model
        stat_calc = Identity(degree=2, cross=0)
        
        # define a distance function
        dist_calc = Euclidean(stat_calc)

        # create fake observed data
        y_obs = [np.array(9.8)]

        # use the rejection sampling scheme
        sampler = RejectionABC([self.model], dist_calc, dummy, seed = 1)
        journal = sampler.sample([y_obs], 10, 1, 10)
        mu_sample = np.array(journal.get_parameters()['mu'])
        sigma_sample = np.array(journal.get_parameters()['sigma'])

        # test shape of samples
        self.assertEqual(np.shape(mu_sample), (10,1))
        self.assertEqual(np.shape(sigma_sample), (10,1))

        # Compute posterior mean
        #self.assertAlmostEqual(np.average(np.asarray(samples[:,0])),1.22301,10e-2)
        self.assertLess(np.average(mu_sample) - 1.22301, 1e-2)
        self.assertLess(np.average(sigma_sample) - 6.992218,10e-2)

        self.assertFalse(journal.number_of_simulations==0)




class PMCTests(unittest.TestCase):
        
    def test_sample(self):
        # setup backend
        backend = BackendDummy()
        
        # define a uniform prior distribution
        mu = Uniform([[-5.0], [5.0]], name='mu')
        sigma = Uniform([[0.0], [10.0]], name='sigma')
        # define a Gaussian model
        self.model = Normal([mu,sigma])

        # define sufficient statistics for the model
        stat_calc = Identity(degree = 2, cross = 0)

        # create fake observed data
        #y_obs = self.model.forward_simulate(1, np.random.RandomState(1))[0].tolist()
        y_obs = [np.array(9.8)]
      
        # Define the likelihood function
        likfun = SynLiklihood(stat_calc)


        T, n_sample, n_samples_per_param = 1, 10, 100
        sampler = PMC([self.model], likfun, backend, seed = 1)
        journal = sampler.sample([y_obs], T, n_sample, n_samples_per_param, covFactors =  np.array([.1,.1]), iniPoints = None)
        mu_post_sample, sigma_post_sample, post_weights = np.array(journal.get_parameters()['mu']), np.array(journal.get_parameters()['sigma']), np.array(journal.get_weights())

        # Compute posterior mean
        mu_post_mean, sigma_post_mean = np.average(mu_post_sample, weights=post_weights, axis=0), np.average(sigma_post_sample, weights=post_weights, axis=0)

        # test shape of sample
        mu_sample_shape, sigma_sample_shape, weights_sample_shape = np.shape(mu_post_sample), np.shape(mu_post_sample), np.shape(post_weights)
        self.assertEqual(mu_sample_shape, (10,1))
        self.assertEqual(sigma_sample_shape, (10,1))
        self.assertEqual(weights_sample_shape, (10,1))
        self.assertLess(abs(mu_post_mean - (-3.64971)), 1e-3)
        self.assertLess(abs(sigma_post_mean - 4.1925), 1e-3)

        self.assertFalse(journal.number_of_simulations == 0)


        # use the PMC scheme for T = 2
        T, n_sample, n_samples_per_param = 2, 10, 100
        sampler = PMC([self.model], likfun, backend, seed = 1)
        journal = sampler.sample([y_obs], T, n_sample, n_samples_per_param, covFactors = np.array([.1,.1]), iniPoints = None)
        mu_post_sample, sigma_post_sample, post_weights = np.array(journal.get_parameters()['mu']), np.array(journal.get_parameters()['sigma']), np.array(journal.get_weights())
        
        # Compute posterior mean
        mu_post_mean, sigma_post_mean = np.average(mu_post_sample, weights=post_weights, axis=0), np.average(sigma_post_sample, weights=post_weights, axis=0)

        # test shape of sample
        mu_sample_shape, sigma_sample_shape, weights_sample_shape = np.shape(mu_post_sample), np.shape(mu_post_sample), np.shape(post_weights)
        self.assertEqual(mu_sample_shape, (10,1))
        self.assertEqual(sigma_sample_shape, (10,1))
        self.assertEqual(weights_sample_shape, (10,1))
        self.assertLess(abs(mu_post_mean - (-3.09297) ), 1e-3)
        self.assertLess(abs(sigma_post_mean - 5.78645), 1e-3)

        self.assertFalse(journal.number_of_simulations == 0)


class PMCABCTests(unittest.TestCase):
    def setUp(self):
        # find spark and initialize it
        self.backend = BackendDummy()

        # define a uniform prior distribution
        # define a uniform prior distribution
        mu = Uniform([[-5.0], [5.0]], name='mu')
        sigma = Uniform([[0.0], [10.0]], name='sigma')
        # define a Gaussian model
        self.model = Normal([mu, sigma])

        # define a distance function
        stat_calc = Identity(degree=2, cross=0)
        self.dist_calc = Euclidean(stat_calc)

        # create fake observed data
        #self.observation = self.model.forward_simulate(1, np.random.RandomState(1))[0].tolist()
        self.observation = [np.array(9.8)]

        
    def test_calculate_weight(self):
        n_samples = 2
        rc = PMCABC([self.model], self.dist_calc, self.backend, seed=1)
        theta = np.array([1.0,1.0])


        weight = rc._calculate_weight(theta)
        self.assertEqual(weight, 0.5)
        
        accepted_parameters = [[1.0, 1.0 + np.sqrt(2)],[0,0]]
        accepted_weights = np.array([[.5], [.5]])
        accepted_cov_mat = [np.array([[1.0,0],[0,1]])]
        rc.accepted_parameters_manager.update_broadcast(rc.backend, accepted_parameters, accepted_weights, accepted_cov_mat)
        kernel_parameters = []
        for kernel in rc.kernel.kernels:
            kernel_parameters.append(
                rc.accepted_parameters_manager.get_accepted_parameters_bds_values(kernel.models))

        rc.accepted_parameters_manager.update_kernel_values(rc.backend, kernel_parameters=kernel_parameters)
        weight = rc._calculate_weight(theta)
        expected_weight = 0.170794684453
        self.assertAlmostEqual(weight, expected_weight)
        

        
    def test_sample(self):
        # use the PMCABC scheme for T = 1
        T, n_sample, n_simulate, eps_arr, eps_percentile = 1, 10, 1, [10], 10
        sampler = PMCABC([self.model], self.dist_calc, self.backend, seed = 1)
        journal = sampler.sample([self.observation], T, eps_arr, n_sample, n_simulate, eps_percentile)
        mu_post_sample, sigma_post_sample, post_weights = np.array(journal.get_parameters()['mu']), np.array(journal.get_parameters()['sigma']), np.array(journal.get_weights())
          
        # Compute posterior mean
        mu_post_mean, sigma_post_mean = np.average(mu_post_sample, weights=post_weights, axis=0), np.average(sigma_post_sample, weights=post_weights, axis=0)

        # test shape of sample
        mu_sample_shape, sigma_sample_shape, weights_sample_shape = np.shape(mu_post_sample), np.shape(mu_post_sample), np.shape(post_weights)
        self.assertEqual(mu_sample_shape, (10,1))
        self.assertEqual(sigma_sample_shape, (10,1))
        self.assertEqual(weights_sample_shape, (10,1))
        self.assertLess(mu_post_mean - 0.03713, 10e-2)
        self.assertLess(sigma_post_mean - 7.727, 10e-2)

        #self.assertEqual((mu_post_mean, sigma_post_mean), (,))
        
        # use the PMCABC scheme for T = 2
        T, n_sample, n_simulate, eps_arr, eps_percentile = 2, 10, 1, [10,5], 10
        sampler = PMCABC([self.model], self.dist_calc, self.backend, seed = 1)
        sampler.sample_from_prior(rng=np.random.RandomState(1))
        journal = sampler.sample([self.observation], T, eps_arr, n_sample, n_simulate, eps_percentile)
        mu_post_sample, sigma_post_sample, post_weights = np.array(journal.get_parameters()['mu']), np.array(journal.get_parameters()['sigma']), np.array(journal.get_weights())
          
        # Compute posterior mean
        mu_post_mean, sigma_post_mean = np.average(mu_post_sample, weights=post_weights, axis=0), np.average(sigma_post_sample, weights=post_weights, axis=0)

        # test shape of sample
        mu_sample_shape, sigma_sample_shape, weights_sample_shape = np.shape(mu_post_sample), np.shape(mu_post_sample), np.shape(post_weights)
        self.assertEqual(mu_sample_shape, (10,1))
        self.assertEqual(sigma_sample_shape, (10,1))
        self.assertEqual(weights_sample_shape, (10,1))
        self.assertLess(mu_post_mean - 0.9356, 10e-2)
        self.assertLess(sigma_post_mean - 7.819, 10e-2)

        self.assertFalse(journal.number_of_simulations == 0)


class SABCTests(unittest.TestCase):
    def setUp(self):
        # find spark and initialize it
        self.backend = BackendDummy()

        # define a uniform prior distribution
        mu = Uniform([[-5.0], [5.0]], name='mu')
        sigma = Uniform([[0.0], [10.0]], name='sigma')
        # define a Gaussian model
        self.model = Normal([mu, sigma])

        # define a distance function
        stat_calc = Identity(degree=2, cross=0)
        self.dist_calc = Euclidean(stat_calc)

        # create fake observed data
        #self.observation = self.model.forward_simulate(1, np.random.RandomState(1))[0].tolist()
        self.observation = [np.array(9.8)]
       
    def test_sample(self):
        # use the SABC scheme for T = 1
        steps, epsilon, n_samples, n_samples_per_param = 1, 10, 10, 1
        sampler = SABC([self.model], self.dist_calc, self.backend, seed = 1)
        journal = sampler.sample([self.observation], steps, epsilon, n_samples, n_samples_per_param)
        mu_post_sample, sigma_post_sample, post_weights = np.array(journal.get_parameters()['mu']), np.array(journal.get_parameters()['sigma']), np.array(journal.get_weights())
          
        # Compute posterior mean
        mu_post_mean, sigma_post_mean = np.average(mu_post_sample, weights=post_weights, axis=0), np.average(sigma_post_sample, weights=post_weights, axis=0)

        # test shape of sample
        mu_sample_shape, sigma_sample_shape, weights_sample_shape = np.shape(mu_post_sample), np.shape(mu_post_sample), np.shape(post_weights)
        self.assertEqual(mu_sample_shape, (10,1))
        self.assertEqual(sigma_sample_shape, (10,1))
        self.assertEqual(weights_sample_shape, (10,1))


        # use the SABC scheme for T = 2
        steps, epsilon, n_samples, n_samples_per_param = 2, 10, 10, 1
        sampler = SABC([self.model], self.dist_calc, self.backend, seed = 1)
        journal = sampler.sample([self.observation], steps, epsilon, n_samples, n_samples_per_param)
        mu_post_sample, sigma_post_sample, post_weights = np.array(journal.get_parameters()['mu']), np.array(journal.get_parameters()['sigma']), np.array(journal.get_weights())
          
        # Compute posterior mean
        mu_post_mean, sigma_post_mean = np.average(mu_post_sample, weights=post_weights, axis=0), np.average(sigma_post_sample, weights=post_weights, axis=0)

        # test shape of sample
        mu_sample_shape, sigma_sample_shape, weights_sample_shape = np.shape(mu_post_sample), np.shape(mu_post_sample), np.shape(post_weights)
        self.assertEqual(mu_sample_shape, (10,1))
        self.assertEqual(sigma_sample_shape, (10,1))
        self.assertEqual(weights_sample_shape, (10,1))
        self.assertLess(mu_post_mean - 2.120856674879079, 10e-2)
        self.assertLess(sigma_post_mean - 6.711723792285109, 10e-2)

        self.assertFalse(journal.number_of_simulations == 0)

class ABCsubsimTests(unittest.TestCase):
    def setUp(self):
        # find spark and initialize it
        self.backend = BackendDummy()

        # define a uniform prior distribution
        mu = Uniform([[-5.0], [5.0]], name='mu')
        sigma = Uniform([[0.0], [10.0]], name='sigma')
        # define a Gaussian model
        self.model = Normal([mu, sigma])

        # define a distance function
        stat_calc = Identity(degree=2, cross=0)
        self.dist_calc = Euclidean(stat_calc)

        # create fake observed data
        #self.observation = self.model.forward_simulate(1, np.random.RandomState(1))[0].tolist()
        self.observation = [np.array(9.8)]
       
    def test_sample(self):

        # use the ABCsubsim scheme for T = 1
        steps, n_samples, n_samples_per_param = 1, 10, 1
        sampler = ABCsubsim([self.model], self.dist_calc, self.backend, seed = 1)
        journal = sampler.sample([self.observation], steps, n_samples, n_samples_per_param)
        mu_post_sample, sigma_post_sample, post_weights = np.array(journal.get_parameters()['mu']), np.array(
            journal.get_parameters()['sigma']), np.array(journal.get_weights())
          
        # Compute posterior mean
        mu_post_mean, sigma_post_mean = np.average(mu_post_sample, weights=post_weights, axis=0), np.average(sigma_post_sample, weights=post_weights, axis=0)

        # test shape of sample
        mu_sample_shape, sigma_sample_shape, weights_sample_shape = np.shape(mu_post_sample), np.shape(mu_post_sample), np.shape(post_weights)
        self.assertEqual(mu_sample_shape, (10,1))
        self.assertEqual(sigma_sample_shape, (10,1))
        self.assertEqual(weights_sample_shape, (10,1))


        # use the ABCsubsim scheme for T = 2
        steps, n_samples, n_samples_per_param = 2, 10, 1
        sampler = ABCsubsim([self.model], self.dist_calc, self.backend, seed = 1)
        sampler.sample_from_prior(rng=np.random.RandomState(1))
        journal = sampler.sample([self.observation], steps, n_samples, n_samples_per_param)
        mu_post_sample, sigma_post_sample, post_weights = np.array(journal.get_parameters()['mu']), np.array(
            journal.get_parameters()['sigma']), np.array(journal.get_weights())
          
        # Compute posterior mean
        mu_post_mean, sigma_post_mean = np.average(mu_post_sample, weights=post_weights, axis=0), np.average(sigma_post_sample, weights=post_weights, axis=0)

        # test shape of sample
        mu_sample_shape, sigma_sample_shape, weights_sample_shape = np.shape(mu_post_sample), np.shape(mu_post_sample), np.shape(post_weights)
        self.assertEqual(mu_sample_shape, (10,1))
        self.assertEqual(sigma_sample_shape, (10,1))
        self.assertEqual(weights_sample_shape, (10,1))
        self.assertLess(mu_post_mean - (-0.81410299), 10e-2)
        self.assertLess(sigma_post_mean - 5.51827908, 10e-2)

        self.assertFalse(journal.number_of_simulations == 0)


class SMCABCTests(unittest.TestCase):
    def setUp(self):
        # find spark and initialize it
        self.backend = BackendDummy()

        # define a uniform prior distribution
        mu = Uniform([[-5.0], [5.0]], name='mu')
        sigma = Uniform([[0.0], [10.0]], name='sigma')
        # define a Gaussian model
        self.model = Normal([mu, sigma])

        # define a distance function
        stat_calc = Identity(degree=2, cross=0)
        self.dist_calc = Euclidean(stat_calc)

        # create fake observed data
        #self.observation = self.model.forward_simulate(1, np.random.RandomState(1))[0].tolist()
        self.observation = [np.array(9.8)]

      
    def test_sample(self):
        # use the SMCABC scheme for T = 1
        steps, n_sample, n_simulate = 1, 10, 1
        sampler = SMCABC([self.model], self.dist_calc, self.backend, seed = 1)
        journal = sampler.sample([self.observation], steps, n_sample, n_simulate)
        mu_post_sample, sigma_post_sample, post_weights = np.array(journal.get_parameters()['mu']), np.array(
            journal.get_parameters()['sigma']), np.array(journal.get_weights())
          
        # Compute posterior mean
        mu_post_mean, sigma_post_mean = np.average(mu_post_sample, weights=post_weights, axis=0), np.average(sigma_post_sample, weights=post_weights, axis=0)

        # test shape of sample
        mu_sample_shape, sigma_sample_shape, weights_sample_shape = np.shape(mu_post_sample), np.shape(mu_post_sample), np.shape(post_weights)
        self.assertEqual(mu_sample_shape, (10,1))
        self.assertEqual(sigma_sample_shape, (10,1))
        self.assertEqual(weights_sample_shape, (10,1))

        #self.assertEqual((mu_post_mean, sigma_post_mean), (,))
        
        # use the SMCABC scheme for T = 2
        T, n_sample, n_simulate = 2, 10, 1
        sampler = SMCABC([self.model], self.dist_calc, self.backend, seed = 1)
        journal = sampler.sample([self.observation], T, n_sample, n_simulate)
        mu_post_sample, sigma_post_sample, post_weights = np.array(journal.get_parameters()['mu']), np.array(
            journal.get_parameters()['sigma']), np.array(journal.get_weights())
          
        # Compute posterior mean
        mu_post_mean, sigma_post_mean = np.average(mu_post_sample, weights=post_weights, axis=0), np.average(sigma_post_sample, weights=post_weights, axis=0)

        # test shape of sample
        mu_sample_shape, sigma_sample_shape, weights_sample_shape = np.shape(mu_post_sample), np.shape(mu_post_sample), np.shape(post_weights)
        self.assertEqual(mu_sample_shape, (10,1))
        self.assertEqual(sigma_sample_shape, (10,1))
        self.assertEqual(weights_sample_shape, (10,1))
        self.assertLess(mu_post_mean - (-0.786118677019), 10e-2)
        self.assertLess(sigma_post_mean - 4.63324738665, 10e-2)

        self.assertFalse(journal.number_of_simulations == 0)

class APMCABCTests(unittest.TestCase):
    def setUp(self):
        # find spark and initialize it
        self.backend = BackendDummy()

        # define a uniform prior distribution
        mu = Uniform([[-5.0], [5.0]], name='mu')
        sigma = Uniform([[0.0], [10.0]], name='sigma')
        # define a Gaussian model
        self.model = Normal([mu, sigma])

        # define a distance function
        stat_calc = Identity(degree=2, cross=0)
        self.dist_calc = Euclidean(stat_calc)

        # create fake observed data
        #self.observation = self.model.forward_simulate(1, np.random.RandomState(1))[0].tolist()
        self.observation = [np.array(9.8)]

      
    def test_sample(self):
        # use the APMCABC scheme for T = 1
        steps, n_sample, n_simulate = 1, 10, 1
        sampler = APMCABC([self.model], self.dist_calc, self.backend, seed = 1)
        journal = sampler.sample([self.observation], steps, n_sample, n_simulate)
        mu_post_sample, sigma_post_sample, post_weights = np.array(journal.get_parameters()['mu']), np.array(
            journal.get_parameters()['sigma']), np.array(journal.get_weights())

        # Compute posterior mean
        mu_post_mean, sigma_post_mean = np.average(mu_post_sample, weights=post_weights, axis=0), np.average(sigma_post_sample, weights=post_weights, axis=0)

        # test shape of sample
        mu_sample_shape, sigma_sample_shape, weights_sample_shape = np.shape(mu_post_sample), np.shape(mu_post_sample), np.shape(post_weights)
        self.assertEqual(mu_sample_shape, (10,1))
        self.assertEqual(sigma_sample_shape, (10,1))
        self.assertEqual(weights_sample_shape, (10,1))

        self.assertFalse(journal.number_of_simulations == 0)

        
        # use the APMCABC scheme for T = 2
        T, n_sample, n_simulate = 2, 10, 1
        sampler = APMCABC([self.model], self.dist_calc, self.backend, seed = 1)
        journal = sampler.sample([self.observation], T, n_sample, n_simulate)
        mu_post_sample, sigma_post_sample, post_weights = np.array(journal.get_parameters()['mu']), np.array(
            journal.get_parameters()['sigma']), np.array(journal.get_weights())
          
        # Compute posterior mean
        mu_post_mean, sigma_post_mean = np.average(mu_post_sample, weights=post_weights, axis=0), np.average(sigma_post_sample, weights=post_weights, axis=0)

        # test shape of sample
        mu_sample_shape, sigma_sample_shape, weights_sample_shape = np.shape(mu_post_sample), np.shape(mu_post_sample), np.shape(post_weights)
        self.assertEqual(mu_sample_shape, (10,1))
        self.assertEqual(sigma_sample_shape, (10,1))
        self.assertEqual(weights_sample_shape, (10,1))
        self.assertLess(mu_post_mean - (-2.785), 10e-2)
        self.assertLess(sigma_post_mean - 6.2058, 10e-2)

        self.assertFalse(journal.number_of_simulations == 0)

class RSMCABCTests(unittest.TestCase):
    def setUp(self):
        # find spark and initialize it
        self.backend = BackendDummy()

        # define a uniform prior distribution
        mu = Uniform([[-5.0], [5.0]], name='mu')
        sigma = Uniform([[0.0], [10.0]], name='sigma')
        # define a Gaussian model
        self.model = Normal([mu, sigma])

        # define a distance function
        stat_calc = Identity(degree=2, cross=0)
        self.dist_calc = Euclidean(stat_calc)

        # create fake observed data
        #self.observation = self.model.forward_simulate(1, np.random.RandomState(1))[0].tolist()
        self.observation = [np.array(9.8)]

      
    def test_sample(self):
        # use the RSMCABC scheme for T = 1
        steps, n_sample, n_simulate = 1, 10, 1
        sampler = RSMCABC([self.model], self.dist_calc, self.backend, seed = 1)
        journal = sampler.sample([self.observation], steps, n_sample, n_simulate)
        mu_post_sample, sigma_post_sample, post_weights = np.array(journal.get_parameters()['mu']), np.array(
            journal.get_parameters()['sigma']), np.array(journal.get_weights())
          
        # Compute posterior mean
        mu_post_mean, sigma_post_mean = np.average(mu_post_sample, weights=post_weights, axis=0), np.average(sigma_post_sample, weights=post_weights, axis=0)

        # test shape of sample
        mu_sample_shape, sigma_sample_shape, weights_sample_shape = np.shape(mu_post_sample), np.shape(mu_post_sample), np.shape(post_weights)
        self.assertEqual(mu_sample_shape, (10,1))
        self.assertEqual(sigma_sample_shape, (10,1))
        self.assertEqual(weights_sample_shape, (10,1))

        self.assertFalse(journal.number_of_simulations == 0)

        #self.assertEqual((mu_post_mean, sigma_post_mean), (,))
        
        # use the RSMCABC scheme for T = 2
        steps, n_sample, n_simulate = 2, 10, 1
        sampler = RSMCABC([self.model], self.dist_calc, self.backend, seed = 1)
        journal = sampler.sample([self.observation], steps, n_sample, n_simulate)
        sampler.sample_from_prior(rng=np.random.RandomState(1))
        mu_post_sample, sigma_post_sample, post_weights = np.array(journal.get_parameters()['mu']), np.array(
            journal.get_parameters()['sigma']), np.array(journal.get_weights())
          
        # Compute posterior mean
        mu_post_mean, sigma_post_mean = np.average(mu_post_sample, weights=post_weights, axis=0), np.average(sigma_post_sample, weights=post_weights, axis=0)

        # test shape of sample
        mu_sample_shape, sigma_sample_shape, weights_sample_shape = np.shape(mu_post_sample), np.shape(mu_post_sample), np.shape(post_weights)
        self.assertEqual(mu_sample_shape, (10,1))
        self.assertEqual(sigma_sample_shape, (10,1))
        self.assertEqual(weights_sample_shape, (10,1))
        self.assertLess(mu_post_mean - (1.52651600439), 10e-2)
        self.assertLess(sigma_post_mean - 6.49994754262, 10e-2)

        self.assertFalse(journal.number_of_simulations == 0)

if __name__ == '__main__':
    unittest.main()
