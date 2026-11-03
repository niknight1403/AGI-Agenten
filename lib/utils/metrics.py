def calculate_agi_metrics(history):
    if not history:
        return {"cycles": 0, "avg_score": None, "trend": "keine Daten", "best_cycle": None}
    scores = [float(x["score"]) for x in history]
    avg = round(sum(scores) / len(scores), 2)
    trend = "steigend" if scores[-1] > scores[0] else ("fallend" if scores[-1] < scores[0] else "stabil")
    index = max(range(len(scores)), key=lambda i: scores[i])
    return {"cycles": len(history), "avg_score": avg, "trend": trend, "best_cycle": history[index].get("cycle", index + 1)}
