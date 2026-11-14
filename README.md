# flatppl-astro-gamma

[Function reference](docs/reference.md) · [Live example](https://live.flatppl.org/#model=https%3A%2F%2Fraw.githubusercontent.com%2Fflatppl-community%2Fflatppl-astro-gamma%2Fmain%2Fexamples%2Fplayground.flatppl&target=Pi_post)

Gamma-ray photon spectra, EBL attenuation, response-folded source counts, and density-coordinate Jacobians for FlatPPL. Library version **0.1**.

```flatppl
flatppl_compat = "0.1"
gamma = load_module("flatppl-astro-gamma/main.flatppl")
flux = gamma.logparabola(2.0, 1e-8, 2.2, 0.1, 1.0)
photon_flux = gamma.powerlaw_photon_integral(0.5, 5.0, 1e-8, 2.2, 1.0)
```

Spectral amplitude denotes differential flux at the reference energy. Curvature uses natural logarithms. Response rows index reconstructed bins. Columns index true-energy quadrature nodes. Response losses remain explicit.

The [synthetic ON/OFF example](examples/synthetic-onoff.flatppl) combines a supplied response, an explicit amplitude prior, and a count likelihood. It does not reproduce MAGIC data.

See the reference for definitions, domains, numerical limits, and validation commands.
