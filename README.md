# flatppl-astro-gamma

Version **0.1**. FlatPPL functions for gamma-ray photon spectra, EBL attenuation,
response-folded source counts, and density-coordinate Jacobians.

Run the [posterior example](https://live.flatppl.org/#model=https%3A%2F%2Fraw.githubusercontent.com%2Fflatppl-community%2Fflatppl-astro-gamma%2Fmain%2Fexamples%2Fplayground.flatppl&target=Pi_post) in the live playground. It loads its library modules from GitHub.

```flatppl
flatppl_compat = "0.1"
gamma = load_module("flatppl-astro-gamma/main.flatppl")
flux = gamma.logparabola(2.0, 1e-8, 2.2, 0.1, 1.0)
photon_flux = gamma.powerlaw_photon_integral(0.5, 5.0, 1e-8, 2.2, 1.0)
```

See the [function reference](docs/reference.md) and the runnable
[synthetic ON/OFF example](examples/synthetic-onoff.flatppl), which exposes source
counts, a joint count law, an explicit amplitude prior, and an unnormalized posterior.
Its invented response is **synthetic**; it is not a reproduction of public MAGIC data.

Spectral amplitude is the differential flux at the reference energy. Curvature
uses natural logarithms. Folding imports `project` from
[flatppl-stats-templates](https://github.com/flatppl-community/flatppl-stats-templates);
the example imports the ON/OFF law from
[flatppl-stats-counts](https://github.com/flatppl-community/flatppl-stats-counts).
Neither library supplies an implicit prior. Source dependencies use commit-pinned URLs.

Response rows are retained reconstructed bins; columns are true-energy quadrature
nodes. Columns may sum to less than one. Supply reconstructed-bin probabilities,
positive true-energy weights, effective area, and live time once each. Apply EBL on
the true-energy grid before folding. Do not add another PSF-containment factor to an
area response that already includes the directional cut. Area and time must use
compatible dead-time conventions. This version supplies numeric formulas and does
not parse FITS, choose a cosmology/EBL table, or run an optimizer or sampler.

Run the independent NumPy/SciPy checks with an existing Python environment:

```sh
FLATPPL_JS_DIR=/path/to/flatppl-js python tests/test_library.py
```

The tests use the JS engine's module loader and worker density evaluator. Optional
`FLATPPL_STATS_TEMPLATES_DIR` and `FLATPPL_STATS_COUNTS_DIR` checkout overrides alter
only the in-memory test bundle. [tests/runtime.flatppl](tests/runtime.flatppl)
exposes `inputs` and `outputs` for compiled values, derivatives, and batching;
[tests/runtime_oracle.py](tests/runtime_oracle.py) supplies independent SciPy
integrals and analytic Jacobians, including both logarithmic integral limits.
