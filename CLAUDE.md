# CLAUDE.md: GPU-accelerated MoM solver and NCC 2027 paper

Started as the handoff from a claude.ai planning session (Sept to Oct 2026), then
updated on 2026-10-08 after a working session that rewrote Fig. 5, fixed the layout,
cut down Section II, and reviewed the whole paper.
Read the whole file before doing anything. Section 4 has the current paper state and
section 5 has the open items, ordered by priority.

---

## 1. Hard rules

1. **Never invent numbers.** Every timing, notch frequency, substrate parameter, iteration
   count, error percentage and S11 curve must come from one of these:
   - the user's data or CST exports,
   - the solver code,
   - a run that actually happened.

   If a value is missing, leave `\XX` in the paper and add it to the open-inputs list you
   report to the user. This includes MoM curves: never synthesize or "approximate" solver
   output, even if the user asks because the code is unavailable at the moment. Offer
   `\XX` placeholders, a script that is ready for the real data, or an honest fallback
   (drop the geometry, or keep the old one and state its mismatch) instead.
2. **The solver is not open source** and will not be released. Never describe it as open
   source or promise a code release. The PS report draft says "open-source" in a few
   places; that is wrong, so don't copy it.
3. **Double-blind review.** The paper must not identify the authors, in the text, figure
   titles, legends, embedded file paths, PDF metadata, or visible placeholder text. That
   rules out:
   - author names and supervisor names,
   - CSIR-NAL / NAL, BITS Pilani,
   - "internship", "Practice School", "PS report", "report Fig. x",
   - cluster or machine hostnames,
   - internal dataset names such as "class 5 #253" or "CST catalog",
   - anything else identifying.

   Cite Joy et al. (2021) in the third person like any other paper. The Acknowledgment
   stays commented out until the camera-ready version.
4. **Format:** IEEEtran `[10pt,conference]`, at most **6 pages including references**.
   Do not modify `IEEEtran.cls`.
5. **The code is the source of truth for the method.** If the paper and the code disagree
   (sign convention, basis, harmonics, precision):
   - change the paper to match the code and tell the user;
   - never change solver numerics just to match the paper, or without the user's okay.
6. **References:** none of the 13 entries has been verified against a real source yet.
   Check authors, title, venue, volume, pages and year before submission. Don't add
   references you cannot verify.
7. **Style:** follow section 7. In short:
   - no em dashes anywhere (no `---` in LaTeX prose, no `—`);
   - human-sounding prose in the IEEE formal register;
   - American spelling.
8. **Abstract and introduction wording** was written or approved by the user. Only fill in
   values or fix factual errors there, and ask before changing anything else. (The intro
   gap sentence was softened on 2026-10-08 with the user's explicit approval.)
9. **Preview before replacing figures.** When the user asks for a new or changed figure,
   show it for review first (a Lavish page with old vs new, the numbers behind it and the
   exact .tex diff), and replace the file only after approval. Keep the old figure as
   `<name>_old.pdf`.
10. **Verify the layout before presenting.** After any change that can move floats,
    recompile and look at every rendered page. Check that figures and tables come before
    the Conclusion, that there are no stray text fragments or half-empty float pages,
    and that the last page is balanced.

---

## 2. Project background (context only, never goes in the paper)

- **Who:** Abhigyan Kumar Singh, MSc Physics + B.E. Mechanical at BITS Pilani.
  - Practice School II internship at CSIR-NAL (Computational Electromagnetics Division),
    Bangalore, Jul to Dec 2026.
  - Expert/supervisor: Vineetha Joy (Scientist). The author list and acknowledgment for
    the camera-ready version are the user's decision.
- **Application:** radar-absorbing metasurfaces / frequency selective surfaces.
  - Unit cell: 10 x 10 mm, a copper (or resistive) pattern on a dielectric substrate over
    a PEC ground, optionally with a superstrate.
  - Absorption appears as notches in S11(f). The PEC ground means no transmission, so
    absorption = 1 - |S11|^2.
- **End goal:** generate large S11 datasets for AI/ML surrogate and inverse-design models.
  The solver also serves as an independent physics check on ML predictions.
- **Reference solver:** CST Studio Suite, frequency-domain FEM, with unit-cell periodic
  boundaries and Floquet ports.
- **History:**
  1. CST reference simulations for several patterns.
  2. Tried open-source solvers to reproduce CST:
     - openEMS (FDTD) failed mainly because it has no direct Floquet-port equivalent.
     - RCWA packages (grcwa, torcwa) also did not match.
  3. Built a custom spectral-domain MoM in Python, then extended it to multi-GPU HPC.
  - Lessons learned: port definitions are a dominant, non-obvious source of mismatch
    between solvers; debug with the simplest geometry first and change one variable at a
    time.
- **The user works partly from home, where the solver code is NOT available.** Anything
  that needs a solver run or a code check has to wait until they are back at the
  institute machines. Prepare scripts and `\XX` placeholders so the update is quick once
  the data arrives.
- **Other deliverables, done outside Claude Code:** PS-II report draft (`DRAFT.pdf`,
  28 Sep 2026), 10-minute progress deck, weekly internship diary (claude.ai only).

---

## 3. Solver summary (as stated in the paper; code not available in this folder)

### Physics model (paper Section II)

- Patterned zero-thickness sheet at z = 0 with surface impedance Zs: 0 for PEC,
  (1+j)sqrt(w*mu0/(2*sigma)) for copper (sigma = 5.8e7 S/m), or a real sheet resistance Rs.
  Substrate (eps_r, tan_delta, h), eps_c = eps_r(1 - j tan_delta), PEC ground at z = -h,
  y-polarized plane wave at normal incidence, e^{jwt} convention.
- Bare slab as a short-circuited line: Zin = j(eta0/sqrt(eps_c)) tan(k0 sqrt(eps_c) h),
  Gamma_bare = (Zin - eta0)/(Zin + eta0), E_bare = (1 + Gamma_bare) E0 y.
- Impedance boundary condition on the metal: E_bare + E_s[J] = Zs J.
- Floquet harmonics at normal incidence: kxm = 2*pi*m/a, kyn = 2*pi*n/b,
  kt^2 = kxm^2 + kyn^2, kzi = sqrt(eps_r,i k0^2 - kt^2) with Im(kz) <= 0
  (Re(kz) >= 0 when real).
- Modal Green's function (paper Eq. 4): G^a = 1/(Y0^a - j Y1^a cot(kz1 h)), with
  Y^TE = kz/(w mu0) and Y^TM = w eps0 eps_r/kz. A superstrate (same eps_c and h) replaces
  Y0^a with its looking-up admittance and adds a scalar factor T_scat in S11.
  **Sign is unresolved, see section 5.**
- Cartesian dyad (paper Eq. 5) checked by hand: correct TM/TE projections, reduces to
  G^TE * I at kt = 0 (G^TE = G^TM there, verified).
- Rooftop basis on a uniform N x N grid (N = 120, Delta = 83.3 um). x-rooftop transform:
  Delta^2 sinc^2(kx Delta/2) sinc(ky Delta/2) e^{j(kx xp + ky yp)}. Galerkin testing gives
  A I = v with A = Zs T - Z, Z_pq = (1/ab) sum F_p^* . G F_q, T = Gram matrix,
  v_p = <f_p, E_bare>.
- S11 = Gamma_bare + (T_scat/(E0 a b)) y . G(0,0) J(0,0), referenced at z = 0. Only
  co-polarized reflection is computed; a constant phase offset vs the CST port may remain
  and does not affect |S11|.

### Numerics (paper Section III)

- Matrix-free FFT matvec (Algorithm 1): scatter onto the grid -> FFT2 -> multiply by
  spectral kernels K_uv = (1/ab) F^{u*} G_uv F^v -> IFFT2 -> gather on metal edges. The
  FFT grid is M = N. Harmonics beyond N/2 are folded in by aliasing (no separate
  truncation).
- GMRES: restart 80, two-pass classical Gram-Schmidt, left Jacobi preconditioner (spectral
  diagonal of G plus the rooftop Gram diagonal).
  - GPU: complex64, rtol 5e-4 (complex64 stalls near 1e-5).
  - CPU reference: NumPy/SciPy, complex128, rtol 1e-8.
  - Warm start from the previous frequency (linear extrapolation of the last two solutions
    when the previous solve was cheap). If the iteration cap is hit with residual > 1e-3,
    the last iterate is kept and the frequency is logged.
- PyTorch with cuFFT. All data stay on the GPU; the only per-frequency transfer is S11.
- Multi-GPU: contiguous frequency blocks (`numpy.array_split`), no inter-GPU
  communication. Batching several frequencies into one GMRES launch is possible on a big
  GPU; T1000 runs use batch size 1.
- Memory figures (re-checked): a dense complex128 Z at N_u = 28,800 is 13.3 GB; the Krylov
  basis is 81 N_u complex64 = 18.7 MB; FFT grids plus kernels are about 0.8 MB in
  complex64 (the paper says "about 1 MB").

### Code checklist (status after 2026-10-08)

- [ ] **Overall sign of G:** open, the highest-priority code check (section 5).
- [x] Floquet harmonics: aliasing on an M = N FFT grid.
- [x] PEC / Cu SIBC / resistive Rs as above.
- [x] PyTorch + cuFFT, complex64 on GPU; NumPy/SciPy complex128 on CPU.
- [x] GMRES details as above. (Own implementation or library: not stated anywhere yet.)
- [x] Frequency-to-GPU: contiguous blocks.
- [ ] Multi-GPU launch mechanism (processes, mpi4py, Ray, SLURM, ...): not stated.
- [x] Sinc factors enter through the kernels K_uv.
- [x] Reference plane z = 0, co-pol only.
- [ ] CST mesh settings and CST hardware: missing.

---

## 4. Paper status (as of 2026-10-08)

### Venue, files and build

- **Venue:** IEEE NCC 2027, IISc Bangalore, 17 to 20 Feb 2027. Six pages, double-blind,
  IEEEtran. The submission deadline and track are not recorded here; check the CFP.
- **Main file:** `ncc2027-example.tex` in the folder root (not `paper/...`). It compiles
  to **5 pages** with no errors, no undefined references and no overfull boxes. The only
  warning is an underfull line in the CST reference URL, which is cosmetic.
- **Build:** there is no TeX on the WSL side. Use Windows MiKTeX from WSL:
  `(cd "/mnt/d/conference_paper v3" && pdflatex.exe -interaction=nonstopmode -synctex=1 ncc2027-example.tex)`,
  run twice. The binaries are in `D:\LaTeX\MiKTeX\miktex\bin\x64\` (`latexmk.exe` too).
  The folder name has a space, so always quote it.
- **Title (current):** Development of a GPU-Accelerated Method of Moments Solver for EM
  Analysis of Metasurfaces. The review suggested a stronger and more accurately scoped
  title (grounded absorbers, normal incidence); the user has not decided.
- **Drafting macros** `\todo`, `\XX`, `\figbox` are still defined in the preamble and must
  be removed before submission.
- **Preamble additions** (deliberate): `placeins` (`\FloatBarrier`), `balance` (last-page
  column balancing), tightened float spacing, and top-aligned float pages (`\@fptop`,
  `\@dblfptop` = 0pt).

### Folder contents

```
CLAUDE.md
ncc2027-example.tex / .pdf     main paper (+ .aux .log .synctex.gz)
IEEEtran.cls + *.sty           class and style files (do not modify IEEEtran.cls)
fig_validation.pdf             Fig. 3, four panels |S11| CST vs MoM (matplotlib)
fig_conv.pdf                   Fig. 4, GMRES iterations vs frequency, G1 (matplotlib)
fig_scaling.pdf                Fig. 5, projected 1000-sweep time (new, 2026-10-08)
fig_scaling_old.pdf            previous Fig. 5, per-geometry grouped bars (backup)
scripts/make_fig_scaling.py    builds Fig. 5 from Data/time comparison.xlsx
Data/Class 5|8|9|19/           CST exports (+ pattern .dxf/.png) per geometry
Data/time comparison.xlsx      per-sweep times: Class, CST (s), CPU (s), HPC (s)
A Python-Native ... .docx      Word version of the paper (not kept in sync)
```

There is no solver code, MoM S11 data, or script for Figs. 3 and 4 in this folder.

### CST export format (`Data/Class N/*.csv`)

There is one comma-separated row: 9 parameter fields, then 201 linear |S11| values for
2 to 18 GHz. The meaning of the parameter fields was inferred from matching them against
Table III; the user has not confirmed it:
`class, eps_r, mu_r(=1), tan_delta, (0), h_mm, resistive_flag, superstrate_flag, R_s(ohm/sq)`.
For example, Class 8 is `8,3.54,1,0.0033,0,3.048,1,0,50`, a 50 ohm/sq resistive sheet in
air.

### Geometries (Table III)

| Paper | CST class | Type | eps_r | tan_d | h (mm) | Above | Conductor | N_u (N=120) |
|---|---|---|---|---|---|---|---|---|
| G1 | 5 #253 | narrowband | 3.45 | 0.0025 | 0.762 | air | Cu SIBC | 1,350 |
| G2 | 8 #424 | moderate WB | 3.54 | 0.0033 | 3.048 | air | 50 ohm/sq | 12,960 |
| G3 | 9 #82 | multi-notch | 2.94 | 0.0021 | 3.05 | superstrate | Cu SIBC | 1,106 |
| G4 | 19 #100 | ultra WB | 2.6 | 0.0013 | 3.175 | superstrate | 40 ohm/sq | 19,752 |

**G4 is being replaced.** `Data/Class 19/Ultra_Wideband.csv` now holds a different
design: pattern `40_img.dxf`, eps_r 10.2, tan_d 0.0023, h 1.27 mm, no superstrate, no
resistive sheet (so presumably copper). Its CST curve has four sharp notches, the deepest
about -13.5 dB near 17.6 GHz. The user did not record the MoM run for it, so the paper
still shows the old G4. See section 5.

### Results currently in the paper (all derived values re-checked 2026-10-08)

- Validation (Table IV), N = 120, delta-f = (f_MoM - f_FEM)/f_FEM:
  - G1: 10.16 vs 10.00 GHz (-1.57%), -15.31 vs -10.58 dB
  - G2: 10.08 vs 10.56 GHz (+4.76%), -25.41 vs -20.87 dB
  - G3: 7.44 vs 7.20 (-3.23%), 9.76 vs 9.60 (-1.64%), 16.56 vs 16.24 (-1.93%)
  - G4: 15.52 vs 15.36 (-1.03%); its weaker first dip is 4.96 vs 6.08 GHz (+22.6%,
    excluded from the "principal notch" claim)
  - Headline: principal notches within 4.8%, depths within 6.2 dB (largest gap is G3
    notch 1, 6.19 dB).
- GMRES iterations (Fig. 4, G1): 30 to 80 off resonance, about 1600 at the notch. The
  resistive sheets G2 and G4 stay at or below 80 across the band.
- Runtime (Table V, one 201-point sweep at N = 120; source `time comparison.xlsx`):

  | | CST (s) | CPU (s) | A100 (s) | vs CPU | vs CST |
  |---|---|---|---|---|---|
  | G1 | 182 | 24 | 0.72 | 33x | 253x |
  | G2 | 199 | 41 | 1.06 | 39x | 188x |
  | G3 | 117 | 44 | 1.07 | 41x | 109x |
  | G4 | 29 | 61 | 1.23 | 50x | 24x |

  The headline "up to 50x" in the abstract, intro and conclusion comes from G4, so it
  will change when G4 is replaced.
- Fig. 5 (new): **projected** time for 1000 sweeps, computed as 1000 x the measured
  single-sweep time. Bars are the mean over G1 to G4 and whiskers span the fastest to
  slowest geometry: CST 36.6 h (8.1 to 55.3), CPU 11.8 h (6.7 to 16.9), A100 17 min
  (12 to 20.5). The caption and the IV-D text say it is projected. Regenerate it with
  `scripts/make_fig_scaling.py "<paper folder>" "<out path without extension>"`; it needs
  matplotlib, reads the xlsx directly and has no hardcoded timings.

### Current layout (verified on the rendered PDF)

- p1: title, abstract, Introduction, start of Section II.
- p2: Section II (Fig. 1 placeholder), Algorithm 1, Table I, start of Section III.
- p3: Section III (Fig. 2 placeholder), Table II, Section IV text. About 40% of the right
  column is empty because the Results text ends there and the Conclusion is forced after
  the floats. The real Figs. 1 and 2 should take up that space.
- p4: Table III and Fig. 3 (full width, top). Left column: Tables IV and V. Right column:
  Figs. 4 and 5, which share one float.
- p5: Conclusion, then the references, columns balanced with `\balance`.
- `\FloatBarrier` sits right before `\section{Conclusion}` so the Conclusion always
  follows every figure and table. The old `\newpage` before the bibliography was removed.

### Changes made on 2026-10-08

1. Fig. 5: replaced the per-geometry bars with the projected 1000-sweep chart (approved
   by the user in a Lavish preview); new caption; added one sentence to IV-D.
2. Layout: the Conclusion now comes after all floats; Tables IV and V are column-width
   with their notes below the table (they used to be stretched-out last rows); Table V
   gained a "vs CST" column (numbers moved out of its footnote); Table III's note was
   moved below the table; the 15 mm spacer was removed; Figs. 4 and 5 are column-width;
   the bibliography `\newpage` was removed; the last page is balanced.
3. `$S_{11} (dB)$` (italic "dB") became `$|S_{11}|$ (dB)` in IV-B and the Fig. 3 caption.
4. Section II cut down from 10 to 8 numbered equations without changing the physics:
   - the kxm/kyn equation and the J expansion became text;
   - the Y_top/Y_bot step folded into Eq. 4;
   - one shared kzi definition;
   - incident field, T_pq and eta1/k1 described in words;
   - Z_pq displayed inside the system equation.

   During review this was found to have dropped the k_t definition, which was restored,
   and k0 and eta0 are now defined.
5. Review fixes (user-approved):
   - IV-C renamed "GMRES Iterations";
   - the Conclusion's error-cause sentence softened to "not yet separated by cause; likely
     contributors are ...";
   - the intro gap sentence softened to "relatively little work has combined them ...";
   - Table III caption reduced to "Four Validation Geometries", with the class/# source
     note removed;
   - "PS report" removed from a comment and from the visible Fig. 2 placeholder text;
   - "well under 1 MB" changed to "about 1 MB".

---

## 5. Open items (priority order)

### Must do before submission

1. **G4 replacement.** Rerun the MoM on the new G4 (40_img, eps_r 10.2, tan_d 0.0023,
   h 1.27 mm, N = 120, 201 points over 2 to 18 GHz) when the user is back at the code.
   This needs the MoM |S11| CSV, N_u, the GMRES iteration counts, the A100 and CPU sweep
   times, and the CST time. Then update all of the following:
   - Fig. 3(d) and the Fig. 1 placeholder file names;
   - Table III G4 row and the N_u list in III-A;
   - Table IV G4 rows and the "weaker first dip" text (IV-B and the Table IV note);
   - the IV-C claim that "G2 and G4 stay <= 80 iterations";
   - Table V G4 row and Fig. 5 (rerun the script);
   - the "50x" in the abstract, intro and conclusion;
   - possibly the "4.8%" and "6.2 dB" figures.

   Fallbacks if no rerun is possible in time: use G1 to G3 only, or keep the old G4 and
   describe its mismatch honestly.
2. **Sign of G (Eq. 4).** The paper has G = +1/(Y0 - jY1 cot); the report has a minus
   sign. Physically, with e^{jwt}, a sheet current radiates a field that opposes it
   (E = -eta0/2 J in free space), which points to the minus sign. Check it in the code and
   make the paper match.
3. **Multi-GPU is claimed but not measured.** It appears in the abstract, a contribution
   bullet and III-C, but every timing is a single A100, and the T1000 in Table II has no
   results. Either add 1, 2 and 4 GPU timings (check for super-linear scaling) or reword
   multi-GPU as a design capability and drop it from the claimed results.
4. **CPU baseline details.** Add the CPU model and thread count. Also state the
   precision and tolerance mismatch (CPU complex128 at 1e-8 vs GPU complex64 at 5e-4),
   or time the CPU with the GPU settings. Say what each timing includes (kernel build,
   warm-up, cuFFT plans).
5. **CST context.** Add the CST hardware, mesh and solver settings. Frame the CST speedups
   (24 to 253x) as indicative, because CST models real copper thickness and the MoM uses a
   zero-thickness sheet.
6. **Fig. 1** (stack cross-section and unit cells) and **Fig. 2** (pipeline): still
   placeholder boxes.
7. **References:** verify all 13. The PyTorch entry lacks a volume (NeurIPS vol. 32).
8. **Cleanup:** delete the drafting macros and their definitions, and remove the
   `% Budget` comments.

### Should do

9. G4's weak first dip error (+22.6%) could look like cherry-picking next to the
   "principal notches" claim. Revisit after the G4 rerun.
10. Optional mesh-convergence study (notch frequency vs N) to back the error-cause
    sentence. There is room: the paper is at 5 of 6 pages.
11. Abstract wording: "on the HPC A100 GPU" reads oddly; "a single NVIDIA A100" is
    clearer. The abstract is user-owned, so ask first.

### Nice to have

12. A stronger, correctly scoped title (user's decision).
13. State the A100 memory size (40 or 80 GB) in Table II.
14. Fig. 4: the legend overlaps the |S11| curve (redraw it if the data is available).
15. III-A writes non-bold `\tilde{G}_{uv}` while the rest of the paper uses bold
    `\Gt`; make them consistent.

### Already checked and fine

- Every delta-f, speedup and depth gap matches its table, and the same numbers are quoted
  identically in the abstract, intro, results and conclusion.
- Anonymity: no names, institutions or report references in the PDF text. The PDF
  metadata has no author field (only MiKTeX producer and a +05:30 timestamp). Figure
  PDFs carry only matplotlib metadata.
- Style: no `---` or em dashes, no banned words, American spelling.

---

## 6. When to stop and ask

Stop when:
- GPU/HPC runs or code checks are needed (the user may be away from the code);
- data or parameters are missing;
- the code and the paper disagree on physics and the fix is not obvious;
- a claim (novelty wording, speedup framing, title) needs the user's decision;
- a figure is about to be replaced (preview first, rule 9);
- the abstract or introduction wording would change.

---

## 7. Writing style guide

The user wants the paper to read as if a person wrote it, because they wrote and edited
parts by hand.

**Don't:**
- use em dashes, or `---` in LaTeX prose. Use commas, parentheses or two sentences
  instead. The en dash `--` is fine for numeric ranges and page numbers.
- write colon-reveal sentences ("X is a natural alternative: ...");
- end several sentences in a row with a trailing ", which ..." clause;
- use "not only X but also Y";
- write reflexive lists of three;
- use stock words: leverage, utilize, seamless, robust, crucial, pivotal, delve, novel
  (unless truly needed), paves the way, plays a key role, it is worth noting,
  comprehensive, cutting-edge, in the realm of;
- copy abstract sentences verbatim into the intro or conclusion;
- use casual phrasing like "shows up as".

**Do:**
- vary sentence length;
- make concrete claims backed by numbers or citations;
- use "we" and the active voice where natural;
- use American spelling (discretized, modeled, normalization);
- hyphenate compound modifiers (radar-absorbing surface, finite-element method, full-wave
  solver);
- define each abbreviation at first use in the abstract, and again in the body;
- keep displayed equations to what a reader needs, and put simple definitions in text
  (the user asked for a less cluttered formulation).

---

## 8. Current abstract (user-approved wording)

> Periodic metasurfaces printed on grounded dielectric substrates are commonly used as
> radar-absorbing surfaces and are typically designed using repeated evaluations of the
> reflection coefficient S11 as a function of frequency. Although full-wave finite-element
> method (FEM) simulations with periodic boundary conditions are accurate, they are too
> slow for the extensive parameter sweeps required to build datasets for data-driven
> design. This paper presents a spectral-domain method of moments (MoM) solver in which
> the substrate and ground plane are incorporated into closed-form TE/TM Floquet Green's
> functions. The MoM operator is applied with fast Fourier transforms, so the dense
> impedance matrix is never explicitly formed, and the resulting system is solved with a
> restarted GMRES iteration that runs entirely on the GPU. Independent frequency points
> are distributed across multiple GPUs. For four representative absorber geometries,
> principal resonant notches agree with a commercial FEM solver to within 4.8% in
> frequency. A full frequency sweep on the HPC A100 GPU is up to 50x faster than the same
> matrix-free FFT-MoM implemented in NumPy/SciPy (complex128) on the CPU.

The "4.8%", the "50x" and the multi-GPU sentence depend on open items 1 and 3.

---

## 9. Working notes for Claude sessions

- The paper folder is `D:\conference_paper v3` (WSL: `/mnt/d/conference_paper v3`).
- There is no matplotlib or PDF tooling on the system Python. Make a throwaway venv
  (`uv venv` + `uv pip install matplotlib pymupdf`) to plot and to render PDF pages for
  layout checks.
- To check the layout, render every page of the compiled PDF to PNG and look at it. The
  compile log alone does not show stray fragments or empty float pages.
- An independent reviewer agent was requested once but could not be launched from the
  firstmate session (subagent dispatch is blocked there). The 2026-10-08 review was done
  in-session instead. For a truly independent review, run it in a plain Claude Code
  session in this folder.
