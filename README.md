# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

My version will prioritize content-based filtering (accustic and musical attributes of the song), along with using behavioral data (from users) in order to decide what songs to reccomend. We can assume that if they make a paylist they would like each song to match the vibe, thus a slow song should be recommended if the music in that playlist are also slow. Same with high energy songs, and because not every song of a single ganre is alike. We can still allow them to give behavioral input and get recommended something different that they might enjoy. Which leads me to approach with a Hybrid system upon more reflection. Since it will mix attributes. This will fit for a future work section perhaps, since it is a little ambitious for this project.

## How The System Works

Explain your design in plain language.

Some prompts to answer:

- What features does each `Song` use in your system
  - For example: genre, mood, energy, tempo
  Under song we would put in data such as its ID, name, the creator and the descriptions that the algorithm will use to sort and organize where it compares with other songs
- What information does your `UserProfile` store
The UserProfile stores the data about the user that profiles what music they listen to the most, their taste, and allows the algorithm to recommend based on current taste as well as direct user data such as hours listened to genre, or spent listening to a specific mood.
- How does your `Recommender` compute a score for each song
The recommender computes a score fore each song based on
-Energy
-Valence Procimity
-Mood
-Genre Match
-And Acousticness 

the Final Score is the Weighted Sum
- How do you choose which songs to recommend

You can include a simple diagram or bullet list if helpful.

All 18 songs are sorted by score, highest to lowest
The top k are returned (default k=5)
Ties are broken by sort order (stable sort — earlier in the CSV wins)


---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
Energy - High vs Low energy song. 
Emotional tone - Is the songs emotional brightness close to what the mood suggest.
Mood - How similar is the songs mood to the users
Genre- Does the song belong to the genre?
Acousticness - Is the song as acoustic or electronic as user wants.
- What information about the user does it use
The system uses favorite genre, favorite mood, target energy and target accoustiness in order to personalize the users experience and link them to the song data.
- How does it turn those into a number
Energy Proximity - Subtracts the difference between songs energy and the target. A perfect match = 35
Valence Prox - Same idea but for emotional brightness
Mood Similarity - Every mood sits at a position on an invisible mao defeined y energy and emotion
Ganre match - yes or no, is it the correct genre. if not, then 0 points earned.
Acousticness - Same as energy, worth 5 points

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

