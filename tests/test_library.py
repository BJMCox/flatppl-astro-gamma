"""Independent quadrature, coordinate-Jacobian, and count-PMF checks."""
import json
import math
import subprocess
import unittest
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from scipy.stats import gamma, poisson

ROOT = Path(__file__).resolve().parents[1]


def decode(value):
    if isinstance(value, dict) and 'shape' in value:
        data = value['data']
        return np.asarray(list(data.values()) if isinstance(data, dict) else data).reshape(value['shape'])
    return value


def evaluate(request):
    result = subprocess.run(['node', str(ROOT / 'tests/evaluate.cjs')], input=json.dumps(request), text=True, capture_output=True, check=True)
    return list(map(decode, json.loads(result.stdout)))


class LibraryTests(unittest.TestCase):
    def test_spectral_conventions(self):
        energy, amplitude, index, curvature, reference = 3.0, 2.0, 2.3, 0.2, 1.4
        x = math.log(energy / reference)
        actual = evaluate([
            f'a.powerlaw({energy},{amplitude},{index},{reference})',
            f'a.logparabola({energy},{amplitude},{index},{curvature},{reference})',
            f'a.cutoff_powerlaw({energy},{amplitude},{index},4.0,1.3,{reference})',
            f'a.cutoff_powerlaw({reference},{amplitude},{index},4.0,1.3,{reference})',
            'a.ebl_transmission(0.7,0.8)',
        ])
        expected = [amplitude * (energy/reference)**(-index), amplitude * math.exp(-index*x-curvature*x*x), amplitude * math.exp(-index*x-(energy/4)**1.3+(reference/4)**1.3), amplitude, math.exp(-0.7*0.8)]
        np.testing.assert_allclose(actual, expected, rtol=3e-14)

    def test_integrals_against_quadrature(self):
        calls, expected = [], []
        for moment, name in [(0, 'photon'), (1, 'energy')]:
            # Exact logarithmic limit, both nearby sides, and the non-series path.
            for index in [moment+1, moment+1-1e-10, moment+1+1e-10, 2.7]:
                calls.append(f'a.powerlaw_{name}_integral(0.13,8.0,2.1,{index},1.7)')
                expected.append(quad(lambda e: e**moment * 2.1 * (e/1.7)**(-index), 0.13, 8.0, epsabs=1e-10, epsrel=2e-13)[0])
        np.testing.assert_allclose(evaluate(calls), expected, rtol=8e-14)
        np.testing.assert_equal(evaluate(['a.powerlaw_photon_integral(1,1,2,1,1)', 'a.powerlaw_energy_integral(1,1,0,2,1)']), [0, 0])
        # Adjacent floating-point bounds must retain their represented width.
        lower = 1.7
        upper = math.nextafter(lower, math.inf)
        expected = 2.1 * (lower/1.3)**(-2.7) * (upper-lower)
        actual = evaluate([f'a.powerlaw_photon_integral({lower},{upper},2.1,2.7,1.3)'])[0]
        np.testing.assert_allclose(actual, expected, rtol=2e-15, atol=0)


    def test_response_and_losses(self):
        actual = evaluate(['a.fold_spectrum(rowstack([[0.7,0.2,0],[0.1,0.6,0.7]]),[1,2,3],[1,2,3],[0.5,1,2],4)'])[0]
        migration = np.array([[0.7,0.2,0],[0.1,0.6,0.7]])
        incident = 4 * np.array([1,2,3])**2 * [0.5,1,2]
        np.testing.assert_allclose(actual, migration @ incident, rtol=2e-15)
        self.assertAlmostEqual(sum(actual), np.dot(migration.sum(axis=0), incident))
        self.assertLess(sum(actual), sum(incident))

    def test_quadrature_refinement(self):
        calls, expected = [], 2.0 * (1/0.5 - 1/4.0)
        for n in [8, 32, 128]:
            edges = np.linspace(0.5, 4.0, n+1)
            nodes, widths = (edges[1:]+edges[:-1])/2, np.diff(edges)
            calls.append(f'a.fold_spectrum(rowstack([{json.dumps([1.0]*n)}]),{json.dumps([1.0]*n)},a.powerlaw.({json.dumps(nodes.tolist())},2.0,2.0,1.0),{json.dumps(widths.tolist())},1.0)[1]')
        errors = abs(np.asarray(evaluate(calls)) - expected)
        self.assertTrue(np.all(errors[1:] < errors[:-1]/10))
        self.assertLess(errors[-1], 0.001)

    def test_coordinate_jacobians(self):
        # Uniform migration density 2 on [0.5,1] at E=3; transformed energy
        # density is 2/3 on [1.5,3], so both bin probabilities equal 0.6.
        energy_density, scaled_density = evaluate(['a.migration_density_to_energy_density(2.0,3.0)', 'a.energy_scale_density(0.5,1.25)'])
        self.assertAlmostEqual(energy_density * (2.7-1.8), 2*(0.9-0.6))
        # Uniform nominal D=0.5 on [0,2], measured D_g=0.4 on [0,2.5].
        self.assertAlmostEqual(scaled_density * (2.0-0.5), 0.5 * (2.0/1.25-0.5/1.25))

    def test_synthetic_observation(self):
        source = 'flatppl_compat = "0.1"\ne = load_module("../examples/synthetic-onoff.flatppl")\ns = e.source_counts\nl = e.log_likelihood_point\np = e.log_posterior_point\n'
        actual = evaluate({'source': source, 'bindings': ['s','l','p']})
        flux = 1e-8 * np.array([0.5,1,2])**(-2) * np.exp(-0.8*np.array([0.05,0.2,0.5]))
        signal = 1e4 * np.array([[0.7,0.2,0],[0.1,0.6,0.7]]) @ (np.array([1e5,2e5,3e5])*flux*[0.5,0.75,1])
        loglik = sum(poisson.logpmf([7,8], signal+[2,3])) + sum(poisson.logpmf([8,12], [8,12]))
        logpost = loglik + gamma.logpdf(1e-8, a=2, scale=1/2e8)
        np.testing.assert_allclose(actual[0], signal, rtol=3e-14)
        np.testing.assert_allclose(actual[1:], [loglik, logpost], rtol=3e-14)


if __name__ == '__main__':
    unittest.main(verbosity=2)
