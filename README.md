[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
# Neerslag App
Neerslag app for Home Assistant. All-in-one package (Sensors + Card).

Display rain forecast using Buienalarm and/or Buienradar sensor data. The Neerslag App (and the sensors) is fully configurable via the Home Assistant interface. 

> This package contains the Neerslag Card. Make sure to uninstall this from Home Assistant before using the Neerslag App, to avoid unexpected behaviour. This includes manually removing the custom sensors.

## Features
* Everything from the Neerslag Card;
* Built-in Buienalarm and Buienradar sensors;
* Ability to configure this app via the GUI;
* Can use build-in Home Assistant configured location.

![Example](https://github.com/aex351/home-assistant-neerslag-app/raw/main/documentation/example.png)

## Installation overview
1) Install via HACS or manual;
2) Configure the Neerslag App (via interface)
2) Add the Neerslag Card to your dashboard

## 1a. Install via HACS (recommended)
This is the recommended option and also allows for easy updates.
1) Add this repository to HACS;
2) Add the Neerslag App in the Home Assistant Community Store;
3) Add the Neerslag App as an Integration in Home Assistant (config/integration).

For updates go to the Community Store (HACS) and click update

## 2 Configure the Neerslag App (via interface)
The Neerslag App is fully configurable via the interface. Go to `config/integrations` and click on options. Select which sensor you want to use and provide the location data. There is an option to use the built-in Home Assistant location data. If this checkbox is selected, it will override the location settings of the individual sensors.

## 3b. Manual install
Not recommended, you will need to track updates manually by browsing to the repository;
1) Download the latest release of the Neerslag App from this repository;
2) In Home Assistant, create a folder `config/custom_components`;
3) Add the Neerslag App to the `custom_components` folder.;
4) Restart Home Assistant
5) Add the Neerslag App as an Integration in Home Assistant (config/integration).

For updates, repeat step 1 to 4. Home Assistant will not delete any configuration.

## 3b. Add the Neerslag Card to your Dashboard
1) Go to your dashboard, go to configure, and click `add card`
2) Find the Neerslag Card in the list of cards
3) Add the card and configure the card.

### Using one sensor:
```yaml
type: 'custom:neerslag-card'
title: Neerslag
entity: sensor.neerslag_buienalarm_regen_data
```
### Using two sensors:
```yaml
type: 'custom:neerslag-card'
title: Neerslag
entities:
  - sensor.neerslag_buienalarm_regen_data
  - sensor.neerslag_buienradar_regen_data
  ```
> Note: If Home Assistant has not yet received data from the sensors, the card can remain blank.

