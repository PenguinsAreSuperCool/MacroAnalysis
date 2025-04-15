from flask import Flask, render_template, request, redirect
import requests
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

def get_country_code(country):
    country.capitalize()
    country_codes = {
        "United States": "US",
        "Canada": "CA",
        "Mexico": "MX",
        "Brazil": "BR",
        "Argentina": "AR",
        # TODO Add more country codes
    }
    return country_codes[country]

def get_gdp(country_code, year):
    try:
        url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD?format=json&per_page=1&date={year}"
        headers = {
            "User-Agent": "DeepA lupchinskileonardo@gmail.com"
        }
        response = requests.get(url, headers=headers)
        response = response.json()
        gdp = response[1][0]["value"]
        if gdp is None:
            return get_gdp(country_code, year - 1)
        return gdp
    except TypeError:
        # handling TypeErrors recursively. Are you proud Yuliia??
        return get_gdp(country_code, year - 1)

def get_inflation(country_code, year):
    try:
        url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/FP.CPI.TOTL.ZG?format=json&per_page=1&date={year}"
        headers = {
            "User-Agent": "DeepA lupchinskileonardo@gmail.com"
        }
        response = requests.get(url, headers=headers)
        response = response.json()
        inflation = response[1][0]["value"]
        if inflation is None:
            return get_inflation(country_code, year - 1)
        return inflation
    except TypeError:
        # handling TypeErrors recursively again.
        return get_inflation(country_code, year - 1)

def get_gdp_per_capita(country_code, year):
    try:
        url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.PCAP.CD?format=json&per_page=1&date={year}"
        headers = {
            "User-Agent": "DeepA lupchinskileonardo@gmail.com"
        }
        response = requests.get(url, headers=headers)
        response = response.json()
        gdp_per_capita = response[1][0]["value"]
        if gdp_per_capita is None:
            return get_gdp_per_capita(country_code, year - 1)
        return gdp_per_capita
    except TypeError:
        # handling TypeErrors recursively and again.
        return get_gdp_per_capita(country_code, year - 1)
    


@app.route("/country", methods=["GET", "POST"])
def country():
    if request.method == "POST":
        country = request.form.get("country")
        if not country:
            return redirect("/")
        country_code = get_country_code(country)
        year = datetime.now().year
        gdp = get_gdp(country_code, year)
        inflation = get_inflation(country_code, year)
        gdp_per_capita = get_gdp_per_capita(country_code, year)
        return render_template("country.html", gdp=gdp, country=country, inflation=inflation, gdp_per_capita=gdp_per_capita)
    else:
        redirect("/")


app.run(debug=True)