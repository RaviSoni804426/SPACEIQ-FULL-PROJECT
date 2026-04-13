try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:
    SentimentIntensityAnalyzer = None


POSITIVE_WORDS = {"great", "clean", "best", "amazing", "good", "perfect", "love", "loved"}
NEGATIVE_WORDS = {"bad", "poor", "dirty", "late", "broken", "slow", "worst", "issue"}
_analyzer = SentimentIntensityAnalyzer() if SentimentIntensityAnalyzer else None



def analyze(text: str) -> dict:
    if _analyzer:
        scores = _analyzer.polarity_scores(text)
        compound = scores["compound"]
        if compound >= 0.05:
            label = "positive"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"
        return {
            "compound": round(compound, 4),
            "label": label,
            "pos": round(scores["pos"], 4),
            "neg": round(scores["neg"], 4),
            "neu": round(scores["neu"], 4),
        }

    words = {word.strip(".,!?").lower() for word in text.split()}
    score = len(words & POSITIVE_WORDS) - len(words & NEGATIVE_WORDS)
    compound = max(-1.0, min(1.0, score / 3))
    label = "positive" if compound > 0 else "negative" if compound < 0 else "neutral"
    return {"compound": round(compound, 4), "label": label, "pos": 0.0, "neg": 0.0, "neu": 1.0}
