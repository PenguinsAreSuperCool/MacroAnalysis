# MacroAnalysis
### Video Demo: https://youtu.be/QDYxbKutPuQ
### Description:

**MacroAnalysis** is a CS50 final project designed to allow users to easily see and compare almost every major macroeconomic indicator for nearly every country in the world.
All data is directly from the **World Bank**. Forecasts are from the **IMF**. 

## Key Features

- **Interactive world map** for country selection
- **Dynamic line graphs**
- **Support for comparing multiple indicators and countries**
- **Dark-themed UI**, as that should be the default
- **Real-time economic data**
- **Forecasting**
- **Ranking**

## How it works:

The project functions as a complete tool for Macroeconomic analysis by combining tens of indicators from the World Bank, uniting them with IMF forecasts, and showing them in a compeling, easy to interpret way for the user. The main features and how they work are:

1. A Map that allows users to select a country from there, which was made by combining two different API for highligting and rendering;
2. a smart searchbox that allows users to search a country by name, accepting things like US, U.S., United States, United States of America, etc.; 
3. Support for many World Bank indicators randing from GDP to Forest Area, which was only possible by using a ThreadPoolExecutor to speed things up;
4. Rezizable, draggable, interactive graphs to visualize data intuitively, which was made using plotly API and JavaScript;
5. Support for comparing multiple data from different countries;
6. Support for identifying correlation between indicators from the same country or different countries;
7. and finally, a ranking system for any indicator from the World Bank.

   

The website can be accessed in https://MacroAnalysis.app

