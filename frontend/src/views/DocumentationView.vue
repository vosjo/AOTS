<template>
  <div class="mx-auto max-w-3xl space-y-8 px-4 py-6 text-aots">
    <header class="space-y-2">
      <h1 class="text-2xl font-semibold tracking-tight">Documentation</h1>
      <p class="text-aots-muted">
        AOTS (Archive of Observations and Time Series) is a project-based archive for
        stellar systems, spectra, light curves, and model analyses — with shared parameters,
        plots, and optional exchange with ASTRA.
      </p>
    </header>

    <nav class="aots-panel-compact text-sm" aria-label="On this page">
      <h2 class="mb-2 font-medium">On this page</h2>
      <ul class="list-inside list-disc space-y-1 text-aots-muted">
        <li><a class="text-aots-link hover:text-aots-link-hover" href="#overview">Overview</a></li>
        <li><a class="text-aots-link hover:text-aots-link-hover" href="#projects">Projects &amp; access</a></li>
        <li><a class="text-aots-link hover:text-aots-link-hover" href="#systems">Systems</a></li>
        <li><a class="text-aots-link hover:text-aots-link-hover" href="#observations">Observations</a></li>
        <li><a class="text-aots-link hover:text-aots-link-hover" href="#analyses">Analyses</a></li>
        <li><a class="text-aots-link hover:text-aots-link-hover" href="#consensus">Parameter consensus</a></li>
        <li><a class="text-aots-link hover:text-aots-link-hover" href="#astra">ASTRA import &amp; export</a></li>
        <li><a class="text-aots-link hover:text-aots-link-hover" href="#dashboard">Dashboard &amp; downloads</a></li>
        <li><a class="text-aots-link hover:text-aots-link-hover" href="#api">API &amp; authentication</a></li>
        <li>
          <a class="text-aots-link hover:text-aots-link-hover" href="#analysis-hdf5">Reference: Analysis HDF5 format</a>
          <ul class="mt-1 list-inside list-disc pl-4">
            <li><a class="text-aots-link hover:text-aots-link-hover" href="#star-matching">Star matching</a></li>
            <li><a class="text-aots-link hover:text-aots-link-hover" href="#categories">Categories and type</a></li>
            <li><a class="text-aots-link hover:text-aots-link-hover" href="#layout-v2">Multi-fit v2</a></li>
            <li><a class="text-aots-link hover:text-aots-link-hover" href="#layout-legacy">Legacy layout</a></li>
            <li><a class="text-aots-link hover:text-aots-link-hover" href="#parameters">Parameters</a></li>
            <li><a class="text-aots-link hover:text-aots-link-hover" href="#series">DATA, MODEL, O−C</a></li>
            <li><a class="text-aots-link hover:text-aots-link-hover" href="#by-category">Notes by category</a></li>
            <li><a class="text-aots-link hover:text-aots-link-hover" href="#failures">Common failures</a></li>
          </ul>
        </li>
      </ul>
    </nav>

    <!-- Overview -->
    <section id="overview" class="scroll-mt-20 space-y-3">
      <h2 class="text-xl font-semibold">Overview</h2>
      <p class="text-aots-muted">
        Work happens inside a <strong class="text-aots">project</strong>. Within a project the usual flow is:
      </p>
      <ol class="list-decimal space-y-2 pl-5 text-aots-muted">
        <li><strong class="text-aots">Systems</strong> — stars (targets) with coordinates, identifiers, and tags.</li>
        <li><strong class="text-aots">Observations</strong> — spectra and light curves attached to those stars.</li>
        <li><strong class="text-aots">Analyses</strong> — HDF5 model results (RV, SED, spectral, light-curve fits, …) that contribute parameters and plots.</li>
      </ol>
      <p class="text-aots-muted">
        Scalar parameters from catalogues and analyses feed a per-star
        <strong class="text-aots">consensus</strong> value (rules are configurable per project).
        The top navigation switches between Dashboard, Systems, Spectra, Light curves, Observatories, and Analyses.
      </p>
    </section>

    <!-- Projects -->
    <section id="projects" class="scroll-mt-20 space-y-3">
      <h2 class="text-xl font-semibold">Projects &amp; access</h2>
      <p class="text-aots-muted">
        Choose a project from the list at <code class="text-sm">/w/projects/</code> or the project selector in the top bar.
        <strong class="text-aots">Public</strong> projects are visible to everyone; private ones only to members.
      </p>
      <p class="text-aots-muted">Membership roles (set by administrators):</p>
      <ul class="list-disc space-y-1 pl-5 text-aots-muted">
        <li><strong class="text-aots">Read-only</strong> — browse data and plots.</li>
        <li><strong class="text-aots">Read/write own</strong> — add data; edit or delete objects (and fits) you uploaded.</li>
        <li><strong class="text-aots">Read/write</strong> — full edit rights in the project, including marking a best fit.</li>
      </ul>
      <p class="text-aots-muted">
        Upload buttons appear only when your account may add to the current project.
        Object-level <em>Edit</em> / <em>Delete</em> follow the same rules.
      </p>
    </section>

    <!-- Systems -->
    <section id="systems" class="scroll-mt-20 space-y-3">
      <h2 class="text-xl font-semibold">Systems</h2>
      <p class="text-aots-muted">
        Under <strong class="text-aots">Systems</strong> you manage stars: create one by one or via CSV bulk upload,
        assign <strong class="text-aots">tags</strong>, and store catalogue identifiers.
        From the systems list you can enrich selected (or all) stars with external data such as
        Gaia DR3, SIMBAD aliases, VizieR photometry, or TESS-related fetches (background jobs where configured).
      </p>
      <p class="text-aots-muted">
        The <strong class="text-aots">star detail</strong> page shows identifiers, parameters (consensus and other measurements),
        linked observations, and analysis plots. Edit metadata when you have permission.
      </p>
    </section>

    <!-- Observations -->
    <section id="observations" class="scroll-mt-20 space-y-3">
      <h2 class="text-xl font-semibold">Observations</h2>
      <div class="space-y-2">
        <h3 class="font-medium">Spectra</h3>
        <p class="text-aots-muted">
          Spectra are organised as <strong class="text-aots">processed</strong> spectra,
          underlying <strong class="text-aots">spectrum files</strong>, and optional
          <strong class="text-aots">raw</strong> files. Use the spectra upload flow to add FITS (or supported ASCII)
          and fill or correct header fields when needed. Detail pages show plots, headers, and linked analyses;
          you can also contribute a spectral fit when a multi-fit container exists.
        </p>
      </div>
      <div class="space-y-2">
        <h3 class="font-medium">Light curves</h3>
        <p class="text-aots-muted">
          Upload and inspect light curves (e.g. TESS), phase/bin tools on the detail page, and linked light-curve fits.
        </p>
      </div>
      <div class="space-y-2">
        <h3 class="font-medium">Observatories</h3>
        <p class="text-aots-muted">
          Maintain observatory metadata (coordinates, altitude) used when associating observations.
        </p>
      </div>
    </section>

    <!-- Analyses -->
    <section id="analyses" class="scroll-mt-20 space-y-3">
      <h2 class="text-xl font-semibold">Analyses</h2>
      <p class="text-aots-muted">
        Analyses are HDF5 results uploaded from <strong class="text-aots">Analyses → Upload analysis(es)</strong>
        (or contributed onto an existing container from spectrum / light-curve / star pages).
        See the <a class="text-aots-link hover:text-aots-link-hover" href="#analysis-hdf5">HDF5 format reference</a>
        for file layout.
      </p>
      <p class="text-aots-muted">On an analysis detail page you can typically:</p>
      <ul class="list-disc space-y-1 pl-5 text-aots-muted">
        <li>Inspect fit and O−C plots, and confidence-interval figures when present.</li>
        <li>Browse scalar parameters (best fit by default; other fits via the fit selector).</li>
        <li>For multi-fit categories (RV, spectral, LC, SED): switch fits, set the
          <strong class="text-aots">best fit</strong> (read/write), or
          <strong class="text-aots">contribute</strong> / edit / delete your own fits (read/write own).</li>
        <li>Open related analyses for the same star or category.</li>
      </ul>
      <p class="text-aots-muted">
        The <strong class="text-aots">parameter plotter</strong> (under Analyses) compares selected parameters across systems.
      </p>
    </section>

    <!-- Consensus -->
    <section id="consensus" class="scroll-mt-20 space-y-3">
      <h2 class="text-xl font-semibold">Parameter consensus</h2>
      <p class="text-aots-muted">
        Each star stores many measurements of the same quantity (catalogues, analyses).
        AOTS computes a <strong class="text-aots">consensus</strong> value used in overviews and the dashboard.
        Project admins with access configure rules under
        <code class="text-sm">/w/&lt;project&gt;/settings/consensus/</code>
        (e.g. weighted average, preferred source, preferred analysis category,
        preferred container best fit, source priority, latest).
      </p>
      <p class="text-aots-muted">
        Marking a fit as best fit matters when the policy uses
        <em>preferred container best fit</em>. Other measurements remain visible as “other measurements” on the star page.
      </p>
    </section>

    <!-- ASTRA -->
    <section id="astra" class="scroll-mt-20 space-y-3">
      <h2 class="text-xl font-semibold">ASTRA import &amp; export</h2>
      <p class="text-aots-muted">
        AOTS can exchange stars, observations, and analyses with
        <a
          class="text-aots-link hover:text-aots-link-hover"
          href="https://github.com/schedar/ASTRA"
          target="_blank"
          rel="noopener"
        >ASTRA</a>
        via <code class="text-sm">.astra</code> packages.
      </p>
      <ul class="list-disc space-y-1 pl-5 text-aots-muted">
        <li><strong class="text-aots">Import</strong> — Systems → ASTRA import (or the interop import route); merge a package into the current project.</li>
        <li><strong class="text-aots">Export</strong> — from the systems list, export selected stars to a downloadable package (runs as a background task).</li>
      </ul>
      <p class="text-aots-muted">
        Matching on import uses stable ASTRA IDs when known, then catalogue IDs and coordinates.
        Multi-fit analyses round-trip as one container with contributor fits.
      </p>
    </section>

    <!-- Dashboard -->
    <section id="dashboard" class="scroll-mt-20 space-y-3">
      <h2 class="text-xl font-semibold">Dashboard &amp; downloads</h2>
      <p class="text-aots-muted">
        The project <strong class="text-aots">dashboard</strong> summarises counts and shows an interactive
        <strong class="text-aots">sky map</strong> of systems (large projects may build the map asynchronously).
      </p>
      <p class="text-aots-muted">
        List pages support <strong class="text-aots">bulk download</strong> of selected spectra, raw files,
        light curves, or analyses as a ZIP (requires background workers on the server).
      </p>
    </section>

    <!-- API -->
    <section id="api" class="scroll-mt-20 space-y-3">
      <h2 class="text-xl font-semibold">API &amp; authentication</h2>
      <p class="text-aots-muted">
        Interactive OpenAPI docs:
        <a class="text-aots-link hover:text-aots-link-hover" href="/api/docs/" target="_blank" rel="noopener">/api/docs/</a>.
        List endpoints use <code class="text-sm">page</code>, <code class="text-sm">page_size</code>, and
        <code class="text-sm">ordering</code>. Project-scoped calls usually send header
        <code class="text-sm">Projectid</code>.
      </p>
      <ul class="list-disc space-y-1 pl-5 text-aots-muted">
        <li><strong class="text-aots">Browser</strong> — session cookie after login (normal UI use).</li>
        <li><strong class="text-aots">Scripts</strong> — DRF token from your profile, or project
          <code class="text-sm">HTTP_PUBLICAPIKEY</code> / <code class="text-sm">HTTP_SECRETAPIKEY</code> for bulk automation.</li>
      </ul>
      <p class="text-aots-muted">
        Example: analysis upload
        <code class="text-sm">POST /api/analysis/analyses/upload/</code>
        (multipart <code class="text-sm">datafile</code>, optional <code class="text-sm">category</code>).
      </p>
    </section>

    <!-- ========== Reference: HDF5 ========== -->
    <div class="border-t border-aots pt-8">
      <p class="mb-6 text-xs font-medium uppercase tracking-wide text-aots-faint-extra">Reference</p>

      <section id="analysis-hdf5" class="scroll-mt-20 space-y-3">
        <h2 class="text-xl font-semibold">Analysis HDF5 upload format</h2>
        <p class="text-aots-muted">
          Analyses are uploaded from
          <strong class="text-aots">Analyses → Upload analysis(es)</strong>
          as HDF5 (<code class="rounded bg-aots-muted/20 px-1 text-sm">.hdf5</code> /
          <code class="rounded bg-aots-muted/20 px-1 text-sm">.h5</code>) files.
          AOTS matches each file to a star in the current project, detects the category
          (or uses your override), and imports scalar parameters when present.
        </p>
        <p class="text-aots-muted">
          Prefer the <a class="text-aots-link hover:text-aots-link-hover" href="#layout-v2">multi-fit v2</a>
          layout for RV, spectral, light-curve, and SED fits. Legacy root
          <code class="text-sm">PARAMETERS</code> / <code class="text-sm">MODEL</code> files still work.
        </p>
      </section>

      <section id="star-matching" class="mt-8 scroll-mt-20 space-y-3">
        <h2 class="text-xl font-semibold">Star matching</h2>
        <p class="text-aots-muted">Every file must identify the star. Matching order:</p>
        <ol class="list-decimal space-y-2 pl-5 text-aots-muted">
          <li>
            If root attributes <code class="text-sm">ra</code> and <code class="text-sm">dec</code>
            are both non-zero (degrees; sexagesimal strings are accepted), AOTS finds a star
            in the project within ±0.01° and picks the closest.
          </li>
          <li>
            Otherwise it looks for an exact case-insensitive match on
            <code class="text-sm">systemname</code>.
            If coordinates are both zero and no matching name exists, upload fails.
          </li>
        </ol>
        <p class="text-aots-muted">
          Optional root metadata: <code class="text-sm">name</code> (analysis title),
          <code class="text-sm">note</code>, <code class="text-sm">reference</code> (ADS bibcode).
        </p>
        <p class="text-aots-muted">
          <strong class="text-aots">ISIS SED</strong> files use group
          <code class="text-sm">info/</code> (<code class="text-sm">oname</code>,
          <code class="text-sm">jradeg</code>, <code class="text-sm">jdedeg</code>) instead of these root attributes.
        </p>
      </section>

      <section id="categories" class="mt-8 scroll-mt-20 space-y-3">
        <h2 class="text-xl font-semibold">Categories and <code class="text-lg">type</code></h2>
        <p class="text-aots-muted">
          Set root attribute <code class="text-sm">type</code> so AOTS can classify the file.
          You can also choose a category in the upload dialog if detection fails.
        </p>
        <div class="overflow-x-auto rounded border border-aots">
          <table class="w-full text-left text-sm">
            <thead class="border-b border-aots bg-aots-muted/10 text-aots-muted">
              <tr>
                <th class="px-3 py-2 font-medium">Category</th>
                <th class="px-3 py-2 font-medium">Typical <code>type</code> values</th>
              </tr>
            </thead>
            <tbody class="text-aots-muted">
              <tr class="border-b border-aots/60">
                <td class="px-3 py-2 text-aots">RV curve</td>
                <td class="px-3 py-2"><code>RC</code>, <code>RV</code>, <code>rv_curve</code></td>
              </tr>
              <tr class="border-b border-aots/60">
                <td class="px-3 py-2 text-aots">SED fit</td>
                <td class="px-3 py-2"><code>SF</code>, <code>SED</code>, <code>sedfit</code> (or ISIS <code>info</code>/<code>results</code> layout)</td>
              </tr>
              <tr class="border-b border-aots/60">
                <td class="px-3 py-2 text-aots">Light curve fit</td>
                <td class="px-3 py-2"><code>LC</code>, <code>LF</code>, <code>lightcurve</code></td>
              </tr>
              <tr class="border-b border-aots/60">
                <td class="px-3 py-2 text-aots">Spectral fit</td>
                <td class="px-3 py-2"><code>XF</code>, <code>spectral</code>, <code>spectral_fit</code></td>
              </tr>
              <tr class="border-b border-aots/60">
                <td class="px-3 py-2 text-aots">Cross correlation</td>
                <td class="px-3 py-2"><code>CC</code>, <code>cross_corr</code></td>
              </tr>
              <tr>
                <td class="px-3 py-2 text-aots">Generic</td>
                <td class="px-3 py-2"><code>??</code>, <code>GF</code>, <code>generic</code>, <code>grid</code></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section id="layout-v2" class="mt-8 scroll-mt-20 space-y-3">
        <h2 class="text-xl font-semibold">Multi-fit v2 layout (recommended)</h2>
        <p class="text-aots-muted">
          One container file per dataset (star / spectrum / light curve) can hold several fits under
          <code class="text-sm">FITS/&lt;fit_id&gt;/</code>. Shared observations live in <code class="text-sm">DATA/</code>.
        </p>
        <pre class="overflow-x-auto rounded border border-aots bg-aots-muted/10 p-3 text-xs leading-relaxed text-aots"><code>/
  @type                         # RC | XF | LC | SF | …
  @&lt;category&gt;_format_version    # = 2
  @best_fit_id                  # id of the preferred fit
  @systemname, @ra, @dec
  @name, @note, @reference      # optional
  DATA/                         # shared observations
  FITS/&lt;fit_id&gt;/
    @isBestFit, @label, @method # optional metadata
    PARAMETERS/                 # scalar fit parameters
    MODEL/                      # optional model curve(s)
    O-C/                        # optional residuals</code></pre>
        <p class="text-aots-muted">Format-version attribute names:</p>
        <ul class="list-disc space-y-1 pl-5 text-aots-muted">
          <li><code class="text-sm">rv_curve_format_version = 2</code></li>
          <li><code class="text-sm">spectral_fit_format_version = 2</code></li>
          <li><code class="text-sm">lc_fit_format_version = 2</code></li>
          <li><code class="text-sm">sed_fit_format_version = 2</code></li>
        </ul>
      </section>

      <section id="layout-legacy" class="mt-8 scroll-mt-20 space-y-3">
        <h2 class="text-xl font-semibold">Legacy single-fit layout</h2>
        <p class="text-aots-muted">
          Still supported: put <code class="text-sm">PARAMETERS/</code>, and optionally
          <code class="text-sm">DATA/</code>, <code class="text-sm">MODEL/</code>, and
          <code class="text-sm">O-C/</code>, at the HDF5 root (no <code class="text-sm">FITS/</code> group).
          AOTS treats this as a single implicit fit.
        </p>
      </section>

      <section id="parameters" class="mt-8 scroll-mt-20 space-y-3">
        <h2 class="text-xl font-semibold">Parameters</h2>
        <p class="text-aots-muted">
          Under <code class="text-sm">PARAMETERS/</code> (root or
          <code class="text-sm">FITS/&lt;id&gt;/PARAMETERS/</code>), each parameter is a one-row
          compound dataset with fields <code class="text-sm">value</code>,
          <code class="text-sm">err_l</code>, <code class="text-sm">err_u</code>, and attribute
          <code class="text-sm">unit</code>.
        </p>
        <p class="text-aots-muted">
          Parameter names must be known to AOTS (or aliases thereof). Unknown names are dropped
          during homogenisation. Common examples:
        </p>
        <ul class="list-disc space-y-1 pl-5 text-aots-muted">
          <li>RV / orbit: <code class="text-sm">p</code>, <code class="text-sm">t0</code>, <code class="text-sm">e</code>, <code class="text-sm">omega</code>, <code class="text-sm">k1</code>/<code class="text-sm">k2</code>, <code class="text-sm">v01</code>/<code class="text-sm">v02</code></li>
          <li>Atmosphere / SED: <code class="text-sm">teff</code>, <code class="text-sm">logg</code>, <code class="text-sm">rad</code>, <code class="text-sm">ebv</code>, <code class="text-sm">z</code>, <code class="text-sm">L</code>, <code class="text-sm">d</code></li>
        </ul>
        <p class="text-aots-muted">
          Units should be Astropy-compatible (e.g. <code class="text-sm">km/s</code>,
          <code class="text-sm">K</code>, <code class="text-sm">d</code>, <code class="text-sm">mag</code>).
          Compatible aliases are converted to AOTS defaults when possible.
        </p>
      </section>

      <section id="series" class="mt-8 scroll-mt-20 space-y-3">
        <h2 class="text-xl font-semibold">DATA, MODEL, and O−C series</h2>
        <p class="text-aots-muted">Observation and model curves are compound arrays. Set dataset attributes:</p>
        <ul class="list-disc space-y-1 pl-5 text-aots-muted">
          <li><code class="text-sm">xpar</code> / <code class="text-sm">ypar</code> — column names used for plotting</li>
          <li><code class="text-sm">datatype</code> — <code class="text-sm">discrete</code> (markers) or <code class="text-sm">continuous</code> (line)</li>
          <li><code class="text-sm">label</code> — optional legend text</li>
        </ul>
        <p class="text-aots-muted">
          Group attributes <code class="text-sm">xlabel</code>, <code class="text-sm">ylabel</code>,
          <code class="text-sm">xscale</code>, <code class="text-sm">yscale</code> are used for axis titles
          and scales. Use <strong class="text-aots">linear</strong> scales for RV curves (negative
          velocities cannot be drawn on a log axis). Synthetic photometry (e.g. SED
          <code class="text-sm">Iflux</code>) must stay <code class="text-sm">discrete</code>.
        </p>
        <p class="text-aots-muted">
          Optional <code class="text-sm">O-C/</code> (root or under a fit) uses the same series pattern
          for residual plots; it is not required for a successful upload.
        </p>
      </section>

      <section id="by-category" class="mt-8 scroll-mt-20 space-y-4">
        <h2 class="text-xl font-semibold">Notes by category</h2>
        <div class="space-y-2">
          <h3 class="font-medium">RV curve</h3>
          <p class="text-aots-muted">
            Prefer <code class="text-sm">DATA/measurements</code> (or any DATA series) with columns that
            resolve to time (<code class="text-sm">time</code>, <code class="text-sm">bjd</code>,
            <code class="text-sm">mjd</code>, <code class="text-sm">hjd</code>, <code class="text-sm">phase</code>, …)
            and radial velocity (<code class="text-sm">rv</code>, <code class="text-sm">vrad</code>, …),
            plus optional formal errors. Measurements-only files (no parameters) are valid.
            Multi-component curves can use several DATA/MODEL datasets (e.g. primary and secondary).
          </p>
        </div>
        <div class="space-y-2">
          <h3 class="font-medium">Spectral fit</h3>
          <p class="text-aots-muted">
            Observed spectrum in <code class="text-sm">DATA/</code>, model in
            <code class="text-sm">FITS/&lt;id&gt;/MODEL/</code>, atmosphere parameters in
            <code class="text-sm">PARAMETERS/</code>.
          </p>
        </div>
        <div class="space-y-2">
          <h3 class="font-medium">Light curve fit</h3>
          <p class="text-aots-muted">
            Observed photometry in <code class="text-sm">DATA/</code>, model curve under the fit,
            orbital / binary parameters in <code class="text-sm">PARAMETERS/</code>.
          </p>
        </div>
        <div class="space-y-2">
          <h3 class="font-medium">SED fit</h3>
          <p class="text-aots-muted">Two layouts are accepted:</p>
          <ul class="list-disc space-y-1 pl-5 text-aots-muted">
            <li>
              <strong class="text-aots">Generic AOTS:</strong>
              <code class="text-sm">type=SF</code>, photometry in <code class="text-sm">DATA/</code>
              (e.g. <code class="text-sm">Obs</code>), continuous model (e.g. <code class="text-sm">tmap</code>)
              and discrete synthetic photometry as separate MODEL series, plus
              <code class="text-sm">PARAMETERS/</code>.
            </li>
            <li>
              <strong class="text-aots">ISIS:</strong>
              groups <code class="text-sm">info/</code>, <code class="text-sm">results/</code>
              (<code class="text-sm">iminimize</code> or <code class="text-sm">igrid_search</code>),
              optional <code class="text-sm">master/sed</code>. Category is detected automatically.
            </li>
          </ul>
        </div>
      </section>

      <section id="failures" class="mt-8 scroll-mt-20 space-y-3">
        <h2 class="text-xl font-semibold">Common upload failures</h2>
        <ul class="list-disc space-y-2 pl-5 text-aots-muted">
          <li><em>wrong format / unreadable</em> — file is not valid HDF5 or cannot be opened.</li>
          <li><em>basic info unreadable</em> — required root (or ISIS <code class="text-sm">info</code>) attributes missing or invalid.</li>
          <li><em>no system information present</em> — no usable <code class="text-sm">ra</code>/<code class="text-sm">dec</code> and no matching <code class="text-sm">systemname</code> in the project.</li>
          <li><em>No parameters included</em> — upload succeeded, but no recognised scalar parameters were found (plots may still work if DATA/MODEL are present).</li>
        </ul>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

onMounted(() => {
  const hash = route.hash?.replace(/^#/, '')
  if (!hash) return
  requestAnimationFrame(() => {
    document.getElementById(hash)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
})
</script>
