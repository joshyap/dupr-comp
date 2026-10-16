# DUPR Comp

DUPR Comp is a Python-first data analysis project that compares a doubles DUPR rating with the published active-player rating distribution and percentile benchmarks. The interactive dashboard is built with Streamlit; pandas loads and analyzes the source data, and Plotly renders the visualizations.

## What the analysis shows

- An entered rating's approximate percentile and distribution band.
- The published percentage of players in each rating band.
- Published percentile benchmarks and an explicitly estimated linear interpolation between them.
- The gap from the entered rating to its next published benchmark.
- Derived summaries of the distribution, including the share rated in the 3s and the share at 4.0 or higher.
- A visible data-scope note explaining who is and is not represented.

The entered rating is held only in the active Streamlit session. It is not written to a database, file, or browser local storage.

## Run locally

Python 3.10 or later is recommended.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints the local address to open in your browser.

## Deploy

GitHub Pages serves static files and does not run Python. To host the interactive Python dashboard, push this repository to GitHub and deploy it with [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Create or sign in to a Streamlit Community Cloud account and connect GitHub.
2. Create an app from this repository and choose the branch to deploy.
3. Set `app.py` as the main file path.
4. Deploy. Streamlit Cloud installs dependencies from `requirements.txt`.

The source data and PDF are included in the repository. No secrets, API keys, or external data fetches are required at runtime.

## Project structure

```text
.
├── analysis.py                      # Validated data loading and analysis functions
├── app.py                           # Streamlit dashboard and Plotly charts
├── data/
│   ├── doubles_distribution.csv     # Published rating-band shares
│   └── percentile_benchmarks.csv    # Published rating/percentile benchmarks
├── source-reference.pdf             # Source citation and data reference
├── requirements.txt                 # Python runtime dependencies
└── tests/
    └── test_analysis.py             # Analysis and boundary tests
```

## Test the analysis

```sh
python -m unittest discover -s tests -v
```

## Data source and methodology

The source is [DUPR's percentile article](https://www.dupr.com/post/dupr-rating-percentiles-see-how-your-rating-stacks-up-2), which describes a doubles-rating snapshot dated September 22, 2026. The snapshot includes players with a result in the prior 12 months. Published rating-band shares are 11%, 20%, 29%, 24%, 11%, 4%, and 1% for 2.000–2.499 through 5.000+, respectively. Published percentile benchmarks are 31st at 3.0, 60th at 3.5, 84th at 4.0, 95th at 4.5, and 99th at 5.0.

For ratings between 3.0 and 5.0, `analysis.py` linearly interpolates between adjacent published percentile benchmarks. The app does not extrapolate below 3.0 or above 5.0, where the source does not provide precise percentiles. Distribution percentages and published percentiles are rounded by the source; interpolated values are estimates and are not official DUPR calculations.

The source covers doubles only and active DUPR participants—not all recreational pickleball players. Players with recorded DUPR results may skew more competitive. See the [source data reference PDF](./source-reference.pdf) and the linked DUPR article for context and updates.
