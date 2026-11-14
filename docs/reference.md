# Gamma-ray astronomy reference

Library version **0.1** · [Package overview](../README.md)

Load `main.flatppl` and call these fields. Scalar spectrum functions may be
broadcast explicitly with `f.(...)`. All energies share one positive energy unit;
amplitude has differential photon-flux units (inverse area, time, and energy).
Inputs must lie in the domains below; the library does not clip, extrapolate,
renormalize responses, or insert priors. Scalar/array coordinate helpers use
positional broadcasting; callers must align the axes explicitly.

| Function | Purpose |
|---|---|
| [`powerlaw`](#powerlaw) | Reference-amplitude power law |
| [`logparabola`](#logparabola) | Natural-log curvature |
| [`cutoff_powerlaw`](#cutoff_powerlaw) | Reference-normalized exponential cutoff |
| [`powerlaw_photon_integral`](#powerlaw_photon_integral) | Analytic photon flux, including index 1 |
| [`powerlaw_energy_integral`](#powerlaw_energy_integral) | Analytic energy flux, including index 2 |
| [`ebl_transmission`](#ebl_transmission) | Optical-depth attenuation |
| [`fold_spectrum`](#fold_spectrum) | True-energy flux to reconstructed-bin counts |
| [`migration_density_to_energy_density`](#migration_density_to_energy_density) | Migration-coordinate Jacobian |
| [`energy_scale_density`](#energy_scale_density) | Reconstructed-energy scale Jacobian |

<a id="powerlaw"></a>
## `powerlaw(energy, amplitude, index, reference_energy)`

For positive `energy` E and `reference_energy` E0, nonnegative `amplitude` N0,
and real `index` gamma, return the scalar differential photon flux:

```math
\phi(E)=N_0\exp[-\gamma\ln(E/E_0)].
```

In particular, `powerlaw(E0,N0,gamma,E0)` returns N0. There is no normalization
over a chosen energy interval.

<a id="logparabola"></a>
## `logparabola(energy, amplitude, index, curvature, reference_energy)`

Arguments have the same domains as `powerlaw`; `curvature` beta is real. Return
scalar differential photon flux, with x the natural logarithm:

```math
x=\ln(E/E_0),\qquad \phi(E)=N_0\exp[-\gamma x-\beta x^2].
```

For a convention written `(E/E0)^(-gamma-b*log10(E/E0))`, supply
`curvature = b/log(10)`. Positive beta gives downward log-log curvature;
nonnegative curvature is a caller's physical assumption, not a library prior.

<a id="cutoff_powerlaw"></a>
## `cutoff_powerlaw(energy, amplitude, index, cutoff_energy, cutoff_power, reference_energy)`

`energy` E, `reference_energy` E0, `cutoff_energy` Ec, and `cutoff_power` kappa
must be positive; `amplitude` N0 is nonnegative and `index` gamma is real.
Return scalar differential photon flux:

```math
\phi(E)=N_0\exp[-\gamma\ln(E/E_0)-(E/E_c)^\kappa+(E_0/E_c)^\kappa].
```

The final term preserves `phi(E0)=N0`. A cutoff formula omitting that term uses a
different amplitude convention.

<a id="powerlaw_photon_integral"></a>
## `powerlaw_photon_integral(lower_energy, upper_energy, amplitude, index, reference_energy)`

`lower_energy` L and `upper_energy` U obey `0 < L <= U`. Other arguments have
the `powerlaw` domains. Return integrated photon flux (inverse area and time):

```math
\begin{aligned}
I_{\rm ph}&=\int_L^U \phi(E)\,dE\\
&=N_0 L (L/E_0)^{-\gamma}\ell\,R((1-\gamma)\ell),\qquad
\ell=\ln(U/L),\\
R(z)&=\frac{\exp(z)-1}{z},\qquad R(0)=1.
\end{aligned}
```

At index 1 the result is `N0*E0*log(U/L)`. The implementation evaluates the log span with `log1p((U-L)/L)` to retain
narrow represented intervals. It uses `expm1` away from zero and a fifth-degree series near zero, with a guarded inactive
denominator. Values and automatic derivatives stay finite at the logarithmic
limit. Equal bounds and zero amplitude return zero. Bounds describe a finite
interval; no infinite-domain convergence convention is supplied.

<a id="powerlaw_energy_integral"></a>
## `powerlaw_energy_integral(lower_energy, upper_energy, amplitude, index, reference_energy)`

Arguments have the same domains as the photon integral. Return integrated
energy flux (energy per area and time):

```math
I_{\rm en}=\int_L^U E\phi(E)\,dE
=N_0 L^2(L/E_0)^{-\gamma}\ell\,R((2-\gamma)\ell).
```

At index 2 the result is `N0*E0^2*log(U/L)`. The stable evaluation and finite
limiting derivatives use the same R as the photon integral. Convert the energy
unit explicitly if another output unit is required.

<a id="ebl_transmission"></a>
## `ebl_transmission(optical_depth, scale)`

`optical_depth` tau is a nonnegative dimensionless optical depth evaluated at
the relevant true energy and redshift; `scale` a is nonnegative and dimensionless.
Return the scalar dimensionless transmission:

```math
T=\exp(-a\tau),\qquad \phi_{\rm observed}=T\phi_{\rm intrinsic}.
```

Apply transmission before response folding. The caller supplies and identifies
the EBL model/grid and any interpolation; inferred redshift requires an explicit
interpolation domain. A fitted attenuation strength can be degenerate with
intrinsic curvature or cutoff parameters.

<a id="fold_spectrum"></a>
## `fold_spectrum(migration_probabilities, effective_area, flux, quadrature_weights, exposure)`

`migration_probabilities` M has shape `[M,N]`: reconstructed-bin probabilities
as rows, true-energy quadrature nodes as columns. Entries are nonnegative and
each column sums to at most one. `effective_area` A and differential photon
`flux` phi are nonnegative `[N]` vectors; positive `quadrature_weights` q `[N]`
have energy units. `exposure` t is nonnegative live time. Return `[M]` expected
source counts by importing the shared `project` operation:

```math
s_j=t\sum_i M_{ji}A_i\phi_i q_i.
```

Keep response loss outside retained bins. M contains integrated reconstructed-bin
probabilities, not a density; no reconstructed-bin width is applied here.
Already integrated true-bin flux must not receive quadrature weights again.
Responses that already contain area or exposure likewise must not receive these
factors twice. Match the response selection, directional cut, live-time convention,
and observing conditions to the counts. For sky intensity, integrate solid angle
explicitly before using this scalar point-source convention.

<a id="migration_density_to_energy_density"></a>
## `migration_density_to_energy_density(density, true_energy)`

`density` is a nonnegative density in dimensionless migration `m=E_reco/E_true`,
evaluated at the desired migration coordinate. `true_energy` E is positive.
Return the corresponding reconstructed-energy density, scalar or broadcast array:

```math
D_{E'}(E'\mid E)=\frac{D_m(E'/E\mid E)}{E}.
```

The caller evaluates the density at `m=E_reco/E_true` first and aligns true-energy
axes. Integrating this result over reconstructed-bin energy produces migration
probabilities for `fold_spectrum`; the helper itself does not integrate bins.

<a id="energy_scale_density"></a>
## `energy_scale_density(density_at_scaled_coordinate, scale)`

For positive scalar `scale` g and nonnegative nominal response density already
evaluated at `E_reco/g`, return a scalar/array measured-energy density:

```math
E'_{\rm measured}=gE'_{\rm nominal},\qquad
D_g(E'\mid E)=\frac{D_0(E'/g\mid E)}{g}.
```

The coordinate evaluation and density Jacobian are both necessary. Keep measured
bin edges fixed and reintegrate across them, including selection changes. This
helper does not shift coordinates or change the bin selection on the caller's
behalf, and does not claim to reproduce a complete instrument recalibration.

## Synthetic example contract

[synthetic-onoff.flatppl](../examples/synthetic-onoff.flatppl) uses an invented
three-node, two-bin response. Its data are ON `[7,8]`, OFF `[8,12]`, ON-background
means `[2,3]`, and OFF/ON exposure ratio 4. The response retains losses. At amplitude
`1e-8`, index 2, reference energy 1 TeV, and EBL scale 0.8, its outputs are:

| Binding | Value |
|---|---|
| `source_counts` | `[16.007483515031158, 13.110053220687654]` |
| `log_likelihood_point` | `-14.913646304612053` |
| `log_posterior_point` | `2.8933288004602016` |

The count law is the product of two shared `counts.onoff` laws, retaining both
Poisson factorial constants. Conditional independence assumes disjoint ON/OFF
events and independent bins. The explicit amplitude prior is Gamma(shape 2, rate
`2e8`), with mean `1e-8`; backgrounds and all other physical parameters are fixed
inputs. `posterior` conditions the joint stochastic model on the stated counts.
`log_posterior_point` is the unnormalized posterior log density (likelihood plus
prior log density), not a log evidence or a normalized posterior density.
No public-data reproduction, parameter recovery, or coverage claim is made.

## Examples and validation

See the [function reference](reference.md) and the runnable
[synthetic ON/OFF example](../examples/synthetic-onoff.flatppl), which exposes source
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
only the in-memory test bundle. [tests/runtime.flatppl](../tests/runtime.flatppl)
exposes `inputs` and `outputs` for compiled values, derivatives, and batching;
[tests/runtime_oracle.py](../tests/runtime_oracle.py) supplies independent SciPy
integrals and analytic Jacobians, including both logarithmic integral limits.
