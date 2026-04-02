# **Moxfield Deck Tagger**

An app that helps you categorize and analyze Moxfield decks based on their composition.

![ezgif-84813d49a15f19b1](https://github.com/user-attachments/assets/e41ac651-4050-465a-bd96-181cdd8469b3)


Built mainly for EDH decks, but it works with any Moxfield list.

For cards that have been automatically tagged incorrectly, the user can manually correct the card's tags and then train the local machine learning model.

## **Commander Deckbuilding Template**


<img width="1717" height="894" alt="image" src="https://github.com/user-attachments/assets/d5b23812-05ab-4207-bc8b-42104b357b1c" />

Source: [Command Zone](https://www.youtube.com/@commandcast)


This tool does NOT handle categories like "win conditions" or "game plan" since those vary heavily on commander.

Example usage of deck getting categorized:

<img width="759" height="552" alt="image" src="https://github.com/user-attachments/assets/07cfd146-3cca-4983-9a83-d5563898f54d" />


## **Machine Learning Feedback Loop**

For cards that are tagged incorrectly, the user can correct tags manually:

The model predicts tags for each card
You can manually correct tags inside the UI
Corrections are saved as new training data
You can retrain the model directly in the app

Over time, the model becomes more accurate and personalized based on real usage.

<img width="769" height="508" alt="image" src="https://github.com/user-attachments/assets/87a6d9ad-35b0-49bd-bbbd-f05e7a173f3c" />

The model gets merged with the current model being used when retrain is clicked, then it is downloaded to your machine. You can upload and change the model you would like to use.

<img width="759" height="170" alt="image" src="https://github.com/user-attachments/assets/39eba30a-94f0-4bcc-9268-bc1a3a430eee" />



## **Local Setup:**
Getting this running on your local machine isn't the easiest mainly cause of the selenium scraping but working on text import to alievate that, but if you want to get it running heres how:

**1. Clone the repo** 
```
git clone <your-repo-url>
cd <repo-name>
```

**2. Install dependencies**
Make sure you have Python installed (3.10+), then run:
```
pip install -r requirements.txt
```
**3. Install ChromeDriver**

This app uses Selenium to scrape Moxfield, so you need ChromeDriver.

Download ChromeDriver:
https://chromedriver.chromium.org/downloads
Make sure it matches your Chrome version
Set the path in config.py:
```
CHROMEDRIVER_PATH = "path/to/chromedriver.exe"
```

**4. Run the app**
Run the app manually in command line with:
```
streamlit run app.py
```
or run the batch file.
