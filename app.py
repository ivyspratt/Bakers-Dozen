from flask import Flask, jsonify, request, send_from_directory

from ai_helper import get_ranked_recipes, get_suggestions, TRUSTED_SITES

app = Flask(__name__) # creates the web server

PAGE_SIZE = 5

@app.route("/") # when someone opens the home address, it sends it to index.html    
def home(): 
    return send_from_directory(app.root_path, "index.html")  

@app.route("/api/recipes") # the address the page calls. reads ingredients from the address, runs the top recipes, sends results back as JSON
def recipes():
    ingredients = request.args.get("ingredients", "").strip()[:200]
    if not ingredients:
        return jsonify({"error": "Please enter at least one ingredient."}), 400 # tells you the page request was bad
    page = max(request.args.get("page", 0, type=int), 0)

    ranked = get_ranked_recipes(ingredients)
    start = page * PAGE_SIZE
    return jsonify({
        "recipes": ranked[start:start + PAGE_SIZE],
        "has_more": start + PAGE_SIZE < len(ranked),
        "total": len(ranked),
    })

@app.route("/api/suggestions")
def suggestions():
    ingredients = request.args.get("ingredients", "").strip()[:200]
    return jsonify(get_suggestions(ingredients))

@app.route("/api/sites")
def sites():
    return jsonify([{"name": n, "url": u} for n, u in TRUSTED_SITES.items()])

if __name__ == "__main__":
    app.run(debug=True)