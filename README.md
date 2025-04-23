# MacroAnalysis
### Video Demo: https://youtu.be/QDYxbKutPuQ
### Description:

**MacroAnalysis** is a CS50 final project designed to allow users to easily see and compare almost every major macroeconomic indicator for nearly every country in the world.
All data is directly from the **World Bank**. Forecasts are from the **OECD**. Due to resource limitations, the OECD forecasting is disabled but all implemented.

## Key Features

- **Interactive world map** for country selection
- **Dynamic line graphs**
- **Support for comparing multiple indicators and countries**
- **Dark-themed UI**, as that should be the default
- **Real-time economic data**

## How it works:

First the user goes to a homepage, where there is a dynamic background, and a few buttons.
The dynamic background was the first challenge because of the non-existence of so wide gifs of good quality. Although I read that it is not ideal, I decided to go forward with a .mp4 video that keeps playing on loop. This is sometimes noticeable if the user's internet is slow or if the server takes too long to respond.

The first one leads to user to a map where they can select a country to see economic data from. There are many indicators the user can choose from, but by default the website shows the ones I considered most significant – GDP, GDP per capita, inflation, and unemployment. There are, however, more than 40 types of data the user can choose from.
Also included is a text search feature that can handle country names and their different spellings (such as US and United States returning the same country). Finally, there is a button for people that make dubious decisions (I leave the user to find out what that does) and buttons to return to the homepage or the compare countries feature (more on that below).

The second button leads to a similar page as before but now allowing many countries to be selected. The idea is to allow the user to compare data from multiple countries (I also added a maximum workload for this function in specific to stop the website from crashing because of a ridiciously high request; the maximum workload is currently 100 API calls).

The page that the user sees after finishing to choose countries to see data from is fairly similar for both the individual and multiple countries features. It shows all the data in a graph structure. The graph also is resizable, draggable, and comes with the option to zoom in, zoom out, isolate a group of data, and more. At the bottom of the page is a feature that allows users to toggle a grid view to visualize things more compactly.

The third leads to the youtube video explaning the usage (the same in the link above).

The fourth is an about page that talks about the creator and gives credit to the wonderful opportunities I received.

The fifth and last leads the user to the scratch project I did in the week 0 of CS50. The project is a dancing game with multiple characters and increasing difficulty.

The challenges of implementing this project was mainly the speed. Implementing ThreadPoolExecutor was crucial to make things speedy. Sadly, the forecasting by OECD wasn't possible even with ThreadPoolExecutor. The reason for that, as I see it, is because the OECD API returns a giant value everytime it is contacted. However, the implementation in code seems to be all correct and could be used just be deleting the commented aspect of it. Were this project to run on a better server, I'm confident the MacroAnalyis tool could be even more useful.

To go around this problem, I even tried to do data fetching client-side, but that didn't work because of CORS issues. I'm really limited by the technology of my time.


The website can be accessed in https://MacroAnalysis.app

