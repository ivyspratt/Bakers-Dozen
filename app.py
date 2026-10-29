from flask import Flask, jsonify, request, send_from_directory

from ai_helper import get_top_recipes

app = Flask(__name__)

@app.route("/api/recipes")
def recipes():
    ingredients = request.args.get("ingredients", "").strip()
    if not ingredients:
        return jsonify({"error": "Please enter at least one ingredient."}), 400
    return jsonify(get_top_recipes(ingredients))