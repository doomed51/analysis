# Overview

Suite of scripts for quick and dirty analysis of securities  

### How to run:

1. Install requirements.txt 
3. Configure main.py to run the analyses you want, current supported analyses 
   - seasonality 
   - momentum / momentum crossover 
2. Run with 
   - python main.py <symbol>
   - python volMonitor.py 

**Note**: Requires locally stored ohlc and term structure data. To download and store data see ![here](https://github.com/doomed51/saveHistoricalData) 


## Screenshots
#### Seasonality
![Seasonality Overview](https://github.com/doomed51/analysis/blob/main/screenshots/analysis_seasonal-overview.JPG)
#### Momentum signal 
![Momo Overview](https://github.com/doomed51/analysis/blob/main/screenshots/analysis_momoOverview.JPG)
#### Volatility Monitor
![Volatility Monitor](https://github.com/doomed51/analysis/blob/main/screenshots/analysis_termStructureMonitor.JPG)

## Structure

Built loosely on component based architecture principles. Directory structure: 

- **core**: core classes for implementing analysis, returns plots  
- **impl**: analysis implementations utilizing core classes 
- **returns**: plots simulated returns of a given strategy implementation 
- **interface**: Handles interactions with local DBs and any external APIs   
- **utils**: Helper functions to standardize calculations across the system   
