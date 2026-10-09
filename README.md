# Agriculture and income: preparing World Bank data

This project prepares a clean country-by-year dataset from World Bank data. It brings together GDP per person, agriculture's share of GDP, and the share of workers employed in agriculture.

The notebook shows each data-cleaning step so it is easy to follow and change.

## Project question

How does agriculture relate to GDP per person across countries?

This notebook prepares the data for exploring that question; it does not try to answer it. A relationship between two measures would not, by itself, show that one causes the other.

## Data

The `phydata_capstone data/` folder contains the CSV files used in the project. They come from the World Bank's World Development Indicators:

- GDP per capita (current US$), indicator `NY.GDP.PCAP.CD`
- Agriculture, forestry and fishing value added (% of GDP), indicator `NV.AGR.TOTL.ZS`
- Employment in agriculture (% of total employment), indicator `SL.AGR.EMPL.ZS`

The notebook keeps country data from 1991 to 2025. Some countries have missing years, so the number of observations can vary.

## Run the notebook

You need Python 3.11 or newer. From the project folder, create an environment and install the project dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\activate
python -m pip install -e .
jupyter notebook
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

Open `Notebooks/capstone_beginner.ipynb` and run the cells from top to bottom. The notebook looks for the included data folder from either the project folder or the `Notebooks/` folder. It saves the result as `capstone_clean.csv` in the data folder.

## Run the Streamlit app

From the project folder, install the project dependencies and start the app:

```powershell
python -m pip install -e .
streamlit run app.py
```

The app reads the root `capstone_clean.csv`, displays the three charts in `figures/`, and lets you filter the summary and cleaned-data table by year and country.

## What the notebook does

1. Loads the three World Bank CSV files and keeps country observations.
2. Reshapes the tables so each row represents one country and year.
3. Joins the indicators and removes incomplete or out-of-range rows.
4. Saves the cleaned dataset as a CSV file for later analysis.

The notebook uses Python and pandas. NumPy is installed as a pandas dependency.
