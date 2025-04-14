from flask import Flask, render_template, request, redirect
import requests

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

def get_gdp(country_code):
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD?format=json&per_page=1"
    headers = {
        "User-Agent": "DeepA lupchinskileonardo@gmail.com"
    }
    response = requests.get(url, headers=headers)
    response = response.json()
    gdp = response[1][0]["value"]
    return gdp

def get_inflation(country_code):
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/FP.CPI.TOTL.ZG?format=json&per_page=1"
    headers = {
        "User-Agent": "DeepA lupchinskileonardo@gmail.com"
    }
    response = requests.get(url, headers=headers)
    response = response.json()
    inflation = response[1][0]["value"]
    return inflation

def get_unemployment(country_code):
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/SL.UEM.TOTL.ZS?format=json&per_page=1"
    headers = {
        "User-Agent": "DeepA lupchinskileonardo@gmail.com"
    }
    response = requests.get(url, headers=headers)
    response = response.json()
    unemployment = response[1][0]["value"]
    return unemployment
    


@app.route("/country", methods=["GET", "POST"])
def country():
    if request.method == "POST":
        country = request.form.get("country")
        if not country:
            return redirect("/")
        country_code = get_country_code(country)
        gdp = get_gdp(country_code)
        inflation = get_inflation(country_code)
        unemployment = get_unemployment(country_code)
        return render_template("country.html", gdp=gdp, country=country, inflation=inflation, unemployment=unemployment)
    else:
        redirect("/")


app.run(debug=True)