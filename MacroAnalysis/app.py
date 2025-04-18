from flask import Flask, render_template, request, redirect
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
        "government_expenditure_gdp": "NE.CON.GOVT.ZS"
    }
# Necessary limit to make the web run faster
Max_work_load = 100

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/map")
def index():
    return render_template("index.html", valid_indicators=codes.keys())

def get_data(data_to_get, country_code, years):
    data_indicator = codes.get(data_to_get)
    try:
        start = min(years)
        end = max(years)
        url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{data_indicator}?format=json&per_page=100&date={start}:{end}"
        headers = {
            "User-Agent": "MacroAnalysis lupchinskileonardo@gmail.com"
        }
        response = requests.get(url, headers=headers).json()
        values = {}
        for item in response[1]:
            year = int(item["date"])
            value = item["value"]
            values[year] = value
        return values
    except (TypeError, IndexError):
        return {}

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
            return redirect("/")
        if not start_year.isdigit() or not end_year.isdigit():
            return redirect("/")
        if not indicators:
            indicators = ["gdp", "gdp_per_capita", "gdp_growth", "inflation", "unemployment"]


        start_year = int(start_year)
        end_year = int(end_year)

        if ((start_year) > (end_year)) or ((start_year) < 1960) or ((end_year) > datetime.now().year - 2):
            return redirect("/")
        country_code = country.upper()
        
        years = list(range(start_year, end_year + 1))
        # insteresting solution to make this viable
        # when not using ThreadPoolExecutor, the code took ages to run!
        # API calls are made in parallel now, which makes it much faster!

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(get_data, indicator, country_code, years): indicator for indicator in indicators}

            results = {indicator: [] for indicator in indicators}
            for future in futures:
                indicator = futures[future]
                values = future.result()
                for year in years:
                    results[indicator].append({
                        "year": year,
                        "value": values.get(year)
                    })

        return render_template("country.html", country=country, indicators=indicators, data_series=results, years=years)
    else:
        return redirect("/")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/compare")
def compare():
    return render_template("compare.html", valid_indicators=codes.keys())

@app.route("/compare/country", methods=["GET", "POST"])
def compare_countries():
    if request.method == "POST":
        countries = []
        # why not make range be inclusive? Would be so awesome
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
        # despite the ThreadPoolExecutor, it is still necessary to limit things here
        if len(countries) * len(indicators) > Max_work_load:
            return redirect("/compare")
        
        start_year = int(start_year)
        end_year = int(end_year)
        
        if start_year > end_year or start_year < 1960 or end_year > datetime.now().year - 2:
            return redirect("/compare")

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
                    data_series[country_code][indicator].append({
                        "year": year,
                        "value": values.get(year)
                    })

        return render_template("compare_countries.html", countries=countries, indicators=indicators, data_series=data_series, years=years)
    else:
        return redirect("/compare")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
