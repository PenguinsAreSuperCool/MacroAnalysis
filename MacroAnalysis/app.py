from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

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
    "gdp_per_capita": "PPPPC",     # GDP per capita, PPP (Current international dollar)
    "inflation": "PCPIPCH",        # Inflation, average consumer prices (Percent change)
    "unemployment": "LUR",         # Unemployment rate (Percent of total labor force)
    "gdp_growth": "NGDP_RPCH"     # Real GDP growth (Annual percent change)
}

# Comprehensive ISO2 to ISO3 country code mapping
country_codes = {
    'AF': 'AFG', 'AX': 'ALA', 'AL': 'ALB', 'DZ': 'DZA', 'AS': 'ASM', 'AD': 'AND', 'AO': 'AGO',
    'AI': 'AIA', 'AQ': 'ATA', 'AG': 'ATG', 'AR': 'ARG', 'AM': 'ARM', 'AW': 'ABW', 'AU': 'AUS',
    'AT': 'AUT', 'AZ': 'AZE', 'BS': 'BHS', 'BH': 'BHR', 'BD': 'BGD', 'BB': 'BRB', 'BY': 'BLR',
    'BE': 'BEL', 'BZ': 'BLZ', 'BJ': 'BEN', 'BM': 'BMU', 'BT': 'BTN', 'BO': 'BOL', 'BA': 'BIH',
    'BW': 'BWA', 'BV': 'BVT', 'BR': 'BRA', 'IO': 'IOT', 'BN': 'BRN', 'BG': 'BGR', 'BF': 'BFA',
    'BI': 'BDI', 'KH': 'KHM', 'CM': 'CMR', 'CA': 'CAN', 'CV': 'CPV', 'KY': 'CYM', 'CF': 'CAF',
    'TD': 'TCD', 'CL': 'CHL', 'CN': 'CHN', 'CX': 'CXR', 'CC': 'CCK', 'CO': 'COL', 'KM': 'COM',
    'CG': 'COG', 'CD': 'COD', 'CK': 'COK', 'CR': 'CRI', 'CI': 'CIV', 'HR': 'HRV', 'CU': 'CUB',
    'CY': 'CYP', 'CZ': 'CZE', 'DK': 'DNK', 'DJ': 'DJI', 'DM': 'DMA', 'DO': 'DOM', 'EC': 'ECU',
    'EG': 'EGY', 'SV': 'SLV', 'GQ': 'GNQ', 'ER': 'ERI', 'EE': 'EST', 'ET': 'ETH', 'FK': 'FLK',
    'FO': 'FRO', 'FJ': 'FJI', 'FI': 'FIN', 'FR': 'FRA', 'GF': 'GUF', 'PF': 'PYF', 'TF': 'ATF',
    'GA': 'GAB', 'GM': 'GMB', 'GE': 'GEO', 'DE': 'DEU', 'GH': 'GHA', 'GI': 'GIB', 'GR': 'GRC',
    'GL': 'GRL', 'GD': 'GRD', 'GP': 'GLP', 'GU': 'GUM', 'GT': 'GTM', 'GG': 'GGY', 'GN': 'GIN',
    'GW': 'GNB', 'GY': 'GUY', 'HT': 'HTI', 'HM': 'HMD', 'VA': 'VAT', 'HN': 'HND', 'HK': 'HKG',
    'HU': 'HUN', 'IS': 'ISL', 'IN': 'IND', 'ID': 'IDN', 'IR': 'IRN', 'IQ': 'IRQ', 'IE': 'IRL',
    'IM': 'IMN', 'IL': 'ISR', 'IT': 'ITA', 'JM': 'JAM', 'JP': 'JPN', 'JE': 'JEY', 'JO': 'JOR',
    'KZ': 'KAZ', 'KE': 'KEN', 'KI': 'KIR', 'KP': 'PRK', 'KR': 'KOR', 'KW': 'KWT', 'KG': 'KGZ',
    'LA': 'LAO', 'LV': 'LVA', 'LB': 'LBN', 'LS': 'LSO', 'LR': 'LBR', 'LY': 'LBY', 'LI': 'LIE',
    'LT': 'LTU', 'LU': 'LUX', 'MO': 'MAC', 'MK': 'MKD', 'MG': 'MDG', 'MW': 'MWI', 'MY': 'MYS',
    'MV': 'MDV', 'ML': 'MLI', 'MT': 'MLT', 'MH': 'MHL', 'MQ': 'MTQ', 'MR': 'MRT', 'MU': 'MUS',
    'YT': 'MYT', 'MX': 'MEX', 'FM': 'FSM', 'MD': 'MDA', 'MC': 'MCO', 'MN': 'MNG', 'ME': 'MNE',
    'MS': 'MSR', 'MA': 'MAR', 'MZ': 'MOZ', 'MM': 'MMR', 'NA': 'NAM', 'NR': 'NRU', 'NP': 'NPL',
    'NL': 'NLD', 'NC': 'NCL', 'NZ': 'NZL', 'NI': 'NIC', 'NE': 'NER', 'NG': 'NGA', 'NU': 'NIU',
    'NF': 'NFK', 'MP': 'MNP', 'NO': 'NOR', 'OM': 'OMN', 'PK': 'PAK', 'PW': 'PLW', 'PS': 'PSE',
    'PA': 'PAN', 'PG': 'PNG', 'PY': 'PRY', 'PE': 'PER', 'PH': 'PHL', 'PN': 'PCN', 'PL': 'POL',
    'PT': 'PRT', 'PR': 'PRI', 'QA': 'QAT', 'RE': 'REU', 'RO': 'ROU', 'RU': 'RUS', 'RW': 'RWA',
    'BL': 'BLM', 'SH': 'SHN', 'KN': 'KNA', 'LC': 'LCA', 'MF': 'MAF', 'PM': 'SPM', 'VC': 'VCT',
    'WS': 'WSM', 'SM': 'SMR', 'ST': 'STP', 'SA': 'SAU', 'SN': 'SEN', 'RS': 'SRB', 'SC': 'SYC',
    'SL': 'SLE', 'SG': 'SGP', 'SK': 'SVK', 'SI': 'SVN', 'SB': 'SLB', 'SO': 'SOM', 'ZA': 'ZAF',
    'GS': 'SGS', 'ES': 'ESP', 'LK': 'LKA', 'SD': 'SDN', 'SR': 'SUR', 'SJ': 'SJM', 'SZ': 'SWZ',
    'SE': 'SWE', 'CH': 'CHE', 'SY': 'SYR', 'TW': 'TWN', 'TJ': 'TJK', 'TZ': 'TZA', 'TH': 'THA',
    'TL': 'TLS', 'TG': 'TGO', 'TK': 'TKL', 'TO': 'TON', 'TT': 'TTO', 'TN': 'TUN', 'TR': 'TUR',
    'TM': 'TKM', 'TC': 'TCA', 'TV': 'TUV', 'UG': 'UGA', 'UA': 'UKR', 'AE': 'ARE', 'GB': 'GBR',
    'US': 'USA', 'UM': 'UMI', 'UY': 'URY', 'UZ': 'UZB', 'VU': 'VUT', 'VE': 'VEN', 'VN': 'VNM',
    'VG': 'VGB', 'VI': 'VIR', 'WF': 'WLF', 'EH': 'ESH', 'YE': 'YEM', 'ZM': 'ZMB', 'ZW': 'ZWE',
}

def get_imf_country_code(iso2_code):
    # Convert 2-letter country codes to 3-letter IMF codes using a comprehensive mapping.
    return country_codes.get(iso2_code.upper(), iso2_code)

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
            latest_actual_year = max([year for year in all_years if year <= current_year])
            
            # Get forecast years (next 5 years after the latest actual data)
            forecast_years = [year for year in all_years 
                            if year > latest_actual_year and 
                            year <= latest_actual_year + 5]
            
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

def get_data(indicator, country_code, years):
    # Get historical and forecast data for a specific indicator and country.
    
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
                        values[year] = {"value": value, "type": "historical"}
        
        # Get forecast data from IMF if available
        if indicator in forecast_supported_indicators:
            imf_country_code = get_imf_country_code(country_code)
            forecast_data = get_imf_forecast_data(forecast_supported_indicators[indicator], imf_country_code)
            if forecast_data:
                values.update(forecast_data)
            
        return values
    except Exception:
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
                        results[indicator].append({
                            "year": year,
                            "value": data["value"],
                            "type": data["type"]
                        })

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
                        data_series[country_code][indicator].append({
                            "year": year,
                            "value": data["value"],
                            "type": data["type"]
                        })

        return render_template("compare_countries.html", countries=countries, indicators=indicators, data_series=data_series, years=years)
    else:
        return redirect("/compare")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
    