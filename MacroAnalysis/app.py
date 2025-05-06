from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import os
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pycountry

app = Flask(__name__)
# Codes for the World Bank API. It's made in a way new ones can be added anytime.
codes = {
        "gdp": "NY.GDP.MKTP.CD",
        "inflation": "FP.CPI.TOTL.ZG",
        "gdp_per_capita": "NY.GDP.PCAP.CD",
        "gdp_growth": "NY.GDP.MKTP.KD.ZG",
        "unemployment": "SL.UEM.TOTL.ZS",
        "literacy_rate": "SE.ADT.LITR.ZS",
        "life_expectancy": "SP.DYN.LE00.IN",
        "population_growth": "SP.POP.GROW",
        "poverty_rate": "SI.POV.DDAY",
        "gini_index": "SI.POV.GINI",
        "Total_population": "SP.POP.TOTL",
        "internet_usage": "IT.NET.USER.ZS",
        "energy_consumption": "EG.USE.PCAP.KG.OE",
        "electricity_access": "EG.ELC.ACCS.ZS",
        "renewable_energy": "EG.FEC.RNEW.ZS",
        "carbon_emissions": "EN.ATM.CO2E.KT",
        "tourism": "ST.INT.ARVL",
        "foreign_investment": "BX.KLT.DINV.CD",
        "trade_balance": "NE.RSB.GNFS.CD",
        "foreign_aid": "DT.ODA.ALLD.CD",
        "debt": "DT.DOD.DECT.CD",
        "stock_market": "CM.MKT.LCAP.CD",
        "interest_rate": "FR.INR.LEND",
        "exports_gdp": "NE.EXP.GNFS.ZS",
        "imports_gdp": "NE.IMP.GNFS.ZS",
        "trade_gdp": "NE.TRD.GNFS.ZS",
        "current_account_balance_gdp": "BN.CAB.XOKA.GD.ZS",
        "employment_ratio_15_plus": "SL.EMP.TOTL.SP.ZS",
        "youth_unemployment": "SL.UEM.1524.ZS",
        "labor_force_participation": "SL.TLF.CACT.ZS",
        "health_expenditure_per_capita": "SH.XPD.CHEX.PC.CD",
        "physicians_per_1000": "SH.MED.PHYS.ZS",
        "hospital_beds_per_1000": "SH.MED.BEDS.ZS",
        "education_expenditure_gdp": "SE.XPD.TOTL.GD.ZS",
        "school_enrollment_secondary": "SE.SEC.ENRR",
        "co2_emissions_per_capita": "EN.ATM.CO2E.PC",
        "forest_area": "AG.LND.FRST.ZS",
        "clean_fuel_access": "EG.CFT.ACCS.ZS",
        "military_expenditure_gdp": "MS.MIL.XPND.GD.ZS",
        "tax_revenue_gdp": "GC.TAX.TOTL.GD.ZS",
        "government_expenditure_gdp": "NE.CON.GOVT.ZS",
        "agriculture_gdp": "NV.AGR.TOTL.ZS",
        "industry_gdp": "NV.IND.TOTL.ZS",
        "services_gdp": "NV.SRV.TOTL.ZS",
        "gdp_per_person_employed": "NY.GDP.PCAP.KD",
        "government_revenue_gdp": "GC.REV.XGRT.GD.ZS",
        "credit_to_private_sector_gdp": "FS.AST.PRVT.GD.ZS",
        "high_tech_exports": "TX.VAL.TECH.MF.ZS",
        "r_and_d_expenditure_gdp": "GB.XPD.RSDV.GD.ZS",
        "external_debt_gni": "DT.DOD.DECT.GN.ZS",
        "undernourishment": "SN.ITK.DEFC.ZS",
        "age_dependency_ratio": "SP.POP.DPND",
        "gender_parity_secondary_education": "SE.ENR.SECO.FM.ZS",
        "homicide_rate": "VC.IHR.PSRC.P5",
        "freshwater_withdrawals": "ER.H2O.FWST.ZS",
        "pm25_air_pollution": "EN.ATM.PM25.MC.M3"
    }
# IMF WEO indicator codes
forecast_supported_indicators = {
    "gdp": "NGDPD",           # Nominal GDP, current prices (Billions of U.S. dollars)
    "gdp_per_capita": "NGDPDPC",   # GDP per capita, current prices (U.S. dollars)
    "inflation": "PCPIPCH",        # Inflation, average consumer prices (Percent change)
    "unemployment": "LUR",         # Unemployment rate (Percent of total labor force)
    "gdp_growth": "NGDP_RPCH"     # Real GDP growth (Annual percent change)
}

def convert_iso2_to_iso3(iso2_code):
    """Convert ISO2 country code to ISO3 country code using pycountry."""
    try:
        # Try to look up by alpha_2 (ISO2)
        country = pycountry.countries.get(alpha_2=iso2_code.upper())
        if country:
            return country.alpha_3
    except (KeyError, AttributeError):
        pass
    
    # If the lookup fails or if the code is already ISO3, return it as is
    return iso2_code.upper()



@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

def get_imf_forecast_data(indicator, country_iso3):
    #Get forecast data from IMF's World Economic Outlook database.
    try:
        current_year = datetime.now().year
        url = f"https://www.imf.org/external/datamapper/api/v1/{indicator}/{country_iso3}"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return {}
            
        data = response.json()
        if not data or 'values' not in data or indicator not in data['values'] or country_iso3 not in data['values'][indicator]:
            return {}
                
        values = {}
        try:
            country_data = data['values'][indicator][country_iso3]
            
            # Sort years to get the most recent actual data
            all_years = sorted([int(year) for year in country_data.keys()])
            
            # Include current year and next 5 years in forecast
            forecast_years = [year for year in all_years 
                            if year >= current_year and 
                            year <= current_year + 5]
            
            # Process forecast years
            for year in forecast_years:
                value = country_data.get(str(year))
                if value is not None:
                    try:
                        value = float(value)
                        
                        # Scale values based on indicator type
                        if indicator == 'NGDPD':
                            # Convert billions to raw dollars
                            value = value * 1_000_000_000
                            
                        values[year] = {"value": value, "type": "forecast"}
                    except (ValueError, TypeError):
                        continue
            
            return values
            
        except KeyError:
            return {}
                    
    except Exception:
        return {}

# Cache directory for storing rankings
RANKINGS_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache', 'rankings')

# Ensure cache directory exists
os.makedirs(RANKINGS_CACHE_DIR, exist_ok=True)

def get_cached_rankings(indicator, year):
    """Get rankings from cache if available and not expired."""
    cache_file = os.path.join(RANKINGS_CACHE_DIR, f'{indicator}_{year}.json')
    
    # Check if cache file exists and is not older than 30 days
    if os.path.exists(cache_file):
        file_modified_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - file_modified_time < timedelta(days=30):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading cache file: {e}")
    
    return None

def save_rankings_to_cache(indicator, year, rankings):
    """Save rankings to cache."""
    cache_file = os.path.join(RANKINGS_CACHE_DIR, f'{indicator}_{year}.json')
    try:
        with open(cache_file, 'w') as f:
            json.dump(rankings, f)
    except Exception as e:
        print(f"Error saving to cache: {e}")

def get_global_data(indicator, year):
    """Get global data for an indicator for a specific year to calculate rankings."""
    # Try to get from cache first
    cached_rankings = get_cached_rankings(indicator, year)
    if cached_rankings:
        return cached_rankings
        
    try:
        # Get data for all countries
        url = f"http://api.worldbank.org/v2/country/all/indicator/{codes[indicator]}?format=json&date={year}"
        wb_response = requests.get(url, headers={"User-Agent": "MacroAnalysis"}, timeout=10)
        
        if wb_response.status_code == 200:
            response = wb_response.json()
            
            # Check if we have pagination and need to get more pages
            total_pages = response[0]['pages'] if isinstance(response, list) and len(response) > 0 else 1
            all_data = response[1] if isinstance(response, list) and len(response) > 1 else []
            
            # Get additional pages if needed (usually won't be more than 2-3 pages)
            for page in range(2, total_pages + 1):
                url = f"http://api.worldbank.org/v2/country/all/indicator/{codes[indicator]}?format=json&date={year}&page={page}"
                page_response = requests.get(url, headers={"User-Agent": "MacroAnalysis"}, timeout=10)
                if page_response.status_code == 200:
                    page_data = page_response.json()
                    if isinstance(page_data, list) and len(page_data) > 1:
                        all_data.extend(page_data[1])
            
            # Filter out entries with no value and sort
            valid_data = [item for item in all_data if item["value"] is not None]
            
            # For most indicators, higher is better, but for some, lower is better
            reverse_order = indicator not in ["unemployment", "inflation", "poverty_rate", "gini_index", "debt", "imports_gdp"]
            
            # Sort data based on indicator value
            sorted_data = sorted(valid_data, key=lambda x: x["value"], reverse=reverse_order)
            
            # Create ranking dictionary
            rankings = {}
            for i, item in enumerate(sorted_data):
                country_code = item["countryiso3code"]
                if country_code:
                    rankings[country_code] = {
                        "rank": i + 1,
                        "total": len(sorted_data),
                        "value": item["value"]
                    }
            
            # Save to cache for future use
            save_rankings_to_cache(indicator, year, rankings)
            return rankings
        
        return {}
    except Exception as e:
        return {}

def get_data(indicator, country_code, years):
    """Get historical and forecast data for a specific indicator and country."""
    
    try:
        values = {}
        
        # Get historical data from World Bank
        url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/{codes[indicator]}?format=json&date={min(years)}:{max(years)}"
        wb_response = requests.get(url, headers={"User-Agent": "MacroAnalysis"}, timeout=10)
        
        if wb_response.status_code == 200:
            response = wb_response.json()
            
            # Process historical data
            if isinstance(response, list) and len(response) > 1:
                for item in response[1]:
                    year = int(item["date"])
                    value = item["value"]
                    if value is not None:
                        values[year] = {
                            "value": value, 
                            "type": "historical"
                        }
        # Get forecast data from IMF if available
        if indicator in forecast_supported_indicators:
            imf_country_code = convert_iso2_to_iso3(country_code)
            forecast_data = get_imf_forecast_data(forecast_supported_indicators[indicator], imf_country_code)
            if forecast_data:
                # Add empty ranking data for forecast values
                for year, data in forecast_data.items():
                    data["ranking"] = {}
                values.update(forecast_data)
            
        # Now add ranking data only for the latest year with data
        historical_years = [year for year, data in values.items() if data["type"] == "historical"]
        if historical_years:
            latest_year = max(historical_years)
            ranking_data = {}
            global_data = get_global_data(indicator, latest_year)
            # Convert ISO2 to ISO3 country code if needed
            iso3_code = convert_iso2_to_iso3(country_code)
            
            if iso3_code in global_data:
                ranking_data = global_data[iso3_code]
            elif country_code in global_data:
                ranking_data = global_data[country_code]
                
            # Add ranking data if available
            if ranking_data:
                values[latest_year]["ranking"] = ranking_data
        
        return values
    except Exception as e:
        return {}

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/map")
def index():
    return render_template("index.html", valid_indicators=codes.keys(), current_year=datetime.now().year)

# Necessary limit to make the application run faster
Max_work_load = 100

@app.route("/country", methods=["GET", "POST"])
def country():
    if request.method == "POST":
        # gets the data from the index.html
        country = request.form.get("country")
        start_year = request.form.get("start_year")
        end_year = request.form.get("end_year")
        indicators = request.form.getlist("indicators")

        # handling misinputs
        if not country or not start_year or not end_year:
            return redirect("/map")
        if not start_year.isdigit() or not end_year.isdigit():
            return redirect("/map")
        if not indicators:
            indicators = ["gdp", "gdp_per_capita", "gdp_growth", "inflation", "unemployment"]

        start_year = int(start_year)
        end_year = int(end_year)

        # if ((start_year) > (end_year)) or ((start_year) < 1960) or ((end_year) > datetime.now().year - 2):
        #    return redirect("/")
        country_code = country.upper()
        
        current_year = datetime.now().year
        # If end year is current year or later and we have forecast indicators, extend the range
        forecast_end_year = None
        if end_year >= current_year and any(i in forecast_supported_indicators for i in indicators):
            forecast_end_year = current_year + 5
            years = list(range(start_year, forecast_end_year + 1))
        else:
            years = list(range(start_year, end_year + 1))

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(get_data, indicator, country_code, years): indicator for indicator in indicators}

            results = {indicator: [] for indicator in indicators}
            for future in futures:
                indicator = futures[future]
                values = future.result()
                for year in years:
                    if year in values:
                        data = values[year]
                        result_item = {
                            "year": year,
                            "value": data["value"],
                            "type": data["type"]
                        }
                        
                        # Add ranking data if available
                        if "ranking" in data and data["ranking"]:
                            result_item["ranking"] = data["ranking"]
                            
                        results[indicator].append(result_item)

        # All data is ready for the template
        
        return render_template("country.html", country=country, indicators=indicators, data_series=results, years=years)
    else:
        return redirect("/map")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/compare")
def compare():
    return render_template("compare.html", valid_indicators=codes.keys(), current_year=datetime.now().year)

@app.route("/compare/country", methods=["GET", "POST"])
def compare_countries():
    if request.method == "POST":
        countries = []
        # Get selected countries
        for i in range(1, 11):
            code = request.form.get(f"country{i}")
            if code:
                countries.append(code.upper())

        start_year = request.form.get("start_year")
        end_year = request.form.get("end_year")
        indicators = request.form.getlist("indicators")

        if not countries or not start_year or not end_year:
            return redirect("/compare")
        if not start_year.isdigit() or not end_year.isdigit():
            return redirect("/compare")
        if not indicators:
            indicators = ["gdp", "gdp_per_capita", "gdp_growth", "inflation", "unemployment"]
        # Limit workload
        if len(countries) * len(indicators) > Max_work_load:
            return redirect("/compare")
        
        start_year = int(start_year)
        end_year = int(end_year)
        
        # Handle forecasting extension
        current_year = datetime.now().year
        if end_year >= current_year and any(i in forecast_supported_indicators for i in indicators):
            forecast_end_year = current_year + 5
            years = list(range(start_year, forecast_end_year + 1))
        else:
            years = list(range(start_year, end_year + 1))

        with ThreadPoolExecutor() as executor:
            futures = {}
            for country_code in countries:
                for indicator in indicators:
                    futures[executor.submit(get_data, indicator, country_code, years)] = (country_code, indicator)

            data_series = {country: {indicator: [] for indicator in indicators} for country in countries}
            for future in futures:
                country_code, indicator = futures[future]
                values = future.result()
                for year in years:
                    if year in values:
                        data = values[year]
                        result_item = {
                            "year": year,
                            "value": data["value"],
                            "type": data["type"]
                        }
                        
                        # Add ranking data if available
                        if "ranking" in data and data["ranking"]:
                            result_item["ranking"] = data["ranking"]
                            
                        data_series[country_code][indicator].append(result_item)

        return render_template("compare_countries.html", countries=countries, indicators=indicators, data_series=data_series, years=years)
    else:
        return redirect("/compare")

@app.route("/correlations", methods=["GET"])
def correlations():
    return render_template("correlations.html", valid_indicators=codes.keys(), current_year=datetime.now().year)

@app.route("/correlations/analyze", methods=["POST"])
def analyze_correlations():
    country = request.form.get("country")
    start_year = request.form.get("start_year")
    end_year = request.form.get("end_year")
    indicator1 = request.form.get("indicator1")
    indicator2 = request.form.get("indicator2")
    
    # Validate inputs
    if not country or not start_year or not end_year or not indicator1 or not indicator2:
        return redirect("/correlations")
    if not start_year.isdigit() or not end_year.isdigit():
        return redirect("/correlations")
    if indicator1 == indicator2:
        return redirect("/correlations")
        
    start_year = int(start_year)
    end_year = int(end_year)
    country_code = country.upper()
    
    # Get data for both indicators
    years = list(range(start_year, end_year + 1))
    
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(get_data, indicator1, country_code, years): indicator1,
            executor.submit(get_data, indicator2, country_code, years): indicator2
        }
        
        results = {
            indicator1: [],
            indicator2: []
        }
        
        for future in futures:
            indicator = futures[future]
            values = future.result()
            for year in years:
                if year in values:
                    data = values[year]
                    results[indicator].append({
                        "year": year,
                        "value": data["value"],
                        "type": data["type"]
                    })
    
    # Calculate correlation
    # First, align the data points by year
    aligned_data = {}
    for year in years:
        aligned_data[year] = {"indicator1": None, "indicator2": None}
    
    for data_point in results[indicator1]:
        aligned_data[data_point["year"]]["indicator1"] = data_point["value"]
        
    for data_point in results[indicator2]:
        aligned_data[data_point["year"]]["indicator2"] = data_point["value"]
    
    # Filter out years where either indicator is missing
    filtered_data = {year: values for year, values in aligned_data.items() 
                    if values["indicator1"] is not None and values["indicator2"] is not None}
    
    # Calculate correlation coefficient if we have enough data points
    correlation = None
    scatter_data = []
    
    if len(filtered_data) > 1:
        x_values = []
        y_values = []
        
        for year, values in filtered_data.items():
            x_values.append(values["indicator1"])
            y_values.append(values["indicator2"])
            scatter_data.append({
                "year": year,
                "x": values["indicator1"],
                "y": values["indicator2"]
            })
        
        # Calculate correlation coefficient
        if len(x_values) > 1:
            correlation = np.corrcoef(x_values, y_values)[0, 1]
    
    return render_template("correlation_results.html", 
                           country=country, 
                           indicator1=indicator1, 
                           indicator2=indicator2, 
                           correlation=correlation,
                           scatter_data=scatter_data,
                           years=sorted(filtered_data.keys()))

if __name__ == "__main__":
    #port = int(os.environ.get("PORT", 5000))
    #app.run(debug=False, host="0.0.0.0", port=port)
    app.run(debug=True)