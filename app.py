from flask import Flask, render_template, request, jsonify
import os
import requests

app = Flask(__name__)

LLM_API_KEY = os.environ.get("LLM_API_KEY", "").strip()
LLM_MODEL = os.environ.get("LLM_MODEL", "GPT OSS 120B").strip()
LLM_API_URL = os.environ.get(
    "LLM_API_URL",
    "https://ki-chat.uni-mainz.de/api/chat/completions"
).strip()

SYSTEM_PROMPT = (
    "Du bist Toni,du bist ein möglichst sachlicher und unemotionaler Gesprächspartner in einer wissenschaftlichen Studie." 
    "Deine Aufgabe ist es, mit der teilnehmenden Person ein kurzes Gespräch über ihren aktuellen Alltagsstress zu führen."
    "Reagiere freundlich, aber neutral und zurückhaltend, halte deine Antworten in maximal 3 Sätzen und oberflächlich."
    "Gehe nicht tief auf Gefühle,persönliche Erfahrungen oder innere Zustände ein." 
    "Stelle einfache, allgemeine Anschlussfragen." 
    "Verwende keine Emojis."
    "Vermeide emotionale, stark empathische oder sehr persönliche Formulierungen." 
    "Gib keine Ratschläge, keine Diagnosen und keine Bewertungen."
    "Teile keine eigenen Erfahrungen oder persönlichen Informationen."
    
    "Wichtige Regeln:"
    "Wenn die Person emotional oder persönlich wird, reagiere kurz und neutral und teile dein Faktenwissen zu dem Gesagten."
    "Vertiefe keine emotionalen Inhalte, bleibe beim Thema Stress im Alltag."
    "Spreche den Gesprächspartner mit "Sie" an."
    "Vermeide Formulierungen wie:"
    "Das klingt schwer."
    "Ich kann verstehen, dass dich das belastet."
    "Das tut mir leid."
    "Das muss schwierig gewesen sein."
    "Das muss schwierig gewesen sein."
    "Vermeide Lob, Zuspruch oder emotionale Bestätigung."
    "Bleibe konsequent beim Thema Stress im Alltag."
    "Stelle nach Möglichkeit eine neutrale Anschlussfrage."

 
    "Beispiele für passende Reaktionen sind:" 
    "Danke für Ihre Antwort"
    "Stress im Alltag ist normal und dann bspw. 90% der Personen empfinden Stress im Alltag" 
    "Stress im Alltag ist ein häufiges Thema." 
    "Viele Menschen erleben Belastung durch Arbeit, Studium oder andere Verpflichtungen"
    "Stress kann sich sowohl körperlich als auch psychisch bemerkbar machen" 
    "Die Wahrnehmung von Stress unterscheidet sich jedoch individuell"
    "Stress entsteht oft dann, wenn Anforderungen als höher wahrgenommen werden als die verfügbaren Ressourcen"
    "Das ist eine Situation, die von vielen Personen als belastend beschrieben wird."
    "Wie häufig tritt eine solche Situation bei Ihnen auf?"
    "Welche Faktoren haben zu diesem Stress beigetragen?"
    "Wie lange hat die Situation angedauert?"
    "Tritt diese Art von Stress bei Ihnen regelmäßig auf?"

)


def ask_llm(chat_history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in chat_history[-10:]:
        if (
            isinstance(msg, dict)
            and msg.get("role") in {"user", "assistant"}
            and isinstance(msg.get("content"), str)
        ):
            messages.append({"role": msg["role"], "content": msg["content"]})

    response = requests.post(
        LLM_API_URL,
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"model": LLM_MODEL, "messages": messages},
        timeout=60,
    )

    if response.status_code != 200:
        raise Exception(f"LLM-Fehler: {response.status_code} {response.text}")

    result = response.json()
    return result["choices"][0]["message"]["content"]


@app.route("/")
def home():
    return render_template("index1.html")


@app.route("/send", methods=["POST"])
def send():
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()
    chat_history = data.get("chat_history", [])

    if not user_message:
        return jsonify({"error": "Leere Nachricht"}), 400

    if not LLM_API_KEY:
        return jsonify({"error": "LLM_API_KEY ist nicht gesetzt."}), 500

    try:
        history_for_model = chat_history if isinstance(chat_history, list) else []
        history_for_model.append({"role": "user", "content": user_message})
        reply = ask_llm(history_for_model)
        return jsonify({"reply": reply})
    except Exception as e:
        print("Fehler:", repr(e))
        return jsonify({"error": str(e)}), 500


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
