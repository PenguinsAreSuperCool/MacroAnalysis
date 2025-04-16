from flask import Flask, render_template, request, redirect
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
codes = {
        "gdp": "NY.GDP.MKTP.CD",
        "inflation": "FP.CPI.TOTL.ZG",
        "gdp_per_capita": "NY.GDP.PCAP.CD",
        "gdp_growth": "NY.GDP.MKTP.KD.ZG",
        "unemployment": "SL.UEM.TOTL.ZS",
        "literacy_rate": "SE.ADT.LITR.ZS",
        "life_expectancy": "SP.DYN.LE00.IN",
        "population": "SP.POP.TOTL",
        "population_growth": "SP.POP.GROW",
        "poverty_rate": "SI.POV.DDAY",
        "gini_index": "SI.POV.GINI",
        "hdi": "SP.POP.TOTL",
        "happiness_index": "SP.POP.TOTL",
        "corruption_index": "SP.POP.TOTL",
        "environmental_quality": "SP.POP.TOTL",
        "internet_usage": "IT.NET.USER.ZS",
        "energy_consumption": "EG.USE.PCAP.KG.OE",
        "electricity_access": "EG.ELC.ACCS.ZS",
        "renewable_energy": "EG.FEC.RNEW.ZS",
        "carbon_emissions": "EN.ATM.CO2E.KT",
        "water_quality": "SP.POP.TOTL",
        "air_quality": "SP.POP.TOTL",
        "biodiversity": "SP.POP.TOTL",
        "waste_management": "SP.POP.TOTL",
        "transportation": "SP.POP.TOTL",
        "education": "SP.POP.TOTL",
        "healthcare": "SP.POP.TOTL",
        "infrastructure": "SP.POP.TOTL",
        "tourism": "ST.INT.ARVL",
        "foreign_investment": "BX.KLT.DINV.CD",
        "trade_balance": "NE.RSB.GNFS.CD",
        "foreign_aid": "DT.ODA.ALLD.CD",
        "debt": "DT.DOD.DECT.CD",
        "stock_market": "CM.MKT.LCAP.CD",
        "interest_rate": "FR.INR.LEND"
    }

@app.route("/")
def index():
    return render_template("index.html", valid_indicators=codes.keys())

def get_data(data_to_get, country_code, years):
    data_indicator = codes.get(data_to_get)
    try:
        start = min(years)
        end = max(years)
        url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{data_indicator}?format=json&per_page=100&date={start}:{end}"
        headers = {
            "User-Agent": "DeepA lupchinskileonardo@gmail.com"
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
        if not country or not start_year or not end_year or not indicators:
            return redirect("/")
        print(f"Looking for country code: input='{country}'")
        if not start_year.isdigit() or not end_year.isdigit():
            print("The issues was year")
            return redirect("/")
        if len(indicators) > 10:
            print("The issues was indicator")
            return redirect("/")
        start_year = int(start_year)
        end_year = int(end_year)
        if ((start_year) > (end_year)) or ((start_year) < 1960) or ((end_year) > datetime.now().year - 2):
            return redirect("/")
        country_code = country.upper()
        
        years = list(range(start_year, end_year + 1))
        # insteresting solution to make this viable
        # when not using ThreadPoolExecutor, the code took ages to run!
        # API calls are made in parallel now, which makes it much faster!
        # limiting the indicators and years is still necessary, though.
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


app.run(debug=True)