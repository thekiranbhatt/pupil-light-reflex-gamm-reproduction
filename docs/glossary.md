# Glossary

**Pupillary light reflex (PLR).** The automatic narrowing of the pupil when light reaches the eye, followed by a slow widening again once the light is gone.

**Constriction / redilation.** Narrowing / widening of the pupil.

**Proportional pupil change (PPC).** Pupil size expressed relative to the size just before the flash. 0 means unchanged, -0.1 means 10% smaller. Using a proportion lets people with naturally larger or smaller pupils be compared.

**Baseline.** The pupil size just before the flash (here the 100 milliseconds before it). Everything is measured against it.

**Sensory processing traits.** How people tend to notice and react to everyday sensations, measured by questionnaire. The paper uses the Adolescent/Adult Sensory Profile, with four types: Low Registration, Sensation Seeking, Sensory Sensitivity and Sensation Avoiding. They combine into two axes: how low a person's threshold for noticing is (LowTh) and how actively they respond (Active).

**Waveform.** The whole curve of pupil size over time, as opposed to a single number such as the lowest point.

**Split-half reliability.** A check on how consistent a measurement is. Split a person's trials into two halves, average each half, and see whether people who score high in one half also score high in the other. A value near 1 means very consistent.

**Spearman-Brown correction.** A formula that adjusts a half-versus-half correlation to estimate the consistency of the full set of trials.

**GAMM (generalized additive mixed model).** A statistical model that can fit curves of any smooth shape instead of straight lines, and that handles repeated measurements from the same people.

**Smooth.** One of those flexible curves inside the model.

**`ti` term (tensor interaction).** A model term that lets a curve over time change depending on another variable, here a trait score. This is how the paper tests whether the *shape* of the response varies with a trait.

**Effective degrees of freedom (edf).** How wiggly the model's fitted curve ended up being. 1 is a straight line; larger numbers are wigglier.

**AR(1) / rho.** A correction for the fact that each measurement is very similar to the one before it. Rho close to 1 means they are almost identical. Without the correction, the model would be overconfident.

**Random effects.** Terms that give each person their own baseline or curve shape, so that differences between people are not mistaken for effects of the traits.

**95% confidence band.** The shaded area around a predicted curve. If the study were repeated many times, about 95% of such bands would contain the true curve.

**Melanopic DER.** How strongly a light stimulates melanopsin, a light-sensitive pigment in certain cells of the eye that contribute to the pupil response, compared with a standard reference light.

**cd/m².** Candela per square metre, a unit of brightness.
