from datetime import datetime
import pytz

class PersonalityMatrix:
    def __init__(self):
        self.timezone = pytz.timezone('US/Central') # He lives in Texas mostly

    def get_biological_factor(self):
        """
        Calculates probability based on his sleep schedule.
        """
        now = datetime.now(self.timezone)
        hour = now.hour

        # The "Vampire Window": He is often awake late, but sleeps 3am-9am
        if 3 <= hour < 9:
            return {"factor": 0.1, "status": "Likely Sleeping"}
        elif 9 <= hour < 12:
            return {"factor": 0.6, "status": "Waking Up / Doomscrolling"}
        elif 22 <= hour <= 23 or 0 <= hour < 3:
            return {"factor": 1.5, "status": "Late Night Grind / Ranting"}
        else:
            return {"factor": 1.0, "status": "Active Hours"}

    def get_meme_index(self):
        """
        Does today have 'Meme Potential'?
        """
        today = datetime.now()
        multiplier = 1.0
        events = []

        # 1. Date Check (4/20, 6/9, Halloween, etc)
        if today.month == 4 and today.day == 20:
            multiplier += 0.5
            events.append("4/20 (Meme Holiday)")
        if today.month == 6 and today.day == 9:
            multiplier += 0.5
            events.append("6/9 (Meme Holiday)")
        
        # 2. Crypto Check (Simulated)
        # If BTC is breaking ATH, he tweets.
        # (In a full build, this would link to Module 3)
        
        # 3. Day of Week Logic (Data shows he tweets MORE on weekdays now)
        if today.weekday() < 5: # Mon-Fri
            multiplier += 0.2
            events.append("Workday Variance")

        return {
            "multiplier": multiplier,
            "triggers": events
        }
