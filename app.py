from flask import Flask, jsonify, request, send_from_directory

from ai_helper import get_top_recipes

app = Flask(__name__) # creates the web server

@app.route("/") # when someone opens the home address, it sends it to index.html    
def home():
    return send_from_directory(app.root_path, "index.html")  

@app.route("/api/recipes") # the address the page calls. reads ingredients from the address, runs the top recipes, sends results back as JSON
def recipes():
    ingredients = request.args.get("ingredients", "").strip()
    if not ingredients:
        return jsonify({"error": "Please enter at least one ingredient."}), 400 # tells you the page request was bad
    return jsonify(get_top_recipes(ingredients))

if __name__ == "__main__":
    app.run(debug=True)