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

def get_country_name(country_code):
    try:
        # Try as alpha-2 first
        country = pycountry.countries.get(alpha_2=country_code)
        if country:
            return country.name
        
        # Try as alpha-3 if alpha-2 fails
        country = pycountry.countries.get(alpha_3=country_code)
        if country:
            return country.name
        
        return country_code
    except:
        return country_code

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
            # Also filter out World Bank region and income group aggregates (non-country codes)
            # These typically have 3-letter codes that aren't actual ISO3 country codes
            # Common non-country codes: WLD (World), OED (OECD), EAS (East Asia), NAC (North America), etc.
            non_country_codes = [
                # World Bank region and income group aggregates
                'WLD', 'OED', 'PST', 'IBT', 'IBD', 'LMY', 'MIC', 'EAS', 'NAC', 'LTE', 'ECS', 'EUU',
                'HIC', 'LIC', 'SSF', 'SSA', 'TSA', 'MEA', 'LAC', 'ECA', 'ARB', 'CEB', 'CSS', 'EMU',
                'UMC', 'LMC', 'FCS', 'OSS', 'SST', 'TEA', 'TEC', 'TLA', 'TMN', 'TSS',
                'EAP', 'EAR', 'LCN', 'SAS', 'IDA', 'XKX', 'AFE', 'AFW', 'CAA', 'CLA', 'INX',
                'MNA', 'MNE', 'MNP', 'TEU', 'TLA', 'TSA', 'TZA', 'AFR', 'XZN', 'XZJ', 'XZG',
                'XK', 'AF', 'EA', 'LC', 'SA', 'ID', 'MN', 'TE', 'TL', 'TS', 'TZ'
            ]
            valid_data = [item for item in all_data if item["value"] is not None and item["countryiso3code"] not in non_country_codes]
            # Sort data based on indicator value - highest values first for all indicators
            sorted_data = sorted(valid_data, key=lambda x: x["value"], reverse=True)
            
            # Filter out non-country codes before creating rankings
            # This ensures we only have actual countries in our sorted data
            filtered_sorted_data = []
            for item in sorted_data:
                country_code = item["countryiso3code"]
                # Check if it's a real country code (not in our non-country list)
                if country_code and country_code not in non_country_codes:
                    # Also check for any 2-letter prefix that might indicate a region
                    if not any(country_code.startswith(prefix) for prefix in ['X', 'Z', 'E', 'L', 'M', 'T', 'S']):
                        filtered_sorted_data.append(item)
            
            # Create ranking dictionary with consecutive numbers
            rankings = {}
            for i, item in enumerate(filtered_sorted_data):
                country_code = item["countryiso3code"]
                rankings[country_code] = {
                    "rank": i + 1,  # Start at 1 and increment consecutively
                    "total": len(filtered_sorted_data),  # Total count of actual countries
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
    
    # Convert country code if needed (handles both ISO2 and ISO3)
    country_code = convert_iso2_to_iso3(country.upper())
    
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
    
    # Get country name
    country_name = get_country_name(country_code)
    
    return render_template("correlation_results.html", 
                           country=country_name, 
                           indicator1=indicator1, 
                           indicator2=indicator2, 
                           correlation=correlation,
                           scatter_data=scatter_data,
                           years=sorted(filtered_data.keys()),
                           is_two_countries=False)

@app.route("/correlations/analyze_two_countries", methods=["POST"])
def analyze_two_countries_correlation():
    country1 = request.form.get("country1")
    country2 = request.form.get("country2")
    start_year = request.form.get("start_year")
    end_year = request.form.get("end_year")
    indicator1 = request.form.get("indicator1")
    indicator2 = request.form.get("indicator2")
    
    # Validate inputs
    if not country1 or not country2 or not start_year or not end_year or not indicator1 or not indicator2:
        return redirect("/correlations")
    if not start_year.isdigit() or not end_year.isdigit():
        return redirect("/correlations")
    
    start_year = int(start_year)
    end_year = int(end_year)
    country1_code = country1.upper()
    country2_code = country2.upper()
    
    # Get data for both countries and indicators
    try:
        # Convert country codes if needed
        if len(country1_code) == 2:
            country1_code = convert_iso2_to_iso3(country1_code)
        if len(country2_code) == 2:
            country2_code = convert_iso2_to_iso3(country2_code)
            
        # Get data for both countries using the existing get_data function
        years_range = list(range(start_year, end_year + 1))
        
        # Get data for first country and indicator
        results1 = {}
        data1 = get_data(indicator1, country1_code, years_range)
        results1[indicator1] = []
        
        # Format data for first country
        for year, data in data1.items():
            results1[indicator1].append({
                "year": year,
                "value": data["value"]
            })
        
        # Get data for second country and indicator
        results2 = {}
        data2 = get_data(indicator2, country2_code, years_range)
        results2[indicator2] = []
        
        # Format data for second country
        for year, data in data2.items():
            results2[indicator2].append({
                "year": year,
                "value": data["value"]
            })
    except Exception as e:
        print(f"Error getting data: {e}")
        return redirect("/correlations")
    
    # Align data points by year
    aligned_data = {}
    for data_point in results1[indicator1]:
        year = data_point["year"]
        aligned_data[year] = {"indicator1": data_point["value"]}
    
    for data_point in results2[indicator2]:
        year = data_point["year"]
        if year in aligned_data:
            aligned_data[year]["indicator2"] = data_point["value"]
    
    # Filter out years where either indicator is missing
    filtered_data = {year: values for year, values in aligned_data.items() 
                    if "indicator1" in values and "indicator2" in values 
                    and values["indicator1"] is not None and values["indicator2"] is not None}
    
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
    
    # Get country names
    country1_name = get_country_name(country1_code)
    country2_name = get_country_name(country2_code)
    
    return render_template("correlation_results.html", 
                           country=f"{country1_name} vs {country2_name}", 
                           indicator1=f"{indicator1} ({country1_name})", 
                           indicator2=f"{indicator2} ({country2_name})", 
                           correlation=correlation,
                           scatter_data=scatter_data,
                           years=sorted(filtered_data.keys()),
                           is_two_countries=True)

@app.route("/rankings")
def rankings():
    current_year = datetime.now().year
    return render_template("rankings.html", current_year=current_year, valid_indicators=codes.keys())

@app.route("/rankings/view", methods=["POST"])
def view_rankings():
    indicator = request.form.get("indicator")
    year = request.form.get("year")
    
    # Validate inputs
    if not indicator or not year or not year.isdigit():
        return redirect("/rankings")
    
    year = int(year)
    
    # Make sure the indicator is valid
    if indicator not in codes:
        return redirect("/rankings")
    
    # Get global rankings for the indicator and year
    rankings_data = get_global_data(indicator, year)
    
    if not rankings_data:
        for i in range(0, 11):
            year = year - i
            rankings_data = get_global_data(indicator, year)
            if rankings_data:
                break
    if not rankings_data:
        current_year = datetime.now().year
        return render_template("rankings.html", current_year=current_year, valid_indicators=codes.keys(), error_message="No data available for the selected indicator")
    
    # Convert rankings to a list of country objects with names
    rankings_list = []
    countries = []
    values = []
    
    # Sort by rank
    sorted_rankings = sorted([(code, data) for code, data in rankings_data.items()], 
                             key=lambda x: x[1]["rank"])
    
    for code, data in sorted_rankings:
        country_name = get_country_name(code)
        rankings_list.append({
            "rank": data["rank"],
            "name": country_name,
            "iso3": code,
            "value": data["value"]
        })
        
        # Only include top 20 countries in the chart
        if len(countries) < 20:
            countries.append(country_name)
            values.append(data["value"])
    
    # Get indicator information
    indicator_info = get_indicator_info(indicator)
    data_source = "World Bank Development Indicators"
    
    return render_template("rankings_results.html",
                           indicator=indicator,
                           year=year,
                           rankings=rankings_list,
                           countries=countries,
                           values=values,
                           indicator_info=indicator_info,
                           data_source=data_source)

def get_indicator_info(indicator):
    indicator_descriptions = {
        "gdp": "Gross Domestic Product (GDP) is the total value of all goods and services produced in a country in a specific time period.",
        "gdp_per_capita": "GDP per capita is the GDP divided by the total population, providing an average measure of economic output per person.",
        "gdp_growth": "GDP growth rate shows the year-over-year percentage change in a country's economic output.",
        "inflation": "Inflation measures the annual percentage change in the general price level of goods and services.",
        "unemployment": "Unemployment rate represents the percentage of the labor force that is jobless and actively seeking employment.",
        "population": "Total population count of a country or region.",
        "life_expectancy": "Average number of years a newborn is expected to live if mortality patterns remain constant.",
        "fdi_inflows": "Foreign Direct Investment inflows represent the value of investments made by foreign entities in the domestic economy.",
        "fdi_outflows": "Foreign Direct Investment outflows represent the value of investments made by domestic entities in foreign economies.",
        "exports_gdp": "Exports as a percentage of GDP measures the value of goods and services sold to other countries relative to economic output.",
        "imports_gdp": "Imports as a percentage of GDP measures the value of goods and services purchased from other countries relative to economic output.",
        "gini_index": "The Gini index measures income inequality, with higher values indicating greater inequality.",
        "poverty_rate": "Percentage of the population living below the national poverty line.",
        "debt": "Government debt as a percentage of GDP indicates the level of a country's indebtedness relative to its economic output."
    }
    
    return indicator_descriptions.get(indicator, f"Data for {indicator.replace('_', ' ').title()}")

@app.template_filter('format_number')
def format_number(value):
    if value is None:
        return "N/A"
    
    if isinstance(value, (int, float)):
        if value >= 1_000_000_000_000:
            return f"${value/1_000_000_000_000:.2f} trillion"
        elif value >= 1_000_000_000:
            return f"${value/1_000_000_000:.2f} billion"
        elif value >= 1_000_000:
            return f"${value/1_000_000:.2f} million"
        elif value >= 1000:
            return f"{value:,.0f}"
        elif value % 1 == 0:
            return f"{value:.0f}"
        else:
            return f"{value:.2f}"
    
    return str(value)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)